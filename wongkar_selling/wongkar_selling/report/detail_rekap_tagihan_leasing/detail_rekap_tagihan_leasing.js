// Copyright (c) 2024, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Detail Rekap Tagihan Leasing"] = {
	"filters": [
		// {
		// 	"fieldname":"from_date",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	"reqd": 1,
		// 	"width": "60px",
		// },
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
		},
		{
			"fieldname":"area",
			"label": __("Nama Area"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"reqd": 0,
			"width": "60px",
		},
	]
};

