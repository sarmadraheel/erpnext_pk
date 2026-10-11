"""Correct the sales tax description on "Sales Tax + Further Tax" templates.

Earlier versions always wrote "Sales Tax @ 17%" even when the account's tax rate (and therefore the rate
actually applied) was different, for example 18%. This makes the description follow the real rate.
"""

import frappe

TEMPLATE_TITLE = "Sales Tax + Further Tax"
STALE_DESCRIPTION = "Sales Tax @ 17%"


def execute():
	templates = frappe.get_all("Sales Taxes and Charges Template", filters={"title": TEMPLATE_TITLE}, pluck="name")

	fixed = 0
	for template in templates:
		rows = frappe.get_all(
			"Sales Taxes and Charges",
			filters={"parent": template, "parenttype": "Sales Taxes and Charges Template", "description": STALE_DESCRIPTION},
			fields=["name", "rate"],
		)
		for row in rows:
			rate = row.rate or 0
			if rate and rate != 17:
				frappe.db.set_value(
					"Sales Taxes and Charges",
					row.name,
					"description",
					f"Sales Tax @ {rate:g}%",
					update_modified=False,
				)
				fixed += 1

	print(f"erpnext_pk: corrected {fixed} sales tax description(s)")
