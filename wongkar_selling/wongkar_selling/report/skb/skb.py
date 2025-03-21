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
		year(sipm.posting_date) as tahun,
		DATE_FORMAT(sipm.posting_date,'%Y%m') as bulan,
		sle.warehouse,
		sipm.territory_real,
		sipm.cost_center,
		sipm.posting_date,
		IF(sn.nama_pemilik or sn.nama_pemilik is not null or sn.nama_pemilik !="",sn.`nama_pemilik`,sipm.`nama_pemilik`),
		sipm.item_code,
		i.item_name,
		sipm.no_rangka,
		sipm.harga,
		sipm.customer_name,
		skb.tanggal_faktur,
		skb.tanggal_terima_faktur,
		skb.no_faktur,
		skb.tanggal_serah_faktur,
		skb.tanggal_terima_stnk,
		skb.no_stnk,
		skb.no_notice_stnk,
		skb.tanggal_serah_stnk,
		skb.tanggal_terima_plat,
		skb.no_plat,
		skb.tanggal_serah_plat,
		skb.tanggal_terima_bpkb,
		skb.no_bpkb,
		skb.tanggal_serah_bpkb,
		skb.keterangan_proses_skb,
		(SELECT cost_center from `tabPurchase Receipt Item` where parent=pr.name Limit 1),
		skb.nama_pemilik,
		i.tahun_rakitan, # tahun_rakit
		i.warna,
		c.alamat,
		c.no_hp,
		(SELECT amount from `tabTabel Biaya Motor` where parent=sipm.name and type="STNK"),
		(SELECT amount from `tabTabel Biaya Motor` where parent=sipm.name and type="BPKB")
		from `tabSales Invoice Penjualan Motor` sipm
		join `tabSerial No` sn on sn.name = sipm.no_rangka
		join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
		join `tabItem` i on i.name = sipm.item_code
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		join `tabCustomer` c on c.name = sipm.pemilik
		left join `tabSKB` skb on skb.serial_no = sn.serial_no
		where sipm.docstatus = 1  and (sle.voucher_type = "Purchase Receipt" or sle.voucher_type="Stock Entry") and sipm.posting_date between '{}' and '{}' """.format(filters.get('from_date'),filters.get('to_date')),as_list=1)

	output = []

	for i in data:
		kt = i[7].split("-")
		nt = i[8].split("-")
		w = i[8].split("-")
		
		if len(w) > 2:
			w2 = w[1]+" - "+w[2]
		else:
			w2 = w[1]

		if "--" in i[9]:
			nr = i[9].split("--")
		elif "/" in i[9]:
			nr = i[9].split("/")

		output.append([
			i[0],
			i[1],
			i[27],
			i[2],# id jual i[4]
			i[3],
			i[4],
			i[5],
			i[6],#konsumen
			i[31],
			i[32],
			i[28],#skb
			kt[0],
			nt[0],
			i[30],#warna
			i[29],
			nr[0],
			nr[1],
			i[10],
			i[11],#nama_jual
			i[33],
			i[34],
			i[33]+i[34],
			i[12],
			i[13],
			i[14],
			i[15],
			i[16],
			i[17],
			i[18],
			i[19],
			i[20],
			i[21],
			i[22],
			i[23],
			i[24],
			i[25],
			i[26]
			])

	return output


def get_columns(filters):
	columns = [
		{
			"label": _("Tahun"),
			"fieldname": "tahun",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Bulan"),
			"fieldname": "bulan",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("CabAsal Unit"),
			"fieldname": "cabasal_unit",
			"fieldtype": "Data",
			"width": 100
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
			"label": _("NamaArea"),
			"fieldname": "namaarea",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TanggalJual"),
			"fieldname": "tanggaljual",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Nama Konsumen"),
			"fieldname": "name_konsumen",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Alamat"),
			"fieldname": "alamat",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("No HP"),
			"fieldname": "no_hp",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Nama SKB"),
			"fieldname": "name_skb",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Kode Tipe"),
			"fieldname": "kode_tipe",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Nama Tipe"),
			"fieldname": "nama_tipe",
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
			"label": _("Tahun Rakit"),
			"fieldname": "tahun_rakit",
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
			"label": _("OTR"),
			"fieldname": "otr",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("NamaJual"),
			"fieldname": "namajual",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Biaya STNK"),
			"fieldname": "biaya_stnk",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Biaya SKB"),
			"fieldname": "biaya_skb",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Tot Biaya SKB"),
			"fieldname": "tot_skb",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("TglMohonFaktur"),
			"fieldname": "tglmohonfaktur",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("TglTerimaFaktur"),
			"fieldname": "tglterimafaktur",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("NoFaktur"),
			"fieldname": "nofaktur",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TglSerahFaktur"),
			"fieldname": "tglserahfakur",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("TglTerimaSTNK"),
			"fieldname": "tglterimastnk",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("No STNK"),
			"fieldname": "notnk",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("No Notice pajak"),
			"fieldname": "no_notice_pajak",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Tgl Serah STNK"),
			"fieldname": "tgl_serah_stnk",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("TglTerimaPlat"),
			"fieldname": "tgl_serah_stnk",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("No Plat"),
			"fieldname": "no_plat",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Tgl Serah Plat"),
			"fieldname": "tgl_serah_plat",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("TglTerimaBPKB"),
			"fieldname": "tgl_terima_bpkb",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("No Bpkb"),
			"fieldname": "no_bpkb",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Tgl Serah BPKB"),
			"fieldname": "tgl_serah_bpkb",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Keterangan Proses SKB"),
			"fieldname": "ket",
			"fieldtype": "Data",
			"width": 100
		},
		

	]

	return columns