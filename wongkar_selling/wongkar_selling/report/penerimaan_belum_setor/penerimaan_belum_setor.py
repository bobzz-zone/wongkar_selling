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
	list_akun = []
	con_list_akun = ""
	area = filters.get('area')
	company = filters.get('company')
	data_akun =  frappe.db.get_list("List Bank Induk",{'parent':company},'account')
	if data_akun:
		for a in data_akun:
			list_akun.appen(a['account'])
		str_list_akun = str(list_akun).replace('[','(').replace(']',')')
		con_list_akun = f" and dp.paid_to not in {str_list_akun} "

	data = frappe.db.sql(""" 
					  SELECT
					  	dp.name AS penerimaan_dp,
						dp.tanggal,
						dp.nama_pemilik AS nama,
						dp.customer_name AS ket,
						dp.territory AS area,
						IF(cara_bayar='Cash',piutang_bpkb_stnk+piutang_motor,piutang_motor) AS jumlahs,
						DATEDIFF(IF(tr.name IS NULL,DATE(NOW()),tr.date),dp.tanggal) AS hari,
						IF(tr.name IS NULL,DATE(NOW()),tr.date),
						IF(pe.name IS NULL,IF(cara_bayar='Cash',piutang_bpkb_stnk+piutang_motor,piutang_motor),0) AS jumlah
					  from `tabPenerimaan DP` dp 
					  left join `tabList Penerimaan DP` pe on pe.penerimaan_dp = dp.name and pe.docstatus = 1
					  left join `tabPayment Entry Internal Transfer` tr on tr.name = pe.parent
					  where dp.docstatus = 1 and dp.territory = '{}' AND pe.name IS NULL {}
					  order by dp.tanggal asc
					  """.format(area,con_list_akun),as_dict=1,debug=1)
	
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Penerimaan DP"),
			"fieldname": "penerimaan_dp",
			"fieldtype": "Link",
			"options": "Penerimaan DP",
			"width": 150
		},
		{
			"label": _("Tanggal"),
			"fieldname": "tanggal",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"label": _("Nama"),
			"fieldname": "nama",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Area"),
			"fieldname": "area",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Keterangan"),
			"fieldname": "ket",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Jumlah"),
			"fieldname": "jumlah",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Hari"),
			"fieldname": "hari",
			"fieldtype": "int",
			"width": 100
		},
	]

	return columns

