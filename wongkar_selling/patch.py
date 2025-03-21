from __future__ import unicode_literals
import frappe, erpnext
import json
import frappe.utils
from frappe.utils import cstr, cint, flt
from num2words import num2words
from erpnext.stock.doctype.serial_no.serial_no import process_serial_no
from datetime import date
from frappe.utils import flt, rounded, add_months,add_days, nowdate, getdate
import time
import datetime
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from wongkar_selling.custom_standard.custom_gl_entry import update_outstanding_amt_custom
import pandas as pd

#DEV

def update_sinv_sp():
	tmp = [

	]
	con = 1
	for i in tmp:
		print(con)
		print(i)
		doc = frappe.get_doc('Sales Invoice',i)
		print(doc.debit_to)
		if doc.docstatus == 1 and doc.is_pos == 1:
			doc.debit_to = '11201.17 - PIUTANG DAGANG SPAREPART - W'
			doc.db_update()
		elif doc.docstatus == 1 and doc.is_pos == 0:
			doc.debit_to = '11201.17 - PIUTANG DAGANG SPAREPART - W'
			doc.db_update()
		if doc.grand_total > 0:
			if doc.update_stock == 1:
				repair_gl_sle_entry("Sales Invoice",doc.name)
			else:
				repair_only_gl_entry("Sales Invoice",doc.name)
			
		frappe.db.commit()
		con += 1
		print(f'{doc.name} || {doc.debit_to} DONE')
			

def patch_je():
	doc = frappe.get_doc("Journal Entry","ACC-JV-2023-01373")
	print(doc.name)
	repair_only_gl_entry("Journal Entry",doc.name)

def patch_tl_oa():
	tmp = [
'ACC-SINVM-2024-00175'
	]
	akun = '11201.01 - PIUTANG DAGANG MOTOR - W'
	customer = 'MMF'
	for i in tmp:
		print(i)
		update_outstanding_amt_custom(akun,'Customer',customer,'Sales Invoice Penjualan Motor',i)

def pacth_sipm():
	frappe.flags.repair = True
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2024-00175")
	print(doc.name)
	repair_gl_sle_entry("Sales Invoice Penjualan Motor",doc.name)
	print('DONE')

def patch_rebuild_tree():
	from frappe.utils.nestedset import rebuild_tree
	rebuild_tree("Account", "parent_account")
	print("DONE")

def patch_sipm_akun_stnk_bpkb():
	data = frappe.db.sql(""" SELECT a.name,a.coa_bpkb_stnk,a.cara_bayar,b.`account_type` 
					  FROM `tabSales Invoice Penjualan Motor` a 
					  JOIN `tabAccount` b ON b.name = a.coa_bpkb_stnk 
					  WHERE a.coa_bpkb_stnk != '11203.03 - UANG TITIPAN BPKB & STNK - W' 
					  AND a.docstatus=1 AND a.cara_bayar = 'Credit' AND b.`account_type` != 'Receivable' """,as_dict=1)
	
	# tmp = ['ACC-SINVM-2023-00043']
	tmp =[]
	for d in data:
		tmp.append(d['name'])

	print(len(tmp), ' tmpxx')
	con = 1
	for i in tmp:
		print(con)
		print(i, ' ixxxx')
		doc = frappe.get_doc('Sales Invoice Penjualan Motor',i)
		doc.coa_bpkb_stnk = '11203.03 - UANG TITIPAN BPKB & STNK - W'
		doc.db_update()
		repair_only_gl_entry('Sales Invoice Penjualan Motor',i)
		print('DONE')
		con += 1


def petch_salah_rate_prec():
	frappe.flags.repair = True
	col = ['name','no_rangka','harga_baru']
	data = pd.read_excel (r'/home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/patch_rate_prec.xls') 
	df = pd.DataFrame(data, columns= col)
	tmp = []
	for idx in range(len(df)):
		tmp.append({
				'name': df[col[0]][idx],
				'no_rangka': df[col[1]][idx],
				'harga_baru': df[col[2]][idx],
			})

	grouped_data = {}
	for item in tmp:
		name = item['name']
		if name not in grouped_data:
			grouped_data[name] = []
		grouped_data[name].append(item)

	print(grouped_data)

	for gd,info in grouped_data.items():
		print(gd, ' gdxxx')
		doc = frappe.get_doc('Purchase Receipt',gd)
		for it in doc.items:
			for inf in info:
				if inf['no_rangka'] in it.serial_no:
					if it.discount_amount == 0:
						print(inf['harga_baru'], ' yyy')
						it.price_list_rate = inf['harga_baru']
						it.rate = inf['harga_baru']
						# patch_po
						if it.purchase_order:
							po = frappe.get_doc('Purchase Order',it.purchase_order)
							print(po.name, ' ponamexxx')
							for poi in po.items:
								if poi.discount_amount == 0:
									if poi.name == it.purchase_order_item:
										poi.price_list_rate = inf['harga_baru']
										poi.rate = inf['harga_baru']
								else:
									frappe.throw('test')
							po.run_method("calculate_taxes_and_totals")
							po.db_update()
							po.update_children()
					else:
						frappe.throw('test')
		doc.run_method("calculate_taxes_and_totals")
		doc.update_valuation_rate()
		doc.db_update()
		doc.update_children()
		repair_gl_sle_entry('Purchase Receipt',gd)
		print('DONE')

	# tmp = ['MAT-PRE-2024-00542']
	# frappe.flags.repair = True
	# for i in tmp:
	# 	doc = frappe.get_doc('Purchase Receipt',i)
	# 	for it in doc.items:
	# 		if 'MH1JM0314RK630645' in it.serial_no:
	# 			if it.discount_amount == 0:
	# 				print(it.serial_no)
	# 				it.price_list_rate = 16779000
	# 				it.rate = 16779000
	# 			else:
	# 				frappe.throw('test')
	# 	doc.run_method("calculate_taxes_and_totals")
	# 	doc.update_valuation_rate()
	# 	doc.db_update()
	# 	doc.update_children()
	# 	repair_gl_sle_entry('Purchase Receipt',i)
	# 	print('DONE')

def patch_stock_prec():
	data = frappe.db.sql(""" SELECT poi.`name`,poi.`parent`,poi.`item_code`,poi.`warehouse` FROM `tabPurchase Order` po
		LEFT JOIN `tabPurchase Order Item` poi ON po.`name` = poi.`parent`
		WHERE po.`docstatus` = 1 GROUP BY poi.`item_code`,poi.`warehouse` """,as_dict=1)

	for i in data:
		# data_order = frappe.db.sql(""" SELECT SUM((po_item.qty - po_item.received_qty)*po_item.conversion_factor) as total,po_item.item_code,po_item.warehouse
		# 	FROM `tabPurchase Order Item` po_item, `tabPurchase Order` po
		# 	WHERE po_item.item_code='{}' AND po_item.warehouse='{}'
		# 	AND po_item.qty > po_item.received_qty AND po_item.parent=po.name
		# 	AND po.status NOT IN ('Closed', 'Delivered') AND po.docstatus=1
		# 	AND po_item.delivered_by_supplier = 0  """.format(i['item_code'],i['warehouse']),as_dict=1)

		data_order = frappe.db.sql(""" 
			SELECT po_item.qty,po_item.received_qty,po_item.conversion_factor,po_item.`parent`
			FROM `tabPurchase Order Item` po_item, `tabPurchase Order` po
			WHERE po_item.item_code='{}' AND po_item.warehouse='{}'
			AND po_item.qty > po_item.received_qty AND po_item.parent=po.name
			AND po.status NOT IN ('Closed', 'Delivered') AND po.docstatus=1
			AND po_item.delivered_by_supplier = 0 """.format(i['item_code'],i['warehouse']),as_dict=1)
		
		for d in data_order:
			if d['received_qty'] >0:
				print(d, ' data_orderxxx')

def patch_akun_pinv():
	data = frappe.db.sql(""" SELECT pinv.name,pinv.`bill_no`,pinv.`credit_to`,pinv.`docstatus` 
		FROM `tabPurchase Invoice` pinv 
		WHERE pinv.`docstatus` < 2 AND pinv.`bill_no` LIKE '%INV%' AND pinv.`credit_to` != '21100.02 - HUTANG DAGANG SPAREPART - W'
		ORDER BY pinv.`posting_date`,pinv.`name` ASC """,as_dict=1)
	
	tmp = []
	# tmp = ['ACC-PINV-2023-00006']
	for d in data:
		tmp.append(d['name'])
	
	print(len(tmp), ' tmpxxx')
	con = 1
	for i in tmp:
		print(con, ' conxx')
		print(i, ' ixxx')
		doc = frappe.get_doc('Purchase Invoice',i)
		doc.credit_to = '21100.02 - HUTANG DAGANG SPAREPART - W'
		doc.db_update()
		if doc.docstatus == 1:
			repair_only_gl_entry('Purchase Invoice',i)
		print('DONE')
		con += 1

