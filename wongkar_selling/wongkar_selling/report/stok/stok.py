# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date

def execute(filters=None):
	# columns, data = [], []
	# return columns, data

	return get_columns(filters), get_data(filters)

def get_data(filters):
	# i.tahun_rakitan
	data = frappe.db.sql(""" SELECT 
		YEAR(sle.posting_date) as tahunbei,
		DATE_FORMAT(sle.posting_date,'%Y%m') as bulanbeli,
		sle.posting_date as tanggalbeli,
		sle.warehouse,
		SUBSTRING_INDEX(sn.`item_code`,' - ', 1) AS kode_tipe,
		sn.item_name as NamaTipe,
		SUBSTRING_INDEX(sn.name,'--', 1) AS nomormesin,
		SUBSTRING_INDEX(sn.name,'--', -1) AS norangka,
		pr.supplier_delivery_note as surat,
		i.tahun_rakitan as tahunrakit, # tahun_rakit
		(SELECT cost_center from `tabPurchase Receipt Item` where parent=pr.name Limit 1),
		sn.kaca_spion as kaca,
		sn.tools,
		sn.helm,
		sn.aki,
		sn.buku_service as buku,
		sn.kunci_kontak as kunci,
		sn.jaket,
		sn.kondisi,
		pr.supplier_delivery_order as do,
		i.warna,
		sn.warehouse,
		(SELECT cost_center from `tabStock Entry Detail` where parent=se.name Limit 1),
		pr.supplier_name as sumber_stok,
		pr.set_warehouse,
		se.to_warehouse,
		sle.warehouse AS asalbeli,
		w.parent_warehouse as cabang,
		w2.parent_warehouse as pos,
		sn.purchase_rate as incoming_rate,
		sn.dpp,
		sn.delivery_date as tanggal_jual,
		sn.harga_jual
		FROM `tabSerial No` sn 
		JOIN `tabStock Ledger Entry` sle ON sle.serial_no LIKE CONCAT("%",sn.name,"%") 
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		join `tabItem` i on i.name = sn.item_code
		join `tabWarehouse` w on w.name = sn.warehouse
		join `tabWarehouse` w2 on w2.name = w.parent_warehouse
		left join `tabStock Entry` se on se.name = sle.voucher_no
		where sn.status = "Active" and (sle.voucher_type = 'Purchase Receipt' or sle.voucher_type = 'Stock Entry') group by sn.name """,as_dict=1,debug=1)

	output =[]

	# for i in data:
	# 	kt = i[4].split("-")
	# 	nt = i[5].split("-")
	# 	tes = str(i[2])

	# 	w = i[5].split("-")
		
	# 	if len(w) > 2:
	# 		w2 = w[1]+" - "+w[2]
	# 	else:
	# 		w2 = w[1]

	# 	if "--" in i[6]:
	# 		nr = i[6].split("--")
	# 	elif "/" in i[6]:
	# 		nr = i[6].split("/")

	# 	if i[23]:
	# 		asal_beli = i[23]
	# 	elif i[24]:
	# 		asal_beli = i[24]
	# 	else:
	# 		asal_beli=i[3]


		# # frappe.msgprint(tes[5:7])
		# output.append([
		# 	i[8],
		# 	i[0],
		# 	i[1],
		# 	i[2],
		# 	i[22],# sumber "MD"
		# 	asal_beli,# asal_beli i[20]
		# 	i[26], # cabang
		# 	i[25], #pos i[3] i[9] i[20]
		# 	i[20], # wh
		# 	i[4], # kt[0] kode tipe
		# 	nt[0],
		# 	nr[0],
		# 	nr[1],
		# 	i[19],
		# 	i[10],
		# 	i[11],
		# 	i[12],
		# 	i[13],
		# 	i[14],
		# 	i[15],
		# 	i[16],
		# 	i[17],
		# 	i[7],
		# 	i[18]
		# 	])

	return data

def get_columns(filters):
	columns = [
		{
			"label": _("TahunRakit"),
			"fieldname": "tahunrakit",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TahunBeli"),
			"fieldname": "tahunbei",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("BulanBeli"),
			"fieldname": "bulanbeli",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TanggalBeli"),
			"fieldname": "tanggalbeli",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Sumber Stok"),
			"fieldname": "sumber_stok",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("AsalBeli"),
			"fieldname": "asalbeli",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 100
		},
		{
			"label": _("Cabang"),
			"fieldname": "cabang",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 100
		},
		{
			"label": _("Pos"),
			"fieldname": "pos",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 100
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 100
		},
		{
			"label": _("KodeTipe"),
			"fieldname": "kode_tipe",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaTipe"),
			"fieldname": "NamaTipe",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NomorMesin"),
			"fieldname": "nomormesin",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NomorRangka"),
			"fieldname": "norangka",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Warna"),
			"fieldname": "warna",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Incoming Rate"),
			"fieldname": "incoming_rate",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("KacaSpion"),
			"fieldname": "kaca",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Tools"),
			"fieldname": "tools",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Helm"),
			"fieldname": "helm",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Aki"),
			"fieldname": "aki",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("BukuServis"),
			"fieldname": "buku",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Jaket"),
			"fieldname": "jaket",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("KunciKontak"),
			"fieldname": "kunci",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Kondisi"),
			"fieldname": "kondisi",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Surat Jalan"),
			"fieldname": "surat",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("No Do"),
			"fieldname": "do",
			"fieldtype": "Data",
			"width": 100
		},
		# {
		# 	"label": _("Tanggal Jual"),
		# 	"fieldname": "tanggal_jual",
		# 	"fieldtype": "Date",
		# 	"width": 100
		# },
		# {
		# 	"label": _("DPP"),
		# 	"fieldname": "dpp",
		# 	"fieldtype": "Currency",
		# 	"width": 100
		# },
		# {
		# 	"label": _("Harga Jual"),
		# 	"fieldname": "harga_jual",
		# 	"fieldtype": "Currency",
		# 	"width": 100
		# },
	]

	return columns
