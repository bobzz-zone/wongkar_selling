// Copyright (c) 2025, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Penerimaan Belum Setor"] = {
	"filters": [
		{
			"fieldname": "area",
			"label": __("Area"),
			"fieldtype": "Link",
			// "width": "80",
			"options": "Territory",
			"reqd": 1
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			// "width": "80",
			"options": "Company",
			"reqd": 1
		},
	]
};
