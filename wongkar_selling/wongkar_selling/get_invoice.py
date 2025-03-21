# -*- coding: utf-8 -*-
# Copyright (c) 2021, w and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
import datetime
from erpnext.accounts.utils import get_fiscal_years, validate_fiscal_year, get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.accounts.general_ledger import make_gl_entries
import json

# pembayaran Motor
@frappe.whitelist()
def get_inv(supplier,types,date_from,date_to):
	# data = frappe.db.get_list('Tabel Biaya Motor',filters={'tertagih': 0,'vendor': supplier,'type': types,'parenttype': 'Sales Invoice Penjualan Motor'},fields=['*'])
	data = frappe.db.sql(""" SELECT 
		si.name, 
		si.posting_date,
		tb.type,
		tb.amount,
		si.item_code,
		si.no_rangka,
		IF(sn.pemilik or sn.pemilik != "",sn.`pemilik`,si.`pemilik`) as pemilik,
		IF(sn.nama_pemilik or sn.nama_pemilik != "",sn.`nama_pemilik`,si.`nama_pemilik`) as nama_pemilik
		FROM `tabSales Invoice Penjualan Motor` si 
		left join `tabTabel Biaya Motor` tb on tb.parent = si.name
		left join `tabSerial No` sn on sn.name = si.no_rangka
		where tb.tertagih = 0 and si.docstatus = 1 and tb.vendor = '{}' and type = '{}' 
		and si.posting_date BETWEEN '{}' and '{}' order	by si.nama_pemilik ASC """.format(supplier,types,date_from,date_to),as_dict=1,debug=1)

	return data

@frappe.whitelist()
def get_invd(customer,date_from,date_to):
	# data = frappe.db.get_list('Table Discount',filters={'customer': customer,"tertagih": 0,'parenttype': 'Sales Invoice Penjualan Motor'},fields=['*'])
	data = frappe.db.sql(""" SELECT si.name,si.posting_date,td.category_discount,td.nominal,si.item_code,
		si.no_rangka,
		IF(sn.pemilik or sn.pemilik !="",sn.`pemilik`,si.`pemilik`) as pemilik,
		IF(sn.nama_pemilik or sn.nama_pemilik!="",sn.`nama_pemilik`,si.`nama_pemilik`) as nama_pemilik
		FROM `tabSales Invoice Penjualan Motor` si 
		left join `tabTable Discount` td on td.parent = si.name 
		left join `tabSerial No` sn on sn.name = si.no_rangka 
		where td.customer = '{}' and td.tertagih = 0 and td.nominal	> 0 and si.docstatus = 1 and si.posting_date BETWEEN '{}' and '{}' 
		group by td.customer,si.name order by si.nama_pemilik """.format(customer,date_from,date_to),as_dict=1)

	return data

@frappe.whitelist()
def get_invd_l(customer,date_from,date_to):
	# data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={'cara_bayar': 'Credit',"docstatus": ["=",1],"tertagih": 0,'nama_leasing': customer},fields=['*'])

	# return data
	# data = frappe.db.sql(""" SELECT sinv.name,sinv.posting_date,sinv.no_rangka,sinv.nama_promo,
	# 	sinv.item_code,
	# 	sinv.`pemilik`,
	# 	sinv.`nama_pemilik`,
	# 	tdl.nama_leasing,
	# 	sinv.total_discoun_leasing as nominal,sinv.outstanding_amount from `tabSales Invoice Penjualan Motor` sinv
	# 	left join `tabTable Disc Leasing` tdl on sinv.name = tdl.parent 
	# 	left join `tabSerial No` sn on sn.name = sinv.no_rangka
	# 	where tdl.nama_leasing = '{0}' and tdl.tertagih = 0 and sinv.docstatus = 1
	# 	and sinv.posting_date BETWEEN '{1}' and '{2}' group by tdl.nama_leasing,sinv.name order by sinv.nama_pemilik asc """.format(customer,date_from,date_to),as_dict=1)
	data = frappe.db.sql(""" SELECT sinv.name,sinv.posting_date,sinv.no_rangka,sinv.nama_promo,
		sinv.item_code,
		IF(sn.pemilik AND (sn.pemilik IS NOT NULL OR sn.pemilik !=""),sn.`pemilik`,sinv.`pemilik`) AS pemilik,
		IF(sn.nama_pemilik AND (sn.nama_pemilik IS NOT NULL OR sn.nama_pemilik !=""),sn.`nama_pemilik`,sinv.`nama_pemilik`) AS nama_pemilik,
		tdl.nama_leasing,
		sinv.total_discoun_leasing as nominal,sinv.outstanding_amount from `tabSales Invoice Penjualan Motor` sinv
		left join `tabTable Disc Leasing` tdl on sinv.name = tdl.parent 
		left join `tabSerial No` sn on sn.name = sinv.no_rangka
		where tdl.nama_leasing = '{0}' and tdl.tertagih = 0 and sinv.docstatus = 1 and tdl.nominal > 0
		and sinv.posting_date BETWEEN '{1}' and '{2}' group by tdl.nama_leasing,sinv.name order by sinv.nama_pemilik asc """.format(customer,date_from,date_to),as_dict=1)
	return data