def patch_akun_item_pinv():
	frappe.flags.repair_sp = True
	# data = frappe.db.sql(""" SELECT pinv.name,pinv.`posting_date`,pinv.`bill_no`,pinv.`credit_to`,pinv.`docstatus` 
	# 	FROM `tabPurchase Invoice` pinv 
	# 	WHERE pinv.`docstatus` < 2 AND pinv.`bill_no` LIKE '%INV%' AND pinv.posting_date BETWEEN '2023-01-01' AND '2023-12-31'
	# 	ORDER BY pinv.`posting_date`,pinv.`name` ASC """,as_dict=1)

	# tmp = []
	# for d in data:
	# 	tmp.append(d['name'])

	# tmp = ['ACC-PINV-2023-00006']
	# tmp = ['ACC-PINV-2023-00007']
	tmp = ['ACC-PINV-RET-2023-00005']
	new_account = '21600.02 - BARANG BELUM DITAGIH - SPAREPART - W'
	old_account = '21600.01 - BARANG BELUM DITAGIH - MOTOR - W'

	cek = 0
	con = 1
	for i in tmp:
		print(con, ' conxx')
		print(i, ' ixxx')
		doc = frappe.get_doc('Purchase Invoice',i)
		for j in doc.items:
			if j.expense_account != new_account:
				j.expense_account = new_account
				print(j.expense_account)
				cek = 1
		doc.set_against_expense_account()
		doc.db_update()
		doc.update_children()
		if doc.docstatus == 1:
			print('masuk sini')
			repair_only_gl_entry('Purchase Invoice',i)
		
		cek_prec = frappe.db.sql(""" SELECT pr.name 
			from `tabPurchase Receipt` pr 
			join `tabPurchase Receipt Item` pri on pr.name = pri.parent
			where pri.purchase_invoice = '{}' and pr.docstatus < 2 group by pr.name """.format(i),as_dict=1)
		
		if cek_prec:
			print(cek_prec, ' Purchase Receiptxxx')
			prec = frappe.get_doc('Purchase Receipt',cek_prec[0]['name'])
			print(prec.name, ' precnamexxx')
			for j in prec.items:
				if j.expense_account != new_account:
					j.expense_account = new_account
					cek = 1
					print(j.expense_account, ' expense_accountxxxx')
			# print()
			prec.db_update()
			prec.update_children()
			if prec.docstatus == 1:
				print("ms")
				repair_only_gl_entry('Purchase Receipt',cek_prec[0]['name'])
		
		print('DONE')
		con += 1

# def patch_akun_item_prec():
# 	frappe.flags.repair_sp = True
# 	tmp = ['MAT-PRE-2023-00057']
# 	new_account = '21600.02 - BARANG BELUM DITAGIH - SPAREPART - W'
# 	old_account = '21600.01 - BARANG BELUM DITAGIH - MOTOR - W'
	
# 	cek = 0
# 	con = 1
# 	for i in tmp:
# 		print(con, ' conxx')
# 		print(i, ' ixxx')
# 		doc = frappe.get_doc('Purchase Receipt',i)
# 		srbnb = doc.get_company_default("stock_received_but_not_billed")
# 		print(srbnb, ' srbnb')
# 		for j in doc.items:
# 			if j.expense_account != new_account:
# 				j.expense_account = new_account
# 				cek = 1
# 				print(j.expense_account, ' expense_accountxxxx')
# 		# print()
# 		doc.db_update()
# 		doc.update_children()
# 		if doc.docstatus == 1:
# 			print("ms")
# 			repair_only_gl_entry('Purchase Receipt',i)
# 		print('DONE')
# 		con += 1


def pacth_akun_je():
	data = frappe.db.sql(""" SELECT pinv.name,pinv.`bill_no`,pinv.`credit_to`,pinv.`docstatus` 
		FROM `tabPurchase Invoice` pinv 
		WHERE pinv.`docstatus` < 2 AND pinv.`bill_no` LIKE '%INV%' AND pinv.`credit_to` = '21100.02 - HUTANG DAGANG SPAREPART - W' 
		AND pinv.`outstanding_amount` > 0
		ORDER BY pinv.`posting_date`,pinv.`name` ASC """,as_dict=1)

	# tmp = ['ACC-PINV-2023-00006']
	tmp = []
	for d in data:
		tmp.append(d['name'])
	
	con = 1
	tmp_je = []
	for i in tmp:
		print(con, ' conxx')
		print(i, ' ixxx')
		cek_pe = frappe.db.sql(""" 
			SELECT 
				per.name,per.parent,per.reference_name 
			FROM `tabPayment Entry Reference` per 
			WHERE per.reference_name = '{}' 
			and per.docstatus < 2 """.format(i),as_dict=1)
		if cek_pe:
			frappe.throw('test')

		cek_je = frappe.db.sql(""" 
			SELECT 
				jea.name,jea.parent,jea.docstatus,jea.account,jea.reference_name
			FROM `tabJournal Entry Account` jea 
			WHERE jea.reference_name = '{}' 
			and jea.docstatus < 2 """.format(i),as_dict=1)

		if cek_je:
			
			for je in cek_je:
				print(je, ' je')
				frappe.db.sql(""" UPDATE `tabJournal Entry Account` set account = '21100.02 - HUTANG DAGANG SPAREPART - W' 
					where name = '{}' """.format(je['name']),debug=1)
				if je['docstatus'] == 1:
					tmp_je.append(je['parent'])
		con += 1
	
	if len(tmp_je) >0:
		tmp_je = list(dict.fromkeys(tmp_je))
		print(tmp_je, ' tmp_jexxx')
		for tje in tmp_je:
			print(tje, ' tjexxx')
			repair_only_gl_entry('Journal Entry',tje)
			print("DONE")
		
def patch_akun_tl():
	frappe.flags.repair = True
	data = frappe.db.sql(""" SELECT a.name,a.customer,a.docstatus,a.coa_lawan,a.date 
					  FROM `tabTagihan Leasing` a WHERE a.docstatus =1 
					  AND a.date BETWEEN '2024-01-01' AND '2024-12-31' ORDER BY a.date ASC """,as_dict=1)
	
	tmp = ['Tagihan-PL-09-2023-00001']
	# for d in data:
	# 	print(d['name'])
	# 	tmp.append(d['name'])
	con =1
	# tmp = [
	# 	"Tagihan-PL-01-2024-00002-1",
	# 	"Tagihan-PL-01-2024-00008-1",
	# 	"Tagihan-PL-01-2024-00009-1",
	# 	"Tagihan-PL-01-2024-00010",
	# 	"Tagihan-PL-01-2024-00014",
	# 	"Tagihan-PL-01-2024-00015",
	# 	"Tagihan-PL-01-2024-00018",
	# 	"Tagihan-PL-01-2024-00019",
	# 	"Tagihan-PL-12-2023-00014"
	# ]
	# # tmp = ['Tagihan-PL-01-2024-00001']
	print(len(tmp), ' tmpxxxx')
	for i in tmp:
		print(con)
		print(i, ' ixx')
		doc = frappe.get_doc('Tagihan Leasing',i)
		if doc.customer == 'FIF':
			doc.coa_lawan = '11202.01 - PIUTANG LEASING - FIF - W'
		elif doc.customer == 'ADMF':
			doc.coa_lawan = '11202.02 - PIUTANG LEASING - ADIRA FINANCE - W'
		elif doc.customer == 'MMF':
			doc.coa_lawan = '11202.03 - PIUTANG LEASING - MANDALA MULTI FINANCE - W'
		elif doc.customer == 'MUF':
			doc.coa_lawan = '11202.04 - PIUTANG LEASING - MANDIRI UTAMA FINANCE - W'
		elif doc.customer == 'IMFI':
			doc.coa_lawan = '11202.07 - PIUTANG LEASING - INDOMOBIL FINANCE INDONESIA - W'
		elif doc.customer == 'SOF':
			doc.coa_lawan = '11202.05 - PIUTANG LEASING - SUMMIT AUTO FINANCE - W'
		elif doc.customer == 'WOM':
			doc.coa_lawan = '11202.06 - PIUTANG LEASING - WOM FINANCE - W'		
		
		print(doc.coa_lawan)
		doc.db_update()
		repair_only_gl_entry('Tagihan Leasing',i)
		print('DONE')
		con += 1

