import frappe
from datetime import datetime, timedelta

@frappe.whitelist()
def can_diskon_sn_ste(self,method):
	data_ste = frappe.db.sql(""" SELECT name,docstatus from `tabStock Entry` where purchase_invoice = '{}'  """.format(self.name),as_dict=1)
	data_je = frappe.db.sql(""" SELECT name,docstatus from `tabJournal Entry` where purchase_invoice = '{}'  """.format(self.name),as_dict=1)

	for i in data_ste:
		if i['docstatus'] == 1:
			doc = frappe.get_doc('Stock Entry',i['name'])
			# doc.purchase_invoice = None
			# doc.db_update()
			doc.cancel()
			doc.workflow_state = 'Canceled'
			doc.db_update()
			doc.flags.ignore_permission=True

	for i in data_je:
		if i['docstatus'] == 1:
			doc = frappe.get_doc('Journal Entry',i['name'])
			# doc.purchase_invoice = None
			# doc.db_update()
			doc.cancel()
			doc.flags.ignore_permission=True

@frappe.whitelist()
def diskon_sn_ste(self,method):
	if not self.is_return:
		diskon_sn(self)
		cek_frezze = frappe.db.get_single_value('Accounts Settings', 'acc_frozen_upto')
		print(cek_frezze, ' cek_frezze')
		po = []
		for i in self.items:
			po.append({
					'purchase_order': i.purchase_order,
					'po_detail': i.po_detail
				})

		dict_sn = []
		selisih = 0
		for i in po:
			# print(i['purchase_order'])
			prec = frappe.db.sql(""" 
				SELECT 
					pri.name,pri.parent,pri.item_code,pri.serial_no,
					pri.amount,pri.rate,pri.purchase_order,pri.purchase_order_item,
					pri.warehouse,prec.posting_date,prec.posting_time,prec.cost_center
				from `tabPurchase Receipt` prec 
				join `tabPurchase Receipt Item` pri on pri.parent = prec.name
				where prec.docstatus = 1 and pri.purchase_order = '{}' and pri.purchase_order_item = '{}' """.format(i['purchase_order'],i['po_detail']),as_dict=1)
			
			
			for i in self.items:
				for item in prec:
					print(item.cost_center, ' item.item.cost_center')
					if i.po_detail == item.purchase_order_item:
						if i.rate != item.rate:
							if item['serial_no']:
								print('masuk sini  xxxxxxxx')
								for serial in item['serial_no'].split('\n'):
									sn = frappe.get_doc('Serial No',serial)
									if sn.status == 'Active' and sn.purchase_document_type != 'Purchase Receipt':
										frappe.throw('Item sudah berpindah Gudang / Dokumen !')

									if sn.status == 'Active' and sn.purchase_document_type == 'Purchase Receipt':
										if cek_frezze:
											if item.posting_date <= cek_frezze:
												posting_date = frappe.utils.add_days(cek_frezze, 1)
												posting_time = '01:00:00'
											else:
												posting_date = item.posting_date
												posting_time = item.posting_time + timedelta(seconds=1)
										else:
											posting_date = item.posting_date
											posting_time = item.posting_time + timedelta(seconds=1)

										# frappe.throw('sadadsa')
										print(posting_date, ' posting_date')
										sn.update_rate = 1
										sn.db_update()
										ste = frappe.new_doc('Stock Entry')
										ste.purchase_invoice = self.name
										ste.stock_entry_type = 'Repack'
										ste.posting_date = posting_date
										ste.posting_time = posting_time
										ste.set_posting_time = 1
										ste.append('items',{
												's_warehouse': item.warehouse,
												'item_code': item.item_code,
												'serial_no': sn.name,
												'cost_center': item.cost_center,
												'qty': 1
											})

										ste.append('items',{
												't_warehouse': item.warehouse,
												'item_code': item.item_code,
												'serial_no': sn.name,
												'cost_center': item.cost_center,
												'basic_rate': i.rate,
												'set_basic_rate_manually': 1,
												'qty': 1										
											})
										ste.save()
										ste.submit()
										ste.flags.ignore_permission=True
										print(ste.name, ' sn_name')
										# print(sn.name, ' sn_name')
									if sn.status == 'Delivered' and sn.delivery_document_type in ['Sales Invoice','Sales Invoice Penjualan Motor']:
										selisih += item.rate - i.rate
										print(item.rate - i.rate, ' sellll')
										print(i.rate, ' | ',item.rate, ' ckckckck')

		print(selisih, ' selisih')
		if selisih != 0:
			if cek_frezze:
				if item.posting_date <= cek_frezze:
					posting_date = frappe.utils.add_days(cek_frezze, 1)
				else:
					posting_date = self.posting_date
			else:
				posting_date = self.posting_date
			je = frappe.new_doc('Journal Entry')
			je.posting_date = posting_date
			je.purchase_invoice = self.name
			deb = {
				'account' : frappe.get_doc('Company',self.company).je_debit, # '21600.01 - BARANG BELUM DITAGIH - MOTOR - W',
				'debit': selisih,
				'debit_in_account_currency': selisih,
				'cost_center': self.cost_center
			} 

			cre = {
				'account' : frappe.get_doc('Company',self.company).je_credit, # '71000.01 - BIAYA KERUGIAN STOCK - W',
				'credit': selisih,
				'credit_in_account_currency': selisih,
				'cost_center': self.cost_center
			} 

			je.append('accounts',deb)
			je.append('accounts',cre)
			je.save()
			je.submit()
			je.flags.ignore_permission=True
			print(je.name, ' je_name')

@frappe.whitelist()
def diskon_sn(self):
	print('masuk diskon_sn !!!')
	po = []
	for i in self.items:
		po.append({
				'purchase_order': i.purchase_order,
				'po_detail': i.po_detail
			})

	dict_sn = []
	for i in po:
		# print(i['purchase_order'])
		prec = frappe.db.sql(""" 
			SELECT 
				pri.name,pri.parent,pri.item_code,pri.serial_no,
				pri.amount,pri.rate,pri.purchase_order,pri.purchase_order_item,
				pri.warehouse,prec.posting_date,prec.posting_time,prec.cost_center
			from `tabPurchase Receipt` prec 
			join `tabPurchase Receipt Item` pri on pri.parent = prec.name
			where prec.docstatus = 1 and pri.purchase_order = '{}' and pri.purchase_order_item = '{}' """.format(i['purchase_order'],i['po_detail']),as_dict=1)

		for i in self.items:
			for item in prec:
				print(item.cost_center, ' item.item.cost_center')
				if i.po_detail == item.purchase_order_item:
					if i.rate != item.rate:
						for serial in item['serial_no'].split('\n'):
							sn = frappe.get_doc('Serial No',serial)
							if sn.status == 'Active':
								sn.update_rate = 1
								sn.db_update()

		for item in prec:
			# print(f"Item: {item['item_code']}")
			# print("Serial Numbers:")
			if item['serial_no']:
				for serial in item['serial_no'].split('\n'):
					sn = frappe.get_doc('Serial No',serial)
					# print(sn.name,' | ',sn.status)
					dict_sn.append({
							'serial_no': sn.name,
							'status': sn.status,
							'purchase_rate': sn.purchase_rate
					})

	self.list_sn = []
	for sn in dict_sn:
		print(sn, ' sn')
		self.append('list_sn',sn)
	self.db_update()
	self.update_children()
	