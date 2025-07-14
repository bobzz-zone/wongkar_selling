// Copyright (c) 2025, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Serial No Reference"] = {
	"filters": [
		{
			"fieldname": "serial_no",
			"label": __("Serial No"),
			"fieldtype": "Link",
			// "width": "80",
			"options": "Serial No",
			// "reqd": 1
		},
	]
};
