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
		sipm.customer_name as leasing,
		sipm.cost_center,
		sipm.nama_pemilik as nama_konsumen,
		sipm.posting_date as tgl_jual,
		if(tl.name is not null,tl.outstanding_sipm,sipm.outstanding_amount) as piutang,
		tdl.date as tgl_tagih,
		if(tdl.date is not null,"Belum Realisasi","Belum Tagih") as ket,
		IFNULL(IF(sipm.tanggal_tagih,DATEDIFF(tdl.date, sipm.posting_date),0),0) as ht,
		IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0) as hc,
		sipm.set_warehouse,
		IFNULL(tl.`outstanding_discount`,0),
		tl.`mode_of_payment_sipm` as mode,
		sipm.name as sipm,
		IFNULL(dl.nominal,0) as tambahan_leasing,
		w.parent_warehouse as cabid_jual,
		w2.parent_warehouse as cab_area_jual,
		IFNULL(tl.terbayarkan,0) as st_tl,
		IFNULL(tl.outstanding_discount,0) as o_tl,
		IFNULL(tl.outstanding_discount-tl.terbayarkan,0) as bt_tl,
		IFNULL(tl.terbayarkan_sipm,0) as st_tp,
		IFNULL(tl.outstanding_sipm,0) as o_tp,
		IFNULL(tl.outstanding_sipm-tl.terbayarkan_sipm,0) as bt_tp
		FROM `tabSales Invoice Penjualan Motor` sipm
		left JOIN `tabDaftar Tagihan Leasing` tl on sipm.name = tl.no_invoice
		left join `tabTagihan Discount Leasing` tdl on tdl.name = tl.parent
		left join `tabTable Disc Leasing` dl on dl.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where tl.docstatus = 1 or sipm.docstatus = 1 and sipm.cara_bayar = "Credit" and sipm.posting_date between '{}' and '{}' 
		group by sipm.name order by sipm.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)
	
	tampil = []
	if data:
		for i in data:
			tampil.append([
				i['sipm'],
				i['leasing'],
				i['cab_area_jual'],
				i['cabid_jual'],
				i['nama_konsumen'],
				i['tgl_jual'],
				i['piutang'],#piutang
				i['tambahan_leasing'],#tl
				i['tgl_tagih'],
				i['ket'],
				# i['bt_tl'],
				# i['st_tl'],
				# i['o_tl'],
				# i['bt_tp'],
				# i['st_tp'],
				# i['o_tp'],
				i['mode'],
				i["ht"],
				i['hc']
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
			"label": _("Cab ID Jual"),
			"fieldname": "cabid_jual",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Cab Area Jual"),
			"fieldname": "cab_area_jual",
			"fieldtype": "Data",
			"width": 100
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


		# {
		# 	"label": _("Belum Terbayrakan Tambahan Leasing"),
		# 	"fieldname": "bt_tl",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("Sudah Terbayrakan Tambahan Leasing"),
		# 	"fieldname": "st_tl",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("outstanding Tambahan Leasing"),
		# 	"fieldname": "o_tl",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },

		# {
		# 	"label": _("Belum Terbayrakan Tagihan Pokok"),
		# 	"fieldname": "bt_tp",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("Sudah Terbayrakan Tagihan Pokok"),
		# 	"fieldname": "st_tp",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("outstanding Tagihan Pokok"),
		# 	"fieldname": "o_tp",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },

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