@frappe.whitelist()
def get_piutang_leasing(customer,date_from,date_to):
	# data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={'cara_bayar': 'Credit',"docstatus": ["=",1],"tertagih": 0,'nama_leasing': customer},fields=['*'])

	# return data
	# data = frappe.db.sql(""" SELECT sinv.name,sinv.posting_date,sinv.no_rangka,sinv.nama_promo,
	# 	sinv.item_code,
	# 	sinv.`pemilik`,
	# 	sinv.`nama_pemilik`,
	# 	tdl.nama_leasing,
	# 	sinv.total_discoun_leasing as nominal,sinv.outstanding_amount from `tabSales Invoice Penjualan Motor` sinv
	# 	left join `tabTable Disc Leasing` tdl on sinv.name = tdl.parent 
	# 	left join `tabSerial No` sn on sn.name = sinv.no_rangka
	# 	where tdl.nama_leasing = '{0}' and tdl.tertagih = 0 and sinv.docstatus = 1
	# 	and sinv.posting_date BETWEEN '{1}' and '{2}' group by tdl.nama_leasing,sinv.name order by sinv.nama_pemilik asc """.format(customer,date_from,date_to),as_dict=1)
	data = frappe.db.sql(""" SELECT sinv.name,sinv.posting_date,sinv.no_rangka,sinv.nama_promo,
		sinv.item_code,
		IF(sn.pemilik AND (sn.pemilik IS NOT NULL OR sn.pemilik !=""),sn.`pemilik`,sinv.`pemilik`) AS pemilik,
		IF(sn.nama_pemilik AND (sn.nama_pemilik IS NOT NULL OR sn.nama_pemilik !=""),sn.`nama_pemilik`,sinv.`nama_pemilik`) AS nama_pemilik,
		tdl.nama_leasing,
		sinv.total_discoun_leasing as nominal,sinv.outstanding_amount from `tabSales Invoice Penjualan Motor` sinv
		left join `tabTable Disc Leasing` tdl on sinv.name = tdl.parent 
		left join `tabSerial No` sn on sn.name = sinv.no_rangka
		where sinv.customer = '{0}' and sinv.tertagih = 0 and sinv.docstatus = 1
		and sinv.posting_date BETWEEN '{1}' and '{2}' group by tdl.nama_leasing,sinv.name order by sinv.nama_pemilik asc """.format(customer,date_from,date_to),as_dict=1)
	return data

@frappe.whitelist()
def get_invc(leasing,date_from,date_to):
	# data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={"customer": leasing,'cara_bayar': 'Credit',"docstatus": ["=",1],'outstanding_amount':['!=',0]},fields=['*'])
	data = frappe.db.sql(""" SELECT name,posting_date,no_rangka,grand_total,item_code,pemilik
		from `tabSales Invoice Penjualan Motor` where customer='{}' and cara_bayar='Credit' and docstatus=1 
		and outstanding_amount != 0 and posting_date BETWEEN '{}' and '{}' """.format(leasing,date_from,date_to),as_dict=1)

	return data

@frappe.whitelist()
def get_item_price(item_code,price_list,posting_date):
	
	data = frappe.db.sql(""" select name, price_list_rate, uom from `tabItem Price` where item_code='{0}' and price_list='{1}' and selling=1 and (valid_from is NULL or valid_from <='{2}') and (valid_upto is NULL or valid_upto >='{2}') order by valid_from desc, batch_no desc, uom desc """.format(item_code,price_list,posting_date),as_dict=1)
	
	return data

