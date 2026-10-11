frappe.listview_settings["Input Tax Claim"] = {
	add_fields: ["status", "claim_date"],
	get_indicator(doc) {
		const colors = {
			Unclaimed: "orange",
			Claimed: "green",
			Expired: "red",
			Expensed: "blue",
		};
		return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
