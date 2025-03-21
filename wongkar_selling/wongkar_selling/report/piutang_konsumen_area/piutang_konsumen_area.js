// Copyright (c) 2016, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Piutang Konsumen Area"] = {
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
			"fieldname":"area",
			"label": __("Area"),
			"fieldtype": "Link",
			"options": "Cost Center",
			// "reqd": 1,
			"width": "60px",
		},
	]
};
