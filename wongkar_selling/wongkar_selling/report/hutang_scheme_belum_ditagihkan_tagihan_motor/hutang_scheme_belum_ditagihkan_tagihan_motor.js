// Copyright (c) 2025, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Hutang Scheme Belum Ditagihkan Tagihan Motor"] = {
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
