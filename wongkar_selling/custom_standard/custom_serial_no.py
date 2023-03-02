import frappe

def rem_sinv(self,method):
	doc = frappe.get_doc("Serial No",self.name)
	if self.delivery_document_type == 'Sales Invoice Penjualan Motor' and self.delivery_document_no:
		data = frappe.get_doc("Sales Invoice Penjualan Motor",self.delivery_document_no)
		# self.sales_invoice_penjualan_motor = self.delivery_document_no
		# self.sales_invoice = None
		if not self.pemilik or self.pemilik == "":
			doc.pemilik = data.pemilik
			doc.customer = data.pemilik
			doc.customer_name = data.nama_pemilik
			doc.nama_pemilik = data.nama_pemilik
			doc.db_update()

	if self.sales_invoice and self.delivery_document_no != 'Sales Invoice Penjualan Motor':
		if frappe.db.exists("Sales Invoice Penjualan Motor",self.sales_invoice):
			data = frappe.get_doc("Sales Invoice Penjualan Motor",self.sales_invoice)
			# self.sales_invoice_penjualan_motor = self.delivery_document_no
			# self.sales_invoice = None
			if not self.pemilik or self.pemilik == "":
				doc.pemilik = data.pemilik
				doc.customer = data.pemilik
				doc.customer_name = data.nama_pemilik
				doc.nama_pemilik = data.nama_pemilik
				doc.db_update()

	if not self.delivery_document_no:
		doc.pemilik = ""
		doc.customer = ""
		doc.customer_name = ""
		doc.nama_pemilik = ""
		doc.db_update()
		# self.sales_invoice_penjualan_motor = None
		# self.sales_invoice = None

	data = frappe.db.sql(""" SELECT 
		sipm.cost_center as cost_center_jual,
		(SELECT cc2.parent_cost_center from 
			`tabPurchase Receipt Item` pri 
			JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where pri.parent=pr.name Limit 1) as cc_beli,
		pr.posting_date as tanggal_beli,
		cc2.parent_cost_center as cc_jual
		from `tabSales Invoice Penjualan Motor` sipm
		join `tabSerial No` sn on sn.name = sipm.no_rangka
		join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
		join `tabItem` i on i.name = sipm.item_code
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
		where sipm.docstatus = 1  and sle.voucher_type = "Purchase Receipt" and sn.name = '{}' """.format(self.name),as_dict=1)

	data_blm = frappe.db.sql(""" SELECT 
		(SELECT cc2.parent_cost_center from 
			`tabPurchase Receipt Item` pri 
			JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where pri.parent=pr.name Limit 1) as cc_beli,
		pr.posting_date as tanggal_beli
		from `tabSerial No` sn
		join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
		join `tabItem` i on i.name = sn.item_code
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		where sle.voucher_type = "Purchase Receipt" and sn.name = '{}' """.format(self.name),as_dict=1)

	data_repack = frappe.db.sql(""" SELECT 
		(SELECT cc2.parent_cost_center from 
			`tabStock Entry Detail` sed 
			JOIN `tabCost Center` cc ON cc.name = sed.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where sed.parent=se.name and sed.serial_no like '%{0}%' Limit 1) as cc_beli,
		se.posting_date as tanggal_beli
		from `tabSerial No` sn
		join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
		join `tabItem` i on i.name = sn.item_code
		left join `tabStock Entry` se on se.name = sle.voucher_no
		where sle.voucher_type = "Stock Entry" and se.stock_entry_type = 'Repack' and sn.name = '{0}' """.format(self.name),as_dict=1)

	data_repack_jual = frappe.db.sql(""" SELECT 
		sipm.cost_center as cost_center_jual,
		(SELECT cc2.parent_cost_center from 
			`tabStock Entry Detail` sed 
			JOIN `tabCost Center` cc ON cc.name = sed.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where sed.parent=se.name and sed.serial_no like '%{0}%' Limit 1) as cc_beli,
		se.posting_date as tanggal_beli,
		cc2.parent_cost_center as cc_jual
		from `tabSales Invoice Penjualan Motor` sipm
		join `tabSerial No` sn on sn.name = sipm.no_rangka
		join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
		join `tabItem` i on i.name = sipm.item_code
		left join `tabStock Entry` se on se.name = sle.voucher_no
		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
		where sipm.docstatus = 1  and sle.voucher_type = "Stock Entry" and se.stock_entry_type = 'Repack' and sn.name = '{0}' """.format(self.name),as_dict=1)

	print(data_repack, ' data_repack')
	print(data_repack_jual, ' data_repack_jual')
	# doc = frappe.get_doc('Serial No',self.name)
		
	if data:
		if 'BJM' in data[0]['cc_jual']:
			doc.asal_jual = 'BJM'
		else:
			doc.asal_jual = 'IFMI'

		if 'BJM' in data[0]['cc_beli']:
			doc.asal_beli = 'BJM'
		else:
			doc.asal_beli = 'IFMI'

		doc.tanggal_beli = data[0]['tanggal_beli']
		doc.db_update()

	if data_blm:
		if 'BJM' in data_blm[0]['cc_beli']:
			doc.asal_beli = 'BJM'
		else:
			doc.asal_beli = 'IFMI'

		doc.tanggal_beli = data_blm[0]['tanggal_beli']
		doc.db_update()

	if data_repack_jual:
		print("masuk Sini")
		if 'BJM' in data_repack_jual[0]['cc_jual']:
			doc.asal_jual = 'BJM'
		else:
			doc.asal_jual = 'IFMI'

		if 'BJM' in data_repack_jual[0]['cc_beli']:
			doc.asal_beli = 'BJM'
		else:
			doc.asal_beli = 'IFMI'

		doc.tanggal_beli = data_repack_jual[0]['tanggal_beli']
		doc.db_update()


	if data_repack:
		if 'BJM' in data_repack[0]['cc_beli']:
			doc.asal_beli = 'BJM'
		else:
			doc.asal_beli = 'IFMI'

		doc.tanggal_beli = data_repack[0]['tanggal_beli']
		doc.db_update()
	
	print(doc.name, ' doc.name')
	print(doc.asal_beli, ' doc.asal_beli')

	print(str(data)+' data')
	print(str(data_blm)+' data_blm')

