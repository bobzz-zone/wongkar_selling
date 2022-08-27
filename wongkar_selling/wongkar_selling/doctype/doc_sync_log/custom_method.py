# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import frappe.utils
from frappe.utils import cstr, flt, getdate, cint, nowdate, add_days, get_link_to_form, strip_html
from datetime import datetime

import json
import hashlib
import time
# import nextapp.file_manager
import operator
# from nextapp.file_manager import upload
# from nextapp.base import validate_method
from frappe.utils import get_fullname, get_request_session
from frappe import utils
import sys
# ERPNEXT
from erpnext.stock.get_item_details import get_item_details

# CUSTOM METHOD
# from nextapp.app.helper import *
# from api_integration.validation import *
# from api_integration.validation import * 
# from api_integration.validation import *
# from nextapp.nextsales import get_item

LIMIT_PAGE = 20



@frappe.whitelist()
def listCustomer():
	list_customer = [	
		[ 'BUSA MANDIRI', '200000000' ],
		[ 'CAHAYA TIMUR TK.', '1000000000' ],
		[ 'CRYPTON', '200000000' ],
		[ 'CURUG FURNITURE TK.', '50000000' ],
		[ 'DIDI SUPRIATNA', '200000000' ],
		[ 'EDWARD', '200000000' ],
		[ 'EK SING', '300000000' ],
		[ 'ERA FOAM', '200000000' ],
		[ 'HAND JANG', '500000000' ],
		[ 'INDOJAYA MAKMUR CV.', '300000000' ],
		[ 'JONO BP', '750000000' ],
		[ 'KAITEN ABANG INBA', '300000000' ],
		[ 'LOUISZ INTERNATIONAL PT.', '200000000' ],
		[ 'MAKMUR JAYA PERKASA CV.', '200000000' ],
		[ 'MATRASTAMA MAESTRA PERKASA', '1000000000' ],
		[ 'MEGA KENCANA MANDIRI PT.', '300000000' ],
		[ 'PELANGI JAYA CV', '50000000' ],
		[ 'SAMPORLAND PT.', '100000000' ],
		[ 'UREST PANN ASIA PT.', '500000000' ],
		[ 'WINNER FOAM', '30000000' ],
		[ 'YONATHAN', '50000000' ],
		[ 'YONGLAND SILAMPARI SPRINGBED PT.', '500000000' ]
	]
	company = frappe.get_value('Global Defaults',"", ['default_company']) 
	for i in list_customer:
		data = {
		    "company": company,
			"customer": i[0],
			"new_credit_limit": i[1]
		}
		updateCredit(data)

@frappe.whitelist()
def updateCredit(data):
	# key yg input dalam data parameter adalah { "customer":"customer", "new_credit_limit":"10000" }
	if "customer" in data:
		result = frappe.get_value('Customer Credit Limit', {'parent': data['customer']}, ['name', 'credit_limit'] ) 
		if result:
			print("{}-1".format(data['customer']))
			child = frappe.get_doc('Customer Credit Limit', {'parent': data['customer']})
			child.credit_limit = int(data['new_credit_limit'])
			child.db_update()
			frappe.db.commit()
		else:
			print("{}-2".format(data['customer']))
			customer_doc = frappe.get_doc("Customer", data['customer'])
			list_credit_limit = {
				"company" : data['company'],
				"credit_limit" : 5000000000
			}
			customer_doc.append("credit_limits",list_credit_limit)
			customer_doc.save()
			result = frappe.get_value('Customer Credit Limit', {'parent': data['customer']}, ['name', 'credit_limit'] ) 
			if result:
				child = frappe.get_doc('Customer Credit Limit', {'parent': data['customer']})
				child.credit_limit = int(data['new_credit_limit'])
				child.db_update()
				frappe.db.commit()

def rename_item():
	list_rename = frappe.db.sql("""select old_name,new_name from `tabRename Item` where old_name IN (select name from `tabItem`) """,as_list=1)
	count=1
	for row in list_rename:
		print(count)
		frappe.rename_doc("Item",row[0],row[1])
		frappe.db.commit()
		count=count+1