def patch_akun_fp():
	data = frappe.db.sql(""" SELECT a.name,a.customer,a.type,a.docstatus,a.posting_date,a.paid_from FROM `tabForm Pembayaran` a 
					  WHERE a.type = 'Pembayaran Tagihan Leasing' AND docstatus = 1 
					  AND a.posting_date BETWEEN '2023-01-01' AND '2023-12-31' ORDER BY a.posting_date ASC """,as_dict=1)
	
	tmp = []

	for d in data:
		tmp.append(d['name'])

	print(len(tmp), ' tmpxxx')
	# tmp = [
	# 	"FP-01-2024-00151",
	# 	"FP-01-2024-00144",
	# 	"FP-01-2024-00143-1",
	# 	"FP-01-2024-00147",
	# 	"FP-01-2024-00145",
	# 	"FP-01-2024-00148-1",
	# 	"FP-01-2024-00149",
	# 	"FP-01-2024-00116-2",
	# 	"FP-01-2024-00150"
	# ]

	con = 1
	for i in tmp:
		print(con)
		print(i, ' ixxx')
		doc = frappe.get_doc('Form Pembayaran',i)
		if doc.customer == 'FIF':
			doc.paid_from = '11202.01 - PIUTANG LEASING - FIF - W'
		elif doc.customer == 'ADMF':
			doc.paid_from = '11202.02 - PIUTANG LEASING - ADIRA FINANCE - W'
		elif doc.customer == 'MMF':
			doc.paid_from = '11202.03 - PIUTANG LEASING - MANDALA MULTI FINANCE - W'
		elif doc.customer == 'MUF':
			doc.paid_from = '11202.04 - PIUTANG LEASING - MANDIRI UTAMA FINANCE - W'
		elif doc.customer == 'IMFI':
			doc.paid_from = '11202.07 - PIUTANG LEASING - INDOMOBIL FINANCE INDONESIA - W'
		elif doc.customer == 'SOF':
			doc.paid_from = '11202.05 - PIUTANG LEASING - SUMMIT AUTO FINANCE - W'
		elif doc.customer == 'WOM':
			doc.paid_from = '11202.06 - PIUTANG LEASING - WOM FINANCE - W'

		doc.db_update()
		repair_only_gl_entry('Form Pembayaran',i)
		print('DONE')

		print(doc.customer)
		print(doc.paid_from)
		con	+= 1


def patch_rate_salah_ste():
	# patch SN
	harga_baru = 27313700
	serial_no = 'KD11E1491244--MH1KD1113RK492089'
	item_code = frappe.get_doc('Serial No',serial_no).item_code
	
	frappe.db.sql(""" UPDATE `tabSerial No` SET purchase_rate={} WHERE name = '{}' """.format(harga_baru,serial_no),debug=1)
	# STE
	se = ['MAT-STE-2024-00644']
	for i in se:
		data = frappe.db.sql(""" SELECT name,parent,item_code,basic_rate,valuation_rate,basic_amount,amount,qty,serial_no FROM `tabStock Entry Detail` 
			WHERE parent = '{}' AND item_code = '{}' AND serial_no LIKE '%{}%' """.format(i,item_code,serial_no),as_dict=1,debug=1)
		if data:
			for d in data:
				frappe.db.sql(""" UPDATE `tabStock Entry Detail` SET basic_rate={} WHERE NAME ='{}' """.format(harga_baru,d['name']),debug=1)
		patch_ste(i)


def patch_rate_salah_prec():
	# patch SN
	harga_baru = 27313700
	serial_no = 'KD11E1490059--MH1KD1112RK490897'
	item_code = frappe.get_doc('Serial No',serial_no).item_code
	
	
	frappe.db.sql(""" UPDATE `tabSerial No` SET purchase_rate={} WHERE name = '{}' """.format(harga_baru,serial_no),debug=1)
	# PECR
	se = ['MAT-PRE-2024-00258']
	for i in se:
		data = frappe.db.sql(""" SELECT name,item_code,price_list_rate,stock_uom_rate,valuation_rate,rate,qty,margin_type,serial_no FROM `tabPurchase Receipt Item` 
			WHERE parent = '{}' AND item_code = '{}' AND serial_no LIKE '%{}%' """.format(i,item_code,serial_no),as_dict=1,debug=1)
		if data:
			for d in data:
				frappe.db.sql(""" UPDATE `tabPurchase Receipt Item` SET rate={0},valuation_rate={0},stock_uom_rate={0}
					WHERE NAME='{1}' """.format(harga_baru,d['name']),debug=1)
		patch_prec(i)


@frappe.whitelist()
def patch_coa():
	rule = frappe.db.sql(""" SELECT 
		sipm.name,sipm.`docstatus`,td.`name` AS td_name,td.`rule` AS td_rule,td.`coa_receivable`, r.`coa_receivable` AS r_coa
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.`name`
		LEFT JOIN `tabRule` r ON r.`name` = td.`rule`
		WHERE sipm.`docstatus` < 2 AND td.`rule` IS NOT NULL ORDER BY sipm.`name` DESC """,as_dict=1)

	rdl = frappe.db.sql(""" SELECT sipm.name,sipm.`docstatus`,tdl.name AS tdl_name,tdl.`rule` AS tdl_rule,tdl.coa,rdl.`coa` AS rdl_coa
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabTable Disc Leasing` tdl ON tdl.`parent` = sipm.`name`
		LEFT JOIN `tabRule Discount Leasing` rdl ON rdl.`name` = tdl.`rule`
		WHERE sipm.`docstatus` < 2 AND tdl.`rule` IS NOT NULL ORDER BY sipm.`name` DESC  """,as_dict=1)

	# rule
	for i in rule:
		coa = frappe.get_doc("Rule",i['td_rule']).coa_receivable
		if i['coa_receivable'] != coa.coa_receivable:
			print(i['name']," | ",coa.coa_receivable)
			frappe.db.sql(""" UPDATE `tabTable Discount` set coa_receivable = '{}' where name = '{}' """.format(coa.coa_receivable,i['td_name']))
		elif i['coa_receivable'] != coa.coa_lawan:
			print(i['name']," | ",coa.coa_receivable)
			frappe.db.sql(""" UPDATE `tabTable Discount` set coa_receivable = '{}' where name = '{}' """.format(coa.coa_receivable,i['td_name']))

	# rdl
	for i in rdl:
		coa = frappe.get_doc("Rule Discount Leasing",i['tdl_rule'])
		if i['coa'] != coa.coa:
			print(i['name']," | ",coa)
			frappe.db.sql(""" UPDATE `tabTable Disc Leasing` set coa = '{}' where name = '{}' """.format(coa,i['tdl_name']))
			# frappe.db.commit()


# def patch_sipm_gl():
# 	tmp = [
# 'ACC-SINVM-2024-00854'
# ]
# 	for i in tmp:
# 		doc = frappe.get_doc('Sales Invoice Penjualan Motor',i)
# 		repair_only_gl_entry('Sales Invoice Penjualan Motor',i)
# 		update_outstanding_amt_custom(doc.debit_to,'Customer',doc.customer,'Sales Invoice Penjualan Motor',doc.name)

def patch_submit_fp_tdl():
	data = frappe.db.sql(""" SELECT 
		f.`name`,f.`docstatus` FROM `tabTagihan Discount Leasing` td
		JOIN `tabList Doc Name` l ON l.`docname` = td.`name`
		JOIN `tabForm Pembayaran` f ON f.`name` = l.`parent`
		WHERE f.`docstatus` = 0 and l.docstatus = 2
		GROUP BY f.`name` limit 10 """,as_dict=1)

	tmp = []
	for d in data:
		tmp.append(d['name'])

	print(len(tmp), ' tmpxx')
	con = 1

	for i in tmp:
		print(con, ' conxx')
		doc = frappe.get_doc('Form Pembayaran',i)
		print(doc.name)
		if doc.docstatus == 0:
			doc.submit()
		con += 1
		print('DONE')

def patch_coa_sipm():
	data = frappe.db.sql(""" 
		SELECT name,posting_date 
		FROM `tabSales Invoice Penjualan Motor`
		WHERE docstatus = 1 AND NAME NOT IN (
		'ACC-SINVM-2024-00965',
		'ACC-SINVM-2024-00985',
		'ACC-SINVM-2024-01045',
		'ACC-SINVM-2023-00002',
		'ACC-SINVM-2024-01091'
		)
		AND posting_date BETWEEN '2024-01-01' AND '2024-12-31'
		ORDER BY posting_date,NAME ASC """,as_dict = 1)

	# ACC-SINVM-2024-01091 sinv aneh gk ada ketranagan submit
	tmp = []
	for d in data:
		tmp.append(d['name'])

	print(len(tmp), ' tmpxx')
	# print(tmp, ' tmp')

	con = 1
	for i in tmp:
		print(con, ' con')
		docname = i
		doc = frappe.get_doc('Sales Invoice Penjualan Motor',docname)
		print(doc.name, ' xxx')
		# r
		for td in doc.table_discount:
			# print(td.parent, ' NAME')
			r = frappe.get_doc("Rule",td.rule)
			frappe.db.sql(""" UPDATE `tabTable Discount` set coa_receivable='{}',coa_lawan='{}' where name = '{}' """.format(r.coa_receivable,r.coa_lawan,td.name))

		#RDL
		for tdl in doc.table_discount_leasing:
			# print(tdl.parent, ' NAME')
			rdl = frappe.get_doc("Rule Discount Leasing",tdl.rule)
			frappe.db.sql(""" UPDATE `tabTable Disc Leasing` set coa='{}',coa_lawan='{}' where name = '{}' """.format(rdl.coa,rdl.coa_lawan,tdl.name))

		repair_only_gl_entry('Sales Invoice Penjualan Motor',i)
		update_outstanding_amt_custom(doc.debit_to,'Customer',doc.customer,'Sales Invoice Penjualan Motor',doc.name)
		print('DONE')
		con += 1

