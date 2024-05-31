// Copyright (c) 2024, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Piutang Scheme Sudah Ditagihkan Tagihan Discount Leasing"] = {
	"filters": [
		{
			"fieldname":"to_date",
			"label": __("To date"),
			"fieldtype": "Date",
			"reqd": 1,
			"width": "60px",
			"default": frappe.datetime.get_today(),
		},
	]
};