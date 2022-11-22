// Copyright (c) 2016, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Invoice"] = {
	
	"filters": [
		// {
		// 	"fieldname":"year",
		// 	"label": __("Year"),
		// 	"fieldtype": "Link",
		// 	"options": "Fiscal Year",
		// 	"default": frappe.defaults.get_user_default("fiscal_year"),
		// 	// "reqd": 1,
		// 	"width": "60px",
		// },
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"width": "60px",
		},
		{
			"fieldname":"to_date",
			"label": __("To date"),
			"fieldtype": "Date",
			"reqd": 1,
			"width": "60px",
		},
		// {
		// 	"fieldname":"month",
		// 	"label": __("Month"),
		// 	"fieldtype": "Select",
		// 	"options": ["1","2","3","4","5","6","7","8","9","10","11","12"],
		// 	"default": "9",
		// 	// "reqd": 1,
		// 	"width": "60px",
		// },
	]
};
