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
			sipm.customer,
			sipm.customer_name AS leasing,
			sipm.nama_pemilik,
			sipm.posting_date AS tgl_jual,
			sipm.`outstanding_amount`,
			IF(sipm.`outstanding_amount`>0,'Belum Tagih',IF(sipm.`outstanding_amount`=0 AND l.`outstanding_sipm`>0,'Sudah Tagih',
			IF(l.`outstanding_sipm` < l.`tagihan_sipm` AND l.`outstanding_sipm` !=0,'Belum Realisasi',IF(sipm.`outstanding_amount`=0 AND l.`outstanding_sipm`=0,'Sudah Realisasi',NULL)))) AS status_sipm,
			l.`outstanding_sipm`,
			l.`tagihan_sipm`,
			tl.date as tgl_tagih,
			IFNULL(IF(sipm.tanggal_tagih,DATEDIFF(tl.date, sipm.posting_date),0),0) AS ht,
			IF(tl.date IS NOT NULL,DATEDIFF(tl.date, sipm.tanggal_cair),0) AS hc,
			sipm.cost_center as nama_area,
			IF(l.outstanding_sipm,l.outstanding_sipm,sipm.outstanding_amount) as piutang,
			l.terbayarkan_sipm,
			tl.name as no_tagih,
			sipm.item_code as kode_motor,
			i.item_name as nama_motor,
			SUBSTRING_INDEX(sipm.no_rangka,'--',1) as no_mesin,
			SUBSTRING_INDEX(sipm.no_rangka,'--',-1) as no_rangka,
			sipm.nama_diskon as category_discount,
			sipm.nama_promo as nama_promo
			FROM `tabSales Invoice Penjualan Motor` sipm
			LEFT JOIN `tabList Tagihan Piutang Leasing` l ON l.no_invoice = sipm.name
			LEFT JOIN `tabTagihan Leasing` tl ON tl.`name` = l.`parent`
			left join `tabItem` i on i.name = sipm.item_code
			WHERE sipm.docstatus = 1 AND sipm.cara_bayar = "Credit" AND tl.name IS NULL
			AND sipm.posting_date <= '{}' and sipm.`outstanding_amount` > 0
			{}
			group by sipm.name order by sipm.customer,sipm.posting_date asc
		 """.format(filters.get('to_date'),kondisi),as_dict = 1,debug=1)

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
			"label": _("Nama Leasing"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
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
			"label": _("Category Discount"),
			"fieldname": "category_discount",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Nama Promo"),
			"fieldname": "nama_promo",
			"fieldtype": "Data",
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
			"label": _("Nama Area"),
			"fieldname": "nama_area",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Nilai Piutang"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 200
		},
		
	]

	# columns.extend(setup_ageing_columns())

	return columns

