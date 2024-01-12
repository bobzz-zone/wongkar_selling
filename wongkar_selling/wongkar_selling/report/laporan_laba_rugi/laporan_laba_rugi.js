// Copyright (c) 2024, w and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.require("assets/wongkar_selling/js/custom_financial_statements.js", function() {
	frappe.query_reports["Laporan Laba Rugi"] = $.extend({},
		erpnext.financial_statements);

	erpnext.utils.add_dimensions('Laporan Laba Rugi', 10);

	frappe.query_reports["Laporan Laba Rugi"]["filters"].push(
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Project', txt);
			},
			"hidden": 1
		},
		{
			"fieldname": "include_default_book_entries",
			"label": __("Include Default Book Entries"),
			"fieldtype": "Check",
			"default": 1,
			"hidden": 1
		}
	);
});

