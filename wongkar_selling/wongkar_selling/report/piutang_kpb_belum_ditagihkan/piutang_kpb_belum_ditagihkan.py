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
			c.customer AS customer,
			sp.customer_name AS nama_pemilik,
			sp.posting_date AS tgl_jual,
			sp.name AS sipm,
			spi.item_code AS kode_barang,
			spi.item_name AS nama_barang,
			sp.no_rangka_manual_atau_lama AS no_rangka,
			sp.no_mesin AS no_mesin,
			sp.grand_total AS outstanding_amount,
			sp.cost_center AS nama_area,
			ip.name,
			l.`outstanding_amount` as l_outstanding_amount
			FROM `tabSales Invoice Sparepart Garansi` sp
			JOIN `tabSales Invoice Sparepart Garansi Item` spi ON spi.parent = sp.name
			LEFT JOIN `tabCompany` c ON c.name = sp.company
			LEFT JOIN `tabList Invoice Penagihan Garansi` l ON l.sales_invoice_sparepart_garansi = sp.name
			LEFT JOIN `tabInvoice Penagihan Garansi` ip ON ip.`name` = l.`parent` AND ip.`docstatus` = 1
			WHERE sp.posting_date <= '{}' AND sp.`docstatus` = 1 AND ip.name IS NULL and sp.tagihan = 0
			{}
			GROUP BY sp.name ORDER BY sp.posting_date ASC
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
			"label": _("Nama Vendor"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200
		},
		{
			"label": _("Nama Customer"),
			"fieldname": "nama_pemilik",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tanggal Transaksi"),
			"fieldname": "tgl_jual",
			"fieldtype": "Date",
			"width": 200
		},
		{
			"label": _("No Transaksi"),
			"fieldname": "sipm",
			"fieldtype": "Link",
			"options": "Sales Invoice Sparepart Garansi",
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

