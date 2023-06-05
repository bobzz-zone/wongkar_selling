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
		YEAR(sle.posting_date),
		DATE_FORMAT(sle.posting_date,'%Y%m') as bulan,
		sle.posting_date,
		sle.warehouse,
		sn.item_code,
		sn.item_name,
		sn.name,
		pr.supplier_delivery_note,
		i.tahun_rakitan, # tahun_rakit
		(SELECT cost_center from `tabPurchase Receipt Item` where parent=pr.name Limit 1),
		sn.kaca_spion,
		sn.tools,
		sn.helm,
		sn.aki,
		sn.buku_service,
		sn.kunci_kontak,
		sn.jaket,
		sn.kondisi,
		pr.supplier_delivery_order,
		i.warna,
		sn.warehouse,
		(SELECT cost_center from `tabStock Entry Detail` where parent=se.name Limit 1),
		pr.supplier
		FROM `tabSerial No` sn 
		join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		join `tabItem` i on i.name = sn.item_code
		left join `tabStock Entry` se on se.name = sle.voucher_no
		where sn.status = "Active" and (sle.voucher_type = 'Purchase Receipt' or sle.voucher_type = 'Stock Entry') group by sn.name """,as_list=1)

	output =[]

	for i in data:
		kt = i[4].split("-")
		nt = i[5].split("-")
		tes = str(i[2])

		w = i[5].split("-")
		
		if len(w) > 2:
			w2 = w[1]+" - "+w[2]
		else:
			w2 = w[1]

		if "--" in i[6]:
			nr = i[6].split("--")
		elif "/" in i[6]:
			nr = i[6].split("/")

		if i[9]:
			asal_beli = i[9]
		else:
			asal_beli = i[21]
		# frappe.msgprint(tes[5:7])
		output.append([
			i[8],
			i[0],
			i[1],
			i[2],
			i[22],# sumber "MD"
			i[20],#asal_beli
			i[20],# cabang
			i[9],#pos i[3]
			i[20],# wh
			i[4], # kt[0] kode tipe
			nt[0],
			nr[0],
			nr[1],
			i[19],
			i[10],
			i[11],
			i[12],
			i[13],
			i[14],
			i[15],
			i[16],
			i[17],
			i[7],
			i[18]
			])

	return output

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
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Cabang"),
			"fieldname": "cabang",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Pos"),
			"fieldname": "pos",
			"fieldtype": "Data",
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
			"fieldname": "Norangka",
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

	]

	return columns
