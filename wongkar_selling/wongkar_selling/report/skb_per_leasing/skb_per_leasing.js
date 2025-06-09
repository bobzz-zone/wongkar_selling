// Copyright (c) 2025, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SKB Per Leasing"] = {
	"filters": [
		{
			"fieldname": "leasing",
			"label": __("Leasing"),
			"fieldtype": "Link",
			// "width": "80",
			"options": "Customer",
			"reqd": 1
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
	]
};