def patch_tagihan_disc():
	data = frappe.db.sql(""" 
		SELECT name FROM `tabTagihan Discount` td 
		WHERE docstatus = 1 AND NAME NOT IN (
		'Tagihan-D-03-2024-00006-1',
		'Tagihan-D-04-2024-00001'
		) """,as_dict = 1)

	tmp = []
	for i in data:
		tmp.append(i['name'])
	
	# ['Tagihan-D-04-2024-00001']

	con = 1
	for i in tmp:
		print(con, 'con')
		print(i, ' xx')
		doc = frappe.get_doc('Tagihan Discount',i)
		print(doc.customer, ' cus')
		if doc.customer == 'AHM':
			doc.coa_tagihan_discount = '11201.03 - PIUTANG DAGANG - DISCOUNT FOR DP FROM AHM - W'
			doc.coa_pendapatan = '42000.03 - PENDAPATAN KLAIM DISKON AHM - W'
		elif doc.customer == 'MD':
			doc.coa_tagihan_discount = '11201.02 - PIUTANG DAGANG - DISCOUNT FOR DP FROM MD - W'
			doc.coa_pendapatan = '42000.02 - PENDAPATAN KLAIM DISKON MD - W'
		
		print(doc.coa_tagihan_discount)
		print(doc.coa_pendapatan)
		doc.db_update()
		print(i, ' xx')
		repair_only_gl_entry('Tagihan Discount',i)
		print('DONE')
		con += 1

# DEVHONDA
def patch_fp_tdl():
	data = frappe.db.sql(""" 
		SELECT 
			f.`name`,f.`docstatus` FROM `tabTagihan Discount Leasing` td
		JOIN `tabList Doc Name` l ON l.`docname` = td.`name`
		JOIN `tabForm Pembayaran` f ON f.`name` = l.`parent`
		WHERE f.`docstatus` = 1 
		AND f.`name` NOT IN (
		'FP-01-2024-00012',
		'FP-01-2024-00013'
		) GROUP BY f.`name` """,as_dict=1)

	tmp = []

	for d in data:
		tmp.append(d['name'])

	print(len(tmp), ' tmpxx')

	con = 1
	for i in tmp:
		print(con, ' con')
		doc = frappe.get_doc('Form Pembayaran',i)
		print(doc.name, ' namexx')
		doc.cancel()
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(doc.name),debug=1)
		frappe.db.sql(""" UPDATE `tabForm Pembayaran` set docstatus=0 where name = '{}' """.format(i),debug=1)
		print('DONE')
		con += 1


def patch_tagihan_disc_leasing():
	tmp = ['Tagihan-L-01-2024-00001']

	for i in tmp:
		doc = frappe.get_doc('Tagihan Discount Leasing',i)
		print(i, ' xxx')
		for d in doc.daftar_tagihan_leasing:
			nominal = frappe.get_doc('Table Disc Leasing',{'parent':d.no_invoice,'nama_leasing':doc.customer}).nominal
			print(nominal, ' nominalxxx')
			d.nilai = nominal
			d.outstanding_discount = nominal
		doc.hitung_pph()
		doc.db_update()
		doc.update_children()
		repair_only_gl_entry('Tagihan Discount Leasing',i)
		print('DONE')

def patch_sn_no_rangka():
	data = frappe.db.sql(""" SELECT name,no_rangka from `tabSerial No` where no_rangka is null limit 100 """,as_dict=1)
	print(len(data))
	for i in data:
		print(i['name'])
		doc = frappe.get_doc('Serial No',i['name'])
		split = doc.name.split("--")
		doc.no_rangka = split[1]
		doc.no_mesin = split[0]
		
		doc.db_update()


def patch_ec_pe():
	pass

def patch_ec():
	from erpnext.stock.stock_ledger import update_entries_after
	
	data = frappe.db.sql(""" SELECT name from `tabExpense Claim` where docstatus = 1 """,as_dict=1)
	tmp = []

	for i in data:
		tmp.append(i['name'])

	print(len(tmp))
	print(tmp, ' tmpppp')

	for t in tmp:
		docname = t
		docu = frappe.get_doc("Expense Claim", docname)
		print(docu.name) 
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))

		docu.make_gl_entries()

		frappe.db.commit()
		print("done")

def patch_po_tax():
	tmp = ['PUR-ORD-2023-00308']
	conter = 1
	for t in tmp:
		print(conter)
		docname = t
		doc = frappe.get_doc("Purchase Order",docname)
		print(doc.name)
		taxes = get_taxes_and_charges("Purchase Taxes and Charges Template","Purchase Tax - W")
		# print(taxes, ' taxes111')
		doc.set_posting_time = 1
		doc.taxes_and_charges = 'Purchase Tax - W'
		doc.taxes = []
		for t in taxes:
			doc.append("taxes",t)
		doc.run_method("calculate_taxes_and_totals")
		doc.db_update()
		doc.update_children()
		frappe.db.commit()
		print("done")
		conter += 1

def patch_prac_tax():
	tmp = ['PUR-ORD-2023-00308']
	conter = 1
	for t in tmp:
		print(conter)
		docname = t
		doc = frappe.get_doc("Purchase Order",docname)
		print(doc.name)
		taxes = get_taxes_and_charges("Purchase Taxes and Charges Template","Purchase Tax - W")
		# print(taxes, ' taxes111')
		doc.set_posting_time = 1
		doc.taxes_and_charges = 'Purchase Tax - W'
		doc.taxes = []
		for t in taxes:
			doc.append("taxes",t)
		doc.run_method("calculate_taxes_and_totals")
		doc.db_update()
		doc.update_children()
		frappe.db.commit()
		print("done")
		conter += 1


def patch_prec(docname):
	# data = frappe.db.sql(""" SELECT pr.name as name,t.`name` as t_name,pr.`supplier` FROM `tabPurchase Receipt` pr
	# 	LEFT JOIN `tabPurchase Taxes and Charges` t ON  t.parent = pr.name 
	# 	WHERE pr.supplier = 'IFMI MOTOR' AND pr.`docstatus` = 1 AND t.`name` IS NULL """,as_dict=1)

	
	# tmp = []

	# for i in data:
	# 	tmp.append(i['name'])

	# print(len(tmp))
	# print(tmp, ' tmpppp')

	# # conter = 1
	# # for t in tmp:
	# # 	print(conter)
	# # 	print(t)
	# # 	conter += 1

	# docname = 'MAT-PRE-2023-00471'
	doc = frappe.get_doc("Purchase Receipt",docname)
	print(doc.name)
	taxes = get_taxes_and_charges("Purchase Taxes and Charges Template","Purchase Tax - W")
	print(taxes, ' taxes111')
	doc.set_posting_time = 1
	doc.taxes_and_charges = 'Purchase Tax - W'
	doc.taxes = []
	for t in taxes:
		doc.append("taxes",t)
	doc.run_method("calculate_taxes_and_totals")
	doc.db_update()
	doc.update_children()
	frappe.db.commit()
	print("done")

def patch_ste(docname):
	# docname = 'MAT-STE-2023-03120'
	doc = frappe.get_doc("Stock Entry",docname)
	print(doc.name)
	doc.set_posting_time = 1
	doc.calculate_rate_and_amount(reset_outgoing_rate=False)
	doc.db_update()
	doc.update_children()
	frappe.db.commit()
	print("done")

def patch_sn():
	docname = 'JMA1E1117814--MH1JMA114PK117983'
	doc = frappe.get_doc("Serial No",docname)
	print(doc.name)
	doc.update_serial_no_reference(docname)
	doc.db_update()
	frappe.db.commit()
	print("done")


@frappe.whitelist()
def repair_only_gl_entry(doctype,docname):	
	# bench --site wongkar2pjk.digitalasiasolusindo.com execute wongkar_selling.patch.repair_only_gl_entry --kwargs '{"doctype":"Tagihan Discount","docname":"Tagihan-D-03-2024-00001"}'
	docu = frappe.get_doc(doctype, docname)
	print(docu.name)
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))
	docu.make_gl_entries()

