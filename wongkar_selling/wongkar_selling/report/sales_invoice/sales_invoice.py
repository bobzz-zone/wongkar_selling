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
	
	data = frappe.db.sql(""" SELECT 
		year(sipm.posting_date) as tahun,
		DATE_FORMAT(sipm.posting_date,'%Y%m') as bulan,
		sipm.territory_real,
		sipm.cost_center,
		sipm.posting_date,
		sipm.nama_pemilik,
		c.nama_kecamatan,
		c.nama_kelurahan,
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
		IF(sipm.cara_bayar = "Cash",sipm.total_advance-sipm.nominal_diskon,sipm.total_advance),
		sipm.name,
		IF(sipm.cara_bayar = "Credit",sipm.customer_name,"CASH"),
		IF(IFNULL(SUM(tdl.nominal),0),SUM(tdl.nominal),0),
		sipm.adj_discount,
		sipm.outstanding_amount,
		sipm.nama_promo,
		u.full_name,
		sipm.status,
		sn.tanggal_faktur,
		(SELECT cost_center from `tabPurchase Receipt Item` where parent=pr.name Limit 1),
		IF(sn.nama_pemilik or sn.nama_pemilik is not null or sn.pemilik !="",sn.`nama_pemilik`,sipm.`nama_pemilik`),
		i.tahun_rakitan,# i.tahun_rakitan tahun_rakit
		sipm.dp_gross_hitung,
		sipm.tanggal_tagih,
		sipm.tanggal_cair,
		IF(sipm.tanggal_tagih AND sipm.tanggal_cair,DATEDIFF(sipm.tanggal_cair, sipm.tanggal_tagih),0),
		sipm.sales_man,# sipm.sales_man marketing
		sipm.jangka_waktu,
		sipm.angsuran,
		IF(sipm.tanggal_tagih,DATEDIFF(sipm.tanggal_tagih, sipm.posting_date),0),
		sipm.tanggal_po,
		sipm.no_po_leasing,
		i.warna,
		sipm.nama_penjualan,
		sipm.foto_gesekan,
		sipm.foto_gesekan_no_rangka,
		sipm.po_attch,
		c.foto_ktp,
		c.foto_kk,
		sipm.foto_invoice,
		sipm.foto_surat_jalan,
		sipm.foto_kwitansi_uang_muka,
		sipm.foto_kwitansi_sub,
		sipm.set_warehouse,
		w.parent_warehouse,
		w2.parent_warehouse,
		sn.warehouse,
		pr.set_warehouse,
		se.to_warehouse
		FROM `tabSales Invoice Penjualan Motor` sipm 
		JOIN `tabCustomer` c ON c.name = sipm.pemilik
		JOIN `tabSerial No` sn ON sn.name = sipm.no_rangka
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		JOIN `tabStock Ledger Entry` sle ON sle.serial_no = sipm.no_rangka
		LEFT JOIN `tabStock Entry` se ON se.name = sle.voucher_no
		JOIN `tabItem` i ON i.name = sipm.item_code
		JOIN `tabUser` u ON u.name = sipm.owner
		LEFT JOIN `tabPurchase Receipt` pr ON pr.name = sle.voucher_no
		LEFT JOIN `tabTable Disc Leasing` tdl ON tdl.parent = sipm.name
		where sipm.docstatus = 1 and (sle.voucher_type = "Purchase Receipt" or sle.voucher_type = "Stock Entry") and sipm.posting_date between '{}' and '{}' group by sipm.name order by sipm.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_list = 1)

	
	output = []
	output_beban = []
	for i in data:
		data2 = frappe.db.sql(""" SELECT sum(td.nominal) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name where sipm.name = '{}' and td.customer = 'AHM' group by sipm.name """.format(i[24]),as_list=1)
		datamd = frappe.db.sql(""" SELECT sum(td.nominal) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name where sipm.name = '{}' and td.customer = 'Anugerah Perdana' group by sipm.name """.format(i[24]),as_list=1)
		datad = frappe.db.sql(""" SELECT sum(td.nominal) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name where sipm.name = '{}' and td.customer = 'Dealer' group by sipm.name """.format(i[24]),as_list=1)

		disc_leasing = frappe.db.sql(""" SELECT IFNULL(nominal,0) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTable Disc Leasing` td ON td.`parent` = sipm.name where sipm.name = '{}' """.format(i[24]),as_list=1)

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

		
		ahm=0
		ap = 0
		dea = 0
		if data2:
			ahm = data2[0][0]
		if datamd:
			ap = datamd[0][0]
		if datad:
			dea = datad[0][0]
		# grosdp = i[28]+ahm+ap+dea

		if i[61]:
			nama_area = i[61]
		else:
			nama_area = i[62]

		
		output.append([i[0],i[1],i[33],i[10],i[2],i[3],i[4],i[5],i[6],i[7],i[8],i[9],i[11],i[12],i[13],i[14],i[15],i[16],kd[0],i_n[0],i[46],i[35],nr[0],nr[1],i[20],
			i[25],i[21],i[22],i[23],bl,tam_les,tam_lain,ahm,ap,dea,i[47],i[48],i[49],i[50],i[51],i[52],i[53],i[54],i[55],i[56],i[57],nama_area,i[58],i[59]])
		

	# output_tes = output
	conter = 0
	tmp = []
	for ot in output:
		# ot.extend(output_beban[conter])
		tmp.append(ot)
		conter = conter+1
	con = 0
	tmp2 = tmp
	tampil = []	
	# frappe.msgprint(str(tmp2)+'tmp2')
	for t in tmp2:
		# frappe.msgprint(data[con][24])
		data_stnk = frappe.db.sql(""" SELECT sum(bm.amount) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTabel Biaya Motor` bm ON bm.`parent` = sipm.name where sipm.name = '{}' and bm.type = "STNK" """.format(data[con][24]),as_list=1)
		data_bpkb = frappe.db.sql(""" SELECT sum(bm.amount) from `tabSales Invoice Penjualan Motor` sipm 
			LEFT JOIN `tabTabel Biaya Motor` bm ON bm.`parent` = sipm.name where sipm.name = '{}' and bm.type = "BPKB" """.format(data[con][24]),as_list=1)
		data_dealer = frappe.db.sql(""" SELECT IFNULL(sum(bm.amount),0) from `tabSales Invoice Penjualan Motor` sipm 
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
		foto_nosin = ""
		foto_rangka = ""
		foto_po = ""
		foto_ktp = ""
		foto_kk = ""
		foto_inv = ""
		foto_sj = ""
		foto_kw_um = ""
		foto_kw_sub = ""

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
		if t[36]:
			foto_nosin = "<a href='"+frappe.utils.get_url()+t[36]+"'>"+frappe.utils.get_url()+t[36]+"</a>"
		if t[37]:
			foto_rangka = "<a href='"+frappe.utils.get_url()+t[37]+"'>"+frappe.utils.get_url()+t[37]+"</a>"
		if t[38]:
			foto_po = "<a href='"+frappe.utils.get_url()+t[38]+"'>"+frappe.utils.get_url()+t[38]+"</a>"
		if t[39]:
			foto_ktp = "<a href='"+frappe.utils.get_url()+t[39]+"'>"+frappe.utils.get_url()+t[39]+"</a>"
		if t[40]:
			foto_kk = "<a href='"+frappe.utils.get_url()+t[40]+"'>"+frappe.utils.get_url()+t[40]+"</a>"
		if t[41]:
			foto_inv = "<a href='"+frappe.utils.get_url()+t[41]+"'>"+frappe.utils.get_url()+t[41]+"</a>"
		if t[42]:
			foto_sj = "<a href='"+frappe.utils.get_url()+t[42]+"'>"+frappe.utils.get_url()+t[42]+"</a>"
		if t[43]:
			foto_kw_um = "<a href='"+frappe.utils.get_url()+t[43]+"'>"+frappe.utils.get_url()+t[43]+"</a>"
		if t[44]:
			foto_kw_sub = "<a href='"+frappe.utils.get_url()+t[44]+"'>"+frappe.utils.get_url()+t[44]+"</a>"
		
		dp_gross = t[28]+t[32]+t[33]+t[34]+t[29]+ t[27]
		# p_gross = 
		if t[26] == "Cash":
			otr = t[24] + t[27]
			piutang_leasing = 0
		else:
			otr = t[24]
			piutang_leasing = t[24]-(dp_gross)+t[29]+t[31]

		a_unit = ''
		if t[3]:
			a_unit = t[3]
		else:
			a_unit = t[4]
	
		
		tampil.append([
			t[0],
			t[1],
			a_unit,
			t[48],# id jual t[3]t[45]
			t[47],#  area jual t[4]
			t[46],# area t[5]
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
			otr,#otr [24]
			t[25],# namajual
			t[26],# cara bayar
			t[27],#potongjual nominal diskon
			t[28] + t[27], #dpmurni t[28] otr - t[27]
			t[32], # beban_ahm
			t[33],#beban_md
			t[34],#beban_de
			t[29], # beban leasing
			0,#cashback d_dealer
			dp_gross,#gross dp data[con][36] t[28]+t[32]+t[33]+t[34]
			t[29], # tambahn leasing t[30]
			t[31], # tambah lain d_dealer
			"",# ket tambahn 
			piutang_leasing,#piutang leasing data[con][28] t[24]-(dp_gross)+t[29]+t[31]
			d_cair,# cair
			d_caird,
			d_cair+d_caird-(t[24]-(dp_gross)+t[29]+t[31]),# selisih cair d_cair-d_caird (t[24]-(dp_gross)+t[29]+t[31])-d_cair-d_caird
			ket_cair,
			data[con][29],
			data[con][37],#tt
			data[con][38],#tc
			data[con][43],
			data[con][39],#hc
			piutang_leasing,#piutang Konsumen data[con][28] t[27] t[24]-(t[28]+t[32]+t[33]+t[34])+t[30]+t[31]
			data[con][44],
			data[con][45],
			# "SALES LAPANGAN",
			t[35], # "Mediator" nama penjualan
			data[con][40],
			data[con][41],#top kredit
			data[con][42], # angsuran
			data[con][32],
			data[con][31],
			stnk,#stnk
			d_bpkb,
			foto_nosin,
			foto_rangka,
			foto_po,
			foto_ktp,
			foto_kk,
			foto_inv,
			foto_sj,
			foto_kw_um,
			foto_kw_sub
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