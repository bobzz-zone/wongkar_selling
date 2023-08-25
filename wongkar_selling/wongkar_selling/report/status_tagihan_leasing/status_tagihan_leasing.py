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
	kondisi = ""
	if filters.get("area"):
		kondisi = " and ec.cost_center = '{}' ".format(filters.get("area"))

	data = frappe.db.sql(""" SELECT 
			sipm.name AS sipm,
			sipm.customer_name AS leasing,
			w2.parent_warehouse AS cabid_jual,
			w.parent_warehouse AS cab_area_jual,
			sipm.nama_pemilik AS nama_konsumen,
			IFNULL(peit.date,null) AS tgl_setor_dp,
			sipm.posting_date AS tgl_jual,
			sipm.tanggal_tagih AS tgl_tagih,
			sipm.outstanding_amount AS piutang,
			IF(ltpl.name IS NOT NULL,ltpl.outstanding_sipm,0) AS tagihan_pokok,
			IFNULL(SUM(tpt.`nilai`),0) AS pencairan_tagihan_pokok,
			fp.posting_date AS tgl_pencairan_pokok,
			ltpl.`mode_of_payment_sipm` AS mode_pokok,
			IF(dtl.name IS NULL,tdl.nominal,if(dtl.outstanding_discount<=0,sum(dtl.outstanding_discount),SUM(dtl.outstanding_discount+(dtl.nilai_diskon*tdc.pph/100)))) AS tambahan_leasing,
			IFNULL(SUM(tpt2.`nilai`+(dtl.nilai_diskon*tdc.pph/100)),0) AS pencairan_tambahan_leasing,
			fp2.`posting_date` AS tgl_pencairan_tambahan_leasing,
			dtl.`mode_of_payment_discount` AS mode_tambahan_leasing,
			IF(ltpl.name IS NOT NULL,ltpl.tagihan_sipm,0) - IFNULL(SUM(tpt.`nilai`),0) - IFNULL(SUM(tpt2.`nilai`),0) + IF(dtl.name IS NULL,tdl.nominal,dtl.nilai) AS selisih_cair,
			IF(tpt.cek_realisasi = 1,"Sudah Realisasi",IF(ltpl.name IS NOT NULL,"Belum Realisasi","Belum Tagih"))  AS ket,
			IFNULL(IF(sipm.tanggal_tagih,DATEDIFF(tl.date, sipm.posting_date),0),0) AS ht,
			IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0) AS hc
			FROM `tabSales Invoice Penjualan Motor` sipm
			LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
			LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
			LEFT JOIN `tabList Tagihan Piutang Leasing` ltpl ON ltpl.docstatus = 1 AND ltpl.no_invoice = sipm.name
			LEFT JOIN `tabTagihan Leasing` tl ON tl.name = ltpl.parent
			LEFT JOIN `tabTagihan Payment Table` tpt ON tpt.docstatus = 1 AND ltpl.parent = tpt.doc_name
			LEFT JOIN `tabForm Pembayaran` fp ON fp.`name` = tpt.`parent` AND fp.`type` = 'Pembayaran Tagihan Leasing'
			LEFT JOIN `tabTable Disc Leasing` tdl ON tdl.`parent` = sipm.`name`
			LEFT JOIN `tabDaftar Tagihan Leasing` dtl ON dtl.`docstatus` = 1 AND dtl.`no_invoice` = sipm.name
			LEFT JOIN `tabTagihan Discount Leasing` tdc ON tdc.name = dtl.parent
			LEFT JOIN `tabTagihan Payment Table` tpt2 ON tpt2.docstatus = 1 AND dtl.parent = tpt2.doc_name
			LEFT JOIN `tabForm Pembayaran` fp2 ON fp2.`name` = tpt2.`parent` AND fp2.`type` = 'Pembayaran Diskon Leasing'
			left join `tabSales Invoice Advance` sia on sia.parent =sipm.name
			left join `tabJournal Entry` je on je.name = sia.reference_name
			left join `tabPenerimaan DP` dp on dp.name = je.penerimaan_dp
			left join `tabList Penerimaan DP` ldp on ldp.penerimaan_dp  = je.penerimaan_dp
			left join `tabPayment Entry Internal Transfer` peit on peit.name = ldp.parent
			WHERE sipm.docstatus = 1 AND sipm.cara_bayar = "Credit" AND sipm.posting_date BETWEEN '{}' AND '{}'
		 """.format(filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)

	frappe.msgprint(str(data))
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("SIPM"),
			"fieldname": "sipm",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 200
		},
		{
			"label": _("Leasing"),
			"fieldname": "leasing",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Cab ID Jual"),
			"fieldname": "cabid_jual",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Cab Area Jual"),
			"fieldname": "cab_area_jual",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Nama Konsumen"),
			"fieldname": "nama_konsumen",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tgl Setor DP"),
			"fieldname": "tgl_setor_dp",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Tgl Jual"),
			"fieldname": "tgl_jual",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Tgl Tagih"),
			"fieldname": "tgl_tagih",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Piutang"),
			"fieldname": "piutang",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tagihan Pokok"),
			"fieldname": "tagihan_pokok",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Pencairan Tagihan Pokok"),
			"fieldname": "pencairan_tagihan_pokok",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tgl Pencairan Pokok"),
			"fieldname": "tgl_pencairan_pokok",
			"fieldtype": "Date",
			"width": 180
		},
		{
			"label": _("Mode Of Payment Pokok"),
			"fieldname": "mode_pokok",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Tambahan Leasing"),
			"fieldname": "tambahan_leasing",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Pencairan Tambahan Leasing"),
			"fieldname": "pencairan_tambahan_leasing",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tgl Pencairan Tambahan Leasing"),
			"fieldname": "tgl_pencairan_tambahan_leasing",
			"fieldtype": "Date",
			"width": 200
		},
		{
			"label": _("Mode Of Payment Tambahan Leasing"),
			"fieldname": "mode_tambahan_leasing",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Selish Cair"),
			"fieldname": "selisih_cair",
			"fieldtype": "Currency",
			"width": 180
		},
		{
			"label": _("Ket Penagihan"),
			"fieldname": "ket",
			"fieldtype": "Data",
			"width": 180
		},


		# {
		# 	"label": _("Belum Terbayrakan Tambahan Leasing"),
		# 	"fieldname": "bt_tl",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("Sudah Terbayrakan Tambahan Leasing"),
		# 	"fieldname": "st_tl",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("outstanding Tambahan Leasing"),
		# 	"fieldname": "o_tl",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },

		# {
		# 	"label": _("Belum Terbayrakan Tagihan Pokok"),
		# 	"fieldname": "bt_tp",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("Sudah Terbayrakan Tagihan Pokok"),
		# 	"fieldname": "st_tp",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },
		# {
		# 	"label": _("outstanding Tagihan Pokok"),
		# 	"fieldname": "o_tp",
		# 	"fieldtype": "Currency",
		# 	"width": 200
		# },

		
		{
			"label": _("Ht"),
			"fieldname": "ht",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Hc"),
			"fieldname": "hc",
			"fieldtype": "Int",
			"width": 100
		},
	]

	return columns