def patch_serial_no(self,method):
	pass
	# frappe.msgprint("test")
	# if frappe.local.site == 'honda2.digitalasiasolusindo.com':
	# data = frappe.db.sql(""" SELECT 
	# 	sipm.cost_center as cost_center_jual,
	# 	(SELECT cc2.parent_cost_center from 
	# 		`tabPurchase Receipt Item` pri 
	# 		JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
	# 		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
	# 		where pri.parent=pr.name Limit 1) as cc_beli,
	# 	pr.posting_date as tanggal_beli,
	# 	cc2.parent_cost_center as cc_jual
	# 	from `tabSales Invoice Penjualan Motor` sipm
	# 	join `tabSerial No` sn on sn.name = sipm.no_rangka
	# 	join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
	# 	join `tabItem` i on i.name = sipm.item_code
	# 	left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
	# 	JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
	# 	JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
	# 	where sipm.docstatus = 1  and sle.voucher_type = "Purchase Receipt" and sn.name = '{}' """.format(self.name),as_dict=1)

	# data_blm = frappe.db.sql(""" SELECT 
	# 	(SELECT cc2.parent_cost_center from 
	# 		`tabPurchase Receipt Item` pri 
	# 		JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
	# 		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
	# 		where pri.parent=pr.name Limit 1) as cc_beli,
	# 	pr.posting_date as tanggal_beli
	# 	from `tabSerial No` sn
	# 	join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
	# 	join `tabItem` i on i.name = sn.item_code
	# 	left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
	# 	where sle.voucher_type = "Purchase Receipt" and sn.name = '{}' """.format(self.name),as_dict=1)

	# data_repack = frappe.db.sql(""" SELECT 
	# 	(SELECT cc2.parent_cost_center from 
	# 		`tabStock Entry Detail` sed 
	# 		JOIN `tabCost Center` cc ON cc.name = sed.cost_center 
	# 		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
	# 		where sed.parent=se.name and sed.serial_no like '%{0}%' Limit 1) as cc_beli,
	# 	se.posting_date as tanggal_beli
	# 	from `tabSerial No` sn
	# 	join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
	# 	join `tabItem` i on i.name = sn.item_code
	# 	left join `tabStock Entry` se on se.name = sle.voucher_no
	# 	where sle.voucher_type = "Stock Entry" and se.stock_entry_type = 'Repack' and sn.name = '{0}' """.format(self.name),as_dict=1)

	# data_repack_jual = frappe.db.sql(""" SELECT 
	# 	sipm.cost_center as cost_center_jual,
	# 	(SELECT cc2.parent_cost_center from 
	# 		`tabStock Entry Detail` sed 
	# 		JOIN `tabCost Center` cc ON cc.name = sed.cost_center 
	# 		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
	# 		where sed.parent=se.name and sed.serial_no like '%{0}%' Limit 1) as cc_beli,
	# 	se.posting_date as tanggal_beli,
	# 	cc2.parent_cost_center as cc_jual
	# 	from `tabSales Invoice Penjualan Motor` sipm
	# 	join `tabSerial No` sn on sn.name = sipm.no_rangka
	# 	join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
	# 	join `tabItem` i on i.name = sipm.item_code
	# 	left join `tabStock Entry` se on se.name = sle.voucher_no
	# 	JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
	# 	JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
	# 	where sipm.docstatus = 1  and sle.voucher_type = "Stock Entry" and se.stock_entry_type = 'Repack' and sn.name = '{0}' """.format(self.name),as_dict=1)

	# print(data_repack, ' data_repack')
	# print(data_repack_jual, ' data_repack_jual')
	# doc = frappe.get_doc('Serial No',self.name)
		
	# if data:
	# 	if 'BJM' in data[0]['cc_jual']:
	# 		doc.asal_jual = 'BJM'
	# 	else:
	# 		doc.asal_jual = 'IFMI'

	# 	if 'BJM' in data[0]['cc_beli']:
	# 		doc.asal_beli = 'BJM'
	# 	else:
	# 		doc.asal_beli = 'IFMI'

	# 	doc.tanggal_beli = data[0]['tanggal_beli']
	# 	doc.db_update()
	# 	frappe.db.commit()

	# if data_blm:
	# 	if 'BJM' in data_blm[0]['cc_beli']:
	# 		doc.asal_beli = 'BJM'
	# 	else:
	# 		doc.asal_beli = 'IFMI'

	# 	doc.tanggal_beli = data_blm[0]['tanggal_beli']
	# 	doc.db_update()
	# 	frappe.db.commit()

	# if data_repack_jual:
	# 	print("masuk Sini")
	# 	if 'BJM' in data_repack_jual[0]['cc_jual']:
	# 		doc.asal_jual = 'BJM'
	# 	else:
	# 		doc.asal_jual = 'IFMI'

	# 	if 'BJM' in data_repack_jual[0]['cc_beli']:
	# 		doc.asal_beli = 'BJM'
	# 	else:
	# 		doc.asal_beli = 'IFMI'

	# 	doc.tanggal_beli = data_repack_jual[0]['tanggal_beli']
	# 	doc.db_update()
	# 	frappe.db.commit()


	# if data_repack:
	# 	if 'BJM' in data_repack[0]['cc_beli']:
	# 		doc.asal_beli = 'BJM'
	# 	else:
	# 		doc.asal_beli = 'IFMI'

	# 	doc.tanggal_beli = data_repack[0]['tanggal_beli']
	# 	doc.db_update()
	# 	frappe.db.commit()
	
	# print(doc.name, ' doc.name')
	# print(doc.asal_beli, ' doc.asal_beli')

	# print(str(data)+' data')
	# print(str(data_blm)+' data_blm')

