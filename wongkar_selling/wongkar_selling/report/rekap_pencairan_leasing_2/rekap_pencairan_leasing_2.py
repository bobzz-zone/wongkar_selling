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
	if filters.get("leasing"):
		kondisi = " and sipm.customer_name = '{}' ".format(filters.get("leasing"))

	data = frappe.db.sql(""" SELECT 
		sipm.customer_name as leasing,
		w.parent_warehouse as cab_area_jual,
		w2.parent_warehouse as cabid_jual,
		sum(dl.nominal)-IFNULL(sum(tl.nilai),0) as bt_tl,
		IFNULL(sum(tl.nilai),0) as st_tl,
		IFNULL(sum(tl.outstanding_discount),0) as o_tl,
		IFNULL(sum(tl.terbayarkan),0) as sb_tl,
		sum(sipm.outstanding_amount)-IFNULL(sum(tl.tagihan_sipm),0) as bt_tp,
		IFNULL(sum(tl.tagihan_sipm),0) as st_tp,
		IFNULL(sum(tl.outstanding_sipm),0) as o_tp,
		IFNULL(sum(tl.terbayarkan_sipm),0) as sb_tp,
		(SELECT IFNULL(SUM(tl.terbayarkan),0) FROM `tabDaftar Tagihan Leasing` tl WHERE tl.mode_of_payment_sipm = "Advance Leasing") AS sb_tpa,
		(SELECT IFNULL(SUM(tl.terbayarkan),0) FROM `tabDaftar Tagihan Leasing` tl WHERE tl.mode_of_payment_sipm != "Advance Leasing") AS sb_tpn
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabDaftar Tagihan Leasing` tl ON tl.`docstatus` = 1 AND sipm.name = tl.no_invoice
		left join `tabTagihan Discount Leasing` tdl on tdl.name = tl.parent
		left join `tabTable Disc Leasing` dl on dl.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.cara_bayar = "Credit" and sipm.posting_date between '{}' and '{}'
		group by sipm.customer_name,w.parent_warehouse  order by sipm.customer_name asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)
	
	return data

def get_columns(filters):
	columns = [
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
			"label": _("Belum Tertagih Tambahan Leasing"),
			"fieldname": "bt_tl",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Tertagih Tambahan Leasing"),
			"fieldname": "st_tl",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Terbayarkan Tambahan Leasing"),
			"fieldname": "sb_tl",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Outstanding Tambahan Leasing"),
			"fieldname": "o_tl",
			"fieldtype": "Currency",
			"width": 200
		},

		{
			"label": _("Belum Tertagih Tagihan Pokok"),
			"fieldname": "bt_tp",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Tertagih Tagihan Pokok"),
			"fieldname": "st_tp",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Terbayarkan Tagihan Pokok Adv"),
			"fieldname": "sb_tpa",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Terbayarkan Tagihan Pokok Normal"),
			"fieldname": "sb_tpn",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tot Pencairan Pokok"),
			"fieldname": "sb_tp",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Outstanding Tagihan Pokok"),
			"fieldname": "o_tp",
			"fieldtype": "Currency",
			"width": 200
		},
	]

	return columns