@frappe.whitelist()
def repair_gl_entry(doctype,docname):
	docu = frappe.get_doc(doctype, docname)

	frappe.db.sql(""" UPDATE `tabSingles` SET value = 1 WHERE field = "allow_negative_stock" """)
	delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(docname))
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))
	docu.update_stock_ledger()
	docu.make_gl_entries()
	docu.repost_future_sle_and_gle()
	frappe.db.sql(""" UPDATE `tabSingles` SET value = 0 WHERE field = "allow_negative_stock" """)
	# print("Membenarkan LEDGER dari {} - DONE ".format(docname))
	frappe.db.commit()

@frappe.whitelist()
def repair_sle_entry(doctype,docname):
	docu = frappe.get_doc(doctype, docname)

	frappe.db.sql(""" UPDATE `tabSingles` SET value = 1 WHERE field = "allow_negative_stock" """)
	delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(docname))
	# delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(docname))
	docu.update_stock_ledger()
	# docu.make_gl_entries()
	frappe.db.sql(""" UPDATE `tabSingles` SET value = 0 WHERE field = "allow_negative_stock" """)
	# print("Membenarkan LEDGER dari {} - DONE ".format(docname))
	frappe.db.commit()

@frappe.whitelist()
def get_invoice_dpi(customer,from_date,to_date):
	data = frappe.db.sql("""
		SELECT NAME,customer,posting_date, grand_total 
		FROM `tabSales Invoice` 
		WHERE customer = "{}"
		AND
		posting_date >= "{}"
		AND
		posting_date <= "{}"
		AND docstatus = 1
		AND is_return = 0 """.format(customer,from_date,to_date))

	return data


@frappe.whitelist()
def get_document_detail(doctype,docname):
	item_tabel = ""
	if str(doctype) == "Delivery Note":
		item_tabel = "Delivery Note Item"
		data = frappe.db.sql("""
		SELECT child.item_code, child.item_name, child.name, child.parent, child.qty_ordered, parent.customer, parent.is_return, 
				parent.transporter,parent.driver, parent.lr_no, parent.vehicle_no, parent.transporter_name, parent.driver_name, parent.lr_date
			FROM `tab{}` child
			JOIN `tab{}` parent on child.parent = parent.name
			WHERE child.parent = "{}" 
			ORDER BY child.idx
		""".format(item_tabel,doctype,docname))

	elif str(doctype) == "Purchase Receipt":
		item_tabel = "Purchase Receipt Item"
		data = frappe.db.sql("""
		SELECT child.item_code, child.item_name, child.name, child.parent, child.qty, parent.supplier, parent.is_return,
		 parent.transporter_name, parent.lr_no, parent.lr_date
			FROM `tab{}` child
			JOIN `tab{}` parent on child.parent = parent.name
			WHERE child.parent = "{}" 
			ORDER BY child.idx
		""".format(item_tabel,doctype,docname))

	elif str(doctype) == "Stock Entry":
		item_tabel = "Stock Entry Detail"
		data = frappe.db.sql("""
		SELECT child.item_code, child.item_name, child.name, child.parent, child.qty, "-", parent.purpose
			FROM `tab{}` child
			JOIN `tab{}` parent on child.parent = parent.name
			WHERE child.parent = "{}" 
			ORDER BY child.idx
		""".format(item_tabel,doctype,docname))
			
	return data
@frappe.whitelist()
def close_purchase_order():
	list_po = ["PO-2021-03-00164-1"]
	for row in list_po:
		doc = frappe.get_doc("Purchase Order", row)
		doc.status = "Closed"
		doc.workflow_state = "Closed"
		doc.db_update()

