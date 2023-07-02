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
		kondisi = " and w.parent_warehouse = '{}' ".format(filters.get("area"))

	data = frappe.db.sql(""" SELECT 
		tag_d.`name`,
		td.customer,
		w.parent_warehouse AS cab_area_jual,
		w2.parent_warehouse AS cabid_jual,
		SUM(td.nominal)-IF(tag_d.`name` IS NULL,0,COALESCE(SUM(dt.nilai),0)) AS bt_t,
		IF(tag_d.`name` IS NULL,0,COALESCE(SUM(dt.nilai),0)) AS st_t,
		IF(tag_d.`name` IS NULL,0, COALESCE(SUM(dt.nilai) - SUM(dt.terbayarkan),0)) AS sb_t,
		IF(tag_d.`name` IS NULL,0,COALESCE(SUM(dt.terbayarkan),0)) AS o_t,
		sipm.cara_bayar
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabDaftar Tagihan` dt ON dt.docstatus = 1 AND sipm.name = dt.no_sinv  
		LEFT JOIN `tabTable Discount` td ON td.parent = sipm.name 
		LEFT JOIN `tabTagihan Discount` tag_d ON  tag_d.name = dt.`parent` AND td.`customer` = tag_d.`customer`
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.posting_date between '{}' and '{}' and td.nominal != 0
		group by td.customer,w.parent_warehouse,sipm.cara_bayar order by w2.parent_warehouse asc,td.customer  """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)
	
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Cab ID Jual"),
			"fieldname": "cabid_jual",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Cab Area Jual"),
			"fieldname": "cab_area_jual",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Belum Tertagih Tagihan"),
			"fieldname": "bt_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Tertagih Tagihan"),
			"fieldname": "st_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Bayar Tagihan"),
			"fieldname": "sb_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Outstanding Tagihan"),
			"fieldname": "o_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Cara Bayar"),
			"fieldname": "cara_bayar",
			"fieldtype": "Data",
			"width": 200
		},
	]

	return columns


