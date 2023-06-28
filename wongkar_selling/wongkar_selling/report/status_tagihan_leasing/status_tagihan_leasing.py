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
		IFNULL(IF(sipm.tanggal_tagih,DATEDIFF(tdl.date, sipm.posting_date),0),0),
		IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0),
		sipm.set_warehouse,
		IFNULL(tl.`outstanding_discount`,0),
		tl.`mode_of_payment_sipm`,
		sipm.name,
		IFNULL(dl.nominal,0)
		FROM `tabSales Invoice Penjualan Motor` sipm
		left JOIN `tabDaftar Tagihan Leasing` tl on sipm.name = tl.no_invoice
		left join `tabTagihan Discount Leasing` tdl on tdl.name = tl.parent
		left join `tabTable Disc Leasing` dl on dl.parent = sipm.name
		where tl.docstatus = 1 or sipm.docstatus = 1 and sipm.cara_bayar = "Credit" and sipm.posting_date between '{}' and '{}' 
		group by sipm.name order by sipm.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_list = 1,debug=1)
	
	tampil = []
	if data:
		for i in data:
			tampil.append([
				i[12],
				i[0],
				i[1],
				i[9],
				i[2],
				i[3],
				i[4],#piutang
				i[13],#tl
				i[5],
				i[6],
				i[11],
				i[7],
				i[8]
			])

	return tampil

def get_columns(filters):
	columns = [
		{
			"label": _("SIPM"),
			"fieldname": "sipm",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 200
		},
		{
			"label": _("Leasing"),
			"fieldname": "leasing",
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
			"label": _("Cab Id Jual"),
			"fieldname": "cab",
			"fieldtype": "Link",
			"options": "Warehouse",
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
			"label": _("Tambahan Leasing"),
			"fieldname": "tambahan_leasing",
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
			"label": _("Mode Of Payment"),
			"fieldname": "mode",
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

