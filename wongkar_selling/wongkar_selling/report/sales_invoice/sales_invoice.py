# Copyright (c) 2013, DAS and contributors
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
	# po = filters.get('year')
	# year = po+"%"
	# frappe.msgprint(year)
	
	data = frappe.db.sql(""" 
			SELECT 
				YEAR(sipm.posting_date) AS tahun,
				DATE_FORMAT(sipm.posting_date,'%Y%m') AS bulan,
				sipm.name AS sipm,
				sle.name,
				sle2.name,
				se.`purpose`,
				IF(sle.name IS NOT NULL,sle.`warehouse`,sle2.`warehouse`)  AS cabasal_unit,
				cc2.parent_cost_center AS cabid_jual,
				cc.parent_cost_center AS cab_area_jual,
				sipm.`cost_center` AS namaarea,
				sipm.`posting_date` AS tanggaljual,
				sipm.`nama_pemilik` AS nama_pemilik,
				sn.nama_pemilik AS nama_skb,
				c.`nama_kecamatan` AS namakecamatan,
				c.`nama_kelurahan` AS namakelurahan,
				c.alamat,
				c.`no_hp` AS hp,
				c.`salutation` AS namaprovesi,
				c.`agama` AS namaagama,
				c.`tanggal_lahir` AS tanggallahir,
				c.`no_ktp` AS ktp,
				c.`no_kk` AS kk,
				SUBSTRING_INDEX(sipm.`item_code`,' - ', 1) AS kode_tipe,
				i.item_name AS nama_tipe,
				i.warna,
				i.`tahun_rakitan` AS tahun_rakit,
				sn.`no_mesin`,
				sn.`no_rangka`,
				sipm.`harga` as otr,
				IF(sipm.cara_bayar = "Credit",sipm.customer_name,"CASH") AS namajual,
				sipm.`cara_bayar`,
				sipm.`nominal_diskon` AS potonganjual,
				IF(sipm.`cara_bayar`="Credit",sipm.`total_advance`,sipm.`harga`-sipm.`nominal_diskon`) AS dpmurni,
				td.`nominal` AS bebanahm,
				td2.`nominal` AS bebanmd,
				IFNULL(td3.`nominal`,0) AS bebandealer,
				0 AS cashback,
				IF(sipm.`cara_bayar`="Credit",sipm.`total_advance`,sipm.`harga`-sipm.`nominal_diskon`) + sipm.nominal_diskon + IFNULL(td3.`nominal`,0) AS grosdp,
				NULL AS kettambahanlain,
				sipm.harga - (IF(sipm.`cara_bayar`="Credit",sipm.`total_advance`,sipm.`harga`-sipm.`nominal_diskon`) + sipm.nominal_diskon + IFNULL(td3.`nominal`,0)) AS piutangleasing,
				ltpl.name,
				IF(ltpl.name IS NOT NULL,ltpl.terbayarkan_sipm,0) AS cair,
				IF(dtl.name IS NOT NULL,IF(dtl.terbayarkan>0,dtl.terbayarkan+(dtl.nilai_diskon*tdl.pph/100),0),0) AS cairlain,
				0  AS selisihcair,
				IF(IFNULL(ltpl.terbayarkan_sipm,0)> 0,'Y','N') AS ketcair,
				sipm.nama_promo AS namaprog,
				sipm.tanggal_tagih AS tanggaltagih,
				sipm.tanggal_cair AS tanggalcair,
				IF(sipm.tanggal_tagih,DATEDIFF(sipm.tanggal_tagih, sipm.posting_date),0) AS ht,
				IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0) AS hc,
				0 AS piutang_konsumen,
				sipm.tanggal_po AS tgl_po,
				sipm.no_po_leasing AS no_po,
				sipm.nama_penjualan,
				sipm.sales_man AS marketing,
				sipm.jangka_waktu as jangkawaktu,
				sipm.angsuran,
				s.tanggal_faktur as tglmohonfaktur,
				sipm.status as docstaus,
				sn.biaya_stnk as biaya_stnk,
				sn.biaya_bpkb as biaya_skb,
				sipm.foto_gesekan as foto_nosin,
				sipm.foto_gesekan_no_rangka as foto_rangka,
				sipm.po_attch as foto_po,
				c.foto_ktp as foto_ktp,
				c.foto_kk as foto_kk,
				sipm.foto_invoice as foto_inv,
				sipm.foto_surat_jalan as foto_sj,
				sipm.foto_kwitansi_uang_muka as foto_kw_um,
				sipm.foto_kwitansi_sub as foto_kw_sub,
				sipm.net_total as dpp,
				t.tax_amount as ppn,
				sipm.`harga` - sipm.`nominal_diskon` - sn.biaya_stnk - sn.biaya_bpkb as total_harga
			FROM `tabSales Invoice Penjualan Motor` sipm 
			join `tabSales Taxes and Charges` t on t.parent = sipm.name and t.idx = 1
			JOIN `tabItem` i ON i.`name` = sipm.`item_code`
			JOIN `tabCustomer` c ON c.name = sipm.`pemilik`
			JOIN `tabSerial No` sn ON sn.name = sipm.no_rangka
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name AND td.customer = 'AHM'
			LEFT JOIN `tabTable Discount` td2 ON td2.`parent` = sipm.name AND td2.customer = 'MD'
			LEFT JOIN `tabTable Discount` td3 ON td3.`parent` = sipm.name AND td3.customer = 'Dealer'
			LEFT JOIN `tabList Tagihan Piutang Leasing` ltpl ON ltpl.docstatus = 1 AND ltpl.no_invoice = sipm.name
			LEFT JOIN `tabDaftar Tagihan Leasing` dtl ON dtl.docstatus = 1 AND dtl.no_invoice = sipm.name
			LEFT JOIN `tabTagihan Discount Leasing` tdl ON tdl.name = dtl.parent
			LEFT JOIN `tabSKB` s ON sn.name = s.serial_no
			LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
			LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
			LEFT JOIN `tabStock Ledger Entry` sle ON sle.voucher_type = "Purchase Receipt" AND  sle.serial_no LIKE CONCAT("%",sn.name,"%")
			LEFT JOIN `tabStock Ledger Entry` sle2 ON sle2.voucher_type = "Stock Entry" AND sle2.serial_no LIKE CONCAT("%",sn.name,"%")
			LEFT JOIN `tabStock Entry` se ON se.`name` = sle2.`voucher_no` AND se.`purpose` = 'Material Receipt'
			LEFT JOIN `tabCost Center` cc on cc.name = sipm.cost_center
			LEFT JOIN `tabCost Center` cc2 on cc2.name = cc.parent_cost_center
			WHERE sipm.docstatus = 1 
			AND sipm.posting_date BETWEEN '{}' AND '{}'
			GROUP BY sipm.name ORDER BY sipm.posting_date ASC 
			 """.format(filters.get('from_date'),filters.get('to_date')),as_dict = 1)
	
	for i in data:
		bl = 0
		tam_les = 0
		tam_lain = 0
		data_leasing = frappe.db.sql(""" SELECT tdl.name,tdl.nominal,tdl.idx from 
			`tabTable Disc Leasing` tdl where parent = '{}' """.format(i['sipm']),as_dict=1)
		if len(data_leasing) == 3:
			bl = data_leasing[0]['nominal']
			tam_les = data_leasing[1]['nominal']
			tam_lain = data_leasing[2]['nominal']
		elif len(data_leasing) == 2:
			bl = data_leasing[0]['nominal']
			tam_les = data_leasing[1]['nominal']
		elif len(data_leasing) == 1:
			bl = data_leasing[0]['nominal']
		i['piutangleasing'] = i['piutangleasing'] + bl +tam_les+tam_lain
		i['piutangkonsumen'] = i['piutangleasing']
		i['selisihcair'] =  i['piutangleasing']  - (i['cair']+i['cairlain'])
		if i['foto_nosin']:
			i['foto_nosin'] = "<a href='"+frappe.utils.get_url()+i['foto_nosin']+"'>"+frappe.utils.get_url()+i['foto_nosin']+"</a>"
		if i['foto_rangka']:
			i['foto_rangka'] = "<a href='"+frappe.utils.get_url()+i['foto_rangka']+"'>"+frappe.utils.get_url()+i['foto_rangka']+"</a>"
		if i['foto_po']:
			i['foto_po'] = "<a href='"+frappe.utils.get_url()+i['foto_po']+"'>"+frappe.utils.get_url()+i['foto_po']+"</a>"
		
		if i['foto_ktp']:
			i['foto_ktp'] = "<a href='"+frappe.utils.get_url()+i['foto_ktp']+"'>"+frappe.utils.get_url()+i['foto_ktp']+"</a>"
		
		if i['foto_kk']:
			i['foto_kk'] = "<a href='"+frappe.utils.get_url()+i['foto_kk']+"'>"+frappe.utils.get_url()+i['foto_kk']+"</a>"
		
		if i['foto_inv']:
			i['foto_inv'] = "<a href='"+frappe.utils.get_url()+i['foto_inv']+"'>"+frappe.utils.get_url()+i['foto_inv']+"</a>"
		
		if i['foto_sj']:
			i['foto_sj'] = "<a href='"+frappe.utils.get_url()+i['foto_sj']+"'>"+frappe.utils.get_url()+i['foto_sj']+"</a>"
		
		if i['foto_kw_um']:
			i['foto_kw_um'] = "<a href='"+frappe.utils.get_url()+i['foto_kw_um']+"'>"+frappe.utils.get_url()+i['foto_kw_um']+"</a>"
		
		if i['foto_kw_sub']:
			i['foto_kw_sub'] = "<a href='"+frappe.utils.get_url()+i['foto_kw_sub']+"'>"+frappe.utils.get_url()+i['foto_kw_sub']+"</a>"

		i.update({
				'bebanleasing': bl,
				'tambahanleasing': tam_les,
				'tambahanLain': tam_lain
			})
	
	# frappe.msgprint(str(data)+" data")
	
	return data

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
			"label": _("SIPM"),
			"fieldname": "sipm",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 200
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
			"fieldname": "nama_pemilik",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Nama SKB"),
			"fieldname": "nama_skb",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaKecamatan"),
			"fieldname": "namakecamatan",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaKelurahan"),
			"fieldname": "namakelurahan",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaDati2"),
			"fieldname": "namadati2",
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
			"label": _("HP"),
			"fieldname": "hp",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaProfesi"),
			"fieldname": "namaprovesi",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaAgama"),
			"fieldname": "namaagama",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TanggalLahir"),
			"fieldname": "tanggallahir",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("No KTP"),
			"fieldname": "ktp",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("No KK"),
			"fieldname": "kk",
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
			"label": _("DPP"),
			"fieldname": "dpp",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("PPN"),
			"fieldname": "ppn",
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
			"label": _("Cara Bayar"),
			"fieldname": "cara_bayar",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("PotonganJual"),
			"fieldname": "potonganjual",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Adj Discount"),
			"fieldname": "adj_discount",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("DPMurni"),
			"fieldname": "dpmurni",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("BebanAHM"),
			"fieldname": "bebanahm",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("BebanMD"),
			"fieldname": "bebanmd",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("BebanDealer"),
			"fieldname": "bebandealer",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("BebanLeasing"),
			"fieldname": "bebanleasing",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("CashBack"),
			"fieldname": "cashback",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("GrosDP"),
			"fieldname": "grosdp",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("TambahanLeasing"),
			"fieldname": "tambahanleasing",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("TambahanLain"),
			"fieldname": "tambahanLain",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Ket Tambahan Lain"),
			"fieldname": "kettambahanlain",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("PiutangLeasing"),
			"fieldname": "piutangleasing",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Cair"),
			"fieldname": "cair",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("CairLain"),
			"fieldname": "cairlain",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("SelisihCair"),
			"fieldname": "selisihcair",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("KetCair"),
			"fieldname": "ketcair",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("NamaProg"),
			"fieldname": "namaprog",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TanggalTagih"),
			"fieldname": "tanggaltagih",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("TanggalCair"),
			"fieldname": "tanggalcair",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("HariTagih"),
			"fieldname": "ht",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("HariCair"),
			"fieldname": "hc",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("PiutangKonsumen"),
			"fieldname": "piutangkonsumen",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Tgl PO"),
			"fieldname": "tgl_po",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("No PO"),
			"fieldname": "no_po",
			"fieldtype": "Data",
			"width": 100
		},
		# {
		# 	"label": _("NamaBooking"),
		# 	"fieldname": "namabooking",
		# 	"fieldtype": "Data",
		# 	"width": 100
		# },
		{
			"label": _("Nama Penjualan"),
			"fieldname": "nama_penjualan",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Nama Marketing"),
			"fieldname": "marketing",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("TOP Kredit"), # jangkawaktu
			"fieldname": "jangkawaktu",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Angsuran"),
			"fieldname": "angsuran",
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
			"label": _("Doc Status"),
			"fieldname": "docstaus",
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
			"label": _("Total Harga"),
			"fieldname": "total_harga",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Foto Gesekan No Mesin"),
			"fieldname": "foto_nosin",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto Gesekan No Rangka"),
			"fieldname": "foto_rangka",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto PO Attch"),
			"fieldname": "foto_po",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto KTP"),
			"fieldname": "foto_ktp",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto KK"),
			"fieldname": "foto_kk",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto Invoice"),
			"fieldname": "foto_inv",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto Surat Jalan"),
			"fieldname": "foto_sj",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto Kwitansi Uang Muka"),
			"fieldname": "foto_kw_um",
			"fieldtype": "HTML",
			"width": 100
		},
		{
			"label": _("Foto Kwitansi Sub"),
			"fieldname": "foto_kw_sub",
			"fieldtype": "HTML",
			"width": 100
		},
		# {
		# 	"label": _("Info SKB"),
		# 	"fieldname": "infoskb",
		# 	"fieldtype": "Data",
		# 	"width": 100
		# },
	]
	return columns
