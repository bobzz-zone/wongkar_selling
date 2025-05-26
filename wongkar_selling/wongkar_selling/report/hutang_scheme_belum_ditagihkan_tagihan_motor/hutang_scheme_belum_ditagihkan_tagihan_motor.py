# Copyright (c) 2013, w and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date
from frappe.utils import cint, cstr, flt, getdate, nowdate

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):
	kondisi = ""
	if filters.get("area"):
		kondisi = " and sipm.cost_center = '{}' ".format(filters.get("area"))

	# frappe.msgprint(str(filters)+ ' filters')
	data = frappe.db.sql(""" SELECT 
			sipm.name AS sipm,
			tbm.vendor,
			sipm.nama_pemilik,
			sipm.posting_date as tgl_jual,
			sipm.item_code as kode_motor,
			i.item_name as nama_motor,
			SUBSTRING_INDEX(sipm.no_rangka,'--',1) as no_mesin,
			SUBSTRING_INDEX(sipm.no_rangka,'--',-1) as no_rangka,
			tbm.`amount` AS nilai_hutang
			FROM `tabSales Invoice Penjualan Motor` sipm
			join `tabTabel Biaya Motor` tbm on tbm.parent = sipm.name
			join `tabItem` i on i.name = sipm.item_code
			left join `tabChild Tagihan Biaya Motor` tb on tb.no_invoice = sipm.name AND tb.`docstatus` = 1
			left join `tabPembayaran Tagihan Motor` ptm on ptm.name = tb.parent
			WHERE sipm.docstatus = 1 
			AND sipm.posting_date <= '{}' AND tbm.`amount` > 0 and tb.`name` IS NULL
			{}
			 ORDER BY sipm.posting_date ASC
		 """.format(filters.get('to_date'),kondisi),as_dict = 1,debug=0)

	

	return data

def setup_ageing_columns():
	columns = []
	range1 = 30
	range2 = 60
	range3 = 90
	range4 = 120
	for i, label in enumerate(
		[
			"0-{range1}".format(range1=range1),
			"{range1}-{range2}".format(
				range1=cint(range1) + 1, range2=range2
			),
			"{range2}-{range3}".format(
				range2=cint(range2) + 1, range3=range3
			),
			"{range3}-{range4}".format(
				range3=cint(range3) + 1, range4=range4
			),
			"{range4}-{above}".format(range4=cint(range4) + 1, above=_("Above")),
		]
	):
			columns.append({
			"label": _(label),
			"fieldname": "range" + str(i + 1),
			"fieldtype": 'Currency',
			"width": 100
		})
	
	return columns

def get_ageing_data(entry_date, row):
	# [0-30, 30-60, 60-90, 90-120, 120-above]
	# row.range1 = row.range2 = row.range3 = row.range4 = row.range5 = 0.0
	row['range1'] = row['range2'] = row['range3'] = row['range4'] = row['range5'] = 0.0

	age_as_on = getdate(nowdate())

	row['age'] = (getdate(age_as_on) - getdate(entry_date)).days or 0
	index = None

	range1 = 30
	range2 = 60
	range3 = 90
	range4 = 120
	
	for i, days in enumerate(
		[range1, range2,range3, range4]
	):
		if cint(row['age']) <= cint(days):
			index = i
			break

	if index is None:
		index = 4

	o_range = "range" + str(index + 1)
	o_piutang = row['piutang']
	row["range" + str(index + 1)] = row['piutang']
	# frappe.msgprint(str(index + 1)+' jkjkj')
	# frappe.msgprint(str(row["range" + str(index + 1)]))
	return o_range,o_piutang
	

def get_columns(filters):
	columns = [
		{
			"label": _("Nama Vendor"),
			"fieldname": "vendor",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 200
		},
		{
			"label": _("Nama Pemilik"),
			"fieldname": "nama_pemilik",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tanggal SIPM"),
			"fieldname": "tgl_jual",
			"fieldtype": "Date",
			"width": 200
		},
		{
			"label": _("No SIPM"),
			"fieldname": "sipm",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 200
		},
		
		{
			"label": _("Kode Motor"),
			"fieldname": "kode_motor",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200
		},
		{
			"label": _("Nama Motor"),
			"fieldname": "nama_motor",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Nomor Mesin"),
			"fieldname": "no_mesin",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Nomor Rangka"),
			"fieldname": "no_rangka",
			"fieldtype": "Data",
			"width": 200
		},
		
		{
			"label": _("Nilai Hutang"),
			"fieldname": "nilai_hutang",
			"fieldtype": "Currency",
			"width": 200
		},
		
	]

	# columns.extend(setup_ageing_columns())

	return columns