@frappe.whitelist()
def get_biaya(item_code,territory,posting_date,from_group):
	if from_group:
		item_group = frappe.get_doc("Item",item_code).item_group
		data = frappe.db.sql(""" SELECT name, vendor,type,amount, coa,valid_from,valid_to from `tabRule Biaya` 
			where item_group='{0}' and  territory = '{1}' and disable = 0 and valid_from <='{2}' 
			and valid_to >= '{2}' group by item_group,type order by valid_from desc """.format(item_group,territory,posting_date),as_dict=1)
	else:
		# item_code
		data = frappe.db.sql(""" SELECT name, vendor,type,amount, coa,valid_from,valid_to from `tabRule Biaya` 
			where item_code='{0}' and  territory = '{1}' and disable = 0 and valid_from <='{2}' 
			and valid_to >= '{2}' order by valid_from desc """.format(item_code,territory,posting_date),as_dict=1)

	return data

@frappe.whitelist()
def get_rule(item_code,territory,posting_date,category_discount,from_group):
	# if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
	# 	if from_group:
	# 		item_group = frappe.get_doc("Item",item_code).item_group
	# 		data = frappe.db.sql(""" SELECT name,customer,category_discount,coa_receivable,amount,discount,percent,valid_from,valid_to from `tabRule` 
	# 			where item_group='{0}' and  territory = '{1}' and category_discount='{3}' and disable = 0 and valid_from <='{2}' 
	# 			and valid_to >= '{2}' and item_code is NULL order by valid_from desc """.format(item_group,territory,posting_date,category_discount),as_dict=1)
	# 	else:
	# 		# item_code
	# 		data = frappe.db.sql(""" SELECT name,customer,category_discount,coa_receivable,amount,discount,percent,valid_from,valid_to from `tabRule` 
	# 			where item_code='{0}' and  territory = '{1}' and category_discount='{3}' and disable = 0 and valid_from <='{2}' 
	# 			and valid_to >= '{2}' order by valid_from desc """.format(item_code,territory,posting_date,category_discount),as_dict=1)

	# if frappe.local.site in ["newbjm.digitalasiasolusindo.com"]:
	if from_group:
		item_group = frappe.get_doc("Item",item_code).item_group
		data = frappe.db.sql(""" SELECT name,customer,category_discount,coa_receivable,amount,discount,percent,valid_from,valid_to,territory,coa_lawan from `tabRule` 
			where item_group='{0}' and  (territory = '{1}' OR territory='All Territories') and category_discount='{3}' and disable = 0 and valid_from <='{2}' 
			and valid_to >= '{2}' and item_code is NULL HAVING territory='All Territories' order by valid_from desc """.format(item_group,territory,posting_date,category_discount),as_dict=1)
		
		if data:
			print("ada all territory")
		else:
			data = frappe.db.sql(""" SELECT name,customer,category_discount,coa_receivable,amount,discount,percent,valid_from,valid_to,territory,coa_lawan from `tabRule` 
				where item_group='{0}' and  (territory = '{1}') and category_discount='{3}' and disable = 0 and valid_from <='{2}' 
				and valid_to >= '{2}' and item_code is NULL order by valid_from desc """.format(item_group,territory,posting_date,category_discount),as_dict=1)
	else:
		# item_code
		data = frappe.db.sql(""" SELECT name,customer,category_discount,coa_receivable,amount,discount,percent,valid_from,valid_to from `tabRule` 
			where item_code='{0}' and  territory = '{1}' and category_discount='{3}' and disable = 0 and valid_from <='{2}' 
			and valid_to >= '{2}' order by valid_from desc """.format(item_code,territory,posting_date,category_discount),as_dict=1)

	return data


