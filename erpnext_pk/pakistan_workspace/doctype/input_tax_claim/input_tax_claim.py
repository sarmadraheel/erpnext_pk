# Copyright (c) 2026, ParaLogic and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, formatdate, getdate, today

STATUSES = ("Unclaimed", "Claimed", "Expired", "Expensed")


class InputTaxClaim(Document):
	def validate(self):
		self.set_invoice_details()
		self.validate_amount()
		self.validate_status_and_claim_date()
		self.validate_not_over_claimed()

	def set_invoice_details(self):
		if not self.purchase_invoice:
			return

		invoice = frappe.db.get_value(
			"Purchase Invoice",
			self.purchase_invoice,
			["docstatus", "is_return", "company", "supplier", "supplier_name", "bill_no", "posting_date"],
			as_dict=True,
		)
		if not invoice:
			frappe.throw(_("Purchase Invoice {0} does not exist").format(frappe.bold(self.purchase_invoice)))
		if invoice.docstatus != 1:
			frappe.throw(_("Purchase Invoice {0} must be submitted").format(frappe.bold(self.purchase_invoice)))
		if invoice.is_return:
			frappe.throw(
				_("Purchase Invoice {0} is a return. Input tax is tracked on the original invoice.").format(
					frappe.bold(self.purchase_invoice)
				)
			)

		self.company = invoice.company
		self.supplier = invoice.supplier
		self.supplier_name = invoice.supplier_name
		self.bill_no = invoice.bill_no
		self.invoice_date = invoice.posting_date
		self.company_currency = frappe.get_cached_value("Company", invoice.company, "default_currency")

		# tax_strn is a custom field added by this app on Supplier
		if frappe.get_meta("Supplier").has_field("tax_strn"):
			self.supplier_strn = frappe.db.get_value("Supplier", invoice.supplier, "tax_strn")

	def validate_amount(self):
		if flt(self.input_tax_amount) <= 0:
			frappe.throw(_("Input Tax Amount must be greater than zero"))

	def validate_status_and_claim_date(self):
		if self.status not in STATUSES:
			frappe.throw(_("Status must be one of: {0}").format(", ".join(STATUSES)))

		if self.status != "Claimed":
			self.claim_date = None
			return

		if not self.claim_date:
			frappe.throw(_("Date of Claim is required when the status is Claimed"))
		if getdate(self.claim_date) > getdate(today()):
			frappe.throw(_("Date of Claim cannot be in the future"))
		if self.invoice_date and getdate(self.claim_date) < getdate(self.invoice_date):
			frappe.throw(
				_("Date of Claim cannot be before the invoice date {0}").format(formatdate(self.invoice_date))
			)

	def validate_not_over_claimed(self):
		invoice_tax = calculate_invoice_input_tax(self.purchase_invoice)
		if not invoice_tax:
			# The invoice has no sales tax lines we can recognise, so there is nothing to compare against
			return

		other_amounts = frappe.get_all(
			"Input Tax Claim",
			filters={"purchase_invoice": self.purchase_invoice, "name": ["!=", self.name or ""]},
			pluck="input_tax_amount",
		)
		total = flt(sum(flt(d) for d in other_amounts)) + flt(self.input_tax_amount)
		if flt(total - invoice_tax, self.precision("input_tax_amount")) > 0:
			frappe.throw(
				_("Input tax recorded for Purchase Invoice {0} ({1}) exceeds the tax on the invoice ({2})").format(
					frappe.bold(self.purchase_invoice),
					frappe.format_value(total, {"fieldtype": "Currency", "options": self.company_currency}),
					frappe.format_value(invoice_tax, {"fieldtype": "Currency", "options": self.company_currency}),
				)
			)


def get_input_tax_accounts(company=None):
	"""Accounts that hold claimable input sales tax.

	Taken from Pakistan Workspace Settings; if none are listed, the company's Sales Tax Account is used.
	"""
	accounts = frappe.get_all(
		"Input Tax Account",
		filters={"parent": "Pakistan Workspace Settings", "parenttype": "Pakistan Workspace Settings"},
		pluck="account",
	)
	if not accounts and company:
		account = frappe.get_cached_value("Company", company, "sales_tax_account")
		accounts = [account] if account else []
	return set(accounts)


def calculate_invoice_input_tax(purchase_invoice):
	"""Input tax on a Purchase Invoice, in company currency.

	This is the total of the tax lines that add to the invoice and post to one of the input sales tax accounts.
	"""
	if not purchase_invoice:
		return 0.0

	company = frappe.db.get_value("Purchase Invoice", purchase_invoice, "company")
	tax_accounts = get_input_tax_accounts(company)
	if not tax_accounts:
		return 0.0

	taxes = frappe.get_all(
		"Purchase Taxes and Charges",
		filters={"parent": purchase_invoice, "parenttype": "Purchase Invoice", "add_deduct_tax": "Add"},
		fields=["account_head", "base_tax_amount_after_discount_amount"],
	)
	return flt(sum(flt(d.base_tax_amount_after_discount_amount) for d in taxes if d.account_head in tax_accounts))


@frappe.whitelist()
def get_invoice_details(purchase_invoice: str):
	frappe.has_permission("Purchase Invoice", "read", doc=purchase_invoice, throw=True)

	company = frappe.db.get_value("Purchase Invoice", purchase_invoice, "company")
	return {
		"input_tax_amount": calculate_invoice_input_tax(purchase_invoice),
		"company": company,
		"company_currency": frappe.get_cached_value("Company", company, "default_currency") if company else None,
	}