@frappe.whitelist()
def patch_sales_invoice():
	sales_invoice_list = frappe.db.sql(""" 
		SELECT sinv.`name` FROM `tabSales Invoice` sinv
		JOIN `tabSales Taxes and Charges` stc ON stc.`parent` = sinv.name
		WHERE sinv.`total_taxes_and_charges` > 0
		AND stc.`included_in_print_rate` = 1
		AND sinv.`docstatus` = 1

	""")

	for row in sales_invoice_list:
		sales_invoice = frappe.get_doc("Sales Invoice", str(row[0]))
		sales_invoice.taxes = []
		frappe.db.sql(""" UPDATE `tabSales Invoice` SET docstatus = 0 WHERE name = "{}" """.format(row[0]))
		sales_invoice.save()
		# # repair ste entry
		frappe.db.sql(""" UPDATE `tabSales Invoice` SET docstatus = 1 WHERE name = "{}" """.format(row[0]))
		
		delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(row[0]))
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(row[0]))
		
		sales_invoice.update_stock_ledger()
		sales_invoice.make_gl_entries()
		frappe.db.commit()

@frappe.whitelist()
def patch_stock_entry():
	list_ste = frappe.db.sql(""" 
		SELECT name FROM `tabStock Entry`
		WHERE  docstatus = 1  """)

	for row in list_ste:
		document = frappe.get_doc("Stock Entry",row[0])
		
		document.dibuat_oleh = frappe.get_doc("User",document.owner).full_name
		document.dibuat_oleh_datetime = document.creation
		document.diapprove_oleh = frappe.get_doc("User",document.modified_by).full_name
		now = datetime.now()
		document.diapprove_oleh_datetime = document.modified
		document.db_update()
		frappe.db.commit()

@frappe.whitelist()
def patch_request_retur():
	list_ste = frappe.db.sql(""" 
		SELECT name FROM `tabRequest Retur`
		WHERE  docstatus = 1  """)

	for row in list_ste:
		document = frappe.get_doc("Request Retur",row[0])
		
		document.dibuat_oleh = frappe.get_doc("User",document.owner).full_name
		document.dibuat_oleh_datetime = document.creation
		document.diapprove_oleh = frappe.get_doc("User",document.modified_by).full_name
		now = datetime.now()
		document.diapprove_oleh_datetime = document.modified
		document.db_update()
		frappe.db.commit()


@frappe.whitelist()
def patch_purchase_invoice():
	sales_invoice_list = frappe.db.sql(""" 
		SELECT sinv.`name` FROM `tabPurchase Invoice` sinv
		WHERE sinv.name = "ACC-PINV-2021- ET00045" or sinv.name = "ACC-PINV-2021- ET00128"
	""")

	for row in sales_invoice_list:
		sales_invoice = frappe.get_doc("Purchase Invoice", str(row[0]))
		sales_invoice.set_posting_time = 1
		print(row[0])
		sales_invoice.taxes = []
		frappe.db.sql(""" UPDATE `tabPurchase Invoice` SET docstatus = 0 WHERE name = "{}" """.format(row[0]))
		sales_invoice.save()
		frappe.db.sql(""" UPDATE `tabPurchase Invoice` SET docstatus = 1 WHERE name = "{}" """.format(row[0]))
		
		delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(row[0]))
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(row[0]))
		
		sales_invoice.update_stock_ledger()
		sales_invoice.make_gl_entries()
		frappe.db.commit()

@frappe.whitelist()
def patch_tt_pinv():
	get_sor = frappe.db.sql(""" SELECT name FROM `tabPurchase Invoice`
	 WHERE docstatus < 2 and (workflow_state IS NOT NULL or workflow_state != "") 
	 """)
	for sor in get_sor:
		no_sales_order = sor[0]

		siapa_buat = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Pending",%"Waiting Confirmation"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_buat) > 0:
			so_doc = frappe.get_doc("Purchase Invoice", no_sales_order)
			so_doc.diketahui_oleh = siapa_buat[0][0]
			so_doc.diketahui_oleh_datetime = siapa_buat[0][1]
			so_doc.db_update()

		# siapa_koor = frappe.db.sql(""" SELECT 
		# 	tus.`full_name`,
		# 	CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

		# 	FROM `tabVersion` tver 
		# 	JOIN `tabUser` tus ON tus.name = tver.`owner`
		# 	WHERE tver.docname = "{}"
		# 	AND tver.data LIKE '%"workflow_state",%"Waiting Confirmation",%"Approved"%'
		# 	LIMIT 1 
		# """.format(no_sales_order))

		# if len(siapa_koor) > 0:
		# 	so_doc = frappe.get_doc("Payment Entry", no_sales_order)
		# 	so_doc.diperiksa = siapa_koor[0][0]
		# 	so_doc.diperiksa_datetime = siapa_koor[0][1]
		# 	so_doc.db_update()

		frappe.db.commit()

