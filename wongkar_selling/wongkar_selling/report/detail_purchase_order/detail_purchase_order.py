# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date

def execute(filters=None):
	# columns, data = [], []
	# return columns, data

	return get_columns(filters), get_data(filters)

def get_data(filters):
	
	data = frappe.db.sql(""" 
		SELECT 
			prec.`supplier`,
			sn.`name`,
			sn.`item_code`,
			prec.`supplier_delivery_note`,
			prec.`supplier_delivery_order`,
			prec.`set_warehouse` AS accepted_warehouse,
			SUBSTRING_INDEX(sn.`name`,"--",1) AS no_rangka,
			SUBSTRING_INDEX(sn.`name`,"--",-1) AS no_mesin,
			SUBSTRING_INDEX(sn.item_code," - ", 1) AS type,
			i.`warna`,
			i.`tahun_rakitan` AS tahun,
			sle.`valuation_rate` AS hpp,
			prec.`posting_date` AS tanggal
			FROM `tabStock Ledger Entry` sle
		JOIN `tabPurchase Receipt` prec ON prec.name = sle.voucher_no
		JOIN `tabSerial No` sn ON sle.serial_no LIKE CONCAT("%",sn.name,"%")
		JOIN `tabItem` i ON i.`name` = sn.`item_code` 
		WHERE prec.docstatus = 1 AND prec.`posting_date` BETWEEN '{}' AND '{}' 
		ORDER BY prec.`posting_date` ASC
		""".format(filters.get('from_date'),filters.get('to_date')),as_dict=1)

	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Tanggal"),
			"fieldname": "tanggal",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 100
		},
		{
			"label": _("Supplier Delivery Note"),
			"fieldname": "supplier_delivery_note",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Supplier Delivery Order"),
			"fieldname": "supplier_delivery_order",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Accepted Warehouse"),
			"fieldname": "accepted_warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 100
		},
		{
			"label": _("Type"),
			"fieldname": "type",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("No Mesin"),
			"fieldname": "no_mesin",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("No Rangka"),
			"fieldname": "no_rangka",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Warna"),
			"fieldname": "warna",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Tahun"),
			"fieldname": "tahun",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Hpp (Rate)"),
			"fieldname": "hpp",
			"fieldtype": "Currency",
			"width": 100
		},

	]

	return columns
