# -*- coding: utf-8 -*-
# Copyright (c) 2015, erpx and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from wongkar_selling.wongkar_selling.frappeclient import FrappeClient
import json
import os
import requests
import subprocess
from frappe.utils.background_jobs import enqueue
from frappe.utils.password import check_password,get_decrypted_password
from frappe.utils import get_site_name

# create sync settings doctype single
class Sync(Document):
	pass


@frappe.whitelist()
def sync_master(doc):
	web_tujuan = "https://honda2.digitalasiasolusindo.com/"
	username = "Administrator"
	server_pajak = [frappe._dict({
			# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
			'password':"admin",
			'username':username,
			'web_tujuan':web_tujuan
		})]
	sync_on = "Items"
	warehouse_tujuan = "Stores - IFMI"

	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)

	# doc = frappe.get_doc(doc.doctype, doc.name)

	kolom_parent = frappe.db.sql(""" SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='tab{}' """.format(doc.doctype))

	kolom_child = frappe.db.sql(""" SELECT td.fieldname, td.options
		FROM `tabDocField` td
		WHERE parent = "{}" AND fieldtype = "Table"
		GROUP BY td.`fieldname`
		ORDER BY OPTIONS;
		 """.format(doc.doctype))

	kolom_table = frappe.db.sql("""SELECT td.fieldname, ic.COLUMN_NAME, ic.DATA_TYPE  FROM `tabDocField` td
		JOIN INFORMATION_SCHEMA.COLUMNS ic ON CONCAT("tab",td.`options`) = ic.`TABLE_NAME`
		WHERE parent = "{}" AND fieldtype = "Table"
		ORDER BY OPTIONS """.format(doc.doctype))


	pr_doc = {}
	for rowkolom in kolom_parent:

		if str(rowkolom[0]) != "docstatus":
			if doc.doctype in ("Customer","Supplier") and (str(rowkolom[0]) == "address_html" 
				or str(rowkolom[0]) == "contact_html" or str(rowkolom[0]) == "default_expedition"):
				continue

			if str(doc.get(str(rowkolom[0]))) != "None" :
				if str(rowkolom[1]) == "date" or str(rowkolom[1]) == "datetime" or str(rowkolom[1]) == "time" :
					pr_doc.update({ (rowkolom[0]) : str(doc.get(str(rowkolom[0]))) })
				else:
					pr_doc.update({ (rowkolom[0]) : (doc.get(str(rowkolom[0]))) })

	for rowkolom in kolom_child:
		if doc.get(rowkolom[0]):
			pr_doc_items = []
			for rowtable in doc.get(rowkolom[0]):
				pr_doc_child = {}
				for rowbaris in kolom_table:
					if rowbaris[0] == rowkolom[0]:
						if str(rowbaris[1]) != "docstatus" and str(rowbaris[1]) != "name" and str(rowbaris[1]) != "so_detail" \
						and str(rowbaris[1]) != "po_detail"and str(rowbaris[1]) != "purchase_order_item":
							if str(rowtable.get(str(rowbaris[1]))) != "None" :
								if str(rowbaris[2]) == "date" or str(rowbaris[2]) == "datetime" or str(rowbaris[2]) == "time" :
									pr_doc_child.update({ rowbaris[1] : str(rowtable.get(str(rowbaris[1]))) })
								else:
									pr_doc_child.update({ rowbaris[1] : (rowtable.get(str(rowbaris[1]))) })

						if doc.doctype == "Purchase Receipt":
							if rowbaris[1] == "purchase_order":
								pr_doc_child.update({ rowbaris[1] : "" })
							if rowbaris[1] == "billed_amt":
								pr_doc_child.update({ rowbaris[1] : "" })
							if rowbaris[1] == "expense_account":
								pr_doc_child.update({ rowbaris[1] : "HPP, Cost of Good sold - ASV" })
							if rowbaris[1] == "item_tax_template" :
								pr_doc_child.update({ rowbaris[1] : "" })
							if rowbaris[1] == "warehouse":
								pr_doc_child.update({ rowbaris[1] : warehouse_tujuan })

							# if rowbaris[1] == "target_warehouse" :
							# 	if doc.is_return == 1:
							# 		pr_doc_child.update({ rowbaris[1] : warehouse_tujuan })
							# 	else:
							# 		pr_doc_child.update({ rowbaris[1] : "" })
								
						# if doc.doctype == "Sales Invoice":
						if doc.doctype == "Sales Invoice Penjualan Motor":
							# if rowbaris[1] == "tax_status":
							# 	if str(rowtable.get(str(rowbaris[1]))) == "Non Tax":
							# 		continue
							# BUAT PAK ANDY, SALAHNYA DI SINI
							# if rowbaris[1] == "target_warehouse" or rowbaris[1] == "warehouse":
							# 	pr_doc_child.update({ rowbaris[1] : server_pajak[0].warehouse_tujuan })
							# frappe.msgprint(str(rowbaris)+"rowbaris")
							if rowbaris[1] == "warehouse":
								pr_doc_child.update({ rowbaris[1] : warehouse_tujuan })
							if rowbaris[1] == "warehouse":
								pr_doc_child.update({ rowbaris[1] : warehouse_tujuan })

							# if rowbaris[1] == "income_account":
							# 	pr_doc_child.update({ rowbaris[1] : "Sales - ASV" })

							# if rowbaris[1] == "expense_account":
							# 	pr_doc_child.update({ rowbaris[1] : "HPP, Cost of Good sold - ASV" })


								
							if rowbaris[1] == "target_warehouse" :
								if doc.is_return == 1:
									pr_doc_child.update({ rowbaris[1] : warehouse_tujuan })
								else:
									pr_doc_child.update({ rowbaris[1] : "" })
							
							if rowbaris[1] == "item_tax_template" :
								pr_doc_child.update({ rowbaris[1] : "" })

							if rowbaris[1] == "barcode" :
								pr_doc_child.update({ rowbaris[1] : "" })

							if rowbaris[1] in ("sales_order","delivery_note","dn_detail","so_detail","pricing_rule"):
								pr_doc_child.update({ rowbaris[1] : "" })

						if doc.doctype == "Item":
							if rowbaris[1] == "default_warehouse":
								pr_doc_child.update({ rowbaris[1] : warehouse_tujuan })
					
						if rowbaris[1] == "company":
							pr_doc_child.update({ rowbaris[1] : company_tujuan })
					
						# if rowbaris[1] == "cost_center":
						# 	pr_doc_child.update({ rowbaris[1] : "Main - ASV" })

				# print("""{} - {}""".format(doc.doctype,sync_on))
				# if sync_on == "Items"  and (doc.doctype == "Sales Invoice" or doc.doctype == "Purchase Receipt") and pr_doc_child.get("tax_status") == "Non Tax":
				if sync_on == "Items"  and (doc.doctype == "Sales Invoice Penjualan Motor" or doc.doctype == "Purchase Receipt"):
					continue
				else:
					# print("""%s = %s = %s""" % (pr_doc_child.get("tax_status"),pr_doc_child.get("item_code"),pr_doc_child.get("warehouse")))

					# custom for different version 
					# if doc.doctype in ("Sales Invoice","Purchase Receipt"):
					# 	if pr_doc_child.get("barcode"):
					# 		_item = clientroot.get_value("Item", ["name","barcode"], {"sync_sumber_name":pr_doc_child['item_code']})
					# 		if not _item:
					# 			_item = clientroot.get_value("Item", ["name","barcode"], {"item_code":pr_doc_child['item_code']})

					# 		if _item:
					# 			_item_doc = clientroot.get_doc("Item",_item['name'])
					# 			_item_doc['barcode'] = pr_doc_child.get("barcode")
					# 			_item_doc['sync_sumber_name'] = frappe.db.get_value("Item",{"item_code": pr_doc_child['item_code']})
					# 			clientroot.update(_item_doc)

					pr_doc_items.append(pr_doc_child)
			pr_doc.update({ rowkolom[0]: pr_doc_items })


	pr_doc.update({ "doctype": doc.doctype })
	# pr_doc.update({ "sync_sumber_name" : doc.name })
	pr_doc.update({ "document_name" : doc.name })
	
	# docu_tujuan = clientroot.get_value(doc.doctype, ["name"], {"sync_sumber_name":doc.name})
	# if not docu_tujuan:
	# 	docu_tujuan = clientroot.get_value(doc.doctype, ["name"], {"name":doc.name})


	if doc.doctype == "Item":
	# 	if "naming_series" in pr_doc:
	# 		del pr_doc['naming_series']
		pr_doc.update({"item_defaults":""})
		
		# if doc.barcodes:
			# bcode = doc.barcodes[0].barcode
			# print(pr_doc.get("barcodes"))
			# pr_doc.update({"barcodes": ""})
			# pr_doc.update({"barcode": bcode})

	# if doc.doctype == "Sales Invoice" :
	if doc.doctype == "Sales Invoice Penjualan Motor":
		item_code = frappe.get_value("Sales Invoice Penjualan Motor Item",{"parent": doc.name}, "item_code")
		pr_doc.update({"update_stock":0})
		# pr_doc.update({"rss_sales_order":""})
		# pr_doc.update({"selling_price_list":server_pajak[0].selling_price_list})
		pr_doc.update({"posting_date": str(doc.posting_date)})
		pr_doc.update({"posting_time": str(doc.posting_time)})
		pr_doc.update({"due_date": str(doc.due_date)})
		pr_doc.update({"set_posting_time": 1})
		pr_doc.update({"is_pos": 0})
		pr_doc.update({"payments":[]})
		pr_doc.update({"items":[{
				'item_code': item_code
			}
			]})
		
		# pr_doc.update({"customer":"Walk in Customer"})
		# pr_doc.update({"customer_name":"Walk in Customer"})
		pr_doc.update({"customer":"Walk in Customer"})
		pr_doc.update({"customer_name":"Walk in Customer"})
		# pr_doc.update({"title":"Walk in Customer"})
		# if doc.debit_to != "Piutang - ASV":
		# 	pr_doc.update({"debit_to":"Piutang - ASV"})
		
		pr_doc.update({"company": doc.company})
		pr_doc.update({"customer_address":""})
		pr_doc.update({"company_address":""})
		pr_doc.update({"contact_person":""})
		pr_doc.update({"contact_display":""})




		# del pr_doc['base_discount_amount']
		# del pr_doc['discount_amount']
		# del pr_doc['base_grand_total']
		# del pr_doc['grand_total']


		pr_doc.update({"packing":""})
		pr_doc.update({"packing_sales_orders":""})
		pr_doc.update({"rss_sales_person":""})
		# pr_doc.update({"naming_series":server_pajak[0].series_sinv})

		# ignore payment entry table
		if pr_doc['due_date'] < pr_doc['posting_date']:
			pr_doc.update({"due_date": str(doc.posting_date)})
			# pr_doc.update({"payment_schedule":""})

		if "advances" in pr_doc:
			pr_doc.update({"advances":""})

		# add tax
		# if sales_tax_template:
		# 	pr_doc.update({"taxes_and_charges": sales_tax_template})
		# 	taxes = [{"charge_type":stax_charge_type,
		# 			  "account_head":stax_account,
		# 			  "rate":stax_rate,
		# 			  "description":stax_description,
		# 			  "included_in_print_rate": 1}]
		# 	pr_doc.update({"taxes": taxes})

	if doc.doctype == "Purchase Receipt":
		# pr_doc.update({"update_stock":1})
		pr_doc.update({"posting_date": str(doc.posting_date)})
		pr_doc.update({"title": doc.title})
		pr_doc.update({"posting_time": str(doc.posting_time)})
		pr_doc.update({"set_posting_time": 1})
		pr_doc.update({"per_billed": ""})
		
		# if not doc.company:
		pr_doc.update({"company":company_tujuan})

		# add tax
		if purchase_tax_template:
			pr_doc.update({"taxes_and_charges":  purchase_tax_template})
			taxes = [{"charge_type": ptax_charge_type,
					"account_head": ptax_account,
					"rate": ptax_rate,
					"description": ptax_description,
					"add_deduct_tax":  ptax_add_deduct,
					"category": "Total",
					"included_in_print_rate": 1
					}]
			pr_doc.update({"taxes":taxes})

	if doc.doctype == "Contact":
		if doc.phone_nos:

			pr_doc.pop("phone_nos")
		if doc.email_ids:
			
			pr_doc.pop("email_ids")

	if doc.doctype == "Address":
		pr_doc.update({"naming_series":""})

	if doc.doctype == "Customer":
		pr_doc.update({"default_price_list":""})

	if doc.doctype == "Pricing Rule":
		pr_doc.update({"discount_percentage":doc.discount_percentage or 0})
		pr_doc.update({"customer_group":doc.customer_group or ""})


	if doc.doctype == "Item":
		pr_doc.update({"default_bom":""})
		# docu_tujuan = clientroot.get_value(doc.doctype, ["name","naming_series"], {"sync_sumber_name":doc.item_code})
		# if not docu_tujuan:
		# 	docu_tujuan = clientroot.get_value(doc.doctype, ["name","naming_series"], {"item_code":doc.item_code})
	# else:
	# 	if doc.doctype in ["Address","Contact","Terms and Conditions","Brand"]:
	# 		docu_tujuan = clientroot.get_value(doc.doctype, ["name"], {"sync_sumber_name":doc.name})
	# 		if not docu_tujuan:
	# 			docu_tujuan = clientroot.get_value(doc.doctype, ["name"], {"name":doc.name})
	
	# sync proses
	# frappe.msgprint(str(docu_tujuan)+"docu_tujuan")	
	docu_tujuan = clientroot.get_value(doc.doctype, ["name"], {"name":doc.name})		
	if docu_tujuan:
		pr_doc.update({ "name": docu_tujuan['name'] })

		if "naming_series" in pr_doc and "naming_series" in docu_tujuan:
			pr_doc.update({ "naming_series": docu_tujuan['naming_series'] })

		if "modified" in pr_doc:
			del pr_doc['modified']

		if doc.docstatus != 1:
			if doc.doctype == "Item":
				del pr_doc['valuation_rate']
			clientroot.update(pr_doc)

		if doc.doctype == 'Purchase Receipt' and doc.docstatus == 1:
			clientroot.update(pr_doc)

		if doc.doctype == "Sales Invoice":
			clientdoc = clientroot.get_doc(doc.doctype, docu_tujuan['name'])
			if doc.company == "ASOVIC BALI":
				clientdoc.update({"additional_discount_percentage":5})
				clientroot.submit(clientdoc)
			else:
				clientdoc.update({"source_company":doc.company})
				clientdoc.update({"debit_to":"Piutang - ASV"})
				clientroot.update(clientdoc)
				
		if doc.doctype not in ("Sales Invoice","Purchase Receipt","Purchase Invoice") and doc.docstatus == 1:
			clientdoc = clientroot.get_doc(doc.doctype, docu_tujuan['name'])
			# clientroot.submit(clientdoc)
			clientroot.update(clientdoc)

		# frappe.db.commit()

		nama_sumber = clientroot.get_value(doc.doctype, "name", {"name":doc.name})
		# if nama_sumber:
		# 	print(nama_sumber['name'])
		# 	frappe.db.sql(""" UPDATE `tab{}` SET sync_pajak_name = "{}" WHERE name = "{}" """.format(doc.doctype,nama_sumber['name'],doc.name))
		# 	frappe.db.commit()



		# frappe.db.commit()
	else:
		pr_doc.update({"amended_from":""})

		if doc.doctype == "Sales Invoice":
			if doc.company == "ASOVIC BALI":
				pr_doc.update({"additional_discount_percentage":5})

			else:
				pr_doc.update({"source_company":"AS Kitchen"})

		# if doc.docstatus == 1:
			# pr_doc.update({"docstatus":1})
		
		# if pr_doc.get("items"):
		# print("dicts: %s" % pr_doc)

		# f = open("/home/frappe/frappe-bench/apps/sync_tax/sync_tax/sync_tax/sinv.json","a")
		# f.write(str(pr_doc))
		# f.close()
		frappe.msgprint(str(pr_doc))
		clientroot.insert(pr_doc)

		nama_sumber = clientroot.get_value(doc.doctype, "name", {"name":doc.name})
		# if nama_sumber:
		# 	print("target_name %s" % nama_sumber['name'])
		# 	frappe.db.sql(""" UPDATE `tab{}` SET sync_pajak_name = "{}" WHERE name = "{}" """.format(doc.doctype,nama_sumber['name'],doc.name))
		# 	frappe.db.commit()


@frappe.whitelist()
def manual_sync_master(doctype,docname):
	doc = frappe.get_doc(doctype, docname)
	
	# web_tujuan = frappe.db.get_single_value("Sync Settings", "web_tujuan")
	web_tujuan = "https://honda2.digitalasiasolusindo.com/"
	# username = frappe.db.get_single_value("Sync Settings", "username")
	username = "Administrator"
	server_pajak = [frappe._dict({
			# 'password':get_decrypted_password("Sync Settings","Sync Settings","password",False),
			'password':"admin",
			'username':username,
			'web_tujuan':web_tujuan
		})]

	clientroot = FrappeClient(server_pajak[0].web_tujuan,server_pajak[0].username,server_pajak[0].password)
	nama_sumber = clientroot.get_value(doc.doctype, "name", {"name":doc.name})
	# if nama_sumber:
	# 	frappe.db.sql(""" UPDATE `tab{}` SET sync_pajak_name = "{}" WHERE name = "{}"; """.format(doc.doctype,nama_sumber['name'],doc.name))
	# 	frappe.db.commit()

	# doc.sync_sumber_name = docname
	sync_master(doc)
	