@frappe.whitelist()
def patch_tt_pe():
	get_sor = frappe.db.sql(""" SELECT name FROM `tabPayment Entry`
	 WHERE docstatus < 2 and (workflow_state IS NOT NULL or workflow_state != "") 
	 """)
	for sor in get_sor:
		no_sales_order = sor[0]

		siapa_buat = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Pending",%"Waiting Confirmation"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_buat) > 0:
			so_doc = frappe.get_doc("Payment Entry", no_sales_order)
			so_doc.mengetahui = siapa_buat[0][0]
			so_doc.mengetahui_datetime = siapa_buat[0][1]
			so_doc.db_update()

		siapa_koor = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Waiting Confirmation",%"Approved"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_koor) > 0:
			so_doc = frappe.get_doc("Payment Entry", no_sales_order)
			so_doc.diperiksa = siapa_koor[0][0]
			so_doc.diperiksa_datetime = siapa_koor[0][1]
			so_doc.db_update()

		frappe.db.commit()

@frappe.whitelist()
def patch_tt_je():
	get_sor = frappe.db.sql(""" SELECT name FROM `tabJournal Entry`
	 WHERE docstatus < 2 
	 and (workflow_state IS NOT NULL or workflow_state != "")
	 and (mengetahui = "" or mengetahui IS NULL)
	 ORDER BY creation DESC """)
	for sor in get_sor:
		no_sales_order = sor[0]

		siapa_buat = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Pending",%"Waiting Confirmation"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_buat) > 0:
			so_doc = frappe.get_doc("Journal Entry", no_sales_order)
			so_doc.mengetahui = siapa_buat[0][0]
			so_doc.mengetahui_datetime = siapa_buat[0][1]
			so_doc.db_update()

		siapa_koor = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Waiting Confirmation",%"Approved"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_koor) > 0:
			so_doc = frappe.get_doc("Journal Entry", no_sales_order)
			so_doc.diperiksa = siapa_koor[0][0]
			so_doc.diperiksa_datetime = siapa_koor[0][1]
			so_doc.db_update()

		frappe.db.commit()

@frappe.whitelist()
def patch_tt_so():
	get_sor = frappe.db.sql(""" SELECT name FROM `tabSales Order` WHERE docstatus < 2 """)
	for sor in get_sor:
		no_sales_order = sor[0]

		siapa_buat = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Pending",%"In DIC"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_buat) > 0:
			so_doc = frappe.get_doc("Sales Order", no_sales_order)
			so_doc.sales = siapa_buat[0][0]
			so_doc.datetime_sales = siapa_buat[0][1]
			so_doc.db_update()

		siapa_koor = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Waiting Confirmation",%"Approved"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_koor) > 0:
			so_doc = frappe.get_doc("Sales Order", no_sales_order)
			so_doc.koordinator = siapa_koor[0][0]
			so_doc.datetime_koordinator = siapa_koor[0][1]
			so_doc.db_update()

		siapa_dic = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND 
			(tver.data LIKE '%"workflow_state",%"In DIC",%"In Purchasing"%'
			OR
			tver.data LIKE '%"workflow_state",%"In DIC",%"Waiting Confirmation"%')
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_dic) > 0:
			so_doc = frappe.get_doc("Sales Order", no_sales_order)
			so_doc.dic = siapa_dic[0][0]
			so_doc.datetime_dic = siapa_dic[0][1]
			so_doc.db_update()

		siapa_purchasing = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"In Purchasing",%"Pending Sales Confirmation"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_purchasing) > 0:
			so_doc = frappe.get_doc("Sales Order", no_sales_order)
			so_doc.purchasing = siapa_purchasing[0][0]
			so_doc.datetime_purchasing = siapa_purchasing[0][1]
			so_doc.db_update()
		print(str(no_sales_order))
		frappe.db.commit()

