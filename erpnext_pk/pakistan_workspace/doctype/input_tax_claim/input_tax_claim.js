// Copyright (c) 2026, ParaLogic and contributors
// For license information, please see license.txt

frappe.ui.form.on("Input Tax Claim", {
	setup(frm) {
		frm.set_query("purchase_invoice", () => ({
			filters: { docstatus: 1, is_return: 0 },
		}));
	},

	purchase_invoice(frm) {
		if (!frm.doc.purchase_invoice) {
			frm.set_value({ input_tax_amount: 0 });
			return;
		}

		frappe.call({
			method: "erpnext_pk.pakistan_workspace.doctype.input_tax_claim.input_tax_claim.get_invoice_details",
			args: { purchase_invoice: frm.doc.purchase_invoice },
			callback(r) {
				if (!r.message) return;
				frm.set_value({
					company: r.message.company,
					company_currency: r.message.company_currency,
					input_tax_amount: r.message.input_tax_amount,
				});
			},
		});
	},

	status(frm) {
		if (frm.doc.status === "Claimed") {
			if (!frm.doc.claim_date) {
				frm.set_value("claim_date", frappe.datetime.get_today());
			}
		} else {
			frm.set_value("claim_date", null);
		}
	},
});