def patch_serial_all():
	# if frappe.local.site == 'honda2.digitalasiasolusindo.com':
	serial = frappe.db.sql(""" Select name from `tabSerial No` """,as_dict=1)
	for i in serial:
		doc = frappe.get_doc('Serial No',i['name'])
		data = frappe.db.sql(""" SELECT 
			sipm.cost_center as cost_center_jual,
			(SELECT cc2.parent_cost_center from 
				`tabPurchase Receipt Item` pri 
				JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
				JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
				where pri.parent=pr.name Limit 1) as cc_beli,
			pr.posting_date as tanggal_beli,
			cc2.parent_cost_center as cc_jual
			from `tabSales Invoice Penjualan Motor` sipm
			join `tabSerial No` sn on sn.name = sipm.no_rangka
			join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
			join `tabItem` i on i.name = sipm.item_code
			left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
			JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where sipm.docstatus = 1  and sle.voucher_type = "Purchase Receipt" and sn.name = '{}' """.format(i['name']),as_dict=1)

		data_blm = frappe.db.sql(""" SELECT 
			(SELECT cc2.parent_cost_center from 
				`tabPurchase Receipt Item` pri 
				JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
				JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
				where pri.parent=pr.name Limit 1) as cc_beli,
			pr.posting_date as tanggal_beli
			from `tabSerial No` sn
			join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
			join `tabItem` i on i.name = sn.item_code
			left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
			where sle.voucher_type = "Purchase Receipt" and sn.name = '{}' """.format(i['name']),as_dict=1)


		if data:
			if 'BJM' in data[0]['cc_jual']:
				doc.asal_jual = 'BJM'
			else:
				doc.asal_jual = 'IFMI'

			if 'BJM' in data[0]['cc_beli']:
				doc.asal_beli = 'BJM'
			else:
				doc.asal_beli = 'IFMI'

			doc.tanggal_beli = data[0]['tanggal_beli']
			doc.db_update()

		if data_blm:
			if 'BJM' in data_blm[0]['cc_beli']:
				doc.asal_beli = 'BJM'
			else:
				doc.asal_beli = 'IFMI'

			doc.tanggal_beli = data_blm[0]['tanggal_beli']
			doc.db_update()
		
		print(i['name'])

		print(str(data)+' data')
		print(str(data_blm)+' data_blm')

