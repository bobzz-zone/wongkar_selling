# -*- coding: utf-8 -*-
# Copyright (c) 2022, w and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from wongkar_selling.wongkar_selling.frappeclient import FrappeClient
from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
from frappe.utils import cint, cstr, formatdate, flt, getdate, nowdate, get_link_to_form
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from erpnext.accounts.general_ledger import make_gl_entries, merge_similar_entries, make_reverse_gl_entries

@frappe.whitelist()
def after_submit_sync(self,method):
	# pass
	# membuat Log ketika SO tersubmit
	cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` """)
	# frappe.msgprint(str(cek_apakah_sumber)+"tes123")
	if len(cek_apakah_sumber) > 0:
		sync_log = frappe.new_doc("Sync Log")
		sync_log.reference_doctype = self.doctype
		sync_log.reference_name = self.name
		sync_log.data = frappe.as_json(self)
		sync_log.save()
		
# untuk generate dari SO log ketika gagal 
# bench --site erp13.crativate.com execute wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.debug_sync_log
@frappe.whitelist()
def debug_sync_log(name):
	pass
	# sync_log = frappe.get_doc("Sync Log",name)
	# sync_baru = json.loads(sync_log.data)
	# # bisa ubah2 detil di sini
	# sync_baru["name"] = name
	# sync_baru["docstatus"] = 0
	# sync_baru["__islocal"] = 1
	# sync_baru["letter_head"] = ""
	# doc_sync_baru = frappe.get_doc(sync_baru)
	# doc_sync_baru.save()

@frappe.whitelist()
def debug_sync_log_by_number(number):
	pass
	# sync_log = frappe.get_doc("Sync Log",number)
	# sync_baru = json.loads(sync_log.data)
	# # bisa ubah2 detil di sini
	# sync_baru["name"] = number
	# sync_baru["docstatus"] = 0
	# sync_baru["__islocal"] = 1
	# sync_baru["letter_head"] = ""
	# doc_sync_baru = frappe.get_doc(sync_baru)
	# doc_sync_baru.save()

@frappe.whitelist()
def validate_method_sync_log_p_chandra(self,method):
	web_tujuan = "https://hondatax.digitalasiasolusindo.com/"
	username = "Administrator"
	server_pajak = [frappe._dict({
			# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
			'password':"admin",
			'username':username,
			'web_tujuan':web_tujuan
		})]
	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
	frappe.msgprint("tes12345wongkartes123p_chandra")
	name = self.reference_name
	frappe.msgprint(name+"name123")
	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` """)
	if len(cek_apakah_tujuan) > 0:
		frappe.msgprint("tes1234")
		sync_baru = json.loads(self.data)
		# bisa ubah2 detil di sini
		# sync_baru["docstatus"] = 0
		# sync_baru["__islocal"] = 1
		# sync_baru["letter_head"] = ""
		# doc_sync_baru = frappe.get_doc(sync_baru)
		# doc_sync_baru.save()
		# clientroot.insert(sync_baru)

@frappe.whitelist()
def validate_method_sync_log(self,method):
	# frappe.msgprint("tes12345wongkartes123")
	name = self.reference_name
	# frappe.msgprint(name+"name123")
	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` """)
	if len(cek_apakah_tujuan) > 0:
		frappe.msgprint("tes1234")
		sync_baru = json.loads(self.data)
		# bisa ubah2 detil di sini
		if sync_baru['tipe'] == "Non Real":
			# sync_baru["name"] = ""
			sync_baru["docstatus"] = 0
			sync_baru["__islocal"] = 1
			# sync_baru["letter_head"] = ""
			sync_baru["no_sync_sumber"] = self.reference_name
			doc_sync_baru = frappe.get_doc(sync_baru)
			if self.reference_doctype == 'Purchase Invoice':
				sync_baru["update_stock"] = 1
				for i in sync_baru['items']:
					if 'purchase_order' in i:
						i.pop("purchase_order")
					if 'po_detail' in i:
						i.pop("po_detail")
					if 'pr_detail' in i:
						i.pop("pr_detail")
					if 'purchase_receipt' in i:
						i.pop("purchase_receipt")
			
			# doc_sync_baru.flags.ignore_permission=True
			# doc_sync_baru.insert()
			doc_sync_baru.save()

			docu_tujuan = frappe.db.sql("""SELECT * from `tab"""+self.reference_doctype+"""` where no_sync_sumber='"""+self.reference_name+"""' """,as_dict=1)
			if docu_tujuan:
				frappe.msgprint("masuk docu_tujuan")
				frappe.db.sql("""UPDATE `tab"""+self.reference_doctype+"""` SET name='"""+self.reference_name+"""' where no_sync_sumber='"""+self.reference_name+"""' """)
				#PINV	
				if self.reference_doctype == 'Purchase Invoice':
					table_items = frappe.db.sql("""SELECT * from `tabPurchase Invoice Item` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_pricing_rules = frappe.db.sql("""SELECT * from `tabPricing Rule Detail` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_supplied_items = frappe.db.sql("""SELECT * from `tabPurchase Receipt Item Supplied` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_taxes = frappe.db.sql("""SELECT * from `tabPurchase Taxes and Charges` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_advances = frappe.db.sql("""SELECT * from `tabPurchase Invoice Advance` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_payment_schedule = frappe.db.sql("""SELECT * from `tabPayment Schedule` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					
					if table_items:
						frappe.db.sql("""UPDATE `tabPurchase Invoice Item` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_pricing_rules:
						frappe.db.sql("""UPDATE `tabPricing Rule Detail` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_supplied_items:
						frappe.db.sql("""UPDATE `tabPurchase Receipt Item Supplied` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_taxes:
						frappe.db.sql("""UPDATE `tabPurchase Taxes and Charges` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_advances:
						frappe.db.sql("""UPDATE `tabPurchase Invoice Advance` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_payment_schedule:
						frappe.db.sql("""UPDATE `tabPayment Schedule` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)

				#JE
				if self.reference_doctype == 'Journal Entry':
					table_accounts = frappe.db.sql("""SELECT * from `tabJournal Entry Account` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					if table_accounts:
						frappe.db.sql("""UPDATE `tabJournal Entry Account` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)

			# frappe.db.sql("""UPDATE `tabPurchase Invoice` SET name='"""+self.reference_name+"""' where no_sync_sumber='"""+self.reference_name+"""' """)
			# doc = frappe.get_doc(self.reference_doctype,{'no_sync_sumber':self.reference_name})
			# doc.name = self.reference_name
			# doc.db_update()
		else:
			# sync_baru["name"] = ""
			sync_baru["docstatus"] = 1
			sync_baru["__islocal"] = 1
			# sync_baru["letter_head"] = ""
			sync_baru["no_sync_sumber"] = self.reference_name
			if self.reference_doctype == 'Purchase Invoice':
				sync_baru["update_stock"] = 1
				for i in sync_baru['items']:
					if 'purchase_order' in i:
						i.pop("purchase_order")
					if 'po_detail' in i:
						i.pop("po_detail")
					if 'pr_detail' in i:
						i.pop("pr_detail")
					if 'purchase_receipt' in i:
						i.pop("purchase_receipt")
					# if i['purchase_receipt']:
					# 	i['purchase_receipt'] = ''
			doc_sync_baru = frappe.get_doc(sync_baru)
			# doc_sync_baru.flags.ignore_permission=True
			# doc_sync_baru.insert()
			doc_sync_baru.save()
			# docu_tujuan = frappe.db.sql("""SELECT * from `tabPurchase Invoice` where no_sync_sumber='"""+self.reference_name+"""' """,as_dict=1)
			# frappe.db.sql("""UPDATE `tabPurchase Invoice` SET name='"""+self.reference_name+"""' where no_sync_sumber='"""+self.reference_name+"""' """)
			# frappe.db.sql("""UPDATE `tabPurchase Invoice Item` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
			
			docu_tujuan = frappe.db.sql("""SELECT * from `tab"""+self.reference_doctype+"""` where no_sync_sumber='"""+self.reference_name+"""' """,as_dict=1)
			if docu_tujuan:
				frappe.msgprint("masuk docu_tujuan")
				frappe.db.sql("""UPDATE `tab"""+self.reference_doctype+"""` SET name='"""+self.reference_name+"""' where no_sync_sumber='"""+self.reference_name+"""' """)
				#PINV	
				if self.reference_doctype == 'Purchase Invoice':
					table_items = frappe.db.sql("""SELECT * from `tabPurchase Invoice Item` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_pricing_rules = frappe.db.sql("""SELECT * from `tabPricing Rule Detail` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_supplied_items = frappe.db.sql("""SELECT * from `tabPurchase Receipt Item Supplied` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_taxes = frappe.db.sql("""SELECT * from `tabPurchase Taxes and Charges` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_advances = frappe.db.sql("""SELECT * from `tabPurchase Invoice Advance` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					table_payment_schedule = frappe.db.sql("""SELECT * from `tabPayment Schedule` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					
					if table_items:
						frappe.db.sql("""UPDATE `tabPurchase Invoice Item` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_pricing_rules:
						frappe.db.sql("""UPDATE `tabPricing Rule Detail` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_supplied_items:
						frappe.db.sql("""UPDATE `tabPurchase Receipt Item Supplied` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_taxes:
						frappe.db.sql("""UPDATE `tabPurchase Taxes and Charges` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_advances:
						frappe.db.sql("""UPDATE `tabPurchase Invoice Advance` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)
					if table_payment_schedule:
						frappe.db.sql("""UPDATE `tabPayment Schedule` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)

				#JE
				if self.reference_doctype == 'Journal Entry':
					table_accounts = frappe.db.sql("""SELECT * from `tabJournal Entry Account` where parent='"""+docu_tujuan[0]['name']+"""' """,as_dict=1)
					if table_accounts:
						frappe.db.sql("""UPDATE `tabJournal Entry Account` SET parent='"""+self.reference_name+"""' where parent='"""+docu_tujuan[0]['name']+"""' """)


			# frappe.db.sql("""UPDATE `tabPurchase Invoice` SET name='"""+self.reference_name+"""' where no_sync_sumber='"""+self.reference_name+"""' """)
			# doc = frappe.get_doc(self.reference_doctype,{'no_sync_sumber':self.reference_name})
			# doc.name = self.reference_name
			# doc.db_update()
			# tujuan

@frappe.whitelist()
def validate_method_sync_log2(self,method):
	frappe.msgprint("masuk validate_method_sync_log2")
	# web_tujuan = "http://erp13.crativate.com/"
	# username = "Administrator"
	# server_pajak = [frappe._dict({
	# 		# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
	# 		'password':"admin",
	# 		'username':username,
	# 		'web_tujuan':web_tujuan
	# 	})]
	# clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
	# cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` """)
	# docu_tujuan = clientroot.get_value(self.reference_doctype, ["name"], {"no_sync_sumber":self.reference_name})
	
	# if len(cek_apakah_tujuan) > 0:
	# 	frappe.msgprint("tes1234")
	# 	sync_baru = json.loads(self.data)
	# 	# bisa ubah2 detil di sini
	# 	if sync_baru['tipe'] == "Non Real":
	# 		# sync_baru.update({ "document_name" : self.reference_name })
	# 		# sync_baru["name"] = self.reference_name
	# 		sync_baru["docstatus"] = 0
	# 		sync_baru["__islocal"] = 1
	# 		sync_baru["letter_head"] = ""
	# 		sync_baru["no_sync_sumber"] = self.reference_name
	# 		clientroot.insert(sync_baru)
	# 		# doc_sync_baru = frappe.get_doc(sync_baru)
	# 		# doc_sync_baru.save()
	# 	else:
	# 		# sync_baru.update({ "document_name" : self.reference_name })
	# 		# sync_baru["name"] = self.reference_name
	# 		sync_baru["docstatus"] = 1
	# 		sync_baru["__islocal"] = 1
	# 		sync_baru["letter_head"] = ""
	# 		sync_baru["no_sync_sumber"] = self.reference_name
	# 		clientroot.insert(sync_baru)
	# 		# doc_sync_baru = frappe.get_doc(sync_baru)
	# 		# doc_sync_baru.save()

	# # tujuan
	# docu_tujuan = clientroot.get_value(self.reference_doctype, ["name"], {"no_sync_sumber":self.reference_name})
	# if docu_tujuan:
	# 	frappe.msgprint("masuk docu_tujuan")
	# 	sync_baru["name"] = self.reference_name
	# 	clientroot.update(sync_baru)
	
			

@frappe.whitelist()
def autoname_document(self,method):
	pass

# bench --site erp13.crativate.com execute wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.coba_update_name
@frappe.whitelist()
def coba_update_name():
	name = 'ACC-PINV-2022-00029'
	frappe.db.sql("""UPDATE `tabPurchase Invoice` SET name='"""+name+"""' where no_sync_sumber='"""+name+"""' """)
	# frappe.db.commit()
	# doc = frappe.get_doc("Purchase Invoice",{'no_sync_sumber':name})
	# doc.name = name
	# # doc.save()
	# doc.db_update()

# @frappe.whitelist()
def cencel_sumber(self,method):
	# pass
	url_sumber = frappe.utils.get_url()
	# frappe.throw(url_sumber+"url_sumber")
	cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_sumber+"""' """)
	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://honda2.digitalasiasolusindo.com' """)
	# frappe.msgprint(str(len(cek_apakah_tujuan))+"tes123")
	web_tujuan = "https://honda2.digitalasiasolusindo.com/"
	username = "Administrator"
	server_pajak = [frappe._dict({
			# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
			'password':"admin",
			'username':username,
			'web_tujuan':web_tujuan
		})]
	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
	if len(cek_apakah_tujuan) > 0: 
		# frappe.msgprint(str(cek_apakah_tujuan)+"tes123")

		# clientroot = FrappeClient('http://dev13.crativate.com/','Administrator','admin')
		clientdoc = clientroot.get_doc(self.doctype, self.no_sync_sumber)
		# frappe.msgprint(str(clientdoc['name'])+"clientdoc")
		clientroot.cancel(self.doctype,clientdoc['name'])
		# if self.no_sync_sumber:
		# 	frappe.msgprint(url_sumber+"url_sumber")
		# 	doc = frappe.get_doc(self.doctype,{'name':self.no_sync_sumber})
		# 	doc.cancel()

def delete_sumber(self,method):
	# pass
	url_sumber = frappe.utils.get_url()
	# frappe.throw(url_sumber+"url_sumber")
	cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_sumber+"""' """)
	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://honda2.digitalasiasolusindo.com' """)
	# frappe.msgprint(str(len(cek_apakah_tujuan))+"tes123")
	web_tujuan = "https://honda2.digitalasiasolusindo.com/"
	username = "Administrator"
	server_pajak = [frappe._dict({
			# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
			'password':"admin",
			'username':username,
			'web_tujuan':web_tujuan
		})]
	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
	if len(cek_apakah_tujuan) > 0: 
		# frappe.msgprint(str(cek_apakah_tujuan)+"tes123")

		# clientroot = FrappeClient('http://dev13.crativate.com/','Administrator','admin')
		clientdoc = clientroot.get_doc(self.doctype, self.no_sync_sumber)
		# frappe.msgprint(str(clientdoc['name'])+"clientdoc")
		clientroot.delete(self.doctype,clientdoc['name'])

	# lama
	# url_sumber = frappe.utils.get_url()
	# # frappe.throw(url_sumber+"url_sumber")
	# cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_sumber+"""' """)
	# cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='http://dev13.crativate.com' """)
	# frappe.msgprint(str(len(cek_apakah_tujuan))+"tes123")
	# web_tujuan = "http://dev13.crativate.com/"
	# username = "Administrator"
	# server_pajak = [frappe._dict({
	# 		# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
	# 		'password':"admin",
	# 		'username':username,
	# 		'web_tujuan':web_tujuan
	# 	})]
	# clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
	# if len(cek_apakah_tujuan) > 0: 
	# 	frappe.msgprint(str(cek_apakah_tujuan)+"tes123")

	# 	# clientroot = FrappeClient('http://dev13.crativate.com/','Administrator','admin')
	# 	sync_log_name = clientroot.get_list('Sync Log',filters={'reference_name': self.no_sync_sumber},fields=['name'])
	# 	frappe.msgprint(str(sync_log_name)+"sync_log_name")
	# 	for i in sync_log_name:
	# 		syncdoc = clientroot.get_doc("Sync Log", i['name'])
	# 		syncdoc.delete("Sync Log",syncdoc['name'])

	# 	clientdoc = clientroot.get_doc(self.doctype, self.no_sync_sumber)
	# 	frappe.msgprint(str(clientdoc['name'])+"clientdoc")
	# 	clientroot.delete(self.doctype,clientdoc['name'])
	# 	# if self.no_sync_sumber:
	# 	# 	frappe.msgprint(url_sumber+"url_sumber")
	# 	# 	doc = frappe.get_doc(self.doctype,{'name':self.no_sync_sumber})
	# 	# 	doc.cancel()
		
def cencel_sumber_asli(self,method):
	# pass
	# honda pjk
	consumer = frappe.db.sql("""SELECT * FROM `tabEvent Consumer` """,as_dict=1)
	if len(consumer)>0:
		#custom bobby , kalo ada consumer lakukan sync
		#decide credential
		username = "Administrator"
		if consumer[0].name=="https://hondapjk.digitalasiasolusindo.com":
			return
			#skip sementara kegiatan di honda
			server_pajak = [frappe._dict({
				'password':"admin",
				'username':username,
				'web_tujuan':consumer[0].name
			})]
		elif consumer[0].name=="https://wongkarpjk.digitalasiasolusindo.com":
			server_pajak =[frappe._dict({
				'password':"Rahasiakit@",
				'username':username,
				'web_tujuan':consumer[0].name
			})]
		elif consumer[0].name=="https://wongkar2pjk.digitalasiasolusindo.com":
			server_pajak = [frappe._dict({
				'password':"Rahasiakit@",
				'username':username,
				'web_tujuan':consumer[0].name
			})]
		clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
		clientdoc = clientroot.get_doc(self.doctype, self.name)
		if not clientdoc:
			pass
		elif clientdoc['docstatus'] == 1:
			clientroot.cancel(self.doctype,clientdoc['name'])
	
# def cencel_sumber_asli(self,method):
# 	# pass
# 	# honda pjk
# 	# frappe.throw("tes")
# 	url_sumber = "https://hondapjk.digitalasiasolusindo.com"
# 	cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_sumber+"""' """)
# 	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://honda.digitalasiasolusindo.com' """)
# 	web_tujuan = "https://hondapjk.digitalasiasolusindo.com/"
# 	username = "Administrator"
# 	server_pajak = [frappe._dict({
# 		'password':"admin",
# 		'username':username,
# 		'web_tujuan':web_tujuan
# 	})]
	
# 	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
# 	if len(cek_apakah_sumber) > 0: 
# 		clientdoc = clientroot.get_doc(self.doctype, self.name)
# 		if clientdoc['docstatus'] == 1:
# 			clientroot.cancel(self.doctype,clientdoc['name'])
	
# 	# wongkar_pjk
# 	url_tujuan_wongkar_pjk = "https://wongkarpjk.digitalasiasolusindo.com"
# 	cek_apakah_sumber_wongkar_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_tujuan_wongkar_pjk+"""' """)
# 	cek_apakah_tujuan_wongkar_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://wongkar.digitalasiasolusindo.com' """)
# 	web_tujuan_wongkar_pjk = "https://wongkarpjk.digitalasiasolusindo.com/"
# 	username_wongkar_pjk = "Administrator"
# 	server_pajak_wongkar_pjk = [frappe._dict({
# 			'password':"Rahasiakit@",
# 			'username':username_wongkar_pjk,
# 			'web_tujuan':web_tujuan_wongkar_pjk
# 		})]
# 	clientroot_wongkar_pjk = FrappeClient(server_pajak_wongkar_pjk[0].web_tujuan,server_pajak_wongkar_pjk[0].username,server_pajak_wongkar_pjk[0].password)
# 	if len(cek_apakah_sumber_wongkar_pjk) > 0: 
# 		clientdoc_wongkar_pjk = clientroot_wongkar_pjk.get_doc(self.doctype, self.name)
# 		# frappe.throw(str(clientdoc['name']))
# 		if clientdoc_wongkar_pjk['docstatus'] == 1:
# 			clientroot_wongkar_pjk.cancel(self.doctype,clientdoc_wongkar_pjk['name'])
# 	#wongkar pajak2
# 	url_tujuan_wongkar2_pjk = "https://wongkar2pjk.digitalasiasolusindo.com"
# 	cek_apakah_sumber_wongkar2_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_tujuan_wongkar2_pjk+"""' """)
# 	cek_apakah_tujuan_wongkar2_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://wongkar2.digitalasiasolusindo.com' """)
# 	web_tujuan_wongkar2_pjk = "https://wongkar2pjk.digitalasiasolusindo.com/"
# 	username_wongkar2_pjk = "Administrator"
# 	server_pajak_wongkar2_pjk = [frappe._dict({
# 			'password':"Rahasiakit@",
# 			'username':username_wongkar2_pjk,
# 			'web_tujuan':web_tujuan_wongkar2_pjk
# 		})]
# 	clientroot_wongkar2_pjk = FrappeClient(server_pajak_wongkar2_pjk[0].web_tujuan,server_pajak_wongkar2_pjk[0].username,server_pajak_wongkar2_pjk[0].password)
# 	if len(cek_apakah_sumber_wongkar2_pjk) > 0: 
# 		clientdoc_wongkar2_pjk = clientroot_wongkar2_pjk.get_doc(self.doctype, self.name)
# 		# frappe.throw(str(clientdoc['name']))
# 		if clientdoc_wongkar2_pjk['docstatus'] == 1:
# 			clientroot_wongkar2_pjk.cancel(self.doctype,clientdoc_wongkar2_pjk['name'])
	
# def delete_sumber_asli(self,method):
# 	# pass
# 	# honda pjk
# 	# frappe.throw("delete")
# 	url_tujuan = "https://hondapjk.digitalasiasolusindo.com"
# 	cek_apakah_sumber = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_tujuan+"""' """)
# 	cek_apakah_tujuan = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://honda.digitalasiasolusindo.com' """)
# 	web_tujuan = "https://hondapjk.digitalasiasolusindo.com/"
# 	username = "Administrator"
# 	server_pajak = [frappe._dict({
# 			'password':"admin",
# 			'username':username,
# 			'web_tujuan':web_tujuan
# 		})]
# 	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
# 	if len(cek_apakah_sumber) > 0: 
# 		clientdoc = clientroot.get_doc(self.doctype, self.name)
# 		# frappe.throw(str(clientdoc['name']))
# 		clientroot.delete(self.doctype,self.name)

# 	# wongkar_pjk
# 	url_tujuan_wongkar_pjk = "https://wongkarpjk.digitalasiasolusindo.com"
# 	cek_apakah_sumber_wongkar_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_tujuan_wongkar_pjk+"""' """)
# 	cek_apakah_tujuan_wongkar_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://wongkar.digitalasiasolusindo.com' """)
# 	web_tujuan_wongkar_pjk = "https://wongkarpjk.digitalasiasolusindo.com/"
# 	username_wongkar_pjk = "Administrator"
# 	server_pajak_wongkar_pjk = [frappe._dict({
# 			'password':"Rahasiakit@",
# 			'username':username_wongkar_pjk,
# 			'web_tujuan':web_tujuan_wongkar_pjk
# 		})]
# 	clientroot_wongkar_pjk = FrappeClient(server_pajak_wongkar_pjk[0].web_tujuan,server_pajak_wongkar_pjk[0].username,server_pajak_wongkar_pjk[0].password)
# 	if len(cek_apakah_sumber_wongkar_pjk) > 0: 
# 		clientdoc_wongkar_pjk = clientroot_wongkar_pjk.get_doc(self.doctype, self.name)
# 		# frappe.throw(str(clientdoc['name']))
# 		clientroot_wongkar_pjk.delete(self.doctype,self.name)

# 	# _wongkar2_pjk
# 	url_tujuan_wongkar2_pjk = "https://wongkar2pjk.digitalasiasolusindo.com"
# 	cek_apakah_sumber_wongkar2_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Consumer` where name ='"""+url_tujuan_wongkar2_pjk+"""' """)
# 	cek_apakah_tujuan_wongkar2_pjk = frappe.db.sql(""" SELECT * FROM `tabEvent Producer` where name='https://wongkar2.digitalasiasolusindo.com' """)
# 	web_tujuan_wongkar2_pjk = "https://wongkar2pjk.digitalasiasolusindo.com/"
# 	username_wongkar2_pjk = "Administrator"
# 	server_pajak_wongkar2_pjk = [frappe._dict({
# 			'password':"Rahasiakit@",
# 			'username':username_wongkar2_pjk,
# 			'web_tujuan':web_tujuan_wongkar2_pjk
# 		})]
# 	clientroot_wongkar2_pjk = FrappeClient(server_pajak_wongkar2_pjk[0].web_tujuan,server_pajak_wongkar2_pjk[0].username,server_pajak_wongkar2_pjk[0].password)
# 	if len(cek_apakah_sumber_wongkar2_pjk) > 0: 
# 		clientdoc_wongkar2_pjk = clientroot_wongkar2_pjk.get_doc(self.doctype, self.name)
# 		# frappe.throw(str(clientdoc['name']))
# 		clientroot_wongkar2_pjk.delete(self.doctype,self.name)
def delete_sumber_asli(self,method):
	# pass
	# honda pjk
	consumer = frappe.db.sql("""SELECT * FROM `tabEvent Consumer` """,as_dict=1)
	if len(consumer)>0:
		#custom bobby , kalo ada consumer lakukan sync
		#decide credential
		username = "Administrator"
		if consumer[0].name=="https://hondapjk.digitalasiasolusindo.com":
			return
			#skip sementara kegiatan di honda
			server_pajak = [frappe._dict({
				'password':"admin",
				'username':username,
				'web_tujuan':consumer[0].name
			})]
		else:
# consumer[0].name=="https://wongkarpjk.digitalasiasolusindo.com":
			server_pajak =[frappe._dict({
				'password':"Rahasiakit@",
				'username':username,
				'web_tujuan':consumer[0].name
			})]
			
		clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
		clientdoc = clientroot.get_doc(self.doctype, self.name)
		if clientdoc['docstatus'] != 1:
			clientroot.delete(self.doctype,clientdoc['name'])

def test_update(self,method):
	# frappe.msgprint("test")
	# update_outstanding_amt(self.credit_to, "Supplier", self.supplier,self.doctype, self.return_against if cint(self.is_return) and self.return_against else self.name)
	frappe.db.sql("""DELETE FROM `tabGL Entry` where voucher_no = "{}" """.format(self.name))

	frappe.db.commit()
	self.calculate_taxes_and_totals()
	self.make_gl_entries()

def test_update_je(self,method):
	# frappe.msgprint("test_update_je")
	# update_outstanding_amt(self.credit_to, "Supplier", self.supplier,self.doctype, self.return_against if cint(self.is_return) and self.return_against else self.name)
	frappe.db.sql("""DELETE FROM `tabGL Entry` where voucher_no = "{}" """.format(self.name))

	frappe.db.commit()
	# self.calculate_taxes_and_totals()
	self.make_gl_entries()

def test_update_ec(self,method):
	frappe.msgprint("test_update_ec")
	# update_outstanding_amt(self.credit_to, "Supplier", self.supplier,self.doctype, self.return_against if cint(self.is_return) and self.return_against else self.name)
	frappe.db.sql("""DELETE FROM `tabGL Entry` where voucher_no = "{}" """.format(self.name))

	frappe.db.commit()
	# self.calculate_taxes_and_totals()
	self.make_gl_entries()