@frappe.whitelist()
def patch_tt_po():
	get_sor = frappe.db.sql(""" SELECT name FROM `tabPurchase Order` WHERE docstatus < 2 and dibuat_oleh IS NOT NULL and (datetime_dibuat_oleh IS NULL OR datetime_dibuat_oleh = "") """)
	for sor in get_sor:
		no_sales_order = sor[0]

		siapa_buat = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Draft",%"Waiting Confirmation"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_buat) > 0:
			so_doc = frappe.get_doc("Purchase Order", no_sales_order)
			if not so_doc.dibuat_oleh:
				so_doc.dibuat_oleh = siapa_buat[0][0]
			so_doc.datetime_dibuat_oleh = siapa_buat[0][1]
			so_doc.db_update()

		siapa_koor = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Waiting Confirmation",%"Approved by Purchasing"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_koor) > 0:
			so_doc = frappe.get_doc("Purchase Order", no_sales_order)
			if not so_doc.mengetahui:
				so_doc.mengetahui = siapa_koor[0][0]
			so_doc.datetime_mengetahui = siapa_koor[0][1]
			so_doc.db_update()

		siapa_dic = frappe.db.sql(""" SELECT 
			tus.`full_name`,
			CONCAT(DATE(tver.`creation`)," ",TIME(tver.creation))

			FROM `tabVersion` tver 
			JOIN `tabUser` tus ON tus.name = tver.`owner`
			WHERE tver.docname = "{}"
			AND tver.data LIKE '%"workflow_state",%"Approved by Purchasing",%"Approved"%'
			LIMIT 1 
		""".format(no_sales_order))

		if len(siapa_dic) > 0:
			so_doc = frappe.get_doc("Purchase Order", no_sales_order)
			if not so_doc.menyetujui:
				so_doc.menyetujui = siapa_dic[0][0]
			so_doc.datetime_menyetujui = siapa_dic[0][1]
			so_doc.db_update()

		print(str(no_sales_order))
		frappe.db.commit()


@frappe.whitelist(allow_guest=False)
def get_item_with_history(is_sales_item='1',is_stock_item='1',ref='',sort='',page='0'):
	seen = ""
	data = get_item(is_sales_item='1',is_stock_item='1',ref='',sort='',page='0')
	
	for row in data:
		history_price_list = ""
		history_price_list_rate = 0
		hasil_price_list = frappe.db.sql(""" 
			SELECT
			IFNULL(rate,0), price_list
			FROM `tabPrice List Generator` plg
			LEFT JOIN `tabPrice List Generator Item` pli
			 ON pli.parent = plg.name
			WHERE 
			(plg.item_code = "{0}" 
			OR pli.item_code = "{0}")
			AND plg.docstatus = 1

			ORDER BY plg.creation DESC
			LIMIT 1 """.format(row['item_code']))

		if len(hasil_price_list) > 0:
			history_price_list = hasil_price_list[0][1]
			history_price_list_rate = hasil_price_list[0][0]

		row['history_price_list'] = history_price_list
		row['history_price_list_rate'] = history_price_list_rate


	return data


@frappe.whitelist()
def debug(account_name):
	print(get_balance_on(account = "1150.001 - Biaya Dibayar Dimuka - ETM-BGR"))

