import frappe

def isi_nosin(self,method):
	split = self.name.split("--")
	self.no_rangka = split[1]
	self.no_mesin = split[0]
	frappe.db.sql(""" UPDATE `tabSerial No` set no_rangka='{}',no_mesin = '{}' where name = '{}' """.format(split[1],split[0],self.name))
	frappe.db.commit()

def rem_sinv(self,method):
	frappe.msgprint("s")
	# doc = frappe.get_doc("Serial No",self.name)
	if self.delivery_document_type == 'Sales Invoice Penjualan Motor' and self.delivery_document_no:
		frappe.msgprint("sss")
		data = frappe.get_doc("Sales Invoice Penjualan Motor",self.delivery_document_no)
		# self.sales_invoice_penjualan_motor = self.delivery_document_no
		# self.sales_invoice = None
		if not self.pemilik or self.pemilik == "":
			frappe.msgprint("ssss")
			self.pemilik = data.pemilik
			self.customer = data.pemilik
			self.customer_name = data.nama_pemilik
			self.nama_pemilik = data.nama_pemilik
			self.db_update()

	if self.sales_invoice and self.delivery_document_no != 'Sales Invoice Penjualan Motor':
		if frappe.db.exists("Sales Invoice Penjualan Motor",self.sales_invoice):
			data = frappe.get_doc("Sales Invoice Penjualan Motor",self.sales_invoice)
			# self.sales_invoice_penjualan_motor = self.delivery_document_no
			# self.sales_invoice = None
			if not self.pemilik or self.pemilik == "":
				self.pemilik = data.pemilik
				self.customer = data.pemilik
				self.customer_name = data.nama_pemilik
				self.nama_pemilik = data.nama_pemilik
				self.db_update()

	if not self.delivery_document_no:
		self.pemilik = ""
		self.customer = ""
		self.customer_name = ""
		self.nama_pemilik = ""
		self.db_update()
		# self.sales_invoice_penjualan_motor = None
		# self.sales_invoice = None

	data = frappe.db.sql(""" SELECT 
		sipm.cost_center as cost_center_jual,
		(SELECT cc2.parent_cost_center from 
			`tabPurchase Receipt Item` pri 
			JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where pri.parent=pr.name and pri.serial_no like '%{0}%' ) as cc_beli,
		pr.posting_date as tanggal_beli,
		cc2.parent_cost_center as cc_jual
		from `tabSales Invoice Penjualan Motor` sipm
		join `tabSerial No` sn on sn.name = sipm.no_rangka
		join `tabStock Ledger Entry` sle on sle.serial_no LIKE CONCAT("%",sn.name,"%") 
		join `tabItem` i on i.name = sipm.item_code
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
		JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
		where sipm.docstatus = 1  and sle.voucher_type = "Purchase Receipt" and sn.name = '{0}' """.format(self.name),as_dict=1,debug=1)

	data_blm = frappe.db.sql(""" SELECT 
		(SELECT cc2.parent_cost_center from 
			`tabPurchase Receipt Item` pri 
			JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where pri.parent=pr.name and pri.serial_no like '%{0}%') as cc_beli,
		pr.posting_date as tanggal_beli
		from `tabSerial No` sn
		join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
		join `tabItem` i on i.name = sn.item_code
		left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
		where sle.voucher_type = "Purchase Receipt" and sn.name = '{0}' """.format(self.name),as_dict=1)

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

	asal_jual = ''
	asal_beli= ''
	tanggal_beli = ''
	if data:
		if 'BJM' in data[0]['cc_jual']:
			asal_jual = 'BJM'
		else:
			asal_jual = 'IFMI'

		if 'BJM' in data[0]['cc_beli']:
			asal_beli = 'BJM'
		else:
			asal_beli = 'IFMI'

		tanggal_beli = data[0]['tanggal_beli']

	if data_blm:
		if 'BJM' in data_blm[0]['cc_beli']:
			asal_beli = 'BJM'
		else:
			asal_beli = 'IFMI'

		tanggal_beli = data_blm[0]['tanggal_beli']
		

	if data_repack_jual:
		print("masuk Sini")
		if 'BJM' in data_repack_jual[0]['cc_jual']:
			asal_jual = 'BJM'
		else:
			asal_jual = 'IFMI'

		if 'BJM' in data_repack_jual[0]['cc_beli']:
			asal_beli = 'BJM'
		else:
			asal_beli = 'IFMI'

		tanggal_beli = data_repack_jual[0]['tanggal_beli']
		

	if data_repack:
		if 'BJM' in data_repack[0]['cc_beli']:
			asal_beli = 'BJM'
		else:
			asal_beli = 'IFMI'

		tanggal_beli = data_repack[0]['tanggal_beli']

	if tanggal_beli != "":
		frappe.db.sql(""" UPDATE `tabSerial No` set asal_beli='{}',asal_jual='{}',tanggal_beli='{}' where name = '{}' """.format(asal_beli,asal_jual,tanggal_beli,self.name))
	print(self.name)

	print(str(data)+' data')
	print(str(data_blm)+' data_blm')
	
	print(self.name, ' doc.name')
	print(self.asal_beli, ' doc.asal_beli')

	print(str(data)+' data')
	print(str(data_blm)+' data_blm')
	frappe.db.commit()

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
	print(len(serial), " --len")
	conter = 1
	for i in serial:
		print(conter, " --conter")
		# doc = frappe.get_doc('Serial No',i['name'])
		data = frappe.db.sql(""" SELECT 
			sipm.cost_center as cost_center_jual,
			(SELECT cc2.parent_cost_center from 
				`tabPurchase Receipt Item` pri 
				JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
				JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
				where pri.parent=pr.name and pri.serial_no like '%{0}%' ) as cc_beli,
			pr.posting_date as tanggal_beli,
			cc2.parent_cost_center as cc_jual
			from `tabSales Invoice Penjualan Motor` sipm
			join `tabSerial No` sn on sn.name = sipm.no_rangka
			join `tabStock Ledger Entry` sle on sle.serial_no = sipm.no_rangka
			join `tabItem` i on i.name = sipm.item_code
			left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
			JOIN `tabCost Center` cc ON cc.name = sipm.cost_center 
			JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
			where sipm.docstatus = 1  and sle.voucher_type = "Purchase Receipt" and sn.name = '{0}' """.format(i['name']),as_dict=1)

		data_blm = frappe.db.sql(""" SELECT 
			(SELECT cc2.parent_cost_center from 
				`tabPurchase Receipt Item` pri 
				JOIN `tabCost Center` cc ON cc.name = pri.cost_center 
				JOIN `tabCost Center` cc2 ON cc2.`name` = cc.`parent_cost_center`
				where pri.parent=pr.name and pri.serial_no like '%{0}%') as cc_beli,
			pr.posting_date as tanggal_beli
			from `tabSerial No` sn
			join `tabStock Ledger Entry` sle on sle.serial_no = sn.name
			join `tabItem` i on i.name = sn.item_code
			left join `tabPurchase Receipt` pr on pr.name = sle.voucher_no
			where sle.voucher_type = "Purchase Receipt" and sn.name = '{0}' """.format(i['name']),as_dict=1)

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
			where sle.voucher_type = "Stock Entry" and se.stock_entry_type = 'Repack' and sn.name = '{0}' """.format(i['name']),as_dict=1)

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
			where sipm.docstatus = 1  and sle.voucher_type = "Stock Entry" and se.stock_entry_type = 'Repack' and sn.name = '{0}' """.format(i['name']),as_dict=1)

		asal_jual = ''
		if data:
			if 'BJM' in data[0]['cc_jual']:
				asal_jual = 'BJM'
			else:
				asal_jual = 'IFMI'

			if 'BJM' in data[0]['cc_beli']:
				asal_beli = 'BJM'
			else:
				asal_beli = 'IFMI'

			tanggal_beli = data[0]['tanggal_beli']

		if data_blm:
			if 'BJM' in data_blm[0]['cc_beli']:
				asal_beli = 'BJM'
			else:
				asal_beli = 'IFMI'

			tanggal_beli = data_blm[0]['tanggal_beli']
			

		if data_repack_jual:
			print("masuk Sini")
			if 'BJM' in data_repack_jual[0]['cc_jual']:
				asal_jual = 'BJM'
			else:
				asal_jual = 'IFMI'

			if 'BJM' in data_repack_jual[0]['cc_beli']:
				asal_beli = 'BJM'
			else:
				asal_beli = 'IFMI'

			tanggal_beli = data_repack_jual[0]['tanggal_beli']
			

		if data_repack:
			if 'BJM' in data_repack[0]['cc_beli']:
				asal_beli = 'BJM'
			else:
				asal_beli = 'IFMI'

			tanggal_beli = data_repack[0]['tanggal_beli']


		frappe.db.sql(""" UPDATE `tabSerial No` set asal_beli='{}',asal_jual='{}',tanggal_beli='{}' where name = '{}' """.format(asal_beli,asal_jual,tanggal_beli,i['name']))
		print(i['name'])

		print(str(data)+' data')
		print(str(data_blm)+' data_blm')
		conter = conter + 1

