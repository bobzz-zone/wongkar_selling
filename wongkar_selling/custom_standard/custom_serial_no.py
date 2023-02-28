import frappe

def rem_sinv(self,method):
	if self.delivery_document_type == 'Sales Invoice Penjualan Motor' and self.delivery_document_no:
		data = frappe.get_doc("Sales Invoice Penjualan Motor",self.delivery_document_no)
		# self.sales_invoice_penjualan_motor = self.delivery_document_no
		# self.seles_invoice = None
		if not self.pemilik or self.pemilik == "":
			self.pemilik = data.pemilik
			self.customer = data.pemilik
			self.customer_name = data.nama_pemilik
			self.nama_pemilik = data.nama_pemilik

	if not self.delivery_document_no:
		self.pemilik = ""
		self.customer = ""
		self.customer_name = ""
		self.nama_pemilik = ""
		# self.sales_invoice_penjualan_motor = None
		# self.seles_invoice = None

def patch_serial_no(self,method):
	# if frappe.local.site == 'honda2.digitalasiasolusindo.com':
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


	if data:
		if 'BJM' in data[0]['cc_jual']:
			self.asal_jual = 'BJM'
		else:
			self.asal_jual = 'IFMI'

		if 'BJM' in data[0]['cc_beli']:
			self.asal_beli = 'BJM'
		else:
			self.asal_beli = 'IFMI'

		self.tanggal_beli = data[0]['tanggal_beli']

	if data_blm:
		if 'BJM' in data_blm[0]['cc_beli']:
			self.asal_beli = 'BJM'
		else:
			self.asal_beli = 'IFMI'

		self.tanggal_beli = data_blm[0]['tanggal_beli']
	
	print(self.name)

	frappe.msgprint(str(data)+' data')
	frappe.msgprint(str(data_blm)+' data_blm')

def patch_serial_all():
	# if frappe.local.site == 'honda2.digitalasiasolusindo.com':
	serial = frappe.db.sql(""" Select name from `tabSerial No` """,as_dict=1)
	for i in serial:
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
			doc = frappe.get_doc('Serial No',i['name'])
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
			doc = frappe.get_doc('Serial No',i['name'])
			if 'BJM' in data_blm[0]['cc_beli']:
				doc.asal_beli = 'BJM'
			else:
				doc.asal_beli = 'IFMI'

			doc.tanggal_beli = data_blm[0]['tanggal_beli']
			doc.db_update()
		
		print(i['name'])

		frappe.msgprint(str(data)+' data')
		frappe.msgprint(str(data_blm)+' data_blm')

