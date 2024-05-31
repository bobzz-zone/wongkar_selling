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
	tampil = []
	data_tagihan_leasing = frappe.db.sql(""" 
		SELECT 
			CURRENT_DATE(),
			sipm.name AS nomor_invoice,
			sipm.`posting_date`,
			sipm.`customer` AS pelanggan,
			sipm.`customer_name`,
			sipm.`cara_bayar`,
			sipm.`outstanding_amount`,
			tl.`name`,
			tl.`docstatus`,
			ll.`outstanding_sipm`,
			tl.date,
			IF(tl.name IS NOT NULL,'Tagihan Leasing','SIPM') as status,
			IF(tl.name IS NOT NULL,ll.outstanding_sipm,sipm.outstanding_amount) AS piutang,
			IF(tl.`date` IS NOT NULL,tl.date,sipm.posting_date) AS tanggal,
			IF(tl.`date` IS NOT NULL,DATEDIFF(CURRENT_DATE(),tl.`date`),DATEDIFF(CURRENT_DATE(),sipm.`posting_date`)) AS umur,
			sipm.item_code as kode_barang,
			i.item_name as nama_barang,
			SUBSTRING_INDEX(sipm.no_rangka,'--',1) as no_mesin,
			SUBSTRING_INDEX(sipm.no_rangka,'--',-1) as no_rangka,
			sipm.cost_center as nama_area
		FROM `tabSales Invoice Penjualan Motor` sipm 
		left join `tabItem` i on i.name = sipm.item_code
		LEFT JOIN `tabList Tagihan Piutang Leasing` ll ON ll.`no_invoice` = sipm.name AND ll.`docstatus`=1
		LEFT JOIN `tabTagihan Leasing` tl ON tl.name = ll.`parent`
		WHERE sipm.`docstatus` = 1 AND sipm.cara_bayar = 'Credit' AND (sipm.`outstanding_amount` > 0 OR ll.`outstanding_sipm` >0) and tl.name IS NOT NULL """,as_dict=1,debug=1)

	data_tagihan_discount_ahm = frappe.db.sql(""" 
		SELECT 
		CURRENT_DATE(),
		sipm.name AS nomor_invoice,
		td.`customer` AS pelanggan,
		sipm.`posting_date`,
		tdisc.date,
		tdisc.`name`,
		td.`nominal`,
		dt.`terbayarkan`,
		IF(tdisc.`name` IS NOT NULL,DATEDIFF(CURRENT_DATE(),tdisc.`date`),DATEDIFF(CURRENT_DATE(),sipm.`posting_date`)) AS umur,
		IF(tdisc.`name` IS NOT NULL,tdisc.date,sipm.`posting_date`) AS tanggal,
		IF(tdisc.name IS NOT NULL,'Tagihan Diskon','SIPM') as status,
		IF(tdisc.`name` IS NOT NULL,dt.`terbayarkan`,td.`nominal`) AS piutang,
		sipm.item_code as kode_barang,
		i.item_name as nama_barang,
		SUBSTRING_INDEX(sipm.no_rangka,'--',1) as no_mesin,
		SUBSTRING_INDEX(sipm.no_rangka,'--',-1) as no_rangka,
		sipm.cost_center as nama_area
		FROM `tabSales Invoice Penjualan Motor` sipm
		left join `tabItem` i on i.name = sipm.item_code
		LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name
		LEFT JOIN `tabDaftar Tagihan` dt ON dt.`no_sinv` = sipm.name
		LEFT JOIN `tabTagihan Discount` tdisc ON tdisc.`name` = dt.`parent` AND tdisc.`docstatus` = 1
		WHERE sipm.docstatus = 1 AND td.`nominal` > 0 AND td.`customer` = 'AHM' AND (dt.`terbayarkan` > 0 OR dt.`terbayarkan` IS NULL ) and tdisc.name IS NOT NULL
		GROUP BY sipm.name  ASC 
		""",as_dict=1,debug=1)

	data_tagihan_discount_md = frappe.db.sql(""" 
		SELECT 
		CURRENT_DATE(),
		sipm.name AS nomor_invoice,
		td.`customer` AS pelanggan,
		sipm.`posting_date`,
		tdisc.date,
		tdisc.`name`,
		td.`nominal`,
		dt.`terbayarkan`,
		IF(tdisc.`name` IS NOT NULL,DATEDIFF(CURRENT_DATE(),tdisc.`date`),DATEDIFF(CURRENT_DATE(),sipm.`posting_date`)) AS umur,
		IF(tdisc.`name` IS NOT NULL,tdisc.date,sipm.`posting_date`) AS tanggal,
		IF(tdisc.name IS NOT NULL,'Tagihan Diskon','SIPM') as status,
		IF(tdisc.`name` IS NOT NULL,dt.`terbayarkan`,td.`nominal`) AS piutang,
		sipm.item_code as kode_barang,
		i.item_name as nama_barang,
		SUBSTRING_INDEX(sipm.no_rangka,'--',1) as no_mesin,
		SUBSTRING_INDEX(sipm.no_rangka,'--',-1) as no_rangka,
		sipm.cost_center as nama_area
		FROM `tabSales Invoice Penjualan Motor` sipm
		left join `tabItem` i on i.name = sipm.item_code
		LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name
		LEFT JOIN `tabDaftar Tagihan` dt ON dt.`no_sinv` = sipm.name
		LEFT JOIN `tabTagihan Discount` tdisc ON tdisc.`name` = dt.`parent` AND tdisc.`docstatus` = 1
		WHERE sipm.docstatus = 1 AND td.`nominal` > 0 AND td.`customer` = 'MD' AND (dt.`terbayarkan` > 0 OR dt.`terbayarkan` IS NULL ) and tdisc.name IS NOT NULL
		GROUP BY sipm.name  ASC 
		""",as_dict=1,debug=1)

	data_tagihan_discount_leasing = frappe.db.sql(""" 
		SELECT 
		CURRENT_DATE(),
		sipm.name AS nomor_invoice,
		td.nominal,
		tdl.`name`,
		dtl.`outstanding_discount`,
		td.`nama_leasing` AS pelanggan,
		IF(tdl.name IS NOT NULL,DATEDIFF(CURRENT_DATE(),tdl.`date`),DATEDIFF(CURRENT_DATE(),sipm.`posting_date`)) AS umur,
		IF(tdl.`name` IS NOT NULL,tdl.date,sipm.`posting_date`) AS tanggal,
		IF(tdl.name IS NOT NULL,'Tagihan Diskon','SIPM') as status,
		IF(tdl.`name` IS NOT NULL,dtl.`outstanding_discount`,td.`nominal`) AS piutang,
		sipm.item_code as kode_barang,
		i.item_name as nama_barang,
		SUBSTRING_INDEX(sipm.no_rangka,'--',1) as no_mesin,
		SUBSTRING_INDEX(sipm.no_rangka,'--',-1) as no_rangka,
		sipm.cost_center as nama_area
		FROM `tabSales Invoice Penjualan Motor` sipm
		left join `tabItem` i on i.name = sipm.item_code
		LEFT JOIN `tabTable Disc Leasing` td ON td.`parent` = sipm.name
		LEFT JOIN `tabDaftar Tagihan Leasing` dtl ON dtl.`no_invoice` = sipm.`name`
		LEFT JOIN `tabTagihan Discount Leasing` tdl ON tdl.`name` = dtl.`parent`
		WHERE sipm.docstatus = 1 AND sipm.`cara_bayar` = 'Credit' AND (dtl.`outstanding_discount` > 0 OR dtl.`outstanding_discount` IS NULL) and tdl.name IS NOT NULL
		""",as_dict=1,debug=1)
							
	for i in data_tagihan_leasing:
		entry_date = i['tanggal']
		i['range1'] = i['range2'] = i['range3'] = i['range4'] = i['range5'] = 0.0
		aging = get_ageing_data(entry_date,i)
		# frappe.msgprint(str(aging)+ ' agingaging')
		i.update({
			aging[0] : aging[1],
		})

	for i in data_tagihan_discount_ahm:
		entry_date = i['tanggal']
		i['range1'] = i['range2'] = i['range3'] = i['range4'] = i['range5'] = 0.0
		aging = get_ageing_data(entry_date,i)
		# frappe.msgprint(str(aging)+ ' agingaging')
		i.update({
			aging[0] : aging[1],
		})

	for i in data_tagihan_discount_md:
		entry_date = i['tanggal']
		i['range1'] = i['range2'] = i['range3'] = i['range4'] = i['range5'] = 0.0
		aging = get_ageing_data(entry_date,i)
		# frappe.msgprint(str(aging)+ ' agingaging')
		i.update({
			aging[0] : aging[1],
		})

	for i in data_tagihan_discount_leasing:
		entry_date = i['tanggal']
		i['range1'] = i['range2'] = i['range3'] = i['range4'] = i['range5'] = 0.0
		aging = get_ageing_data(entry_date,i)
		# frappe.msgprint(str(aging)+ ' agingaging')
		i.update({
			aging[0] : aging[1],
		})

	tampil.extend(data_tagihan_leasing or [])
	tampil.extend(data_tagihan_discount_ahm or [])
	tampil.extend(data_tagihan_discount_md or [])
	tampil.extend(data_tagihan_discount_leasing or [])

	return tampil

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
			"width": 200
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
			"label": _("Pelanggan"),
			"fieldname": "pelanggan",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 100
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Umur (hr)"),
			"fieldname": "umur",
			"fieldtype": "int",
			"width": 100
		},
		{
			"label": _("Nomor Invoice"),
			"fieldname": "nomor_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 200
		},
		{
			"label": _("Kode Barang"),
			"fieldname": "kode_barang",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200
		},
		{
			"label": _("Nama Barang"),
			"fieldname": "nama_barang",
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
			"label": _("No Rangka"),
			"fieldname": "no_rangka",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Nama Area"),
			"fieldname": "nama_area",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Tanggal"),
			"fieldname": "tanggal",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Piutang"),
			"fieldname": "piutang",
			"fieldtype": "Currency",
			"width": 200
		},
		# {
		# 	"label": _("Blm Tempo"),
		# 	"fieldname": "blm_tempo",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
	]

	columns.extend(setup_ageing_columns())

	return columns