@frappe.whitelist()
def get_balance_on(account=None, date=None, party_type=None, party=None, company=None,
	in_account_currency=True, cost_center=None, ignore_account_permission=False):
	from erpnext.accounts.utils import FiscalYearError, get_fiscal_year


	if not account and frappe.form_dict.get("account"):
		account = frappe.form_dict.get("account")
	if not date and frappe.form_dict.get("date"):
		date = frappe.form_dict.get("date")
	if not party_type and frappe.form_dict.get("party_type"):
		party_type = frappe.form_dict.get("party_type")
	if not party and frappe.form_dict.get("party"):
		party = frappe.form_dict.get("party")
	if not cost_center and frappe.form_dict.get("cost_center"):
		cost_center = frappe.form_dict.get("cost_center")


	cond = []
	if date:
		cond.append("posting_date <= %s" % frappe.db.escape(cstr(date)))
	else:
		# get balance of all entries that exist
		date = nowdate()

	if account:
		acc = frappe.get_doc("Account", account)

	try:
		year_start_date = get_fiscal_year(date, company=company, verbose=0)[1]
	except FiscalYearError:
		if getdate(date) > getdate(nowdate()):
			# if fiscal year not found and the date is greater than today
			# get fiscal year for today's date and its corresponding year start date
			year_start_date = get_fiscal_year(nowdate(), verbose=1)[1]
		else:
			# this indicates that it is a date older than any existing fiscal year.
			# hence, assuming balance as 0.0
			return 0.0

	if account:
		report_type = acc.report_type
	else:
		report_type = ""

	if cost_center and report_type == 'Profit and Loss':
		cc = frappe.get_doc("Cost Center", cost_center)
		if cc.is_group:
			cond.append(""" exists (
				select 1 from `tabCost Center` cc where cc.name = gle.cost_center
				and cc.lft >= %s and cc.rgt <= %s
			)""" % (cc.lft, cc.rgt))

		else:
			cond.append("""gle.cost_center = %s """ % (frappe.db.escape(cost_center, percent=False), ))


	if account:

		if not (frappe.flags.ignore_account_permission
			or ignore_account_permission):
			acc.check_permission("read")

		if report_type == 'Profit and Loss':
			# for pl accounts, get balance within a fiscal year
			cond.append("posting_date >= '%s' and voucher_type != 'Period Closing Voucher'" \
				% year_start_date)
		# different filter for group and ledger - improved performance
		if acc.is_group:
			cond.append("""exists (
				select name from `tabAccount` ac where ac.name = gle.account
				and ac.lft >= %s and ac.rgt <= %s
			)""" % (acc.lft, acc.rgt))

			# If group and currency same as company,
			# always return balance based on debit and credit in company currency
			if acc.account_currency == frappe.get_cached_value('Company',  acc.company,  "default_currency"):
				in_account_currency = False
		else:
			cond.append("""gle.account = %s """ % (frappe.db.escape(account, percent=False), ))

	if party_type and party:
		cond.append("""gle.party_type = %s and gle.party = %s """ %
			(frappe.db.escape(party_type), frappe.db.escape(party, percent=False)))

	if company:
		cond.append("""gle.company = %s """ % (frappe.db.escape(company, percent=False)))

	if account or (party_type and party):
		if in_account_currency:
			select_field = "sum(debit_in_account_currency) - sum(credit_in_account_currency)"
		else:
			select_field = "sum(debit) - sum(credit)"

		print("""
			SELECT {0}
			FROM `tabGL Entry` gle
			WHERE {1}""".format(select_field, " and ".join(cond)))

		bal = frappe.db.sql("""
			SELECT {0}
			FROM `tabGL Entry` gle
			WHERE {1}""".format(select_field, " and ".join(cond)))[0][0]

		# if bal is None, return 0
		return flt(bal)

@frappe.whitelist()
def item_end_of_life(item_code):
	from erpnext.stock.doctype.item.item import validate_end_of_life
	validate_end_of_life(item_code)

def validate_after_amend(self, method):
	if self.amended_from and not self.alasan_amend:
		frappe.throw(title='Missing Fields',msg='Alasan Amend field is required')