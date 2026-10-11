from erpnext_pk.install import make_custom_fields, apply_property_setters


def execute():
	# Re-applies custom field definitions for ERPNext v16: Supplier tax fields are now anchored after
	# tax_id (the "pan" field no longer exists). create_custom_fields updates existing fields in place.
	make_custom_fields()
	apply_property_setters()
