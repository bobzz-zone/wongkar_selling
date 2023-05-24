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
	data = frappe.db.sql(""" SELECT 
		sipm.set_warehouse,
		sipm.posting_date,
		sipm.nama_pemilik,
		sipm.cara_bayar,
		tl.outstanding_sipm,
		datediff(if(tl.outstanding_sipm<0 and sipm.tanggal_cair,sipm.tanggal_cair,current_date()),sipm.posting_date )
		FROM `tabSales Invoice Penjualan Motor` sipm
		JOIN `tabDaftar Tagihan Leasing` tl on sipm.name = tl.no_invoice
		where tl.docstatus = 1 and sipm.docstatus = 1 and sipm.posting_date between '{}' and '{}' group by sipm.name order by sipm.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_list = 1)
	
	tampil = []
	if data:
		for i in data:
			tampil.append([
				i[0],
				i[1],
				i[2],
				i[3],
				i[4],
				i[5]
			])

	return tampil

def get_columns(filters):
	columns = [
		{
			"label": _("Pos"),
			"fieldname": "pos",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tgl Jual"),
			"fieldname": "tgl_jual",
			"fieldtype": "Date",
			"width": 200
		},
		{
			"label": _("Nama"),
			"fieldname": "nama",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Ket Jual"),
			"fieldname": "ket_jual",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Jumlah"),
			"fieldname": "jumlah",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Hari"),
			"fieldname": "hari",
			"fieldtype": "Int",
			"width": 100
		}
	]

	return columns

