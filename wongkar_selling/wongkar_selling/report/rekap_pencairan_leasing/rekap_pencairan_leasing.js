// Copyright (c) 2016, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rekap Pencairan leasing"] = {
	"filters": [
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
		{
			"fieldname":"leasing",
			"label": __("Leasing"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 1,
			"width": "60px",
		}
	]
};