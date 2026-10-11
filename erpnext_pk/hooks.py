app_name = "erpnext_pk"
app_title = "Pakistan Workspace"
app_publisher = "ParaLogic"
app_description = "Sales tax reporting and compliance for Pakistan"
app_email = "info@paralogic.io"
app_license = "GNU General Public License (v3)"
required_apps = ["frappe/erpnext"]

app_logo_url = "/assets/erpnext_pk/images/erpnext-pk-logo.svg"
app_home = "/desk/pakistan"

add_to_apps_screen = [
	{
		"name": "erpnext_pk",
		"logo": "/assets/erpnext_pk/images/erpnext-pk-logo.svg",
		"title": "Pakistan Workspace",
		"route": app_home,
	}
]

before_install = "erpnext_pk.install.before_install"
after_install = "erpnext_pk.install.after_install"
setup_wizard_stages = "erpnext_pk.setup.get_setup_stages"

# Includes in <head>
# ------------------
# Built by the desk's esbuild from public/js/*.bundle.js
app_include_js = ["erpnext_pk.bundle.js"]
# SVG sprite of <symbol> elements, inserted into the desk's icon container
app_include_icons = ["/assets/erpnext_pk/icons/erpnext_pk_icons.svg"]

doctype_js = {
	"Customer": "public/js/customer.js",
	"Supplier": "public/js/supplier.js",
	"Employee": "public/js/employee.js",
	"Company": "public/js/company.js",
}

doc_events = {
	"Customer": {
		"validate": "erpnext_pk.events.validate_ntn_nic_strn_in_document",
	},
	"Supplier": {
		"validate": "erpnext_pk.events.validate_ntn_nic_strn_in_document",
	},
	"Company": {
		"validate": "erpnext_pk.events.validate_ntn_nic_strn_in_document",
	},
	"Employee": {
		"validate": "erpnext_pk.events.validate_ntn_nic_strn_in_document",
	},
}