@frappe.whitelist()
def get_leasing(item_code,nama_promo,territory_real,posting_date,from_group):
	if from_group:
		item_group = frappe.get_doc("Item",item_code).item_group
		# data = frappe.db.sql(""" SELECT rdl.leasing,tdl.coa,tdl.amount as amount,rdl.valid_from,rdl.valid_to,rdl.name,rdl.beban_dealer  from `tabRule Discount Leasing` rdl 
		# 	join `tabTable Discount Leasing` tdl on rdl.name = tdl.parent
		# 	where rdl.item_group='{0}' and rdl.nama_promo='{1}' and rdl.territory='{2}' 
		# 	and (rdl.valid_from is NULL or rdl.valid_from <='{3}') and (rdl.valid_to is NULL or rdl.valid_to >='{3}') 
		# 	AND rdl.disable = 0 group by rdl.item_group,rdl.leasing,tdl.coa order by rdl.valid_from desc, tdl.idx asc """.format(item_group,nama_promo,territory_real,posting_date),as_dict=1)

		data = frappe.db.sql(""" SELECT rdl.leasing,rdl.coa,rdl.coa_lawan,rdl.amount as amount,rdl.valid_from,rdl.valid_to,rdl.name,rdl.beban_dealer  from `tabRule Discount Leasing` rdl 
			where rdl.item_group='{0}' and rdl.nama_promo='{1}' and rdl.territory='{2}' 
			and (rdl.valid_from is NULL or rdl.valid_from <='{3}') and (rdl.valid_to is NULL or rdl.valid_to >='{3}') 
			AND rdl.disable = 0 group by rdl.item_group,rdl.leasing order by rdl.valid_from desc """.format(item_group,nama_promo,territory_real,posting_date),as_dict=1)
		# frappe.msgprint(str(data))
	else:
		data = frappe.db.sql(""" SELECT rdl.leasing,tdl.coa,tdl.amount,rdl.valid_from,rdl.valid_to,rdl.name,rdl.coa_lawan  from `tabRule Discount Leasing` rdl 
			join `tabTable Discount Leasing` tdl on rdl.name = tdl.parent
			where rdl.item_code='{0}' and rdl.nama_promo='{1}' and rdl.territory='{2}' 
			and (rdl.valid_from is NULL or rdl.valid_from <='{3}') and (rdl.valid_to is NULL or rdl.valid_to >='{3}') 
			AND rdl.disable = 0 order by rdl.valid_from desc  """.format(item_code,nama_promo,territory_real,posting_date),as_dict=1)

	return data

def cek_tagihan(self,method):
	if self.tagihan:
		if self.tagihan_payment_table:
			if len(self.tagihan_payment_table) > 0:
				tot = 0
				for i in self.tagihan_payment_table:
					tot = tot + i.nilai
		self.paid_amount = tot

@frappe.whitelist()
def get_inv_stnk_bpkb(supplier_stnk,supplier_bpkb,date_from,date_to):
	data = frappe.db.sql(""" SELECT 
		si.name, 
		si.posting_date,
		tb.type,
		tb.amount,
		si.item_code,
		si.no_rangka,
		(select tb2.amount from `tabTabel Biaya Motor` tb2 where tb2.parent = si.name and tb2.vendor = '{1}' and type = '{3}') as amount_bpkb,
		IF(sn.pemilik or sn.pemilik != "",sn.`pemilik`,si.`pemilik`) as pemilik,
		IF(sn.nama_pemilik or sn.nama_pemilik != "",sn.`nama_pemilik`,si.`nama_pemilik`) as nama_pemilik
		FROM `tabSales Invoice Penjualan Motor` si 
		left join `tabTabel Biaya Motor` tb on tb.parent = si.name
		join `tabSerial No` sn on sn.name = si.no_rangka
		where tb.tertagih = 0 and si.docstatus = 1 and tb.vendor = '{0}' and type = '{2}'
		and si.posting_date BETWEEN '{4}' and '{5}' order by si.nama_pemilik asc """.format(supplier_stnk,supplier_bpkb,"STNK","BPKB",date_from,date_to),as_dict=1)

	return data

