# Copyright (c) 2013, w and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):

	leasing = filters.get('leasing')
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')
	# from_date = '2024-05-01'
	# to_date = '2024-05-31'

	data = frappe.db.sql(""" 
					SELECT 
						b.`customer` as leasing,
						a.`serial_no`,
						SUBSTRING_INDEX(a.`serial_no`,"--",1) AS no_mesin,
						SUBSTRING_INDEX(a.`serial_no`,"--",-1) AS no_rangka,
						a.`item_code`,
						b.`nama_pemilik`,
						b.name AS sales_invoice_penjualan_motor,
						a.`biaya_bpkb`,
						a.`no_bpkb`,
						a.`tanggal_terima_bpkb`,
						a.`tanggal_serah_bpkb`,
						b.`territory_real` AS area,
					  	b.cara_bayar
						FROM `tabSKB` a 
					JOIN `tabSales Invoice Penjualan Motor` b ON a.`sales_invoice_penjualan_motor` = b.`name`
					WHERE b.`cara_bayar` = 'Credit' and b.customer = '{}' 
					and a.`tanggal_serah_bpkb` between '{}' and '{}'
					  """.format(leasing,from_date,to_date),as_dict=1,debug=1)
	
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Leasing"),
			"fieldname": "leasing",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150
		},
		{
			"label": _("Cara Bayar"),
			"fieldname": "cara_bayar",
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
			"label": _("No Mesin"),
			"fieldname": "no_mesin",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Nama Pemilik"),
			"fieldname": "nama_pemilik",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Sales Invoice Penjualan Motor"),
			"fieldname": "sales_invoice_penjualan_motor",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 150
		},
		{
			"label": _("Biaya BPKB"),
			"fieldname": "biaya_bpkb",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("No BPKB"),
			"fieldname": "no_bpkb",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Tanggal Terima BPKB"),
			"fieldname": "tanggal_terima_bpkb",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"label": _("Tanggal Serah BPKB"),
			"fieldname": "tanggal_serah_bpkb",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"label": _("Area"),
			"fieldname": "area",
			"fieldtype": "Data",
			"width": 100
		}
	]

	return columns

