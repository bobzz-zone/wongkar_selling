// Copyright (c) 2016, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kas Kecil"] = {
	"filters": [
		{
			"fieldname":"month",
			"label": __("Bulan"),
			"fieldtype": "Select",
			"options": [
				"Januari",
				"Februari",
				"Maret",
				"April",
				"Mei",
				"Juni",
				"Juli",
				"Agustus",
				"September",
				"Oktober",
				"November",
				"Desember"],
			// "default": "9",
			"reqd": 1,
			"width": "60px",
		},
		{
			"fieldname":"year",
			"label": __("Tahun"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1,
			"width": "60px",
		},
	]
};