@frappe.whitelist()
def get_tagihan(doc_type,tipe_pembayaran,data,name_pe,paid_from,oli=None):
	# frappe.msgprint(doc_type+" "+tipe_pembayaran)
	tes = json.loads(data)
	# frappe.msgprint(str(tes)+" tes")
	# for i in tes:
	# 	frappe.msgprint(i['reference_name'])
	tmp = []
	# doc = frappe.get_doc("Payment Entry",dt)
	# Pembayaran Tagihan Motor
	# paid_from = frappe.get_doc("Payment Entry",name_pe).paid_from
	# payment_type = frappe.get_doc("Payment Entry",name_pe).payment_type
	# frappe.msgprint(str(tes)+ " tes")
	# frappe.msgprint(tes[0]['reference_doctype']+tes[0]['docname']+"weee")
	if tes[0]['reference_doctype'] == 'Tagihan Discount Leasing':
		cek = frappe.get_doc(tes[0]['reference_doctype'],tes[0]['docname'])
		# frappe.msgprint(str(cek.daftar_tagihan_leasing[0].no_invoice)+ " cek")
		cek_debit_to = frappe.get_doc("Sales Invoice Penjualan Motor",cek.daftar_tagihan_leasing[0].no_invoice).debit_to
		coa_tagihan_sipm = frappe.get_doc('Tagihan Discount Leasing',tes[0]['docname']).coa_tagihan_sipm
		if coa_tagihan_sipm != paid_from:
			pass
			# frappe.throw("Akun paid from harus" + cek_debit_to+ " !")

	if tes[0]['reference_doctype'] == 'Tagihan Discount':
		cek = frappe.get_doc(tes[0]['reference_doctype'],tes[0]['docname'])
		# frappe.msgprint(str(cek.daftar_tagihan[0].no_sinv)+ " cek")
		cek_debit_to = frappe.get_doc("Sales Invoice Penjualan Motor",cek.daftar_tagihan[0].no_sinv).debit_to
		if cek_debit_to != paid_from:
			pass
			# frappe.throw("Akun paid from harus" + cek_debit_to+ " !")

	if doc_type == "Pembayaran Tagihan Motor" and tipe_pembayaran == "Pembayaran STNK":
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				outstanding_stnk as outstanding,
				parenttype,
				parent,
				no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabChild Tagihan Biaya Motor` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)
	elif doc_type == "Pembayaran Tagihan Motor" and tipe_pembayaran == "Pembayaran BPKB":
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				outstanding_bpkb as outstanding,
				parenttype,
				parent,
				no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabChild Tagihan Biaya Motor` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)
	elif doc_type == "Pembayaran Tagihan Motor" and tipe_pembayaran == "Pembayaran Diskon Dealer":
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				terbayarkan as outstanding,
				parenttype,
				parent,
				no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabChild Tagihan Biaya Motor` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)

	# Tagihan Discount Leasing
	elif doc_type == "Tagihan Discount Leasing" and tipe_pembayaran == "Pembayaran Diskon Leasing":
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				outstanding_discount as outstanding,
				parenttype,
				parent,
				no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabDaftar Tagihan Leasing` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)
	elif doc_type == "Tagihan Discount Leasing" and tipe_pembayaran == "Pembayaran SIPM":
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				outstanding_sipm as outstanding,
				parenttype,
				parent,
				no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabDaftar Tagihan Leasing` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)

	# Tagihan Discount
	elif doc_type == "Tagihan Discount" and tipe_pembayaran == "Pembayaran Diskon" :
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				terbayarkan as outstanding,
				parenttype,
				parent,
				no_sinv as no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabDaftar Tagihan` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)

	# tagihan leasing
	elif doc_type == "Tagihan Leasing" and tipe_pembayaran == 'Pembayaran Tagihan Leasing':
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				pemilik,
				item,
				no_rangka,
				outstanding_sipm as outstanding,
				parenttype,
				parent,
				no_invoice,
				nama_pemilik,
				name as id_detail
				from `tabList Tagihan Piutang Leasing` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)

	elif doc_type == 'Invoice Penagihan Garansi' and tipe_pembayaran == 'Pembayaran Invoice Garansi' and not oli:
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				customer as pemilik,
				customer_name as nama_pemilik,
				sales_invoice_sparepart_garansi,
				grand_total,
				outstanding_amount as outstanding,
				parenttype,
				parent,
				name as id_detail,
				CONCAT(no_rangka,"--",no_mesin) as no_rangka2
				from `tabList Invoice Penagihan Garansi` where parent = '{}' """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)
	elif doc_type == 'Invoice Penagihan Garansi' and tipe_pembayaran == 'Pembayaran Invoice Garansi' and oli:
		for i in tes:
			data = frappe.db.sql(""" SELECT 
				customer as pemilik,
				customer_name as nama_pemilik,
				sales_invoice_sparepart_garansi,
				grand_total_oli as grand_total,
				outstanding_amount_oli as outstanding,
				parenttype,
				parent,
				name as id_detail,
				CONCAT(no_rangka,"--",no_mesin) as no_rangka2
				from `tabList Invoice Penagihan Garansi` where parent = '{}' and outstanding_amount_oli > 0 """.format(i['docname']),as_dict=1,debug=1)
			# frappe.msgprint(data)
			tmp.append(data)

	# frappe.msgprint(str(data))
	return tmp