@frappe.whitelist()
def repair_gl_sle_entry(doctype,docname):
	
	docu = frappe.get_doc(doctype, docname)
	print(docu.name)
	delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(docname))
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))


	frappe.db.sql(""" UPDATE `tabSingles` SET VALUE = 1 WHERE `field` = "allow_negative_stock" """)
	docu.update_stock_ledger()

	docu.make_gl_entries()
	docu.repost_future_sle_and_gle()
	
	# docu = frappe.get_doc("Stock Entry", docname)
	# print("accountings", docu.items[0].basic_rate)
	frappe.db.sql(""" UPDATE `tabSingles` SET VALUE = 0 WHERE `field` = "allow_negative_stock" """)
	# frappe.db.commit()


def test_ste():
	ste_list=frappe.db.sql("""select name from `tabStock Entry` where mark=1 and updated=0  order by posting_date asc,posting_time asc """,as_list=1)
	count=1
	for row in ste_list:
		print("{} - {}".format(count,row[0]))
		ste=frappe.get_doc("Stock Entry",row[0])
		ste.get_stock_and_rate()
		ste.updated=1
		try:
			ste.save()
			frappe.db.commit()
		except:
			print("failed")
		count=count+1

def patch_rule():
	rule_list=frappe.db.sql("""select name from `tabRule Discount Leasing` where disable=0 order by valid_from desc """,as_list=1)
	for row in rule_list:
		doc=frappe.get_doc("Rule Discount Leasing",row[0])
		if doc.disable==0:
			doc.validate()
			frappe.db.commit()
def patch_sle():
	list_sle = frappe.db.sql(""" 
		SELECT sle.name, ste.name `ste`
		FROM `tabStock Entry` ste 
		JOIN `tabStock Ledger Entry` sle ON sle.voucher_no = ste.name 
		WHERE DATE(ste.modified) BETWEEN '2022-04-10' AND '2022-04-11' 
		and ste.docstatus = 1 """,as_dict=1)

	for row in list_sle:
		sle = frappe.get_doc("Stock Ledger Entry",row.name)
		print(sle.name, sle.voucher_no, sle.warehouse)
		process_serial_no(sle)

	frappe.db.commit()


#patch purchase_rate diserial no
def patch_serial():
	serial_data=frappe.db.sql("""select name,item_code,purchase_rate from `tabSerial No`""",as_dict=1)
	count=1
	for row in serial_data:
		pr = frappe.db.sql("""select net_rate from `tabPurchase Receipt Item` where item_code="{}" and (serial_no = "{}" or serial_no="{}\n") """.format(row.item_code,row.name,row.name),as_dict=1)
		logs="Count {}".format(count)
		if pr and len(pr)>0:
			if flt(pr[0].net_rate)!=flt(row.purchase_rate):
				frappe.db.sql("""update `tabSerial No` set purchase_rate={} where name="{}" """.format(pr[0].net_rate,row.name))
				logs="{} updated".format(logs)
		else:
			logs="{} skipped".format(logs)
		print(logs)
		count=count+1
@frappe.whitelist()
def kosongin_warehouse(nomor_do):
	list_serial = frappe.db.sql(""" 
		SELECT serial_no, warehouse
		FROM `tabStock Ledger Entry`
		WHERE voucher_no = "{}"
	 """.format(nomor_do),as_dict=1)
	for row in list_serial:
		if row.serial_no:
			array_serial = row.serial_no.split("\n")
			for serial in array_serial:
				serial_doc = frappe.get_doc("Serial No", serial)
				serial_doc.warehouse_temp = serial_doc.warehouse
				serial_doc.warehouse = ""
				serial_doc.db_update()

@frappe.whitelist()
def kosongin_warehouse_patch_material_transfer(nomor_do):
	list_serial = frappe.db.sql(""" 
		SELECT serial_no, warehouse
		FROM `tabStock Ledger Entry`
		WHERE voucher_no = "{}" and actual_qty < 0
	 """.format(nomor_do),as_dict=1)
	for row in list_serial:
		if row.serial_no:
			array_serial = row.serial_no.split("\n")
			for serial in array_serial:
				if serial:
					serial_doc = frappe.get_doc("Serial No", serial)
					serial_doc.warehouse_temp = serial_doc.warehouse
					serial_doc.warehouse = row.warehouse
					print(row.warehouse)
					serial_doc.db_update()

@frappe.whitelist()
def isi_warehouse(nomor_do):
	list_serial = frappe.db.sql(""" 
		SELECT serial_no, warehouse
		FROM `tabStock Ledger Entry`
		WHERE voucher_no = "{}"
	 """.format(nomor_do),as_dict=1)
	for row in list_serial:
		if row.serial_no:
			array_serial = row.serial_no.split("\n")
			for serial in array_serial:
				if serial:
					serial_doc = frappe.get_doc("Serial No", serial)
					serial_doc.warehouse = serial_doc.warehouse_temp
					serial_doc.warehouse_temp = ""
					serial_doc.db_update()



@frappe.whitelist()
def check_one_ledger():

	list_docname = [
		"MAT-STE-2022-02168"]

	for row in list_docname:
		docname = row
		if "STE" in row:
			doctype = "Stock Entry"
		else:
			doctype	= "Purchase Receipt"
		print("docname",docname)
		check = 0
		docu = frappe.get_doc(doctype, docname)
		
		delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(docname))
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))


		frappe.db.sql(""" UPDATE `tabSingles` SET VALUE = 1 WHERE `field` = "allow_negative_stock" """)
		docu.update_stock_ledger()

		# docu = frappe.get_doc("Stock Entry", docname)
		# print("sle", docu.items[0].basic_rate)

		docu.make_gl_entries()
		
		# docu = frappe.get_doc("Stock Entry", docname)
		# print("accountings", docu.items[0].basic_rate)
		frappe.db.sql(""" UPDATE `tabSingles` SET VALUE = 0 WHERE `field` = "allow_negative_stock" """)

	# list_docname = [
	# 	"MAT-PRE-2022-00141",
	# 	"MAT-PRE-2022-00147",
	# 	"MAT-PRE-2022-00150",
	# 	"MAT-PRE-2022-00151",
	# 	"MAT-PRE-2022-00156",
	# 	"MAT-PRE-2022-00158",
	# 	"MAT-PRE-2022-00167",
	# 	"MAT-PRE-2022-00155",
	# 	"MAT-STE-2022-00969",
	# 	"MAT-PRE-2022-00204",
	# 	"MAT-PRE-2022-00205",
	# 	"MAT-PRE-2022-00207",
	# 	"MAT-PRE-2022-00208",
	# 	"MAT-PRE-2022-00209",
	# 	"MAT-PRE-2022-00163",
	# 	"MAT-PRE-2022-00165",
	# 	"MAT-PRE-2022-00166",
	# 	"MAT-STE-2022-00834",
	# 	"MAT-STE-2022-01138-1",
	# 	"MAT-STE-2022-01198",
	# 	"MAT-PRE-2022-00187",
	# 	"MAT-STE-2022-01152",
	# 	"MAT-PRE-2022-00190",
	# 	"MAT-PRE-2022-00178",
	# 	"MAT-STE-2022-01406",
	# 	"MAT-STE-2022-01391-1",
	# 	"MAT-STE-2022-01466",
	# 	"MAT-PRE-2022-00193",
	# 	"MAT-STE-2022-01384-1",
	# 	"MAT-PRE-2022-00212",
	# 	"MAT-STE-2022-01416",
	# 	"MAT-STE-2022-01448",
	# 	"MAT-PRE-2022-00198",
	# 	"MAT-STE-2022-01289-1",
	# 	"MAT-STE-2022-01157",
	# 	"MAT-STE-2022-01260",
	# 	"MAT-STE-2022-01442",
	# 	"MAT-PRE-2022-00218",
	# 	"MAT-PRE-2022-00222",
	# 	"MAT-PRE-2022-00228",
	# 	"MAT-PRE-2022-00229",
	# 	"MAT-STE-2022-01164",
	# 	"MAT-PRE-2022-00238",
	# 	"MAT-STE-2022-01285",
	# 	"MAT-STE-2022-01334",
	# 	"MAT-PRE-2022-00232",
	# 	"MAT-PRE-2022-00239",
	# 	"MAT-STE-2022-01167",
	# 	"MAT-PRE-2022-00233",
	# 	"MAT-PRE-2022-00240",
	# 	"MAT-STE-2022-01467",
	# 	"MAT-PRE-2022-00241",
	# 	"MAT-STE-2022-01217",
	# 	"MAT-STE-2022-01145",
	# 	"MAT-STE-2022-01178",
	# 	"MAT-STE-2022-01314-1",
	# 	"MAT-PRE-2022-00248",
	# 	"MAT-PRE-2022-00249",
	# 	"MAT-PRE-2022-00263",
	# 	"MAT-PRE-2022-00251",
	# 	"MAT-PRE-2022-00253",
	# 	"MAT-PRE-2022-00255",
	# 	"MAT-PRE-2022-00256",
	# 	"MAT-PRE-2022-00244",
	# 	"MAT-STE-2022-01254",
	# 	"MAT-STE-2022-01274-1",
	# 	"MAT-STE-2022-01275",
	# 	"MAT-STE-2022-01293-1",
	# 	"MAT-STE-2022-01317-1",
	# 	"MAT-STE-2022-01408",
	# 	"MAT-PRE-2022-00270",
	# 	"MAT-PRE-2022-00271",
	# 	"MAT-PRE-2022-00277",
	# 	"MAT-PRE-2022-00278",
	# 	"MAT-PRE-2022-00274",
	# 	"MAT-PRE-2022-00279",
	# 	"MAT-PRE-2022-00280",
	# 	"MAT-PRE-2022-00275",
	# 	"MAT-STE-2022-01372-1",
	# 	"MAT-STE-2022-01222-1",
	# 	"MAT-STE-2022-01286",
	# 	"MAT-STE-2022-01127",
	# 	"MAT-PRE-2022-00290",
	# 	"MAT-PRE-2022-00289"]

