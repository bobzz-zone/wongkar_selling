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
	# i.tahun_rakitan
	data = frappe.db.sql(""" SELECT 
		year(sipm.posting_date) as tahun,
		DATE_FORMAT(sipm.posting_date,'%Y%m') as bulan,
		sipm.territory_real,
		sipm.cost_center,
		sipm.posting_date,
		sipm.nama_pemilik,
		c.kecamatan,
		c.kelurahan,
		c.nama_dati2,
		c.alamat,
		sle.warehouse,
		c.no_hp,
		c.salutation,
		c.agama,
		c.tanggal_lahir,
		c.no_ktp,
		c.no_kk,
		i.item_code,
		i.item_name,
		sipm.no_rangka,
		sipm.harga,
		sipm.cara_bayar,
		sipm.nominal_diskon,
		sipm.total_advance,
		sipm.name,
		sipm.customer_name,
		IF(IFNULL(SUM(tdl.nominal),0),SUM(tdl.nominal),0),
		sipm.adj_discount,
		sipm.outstanding_amount,
		sipm.nama_promo,
		u.full_name,
		sipm.status,
		sn.tanggal_faktur,
		(SELECT cost_center from `tabPurchase Receipt Item` where parent=pr.name Limit 1),
		sn.nama_pemilik,
		i.tahun_rakit,
		sipm.dp_gross_hitung,
		sipm.tanggal_tagih,
		sipm.tanggal_cair,
		IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0),
		sipm.marketing,
		sipm.jangka_waktu,
		sipm.angsuran,
		IF(sipm.tanggal_tagih,DATEDIFF(sipm.tanggal_tagih, sipm.posting_date),0),
		sipm.tanggal_po,
		sipm.no_po_leasing,
		i.warna
		from `tabSales Invoice Penjualan Motor` sipm 
		join `tabCustomer` c on c.name = sipm.pemilik
		join `tabSerial No` sn on sn.name = sipm.no_rangka
		join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
		join `tabItem` i on i.name = sipm.item_code
		join `tabUser` u on u.name = sipm.owner
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		LEFT JOIN `tabTable Disc Leasing` tdl ON tdl.parent = sipm.name
		where sipm.docstatus = 1 and sle.voucher_type = "Purchase Receipt" and sipm.posting_date between '{}' and '{}' group by sipm.name order by sipm.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_list = 1)

	
	output = []
	for i in data:
		kd = i[17].split("-")
		i_n = i[18].split("-")
		w = i[18].split("-")
		if "--" in i[19]:
			nr = i[19].split("--")
		elif "/" in i[19]:
			nr = i[19].split("/")
		if len(w) > 2:
			w2 = w[1]+" - "+w[2]
		else:
			w2 = w[1]
		output.append([i[0],i[1],i[33],i[10],i[2],i[3],i[4],i[5],i[6],i[7],i[8],i[9],i[11],i[12],i[13],i[14],i[15],i[16],kd[0],i_n[0],i[46],i[35],nr[0],nr[1],i[20],i[25],i[21],i[22],i[23]])

	output_beban = []
	for d in data:
		data2 = frappe.db.sql(""" SELECT sum(td.nominal) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name where sipm.name = '{}' and td.customer = 'AHM' group by sipm.name """.format(d[24]),as_list=1)
		datamd = frappe.db.sql(""" SELECT sum(td.nominal) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name where sipm.name = '{}' and td.customer = 'Anugerah Perdana' group by sipm.name """.format(d[24]),as_list=1)
		datad = frappe.db.sql(""" SELECT sum(td.nominal) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name where sipm.name = '{}' and td.customer = 'Dealer' group by sipm.name """.format(d[24]),as_list=1)

		disc_leasing = frappe.db.sql(""" SELECT nominal from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Disc Leasing` td ON td.`parent` = sipm.name where sipm.name = '{}' """.format(d[24]),as_list=1)


		bl = 0
		tam_les = 0
		tam_lain = 0
		if len(disc_leasing) == 3:
			bl = disc_leasing[0][0]
			tam_les = disc_leasing[1][0]
			tam_lain = disc_leasing[2][0]
		elif len(disc_leasing) == 2:
			bl = disc_leasing[0][0]
			tam_les = disc_leasing[1][0]
		elif len(disc_leasing) == 1:
			bl = disc_leasing[0][0]

		
		# data_leasing = frappe.db.sql(""" SELECT td.nominal from `tabSales Invoice Penjualan Motor` sipm 
		# 	LEFT JOIN `tabTable Disc Leasing` td ON td.`parent` = sipm.name where sipm.name = '{}' order by idx asc """.format(d[24]),as_list=1)

		# if data_leasing:
		# 	if len(data_leasing) > 2:
		# 		pass

		ahm=0
		ap = 0
		dea = 0
		if data2:
			ahm = data2[0][0]
		if datamd:
			ap = datamd[0][0]
		if datad:
			ap = datad[0][0]

		# if datad:
		# 	output_beban.append([0,0,datad[0][0],0,0])
		# else:
		# 	output_beban.append([0,0,0,0,0])

		# if data2 and datamd and datad:
		# 	output_beban.append([data2[0][0],datamd[0][0],datad[0][0],0,0])
		# elif data2 and not datamd and datad:
		# 	output_beban.append([data2[0][0],0,datad[0][0],0,0])
		# elif data2 and datamd and not datad:
		# 	output_beban.append([data2[0][0],datamd[0][0],0,0,0])
		# elif data2 and not datamd and not datad:
		# 	output_beban.append([data2[0][0],0,0,0,0])
		# elif not data2 and datamd and datad:
		# 	output_beban.append([0,datamd[0][0],datad[0][0],0,0])
		# elif not data2 and datamd and not datad:
		# 	output_beban.append([0,datamd[0][0],0,0,0])
		# elif not data2 and not datamd and datad:
		# 	output_beban.append([0,0,datad[0][0],0,0])
		# else:	
		# 	output_beban.append([0,0,0,0,0])
	
		output_beban.append([ahm,ap,ap])
		

	# output_tes = output
	conter = 0
	tmp = []
	for ot in output:
		ot.extend(output_beban[conter])
		tmp.append(ot)
		conter = conter+1
	con = 0
	tmp2 = tmp
	tampil = []	
	for t in tmp2:
		# frappe.msgprint(data[con][24])
		data_stnk = frappe.db.sql(""" SELECT sum(bm.amount) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTabel Biaya Motor` bm ON bm.`parent` = sipm.name where sipm.name = '{}' and bm.type = "STNK" """.format(data[con][24]),as_list=1)
		data_bpkb = frappe.db.sql(""" SELECT sum(bm.amount) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTabel Biaya Motor` bm ON bm.`parent` = sipm.name where sipm.name = '{}' and bm.type = "BPKB" """.format(data[con][24]),as_list=1)
		data_dealer = frappe.db.sql(""" SELECT sum(bm.amount) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTabel Biaya Motor` bm ON bm.`parent` = sipm.name where sipm.name = '{}' and bm.vendor = "Dealer" """.format(data[con][24]),as_list=1)

		cair = frappe.db.sql(""" SELECT tagihan_sipm-outstanding_sipm from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabDaftar Tagihan Leasing` bm ON bm.`no_invoice` = sipm.name where bm.docstatus=1 and sipm.name='{0}' """.format(data[con][24]),as_list=1)

		cair_disc = frappe.db.sql(""" SELECT nilai-terbayarkan from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabDaftar Tagihan Leasing` bm ON bm.`no_invoice` = sipm.name where bm.docstatus=1 and sipm.name='{0}' """.format(data[con][24]),as_list=1)
		# frappe.msgprint(str(data_stnk[0][0]))
		# frappe.msgprint(str(cair)+" "+data[con][24])
		stnk=0
		d_dealer = 0
		d_cair = 0
		ket_cair = 'N'
		d_caird = 0
		d_bpkb = 0
		if data_stnk:
			stnk=data_stnk[0][0]
		if data_dealer:
			d_dealer=data_dealer[0][0]
		if cair:
			d_cair=cair[0][0]
			ket_cair = 'Y'
		if cair_disc:
			d_caird=cair_disc[0][0]
		if data_bpkb:
			d_bpkb=data_bpkb[0][0]
		
		tampil.append([
			t[0],
			t[1],
			t[2],
			t[3],
			t[4],
			t[5],
			t[6],
			t[7],
			data[con][34],
			t[8],
			t[9],
			t[10],
			t[11],
			t[12],
			t[13],
			t[14],
			t[15],
			t[16],
			t[17],
			t[18],
			t[19],
			t[20],
			t[21],
			t[22],
			t[23],#no rangka
			t[24],
			t[25],
			t[26],
			t[27],#potongjual nominal diskon
			t[28],
			t[29],
			t[30],
			t[31],
			bl, # beban leasing
			d_dealer,#cashback
			data[con][36],#gross dp
			tam_les,
			tam_lain, # tambah lain d_dealer
			"",# ket tambahn
			data[con][28],
			d_cair,# cair
			d_caird,
			d_cair-d_caird,
			ket_cair,
			data[con][29],
			data[con][37],#tt
			data[con][38],#tc
			data[con][43],
			data[con][39],#hc
			data[con][28],#piutang Konsumen
			data[con][44],
			data[con][45],
			# "SALES LAPANGAN",
			data[con][40],
			data[con][41],#top kredit
			data[con][42], # angsuran
			data[con][32],
			data[con][31],
			stnk,#stnk
			d_bpkb
			])
		con = con + 1


	# for t in data:
	# 	tmp2.append([t[26]])


	# frappe.msgprint(str(tampil))
	return tampil

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
			"label": _("NamaJual"),
			"fieldname": "namajual",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Cara Bayar"),
			"fieldname": "Cara Bayar",
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
			"fieldname": "cashBack",
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
			"fieldname": "kettambahanLain",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("PiutangLeasing"),
			"fieldname": "PiutangLeasing",
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
			"fieldname": "haritagih",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("HariCair"),
			"fieldname": "HariCair",
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
			"label": _("Marketing"),
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
			"fieldtype": "Int",
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
		# {
		# 	"label": _("Info SKB"),
		# 	"fieldname": "infoskb",
		# 	"fieldtype": "Data",
		# 	"width": 100
		# },
	]
	return columns