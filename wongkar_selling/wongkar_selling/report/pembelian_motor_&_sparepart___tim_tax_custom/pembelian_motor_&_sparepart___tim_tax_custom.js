// Copyright (c) 2024, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pembelian Motor & Sparepart - Tim TAX Custom"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "purchase_invoice",
			"label": __("Purchase Invoice"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Purchase Invoice"
		},
	]
};
