from __future__ import unicode_literals
import frappe, erpnext
import json
import frappe.utils
from frappe.utils import cstr, cint, flt
from num2words import num2words
from erpnext.stock.doctype.serial_no.serial_no import process_serial_no

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
def repair_gl_entry():
	doctype = "Sales Invoice Penjualan Motor"
	docname = "ACC-SINVM-2022-02135"
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
	data = frappe.db.sql(""" SELECT sipm.name,sipm.cost_center,cc.parent_cost_center as cc,cc2.`parent_cost_center` as cc2
		FROM `tabSales Invoice Penjualan Motor` sipm 
		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
		WHERE sipm.`docstatus`=1 AND cc2.parent_cost_center LIKE 'BJM%' """,as_dict=1)

	tmp = []
	print(len(data))
	for i in data:
		try:
			print(i['name']+'|'+i['cc2'])
			# doc = frappe.get_doc("Sales Invoice Penjualan Motor",i['name'])
			# doc.cancel()
			# doc.delete()
			print(doc.name+"-"+"DONE")
		except Exception as e:
			tmp.append(i['name']+'|'+i['cc2']+'-'+e)
	print(tmp)
			

@frappe.whitelist()
def repair_cost_center_ifmi():
	# Ifmi
	data = frappe.db.sql(""" SELECT sipm.name,sipm.cost_center,cc.parent_cost_center as cc,cc2.`parent_cost_center` as cc2
		FROM `tabSales Invoice Penjualan Motor` sipm 
		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
		WHERE sipm.`docstatus`=1 AND cc2.parent_cost_center LIKE 'IFMI%' """,as_dict=1)

	tmp = []
	print(len(data))
	for i in data:
		try:
			print(i['name']+'|'+i['cc2'])
			# doc = frappe.get_doc("Sales Invoice Penjualan Motor",i['name'])
			# doc.cancel()
			# doc.delete()
			print(doc.name+"-"+"DONE")
		except Exception as e:
			tmp.append(i['name']+'|'+i['cc2']+'-'+e)
	print(tmp)



@frappe.whitelist()
def repair_sipm():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2023-01491")
	doc.cancel()
	print(doc.name)
	print(doc.docstatus)

@frappe.whitelist()
def repair_sipm_after():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2023-01491")
	frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set docstatus = 0 where name = '{}' """.format(doc.name))
	delete_sl = frappe.db.sql(""" DELETE FROM `tabStock Ledger Entry` WHERE voucher_no = "{}" """.format(doc.name))
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(doc.name))
	doc2 = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2023-01491")
	print(doc2.name)
	doc2.custom_missing_values()
	doc2.set_posting_time = 1
	doc2.save()
	doc2.submit()