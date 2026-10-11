"""Copy NTN / NIC / STRN numbers from site-specific legacy fields into the erpnext_pk fields.

The Annexure C report reads ``tax_ntn``, ``tax_nic`` and ``tax_strn`` from Sales Invoice, which are fetched
from Customer and Company. Sites that already stored these numbers in their own custom fields (for example
``Customer.ntn``, ``Customer.nic``, ``Supplier.custom_strn``) need that data copied across once, and
submitted transactions need the numbers back-filled because fetch_from only runs on new documents.

The patch is idempotent and never overwrites a value that is already set. Run it again at any time, for
example after filling in the Company NTN/STRN:

	bench --site [site name] execute erpnext_pk.patches.v16.migrate_legacy_tax_fields.execute
"""

import re

import frappe

NIC_RE = re.compile(r"^.....-.......-.$")
NTN_RE = re.compile(r"^.......-.$")
STRN_RE = re.compile(r"^..-..-....-...-..$")

# {doctype: {legacy fieldname: erpnext_pk fieldname}}
LEGACY_FIELDS = {
	"Customer": {"nic": "tax_nic", "ntn": "tax_ntn"},
	"Supplier": {"custom_strn": "tax_strn"},
}

TRANSACTION_DOCTYPES = ["Sales Invoice", "Sales Order", "Delivery Note", "POS Invoice"]

# (master doctype, link field on the transaction, {master fieldname: transaction fieldname})
TRANSACTION_SOURCES = [
	("Customer", "customer", {"tax_nic": "tax_nic", "tax_ntn": "tax_ntn", "tax_strn": "tax_strn"}),
	("Company", "company", {"tax_ntn": "company_tax_ntn", "tax_strn": "company_tax_strn"}),
]


def normalize_ntn(value):
	value = re.sub(r"[^A-Z0-9]", "", str(value).upper())
	if len(value) >= 7:
		value = value[:7] + "-" + value[7:]
	return value


def normalize_nic(value):
	value = re.sub(r"[^0-9]", "", str(value))
	if len(value) >= 12:
		value = value[:12] + "-" + value[12:]
	if len(value) >= 5:
		value = value[:5] + "-" + value[5:]
	return value


def normalize_strn(value):
	value = re.sub(r"[^A-Z0-9]", "", str(value).upper())
	if len(value) >= 11:
		value = value[:11] + "-" + value[11:]
	if len(value) >= 8:
		value = value[:8] + "-" + value[8:]
	if len(value) >= 4:
		value = value[:4] + "-" + value[4:]
	if len(value) >= 2:
		value = value[:2] + "-" + value[2:]
	return value


RULES = {
	"tax_ntn": (normalize_ntn, NTN_RE),
	"tax_nic": (normalize_nic, NIC_RE),
	"tax_strn": (normalize_strn, STRN_RE),
}


def execute():
	copy_legacy_values()
	backfill_transactions()


def copy_legacy_values():
	copied = 0
	skipped = []

	for doctype, mapping in LEGACY_FIELDS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)

		for source, target in mapping.items():
			if not (meta.has_field(source) and meta.has_field(target)):
				continue

			normalize, pattern = RULES[target]
			fields = ["name", source, target]
			if "tax_nic" not in fields and meta.has_field("tax_nic"):
				fields.append("tax_nic")
			rows = frappe.get_all(doctype, filters={source: ["is", "set"]}, fields=fields)

			for row in rows:
				if row.get(target):
					continue

				raw = row.get(source)
				value = normalize(raw)

				if target == "tax_ntn" and re.fullmatch(r"\d{13}", str(raw).strip()):
					# For individuals the CNIC is the NTN: keep it as the NTN (CNIC format) and also make sure
					# it is stored in the CNIC field.
					cnic = normalize_nic(raw)
					if NIC_RE.match(cnic):
						frappe.db.set_value(doctype, row.name, "tax_ntn", cnic, update_modified=False)
						copied += 1
						if meta.has_field("tax_nic") and not row.get("tax_nic"):
							frappe.db.set_value(doctype, row.name, "tax_nic", cnic, update_modified=False)
							copied += 1
					continue

				if pattern.match(value):
					frappe.db.set_value(doctype, row.name, target, value, update_modified=False)
					copied += 1
				else:
					skipped.append((doctype, row.name, raw))

	print(f"erpnext_pk: copied {copied} legacy tax number(s)")
	for doctype, name, value in skipped:
		print(f"erpnext_pk: skipped {doctype} {name}: '{value}' is not a valid format, fix it manually")


def backfill_transactions():
	updated_sources = 0

	for master, link_field, mapping in TRANSACTION_SOURCES:
		records = frappe.get_all(master, fields=["name", *mapping.keys()])

		for record in records:
			for master_field, transaction_field in mapping.items():
				value = record.get(master_field)
				if not value:
					continue

				for doctype in TRANSACTION_DOCTYPES:
					if not frappe.db.exists("DocType", doctype):
						continue
					if not frappe.get_meta(doctype).has_field(transaction_field):
						continue

					frappe.db.set_value(
						doctype,
						{link_field: record.name, transaction_field: ["is", "not set"]},
						transaction_field,
						value,
						update_modified=False,
					)
				updated_sources += 1

	print(f"erpnext_pk: back-filled tax numbers on transactions from {updated_sources} master value(s)")
