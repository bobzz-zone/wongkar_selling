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
	kondisi = ""
	if filters.get("area"):
		kondisi = " and ec.cost_center = '{}' ".format(filters.get("area"))

	data = frappe.db.sql(""" SELECT 
		sipm.customer_name,
		sipm.cost_center,
		sipm.nama_pemilik,
		sipm.posting_date,
		if(tl.name is not null,tl.outstanding_sipm,sipm.outstanding_amount),
		tdl.date,
		if(tdl.date is not null,"Belum Realisasi","Belum Tagih"),
		IF(sipm.tanggal_tagih,DATEDIFF(tdl.date, sipm.posting_date),0),
		IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0)
		FROM `tabSales Invoice Penjualan Motor` sipm
		left JOIN `tabDaftar Tagihan Leasing` tl on sipm.name = tl.no_invoice
		left join `tabTagihan Discount Leasing` tdl on tdl.name = tl.parent
		where tl.docstatus = 1 or sipm.docstatus = 1 and sipm.cara_bayar = "Credit" and sipm.posting_date between '{}' and '{}' 
		group by sipm.name order by sipm.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_list = 1,debug=1)
	
	tampil = []
	if data:
		for i in data:
			tampil.append([
				i[0],
				i[1],
				i[2],
				i[3],
				i[4],
				i[5],
				i[6],
				i[7],
				i[8]
			])

	return tampil

def get_columns(filters):
	columns = [
		{
			"label": _("Leasing"),
			"fieldname": "pos",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Area"),
			"fieldname": "area",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 200
		},
		{
			"label": _("Nama Konsumen"),
			"fieldname": "nama_konsumen",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tgl Jual"),
			"fieldname": "tgl_jual",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Piutang"),
			"fieldname": "piutang",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tgl Tagih"),
			"fieldname": "tgl_tagih",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Ket Penagihan"),
			"fieldname": "ket",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Ht"),
			"fieldname": "ht",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Hc"),
			"fieldname": "hc",
			"fieldtype": "Int",
			"width": 100
		},
	]

	return columns

