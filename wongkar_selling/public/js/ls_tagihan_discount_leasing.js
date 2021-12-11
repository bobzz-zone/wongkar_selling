// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Tagihan Discount Leasing'] = {
	get_indicator: function(doc) {
		var status_color = {
			"Paid": "green",
			"Draft": "grey",
			"Submitted": "blue"
		};
		return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
	},
	right_column: "coa_tagihan_discount_leasing"
};
