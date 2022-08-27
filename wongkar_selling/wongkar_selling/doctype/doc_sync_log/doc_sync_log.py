# Copyright (c) 2022, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from wongkar_selling.wongkar_selling.frappeclient import FrappeClient
import pandas as pd
from wongkar_selling.custom_method import repair_gl_entry

from datetime import date
from frappe.utils import flt, rounded, add_months,add_days, nowdate, getdate
import time
import datetime

#wongkar
class DocSyncLog(Document):
	pass
	# def after_insert(self):
	# 	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` """)
	# 	if len(cek_apakah_tujuan) > 0:
	# 		sync_baru = json.loads(self.data)
	# 		sync_baru["no_sync_asal"] = self.reference_name
	# 		doc_sync_baru = frappe.get_doc(sync_baru)
	# 		doc_sync_baru.__islocal = 1
	# 		doc_sync_baru.flags.name_set = 1
	# 		print(doc_sync_baru,'dssads')
	# 		doc_sync_baru.flags.ignore_permissions=True
	# 		doc_sync_baru.save()

@frappe.whitelist()
def after_insert_doc(self,method):
	today = date.today()
	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` """)
	if len(cek_apakah_tujuan) > 0:
		sync_baru = json.loads(self.data)
		sync_baru["no_sync_asal"] = self.reference_name
		doc_sync_baru = frappe.get_doc(sync_baru)
		if doc_sync_baru.doctype in ['Purchase Receipt','Purchase Invoice','Delivery Note','Sales Invoice','Sales Invoice Penjualan Motor','Stock Entry','Stock Reconciliation','POS Invoice']:
			if doc_sync_baru.posting_date != today:
				doc_sync_baru.set_posting_time = 1
		doc_sync_baru.__islocal = 1
		doc_sync_baru.flags.name_set = 1
		print(doc_sync_baru,'dssads')
		doc_sync_baru.flags.ignore_permissions=True
		doc_sync_baru.submit()
		repair_gl_entry(sync_baru['doctype'],sync_baru['name'])
		

			# docu_tujuan = frappe.db.sql("""SELECT * from `tab"""+self.reference_doctype+"""` where no_sync_asal='"""+self.reference_name+"""' """,as_dict=1)
			# if docu_tujuan:
			# 	frappe.msgprint("masuk docu_tujuan")
			# 	frappe.db.sql("""UPDATE `tab"""+self.reference_doctype+"""` SET name='"""+self.reference_name+"""' where no_sync_asal='"""+self.reference_name+"""' """)
			# 	#SINV	
			# 	if self.reference_doctype == 'Sales Invoice':
			# 		table_items = frappe.db.sql("""SELECT * from `tabSales Invoice Item` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_pricing_rules = frappe.db.sql("""SELECT * from `tabPricing Rule Detail` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_packed_items = frappe.db.sql("""SELECT * from `tabPacked Item` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_timesheets = frappe.db.sql("""SELECT * from `tabSales Invoice Timesheet` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_taxes = frappe.db.sql("""SELECT * from `tabSales Taxes and Charges` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_advances = frappe.db.sql("""SELECT * from `tabSales Invoice Advance` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_payment_schedule = frappe.db.sql("""SELECT * from `tabPayment Schedule` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_payment = frappe.db.sql("""SELECT * from `tabSales Invoice Payment` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
			# 		table_sales_team = frappe.db.sql("""SELECT * from `tabSales Team` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					
			# 		if table_items:
			# 			frappe.db.sql("""UPDATE `tabSales Invoice Item` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_pricing_rules:
			# 			frappe.db.sql("""UPDATE `tabPricing Rule Detail` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_packed_items:
			# 			frappe.db.sql("""UPDATE `tabPacked Item` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_timesheets:
			# 			frappe.db.sql("""UPDATE `tabSales Invoice Timesheet` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_taxes:
			# 			frappe.db.sql("""UPDATE `tabSales Taxes and Charges` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_advances:
			# 			frappe.db.sql("""UPDATE `tabSales Invoice Advance` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_payment_schedule:
			# 			frappe.db.sql("""UPDATE `tabPayment Schedule` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_payment:
			# 			frappe.db.sql("""UPDATE `tabSales Invoice Payment` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			# 		if table_sales_team:
			# 			frappe.db.sql("""UPDATE `tabSales Team` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					
					
@frappe.whitelist()
def after_submit_sync(self,method):
	# pass
	# membuat Log ketika SO tersubmit
	cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` """)
	# frappe.msgprint(str(cek_apakah_sumber)+"tes123")
	if len(cek_apakah_sumber) > 0:
		sync_log = frappe.new_doc("Doc Sync Log")
		sync_log.reference_doctype = self.doctype
		sync_log.reference_name = self.name
		sync_log.data = frappe.as_json(self)
		sync_log.save()

@frappe.whitelist()
def debug_sync_log(name):
	today = date.today()
	sync_log = frappe.get_doc("Doc Sync Log",name)
	sync_baru = json.loads(sync_log.data)
	sync_baru["no_sync_asal"] = sync_log.reference_name
	doc_sync_baru = frappe.get_doc(sync_baru)
	if doc_sync_baru.doctype in ['Purchase Receipt','Purchase Invoice','Delivery Note','Sales Invoice','Sales Invoice Penjualan Motor','Stock Entry','Stock Reconciliation','POS Invoice']:
		if doc_sync_baru.posting_date != today:
			doc_sync_baru.set_posting_time = 1
		
	doc_sync_baru.__islocal = 1
	doc_sync_baru.flags.name_set = 1
	print(doc_sync_baru,'dssads')
	doc_sync_baru.flags.ignore_permissions=True
	doc_sync_baru.submit()
	repair_gl_entry(sync_baru['doctype'],sync_baru['name'])

# @frappe.whitelist()
# def debug_sync_log_2(name):
# 	sync_log = frappe.get_doc("Doc Sync Log",name)
# 	sync_baru = json.loads(sync_log.data)
# 	sync_baru["no_sync_asal"] = sync_log.reference_name
# 	sync_baru["amended_from"] = ""
# 	doc_sync_baru = frappe.get_doc(sync_baru)
# 	doc_sync_baru.__islocal = 1
# 	doc_sync_baru.flags.name_set = 1
# 	print(doc_sync_baru,'dssads')
# 	doc_sync_baru.flags.ignore_permissions=True
# 	doc_sync_baru.submit()


@frappe.whitelist()
def benerin_data():
	# /home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/wongkar_selling/doctype/doc_sync_log
	# wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.benerin_data
	col = ["Type","Name"]
	data = pd.read_excel (r'/home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/wongkar_selling/doctype/doc_sync_log/template_sync_wongkar.xls') 
	df = pd.DataFrame(data, columns= col)
	
	# print(str(df[col[0]][0]))
	for idx in range(len(df)):
		print(df[col[1]][idx])
		if frappe.db.exists(df[col[0]][idx],df[col[1]][idx]):
			data = frappe.get_doc(df[col[0]][idx], df[col[1]][idx])
			sync_log = frappe.new_doc("Doc Sync Log")
			sync_log.reference_doctype = data.doctype
			sync_log.reference_name = data.name
			sync_log.data = frappe.as_json(data)
			sync_log.save()
			

	print("Sudah selesai !")

@frappe.whitelist()
def hapus_data():
	col = ["Type","Name"]
	data = pd.read_excel (r'/home/frappe/frappe-bench/apps/wongkar_selling/wongkar_selling/wongkar_selling/doctype/doc_sync_log/') 
	df = pd.DataFrame(data, columns= col)
	
	# print(str(df[col[0]][0]))
	for idx in range(len(df)):
		print(df[col[1]][idx])
		if frappe.db.exists(df[col[0]][idx],df[col[1]][idx]):
			data = frappe.get_doc(df[col[0]][idx], df[col[1]][idx])
			if data.docstatus == 0:
				data.delete()
			

	frappe.msgprint("Sudah selesai !")