@frappe.whitelist()
def benerin_sim_cancel():
	
	doc = frappe.get_doc("Sales Invoice Penjualan Motor",'ACC-SINVM-2022-05618')
	print(doc.name)
	doc.cancel()
	

@frappe.whitelist()
def benerin_sim():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor",'ACC-SINVM-2022-05618')
	# # print(doc.name)
	frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set docstatus = 0 where name = '{}' """.format(doc.name))
	frappe.db.commit()
	doc = frappe.get_doc("Sales Invoice Penjualan Motor",'ACC-SINVM-2022-05618')
	print(doc.name)
	print(doc.posting_date)
	doc.custom_missing_values2()
	doc.flags.ignore_permission = True
	doc.save()
	

@frappe.whitelist()
def benerin_sim_submit():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor",'ACC-SINVM-2022-05619')
	print(doc.name)
	print(doc.posting_date)
	doc.submit()
	

@frappe.whitelist()
def repair_cost_center_bjm():
	# bjm
	data = frappe.db.sql(""" SELECT sipm.name,sipm.cost_center,cc.parent_cost_center AS cc,cc2.`parent_cost_center` AS cc2 
		FROM `tabSales Invoice Penjualan Motor` sipm 
		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
		WHERE sipm.`docstatus`=2 AND cc2.parent_cost_center LIKE 'BJM%' ORDER BY sipm.`name` DESC LIMIT 1000 """,as_dict=1)

	tmp = []
	print(len(data))
	for i in data:
		try:
			print(i['name']+'|'+i['cc2'])
			if frappe.db.exists("Repost Item Valuation",{"voucher_no":i['name']}):
				doc_rep = frappe.db.get_list("Repost Item Valuation",{"voucher_no":i['name']})
				for r in doc_rep:
					print(r['name'], "rname")
					doc_rep2 = frappe.get_doc("Repost Item Valuation",{"voucher_no":i['name']})
					if doc_rep2.docstatus == 1:
						print(doc_rep2.name+"||"+doc_rep2.voucher_no)
						doc_rep2.cancel()
						doc_rep2.delete()
					else:
						doc_rep2.delete()
			doc = frappe.get_doc("Sales Invoice Penjualan Motor",i['name'])
			# doc.cancel()
			doc.delete()
			# frappe.db.commit()
			print(doc.name+"-"+"DONE")
		except Exception as e:
			print(i['name']+'|'+i['cc2']+'-'+str(e))
			# tmp.append(i['name']+'|'+i['cc2']+'-'+str(e))
	print(tmp)
			

# @frappe.whitelist()
# def repair_cost_center_ifmi():
# 	# Ifmi
# 	data = frappe.db.sql(""" SELECT sipm.name,sipm.cost_center,cc.parent_cost_center as cc,cc2.`parent_cost_center` as cc2
# 		FROM `tabSales Invoice Penjualan Motor` sipm 
# 		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
# 		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
# 		WHERE sipm.`docstatus`=1 AND cc2.parent_cost_center LIKE 'IFMI%' """,as_dict=1)

# 	tmp = []
# 	print(len(data))
# 	for i in data:
# 		try:
# 			print(i['name']+'|'+i['cc2'])
# 			# doc = frappe.get_doc("Sales Invoice Penjualan Motor",i['name'])
# 			# doc.cancel()
# 			# doc.delete()
# 			print(doc.name+"-"+"DONE")
# 		except Exception as e:
# 			tmp.append(i['name']+'|'+i['cc2']+'-'+e)
# 	print(tmp)



@frappe.whitelist()
def repair_sipm():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2022-24176")
	doc.cancel()
	print(doc.name)
	print(doc.docstatus)

