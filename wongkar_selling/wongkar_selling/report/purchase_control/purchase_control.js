// Copyright (c) 2024, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Control"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
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
			"fieldname": "pt",
			"label": __("Purchase Type"),
			"fieldtype": "Select",
			"width": "80",
			"options": ['Motor','Sperepart'],
			"default": 'Motor'
		},
		{
			"fieldname": "po",
			"label": __("Purchase Order"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Purchase Order",
			// "depends_on": frappe.query_report.get_filter_value("pt") == 'Motor'
		},
		{
			"fieldname": "pinv",
			"label": __("Purchase Invoice"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Purchase Invoice",
		},
	]
};