@frappe.whitelist()
def repair_sipm_after():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2022-24176")
	frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set docstatus = 0 where name = '{}' """.format(doc.name))
	delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(doc.name))
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(doc.name))
	print(doc.name)
	print(doc.docstatus)


@frappe.whitelist()
def repair_rule():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2022-24176")
	# doc.from_group = 1
	doc.custom_repair_rule()
	doc.save()
	print(doc.name)
	print(doc.docstatus)
	# doc.submit()


@frappe.whitelist()
def balik_sipm():
	today = date.today()
	list_sipm = ['103af53deb']	
	# 103af53deb
	# 1125aaa67a benar
	tmp = []
	for i in list_sipm:
		# get_del = frappe.get_doc("Deleted Document",{"deleted_name":i,})
		get_del = frappe.get_doc("Deleted Document",i)
		print(get_del.name," | ",get_del.deleted_name," | ",get_del.creation," | ",get_del.owner)
		sync_baru = json.loads(get_del.data)
		doc_sync_baru = frappe.get_doc(sync_baru)
		if doc_sync_baru.doctype in ['Purchase Receipt','Purchase Invoice','Delivery Note','Sales Invoice','Sales Invoice Penjualan Motor','Stock Entry','Stock Reconciliation','POS Invoice']:
			if doc_sync_baru.posting_date != today:
				doc_sync_baru.set_posting_time = 1
		doc_sync_baru.status = "Draft"
		doc_sync_baru.docstatus = 0
		doc_sync_baru.amended_from = ""
		doc_sync_baru.__islocal = 1
		doc_sync_baru.flags.name_set = 1
		doc_sync_baru.flags.ignore_permissions=True
		doc_sync_baru.save()
		# doc_sync_baru.submit()
		print(doc_sync_baru.name,' --DONE')

		# try:
		# 	get_del = frappe.get_doc("Deleted Document",{"deleted_name":i})
		# 	# get_del = frappe.get_doc("Deleted Document",i)
		# 	print(get_del.name," | ",get_del.deleted_name," | ",get_del.creation," | ",get_del.owner)
		# 	sync_baru = json.loads(get_del.data)
		# 	doc_sync_baru = frappe.get_doc(sync_baru)
		# 	if doc_sync_baru.doctype in ['Purchase Receipt','Purchase Invoice','Delivery Note','Sales Invoice','Sales Invoice Penjualan Motor','Stock Entry','Stock Reconciliation','POS Invoice']:
		# 		if doc_sync_baru.posting_date != today:
		# 			doc_sync_baru.set_posting_time = 1
		# 	doc_sync_baru.status = "Draft"
		# 	doc_sync_baru.docstatus = 0
		# 	doc_sync_baru.amended_from = ""
		# 	doc_sync_baru.__islocal = 1
		# 	doc_sync_baru.flags.name_set = 1
		# 	doc_sync_baru.flags.ignore_permissions=True
		# 	doc_sync_baru.save()
		# 	doc_sync_baru.submit()
		# 	print(doc_sync_baru.name,' --DONE')
		# except Exception as e:
		# 	tmp.append(get_del.name+" e|r "+get_del.deleted_name+str(e))
	print(tmp, " tmp")

@frappe.whitelist()
def cencel_sipm():
	list_sipm = [
'ACC-SINVM-2022-18075',
'ACC-SINVM-2022-18087',
'ACC-SINVM-2022-18785',
'ACC-SINVM-2022-23658',
'ACC-SINVM-2022-18134',
'ACC-SINVM-2022-18136',
'ACC-SINVM-2022-18138',
'ACC-SINVM-2022-18144',
'ACC-SINVM-2022-18157',
'ACC-SINVM-2022-18159',
'ACC-SINVM-2022-22103',
'ACC-SINVM-2022-22581',
'ACC-SINVM-2022-23584',
'ACC-SINVM-2022-18552',
'ACC-SINVM-2022-18824',
'ACC-SINVM-2022-18567',
'ACC-SINVM-2022-18583',
'ACC-SINVM-2022-18593',
'ACC-SINVM-2022-18596',
'ACC-SINVM-2022-23411',
'ACC-SINVM-2022-19022',
'ACC-SINVM-2022-18655',
'ACC-SINVM-2022-18859',
'ACC-SINVM-2022-18665',
'ACC-SINVM-2022-18826',
'ACC-SINVM-2022-19025',
'ACC-SINVM-2022-19026',
'ACC-SINVM-2022-19056',
'ACC-SINVM-2022-19493',
'ACC-SINVM-2022-19632',
'ACC-SINVM-2022-18767',
'ACC-SINVM-2022-23580'
]
	conter = 1
	tmp = []
	print(len(list_sipm), " --list_sipm")
	for i in list_sipm:
		print(conter, " --conter")
		doc = frappe.get_doc("Sales Invoice Penjualan Motor",i)
		print(doc.name, " --name")
		if doc.docstatus == 1:
			doc.cancel()
			print(doc.name, " --DONE")
		else:
			tmp.append(doc.name+'-'+str(doc.docstatus)+"-SC")
		conter = conter + 1
	print(tmp, '-tmp')


@frappe.whitelist()
def cancel_ste():
	list_sn = [
'JBK1E1876303--MH1JBK111NK878740'
]
	conter = 1
	tmp = []
	tmp2 = []
	tmp3 = []
	tmp4= []
	tmp5=[]
	print(len(list_sn), " --list_sn")
	file_name = "test.txt"
	file_path = frappe.utils.get_files_path(file_name)
	new_file = open("/home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/test.txt", "w")
	for i in list_sn:
		print(conter, " --conter")
		print(i, " --list_sn")
		data = frappe.db.sql(""" SELECT sle.`name`,sle.`creation`,sle.`serial_no`,sle.`voucher_type`,sle.`voucher_no`,sle.`warehouse`,
			se.`posting_date` 
			FROM `tabStock Ledger Entry` sle 
			LEFT JOIN `tabStock Entry` se ON se.name = sle.`voucher_no`
			WHERE sle.`voucher_type`='Stock Entry' AND sle.`is_cancelled` = 0 AND sle.`serial_no` LIKE '%{}%'
			GROUP BY sle.`voucher_no` ORDER BY se.posting_date DESC,se.`posting_time` DESC """.format(i),as_dict=1)
		if data:
			for d in data:
				print(d['voucher_no'],'|',d.posting_date)
				doc = frappe.get_doc("Stock Entry",d['voucher_no'])
				print(doc.name, " --name")
				if doc.docstatus == 1:
					try:
						# frappe.db.begin()
						doc.cancel()
						# frappe.db.commit()
						print(doc.name, " --DONE")
						tmp4.append(i+"|"+doc.name+"|DONE")
						tmp5.append(i+"|"+doc.name+"|DONE")
					except Exception as e:
						print(i+"|"+doc.name+'|'+str(e)+"|err")
						tmp2.append(i+"|"+doc.name+'|'+str(e)+"|err")
						tmp5.append(i+"|"+doc.name+'|'+str(e)+"|err")
						# raise e
						frappe.db.rollback()
				else:
					print(i+"|"+doc.name+'|'+str(doc.docstatus)+"|SC")
					tmp.append(i+"|"+doc.name+'|'+str(doc.docstatus)+"|SC")
		else:
			print(i+"|STEC")
			tmp3.append(i+"|STEC")
		conter = conter + 1
	new_file.write(str(tmp)+"|tmp"+'\n'+str(tmp2)+"|tmp2"+'\n'+str(tmp3)+"|tmp3"+'\n'+str(tmp4)+"|tmp4"+'\n'+str(tmp5)+'|tmp5')
	new_file.close()
	# print(tmp, '-tmp')
	# print(tmp2, '-tmp2')
	# print(tmp3, '-tmp3')

@frappe.whitelist()
def cancel_prec():
	list_prec = [
'JBK1E1817059--MH1JBK111NK820935'
]
	conter = 1
	tmp = []
	tmp2 = []
	tmp3 = []
	tmp4= []
	tmp5=[]
	print(len(list_prec), " --list_prec")
	file_name = "test.txt"
	file_path = frappe.utils.get_files_path(file_name)
	new_file = open("/home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/test.txt", "w")
	for i in list_prec:
		print(conter, " --conter")
		print(i, " --list_prec")
		data = frappe.db.sql(""" SELECT sle.`name`,sle.`creation`,sle.`serial_no`,sle.`voucher_type`,sle.`voucher_no`,sle.`warehouse` 
			FROM `tabStock Ledger Entry` sle 
			WHERE sle.`voucher_type`='Purchase Receipt' AND sle.`is_cancelled` = 0 AND sle.`serial_no` LIKE '%{}%'
			GROUP BY sle.`voucher_no` """.format(i),as_dict=1)
		if data:
			for d in data:
				print(d['voucher_no'],'|',d.posting_date)
				doc = frappe.get_doc("Purchase Receipt",d['voucher_no'])
				print(doc.name, " --name")
				if doc.docstatus == 1:
					try:
						# frappe.db.begin()
						doc.cancel()
						# frappe.db.commit()
						print(doc.name, " --DONE")
						tmp4.append(i+"|"+doc.name+"|DONE")
						tmp5.append(i+"|"+doc.name+"|DONE")
					except Exception as e:
						print(i+"|"+doc.name+'|'+str(e)+"|err")
						tmp2.append(i+"|"+doc.name+'|'+str(e)+"|err")
						tmp5.append(i+"|"+doc.name+'|'+str(e)+"|err")
						# raise e
						frappe.db.rollback()
				else:
					print(i+"|"+doc.name+'|'+str(doc.docstatus)+"|SC")
					tmp.append(i+"|"+doc.name+'|'+str(doc.docstatus)+"|SC")
		else:
			print(i+"|PREC")
			tmp3.append(i+"|PREC")
		conter = conter + 1
	new_file.write(str(tmp)+"|tmp"+'\n'+str(tmp2)+"|tmp2"+'\n'+str(tmp3)+"|tmp3"+'\n'+str(tmp4)+"|tmp4"+'\n'+str(tmp5)+'|tmp5')
	new_file.close()
	# print(tmp, '-tmp')
	# print(tmp2, '-tmp2')
	# print(tmp3, '-tmp3')

@frappe.whitelist()
def cancel_prec_pinv():
	list_prec = [
"JMB1E1055152--MH1JMB111NK055008",
"JMB1E1055173--MH1JMB11XNK055010",
"JMB1E1058774--MH1JMB116PK058778",
"JMB1E1060255--MH1JMB11XPK060260",
"JMB1E1060272--MH1JMB114PK060271",
"JMB1E1061621--MH1JMB112PK061628",
"JMB1E1063121--MH1JMB117PK063245",
"JMD1E1054419--MH1JMD117NK054196",
"KCB1E1040068--MH1KCB115PK040117",
"KCD2E1033906--MH1KCD217PK033955",
"KCE1E1006100 / MH1KCE111NK006075",
"KCE1E1006148 / MH1KCE113NK006059",
"KD11E1357267--MH1KD1110PK357939",
"KD11E1359696--MH1KD1115PK360416",
"KD11E1360050--MH1KD1112PK360759",
"KF71E1472128--MH1KF7118PK472060",
"JMB1E1055069--MH1JMB112NK054921",
"KB11E1318863--MH1KB1112NK319325",
"KFB2E1008261--MH1KFB214NK008276",
"KFB2E1009997--MH1KFB213NK009905"
]
	conter = 1
	tmp = []
	tmp2 = []
	tmp3 = []
	tmp4= []
	tmp5=[]
	tmp_pi = []
	tmp_lcv = []
	print(len(list_prec), " --list_prec")
	file_name = "test.txt"
	file_path = frappe.utils.get_files_path(file_name)
	new_file = open("/home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/test.txt", "w")
	for i in list_prec:
		print(conter, " --conter")
		print(i, " --list_prec")
		data = frappe.db.sql(""" SELECT sle.`name`,sle.`creation`,sle.`serial_no`,sle.`voucher_type`,sle.`voucher_no`,sle.`warehouse` 
			FROM `tabStock Ledger Entry` sle 
			WHERE sle.`voucher_type`='Purchase Receipt' AND sle.`is_cancelled` = 0 AND sle.`serial_no` LIKE '%{}%'
			GROUP BY sle.`voucher_no` """.format(i),as_dict=1)
		if data:
			for d in data:
				print(d['voucher_no'],'|',d.posting_date)
				cek_lcv = frappe.db.sql(""" SELECT DISTINCT lcv.name from `tabLanded Cost Purchase Receipt` lc 
					join `tabLanded Cost Voucher` lcv on lcv.name = lc.parent
					where lc.receipt_document = '{}' and lcv.docstatus = 1 """.format(d['voucher_no']),as_dict=1)

				if cek_lcv:
					for l in cek_lcv:
						print(l['name'], ' --cek_lcv')
						tmp_lcv.append(i+"|"+l['name']+'|LCV')
						doc_lcv = frappe.get_doc("Landed Cost Voucher",l['name'])
						doc_lcv.cancel()

				cek = frappe.db.sql(""" SELECT DISTINCT  pi.name from `tabPurchase Invoice Item` pii 
					join `tabPurchase Invoice` pi on pi.name = pii.parent 
					where pii.purchase_receipt = '{}' and pi.docstatus = 1 """.format(d['voucher_no']),as_dict=1)
				if cek:
					for c in cek:
						print(c['name'], ' --pi_name')
						tmp_pi.append(i+"|"+c['name']+'|PI')
						doc_pi = frappe.get_doc("Purchase Invoice",c['name'])
						doc_pi.cancel()
				
				doc = frappe.get_doc("Purchase Receipt",d['voucher_no'])
				print(doc.name, " --name")
				if doc.docstatus == 1:
					try:
						# frappe.db.begin()
						doc.cancel()
						# frappe.db.commit()
						print(doc.name, " --DONE")
						tmp4.append(i+"|"+doc.name+"|DONE")
						tmp5.append(i+"|"+doc.name+"|DONE")
					except Exception as e:
						print(i+"|"+doc.name+'|'+str(e)+"|err")
						tmp2.append(i+"|"+doc.name+'|'+str(e)+"|err")
						tmp5.append(i+"|"+doc.name+'|'+str(e)+"|err")
						# raise e
						frappe.db.rollback()
				else:
					print(i+"|"+doc.name+'|'+str(doc.docstatus)+"|SC")
					tmp.append(i+"|"+doc.name+'|'+str(doc.docstatus)+"|SC")
		else:
			print(i+"|PREC")
			tmp3.append(i+"|PREC")
		conter = conter + 1
	new_file.write(str(tmp)+"|tmp"+'\n'+str(tmp2)+"|tmp2"+'\n'+str(tmp3)+"|tmp3"+'\n'+str(tmp4)+"|tmp4"+'\n'+str(tmp5)+'|tmp5'+'\n'+str(tmp_pi)+'|tmp_pi'+'\n'+str(tmp_lcv)+'|tmp_lcv')
	new_file.close()
	# print(tmp, '-tmp')
	# print(tmp2, '-tmp2')
	# print(tmp3, '-tmp3')

@frappe.whitelist()
def patch_rdl():
	pass
	docname = [
'ACC-SINVM-2023-02465'
]
	# "ACC-SINVM-2023-02751"
	conter = 1
	print(len(docname)," Jumlah")
	for i in docname:
		print(i)
		frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set docstatus = 0 where name = '{}' """.format(i))
		doc = frappe.get_doc("Sales Invoice Penjualan Motor",i)
		doc.set_posting_time = 1
		doc.diskon = 1
		doc.items = []
		doc.custom_missing_values2()
		doc.set_status()
		doc.save()
		
		frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set docstatus = 1 where name = '{}' """.format(i))
		frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor Item` set docstatus = 1 where parent = '{}' """.format(i))
		frappe.db.commit()
		
		docu = frappe.get_doc("Sales Invoice Penjualan Motor",i)

		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(i))

		# docu.calculate_taxes_and_totals()
		docu.set_status()
		docu.make_gl_entries()
		print(docu.status)
		frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set status = '{}' where name = '{}' """.format(docu.status,i))
		frappe.db.commit()
		print(conter, " conter")
		print(i," --DONE")
		conter = conter + 1


@frappe.whitelist()
def patch_rdl2():
	docname = [
'ACC-SINVM-2023-02821',
'ACC-SINVM-2023-02825',
'ACC-SINVM-2023-02833',
'ACC-SINVM-2023-02835',
'ACC-SINVM-2023-02836',
'ACC-SINVM-2023-02837',
'ACC-SINVM-2023-02840',
'ACC-SINVM-2023-02841',
'ACC-SINVM-2023-02842',
'ACC-SINVM-2023-02848',
'ACC-SINVM-2023-02850',
'ACC-SINVM-2023-02851',
'ACC-SINVM-2023-02852',
'ACC-SINVM-2023-02855',
'ACC-SINVM-2023-02866',
'ACC-SINVM-2023-02867',
'ACC-SINVM-2023-02869',
'ACC-SINVM-2023-02870',
'ACC-SINVM-2023-02872',
'ACC-SINVM-2023-02873',
'ACC-SINVM-2023-02874',
'ACC-SINVM-2023-02875',
'ACC-SINVM-2023-02876',
'ACC-SINVM-2023-02878',
'ACC-SINVM-2023-02880',
'ACC-SINVM-2023-02881',
'ACC-SINVM-2023-02882',
'ACC-SINVM-2023-02883',
'ACC-SINVM-2023-02884',
'ACC-SINVM-2023-02885',
'ACC-SINVM-2023-02886',
'ACC-SINVM-2023-02890',
'ACC-SINVM-2023-02891',
'ACC-SINVM-2023-02892',
'ACC-SINVM-2023-02893',
'ACC-SINVM-2023-02896',
'ACC-SINVM-2023-02897',
'ACC-SINVM-2023-02898',
'ACC-SINVM-2023-02899',
'ACC-SINVM-2023-02900',
'ACC-SINVM-2023-02901',
'ACC-SINVM-2023-02904',
'ACC-SINVM-2023-02905',
'ACC-SINVM-2023-02906',
'ACC-SINVM-2023-02908',
'ACC-SINVM-2023-02909',
'ACC-SINVM-2023-02910',
'ACC-SINVM-2023-02911',
'ACC-SINVM-2023-02912',
'ACC-SINVM-2023-02913',
'ACC-SINVM-2023-02914',
'ACC-SINVM-2023-02915',
'ACC-SINVM-2023-02916',
'ACC-SINVM-2023-02917',
'ACC-SINVM-2023-02918',
'ACC-SINVM-2023-02919',
'ACC-SINVM-2023-02920',
'ACC-SINVM-2023-02923',
'ACC-SINVM-2023-02924',
'ACC-SINVM-2023-02927',
'ACC-SINVM-2023-02928',
'ACC-SINVM-2023-02930',
'ACC-SINVM-2023-02932',
'ACC-SINVM-2023-02933',
'ACC-SINVM-2023-02947',
'ACC-SINVM-2023-02948',
'ACC-SINVM-2023-02951',
'ACC-SINVM-2023-02953',
'ACC-SINVM-2023-02955',
'ACC-SINVM-2023-02957',
'ACC-SINVM-2023-02964',
'ACC-SINVM-2023-02965',
'ACC-SINVM-2023-02966',
'ACC-SINVM-2023-02968',
'ACC-SINVM-2023-02969',
'ACC-SINVM-2023-02970',
'ACC-SINVM-2023-02971',
'ACC-SINVM-2023-02972',
'ACC-SINVM-2023-02976',
'ACC-SINVM-2023-02978',
'ACC-SINVM-2023-02979',
'ACC-SINVM-2023-02982',
'ACC-SINVM-2023-02984',
'ACC-SINVM-2023-02986',
'ACC-SINVM-2023-02987',
'ACC-SINVM-2023-02988',
'ACC-SINVM-2023-02989',
'ACC-SINVM-2023-02991',
'ACC-SINVM-2023-02997',
'ACC-SINVM-2023-03002',
'ACC-SINVM-2023-03003',
'ACC-SINVM-2023-03004',
'ACC-SINVM-2023-03005',
'ACC-SINVM-2023-03010',
'ACC-SINVM-2023-03015',
'ACC-SINVM-2023-03016',
'ACC-SINVM-2023-03023',
'ACC-SINVM-2023-03025',
'ACC-SINVM-2023-03026-1',
'ACC-SINVM-2023-03027',
'ACC-SINVM-2023-03028',
'ACC-SINVM-2023-03029',
'ACC-SINVM-2023-03037',
'ACC-SINVM-2023-03038',
'ACC-SINVM-2023-03055',
'ACC-SINVM-2023-03059',
'ACC-SINVM-2023-03062',
'ACC-SINVM-2023-03063',
'ACC-SINVM-2023-03064',
'ACC-SINVM-2023-03065',
'ACC-SINVM-2023-03066',
'ACC-SINVM-2023-03067',
'ACC-SINVM-2023-03069',
'ACC-SINVM-2023-03070',
'ACC-SINVM-2023-03071',
'ACC-SINVM-2023-03072',
'ACC-SINVM-2023-03073',
'ACC-SINVM-2023-03074'
]
	# "ACC-SINVM-2023-02751"
	conter = 1
	print(len(docname)," Jumlah")
	for i in docname:
		print(i)
		doc = frappe.get_doc("Sales Invoice Penjualan Motor",i)
		doc.cancel()
		frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set docstatus = 0 where name = '{}' """.format(i))
		delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(i))
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(i))

		docu = frappe.get_doc("Sales Invoice Penjualan Motor",i)
		docu.set_posting_time = 1
		docu.diskon = 1
		docu.save()
		docu.submit()
		frappe.db.commit()
		print(conter, " --conter")
		print(i, " --Done")
		conter = conter + 1
		




