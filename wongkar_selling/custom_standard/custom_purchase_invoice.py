from wongkar_selling.custom_standard.custom_gl_entry import update_outstanding_amt_custom
from wongkar_selling.wongkar_selling.doctype.sales_invoice_penjualan_motor.sales_invoice_penjualan_motor import get_warehouse_account_map
from erpnext.assets.doctype.asset.asset import is_cwip_accounting_enabled
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account
import frappe
from frappe import _, throw
from datetime import datetime, timedelta
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
import erpnext

from erpnext.accounts.general_ledger import (
	merge_similar_entries,
)
from frappe.utils import get_link_to_form

class PurchaseInvoiceCustom(PurchaseInvoice):
	def cek_item_saprepart(self,item_code):
		item_group = frappe.get_doc('Item',item_code).item_group
		if item_group in ['H3 - Sparepart','HGA','Oli','Sparepart','Tools']:
			print(item_group, ' cek_igxxx2321323')
			return True
		else:
			return False
	
	def set_expense_account(self, for_validate=False):
		auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)

		if auto_accounting_for_stock:
			stock_not_billed_account = self.get_company_default("stock_received_but_not_billed")
			stock_items = self.get_stock_items()

		asset_items = [d.is_fixed_asset for d in self.items if d.is_fixed_asset]
		if len(asset_items) > 0:
			asset_received_but_not_billed = self.get_company_default("asset_received_but_not_billed")

		if self.update_stock:
			self.validate_item_code()
			self.validate_warehouse(for_validate)
			if auto_accounting_for_stock:
				warehouse_account = get_warehouse_account_map(self.company)

		for item in self.get("items"):
			# in case of auto inventory accounting,
			# expense account is always "Stock Received But Not Billed" for a stock item
			# except opening entry, drop-ship entry and fixed asset items
			if item.item_code:
				asset_category = frappe.get_cached_value("Item", item.item_code, "asset_category")

			if (
				auto_accounting_for_stock
				and item.item_code in stock_items
				and self.is_opening == "No"
				and not item.is_fixed_asset
				and (
					not item.po_detail
					or not frappe.db.get_value("Purchase Order Item", item.po_detail, "delivered_by_supplier")
				)
			):

				if self.update_stock and (not item.from_warehouse):
					if (
						for_validate
						and item.expense_account
						and item.expense_account != warehouse_account[item.warehouse]["account"]
					):
						msg = _(
							"Row {0}: Expense Head changed to {1} because account {2} is not linked to warehouse {3} or it is not the default inventory account"
						).format(
							item.idx,
							frappe.bold(warehouse_account[item.warehouse]["account"]),
							frappe.bold(item.expense_account),
							frappe.bold(item.warehouse),
						)
						frappe.msgprint(msg, title=_("Expense Head Changed"))
					item.expense_account = warehouse_account[item.warehouse]["account"]
				else:
					# check if 'Stock Received But Not Billed' account is credited in Purchase receipt or not
					if item.purchase_receipt:
						cek_stock_not_billed_account = self.cek_item_saprepart(item.item_code)
						if cek_stock_not_billed_account:
							stock_not_billed_account = self.get_company_default("stock_received_but_not_billed_sparepart")

						negative_expense_booked_in_pr = frappe.db.sql(
							"""select name from `tabGL Entry`
							where voucher_type='Purchase Receipt' and voucher_no=%s and account = %s""",
							(item.purchase_receipt, stock_not_billed_account),
						)

						if negative_expense_booked_in_pr:
							if (
								for_validate and item.expense_account and item.expense_account != stock_not_billed_account
							):
								msg = _(
									"Row {0}: Expense Head changed to {1} because expense is booked against this account in Purchase Receipt {2}"
								).format(
									item.idx, frappe.bold(stock_not_billed_account), frappe.bold(item.purchase_receipt)
								)
								frappe.msgprint(msg, title=_("Expense Head Changed"))

							item.expense_account = stock_not_billed_account
					else:
						# If no purchase receipt present then book expense in 'Stock Received But Not Billed'
						# This is done in cases when Purchase Invoice is created before Purchase Receipt
						
						cek_stock_not_billed_account = self.cek_item_saprepart(item.item_code)
						if cek_stock_not_billed_account:
							stock_not_billed_account = self.get_company_default("stock_received_but_not_billed_sparepart")
							
						print(stock_not_billed_account, ' stock_not_billed_accountxxxx123')
						if (
							for_validate and item.expense_account and item.expense_account != stock_not_billed_account
						):
							msg = _(
								"Row {0}: Expense Head changed to {1} as no Purchase Receipt is created against Item {2}."
							).format(
								item.idx, frappe.bold(stock_not_billed_account), frappe.bold(item.item_code)
							)
							msg += "<br>"
							msg += _(
								"This is done to handle accounting for cases when Purchase Receipt is created after Purchase Invoice"
							)
							frappe.msgprint(msg, title=_("Expense Head Changed"))

						item.expense_account = stock_not_billed_account

			elif item.is_fixed_asset and not is_cwip_accounting_enabled(asset_category):
				asset_category_account = get_asset_category_account(
					"fixed_asset_account", item=item.item_code, company=self.company
				)
				if not asset_category_account:
					form_link = get_link_to_form("Asset Category", asset_category)
					throw(
						_("Please set Fixed Asset Account in {} against {}.").format(form_link, self.company),
						title=_("Missing Account"),
					)
				item.expense_account = asset_category_account
			elif item.is_fixed_asset and item.pr_detail:
				item.expense_account = asset_received_but_not_billed
			elif not item.expense_account and for_validate:
				throw(_("Expense account is mandatory for item {0}").format(item.item_code or item.item_name))


@frappe.whitelist()
def cek_oa_nol(self,method):
	if self.outstanding_amount == 0 and self.total_advance != self.grand_total:
		update_outstanding_amt_custom(self.credit_to,'Supplier',self.supplier,'Purchase Invoice',self.name)

@frappe.whitelist()
def can_diskon_sn_ste(self,method):
	frappe.db.sql(""" UPDATE `tabSingles` SET value = 1 WHERE field = "allow_negative_stock" """)
	data_ste = frappe.db.sql(""" SELECT name,docstatus from `tabStock Entry` where purchase_invoice = '{}'  """.format(self.name),as_dict=1)
	data_je = frappe.db.sql(""" SELECT name,docstatus from `tabJournal Entry` where purchase_invoice = '{}'  """.format(self.name),as_dict=1)

	for i in data_ste:
		if i['docstatus'] == 1:
			doc = frappe.get_doc('Stock Entry',i['name'])
			doc.purchase_invoice = None
			doc.db_update()
			doc.cancel()
			doc.workflow_state = 'Canceled'
			doc.db_update()
			sn = frappe.get_doc('Serial No',doc.items[0].serial_no)
			sn.purchase_rate = doc.items[0].basic_rate
			# if sn.name == 'KC02E1253206--MH1KC0216RK253731':
			# 	frappe.throw(str(sn.purchase_rate)+ ' sn.purchase_ratexx111')
			sn.db_update()
			doc.flags.ignore_permission=True

	for j in data_je:
		if j['docstatus'] == 1:
			doc = frappe.get_doc('Journal Entry',j['name'])
			doc.purchase_invoice = None
			doc.db_update()
			doc.cancel()
			doc.flags.ignore_permission=True

	frappe.db.sql(""" UPDATE `tabSingles` SET value = 0 WHERE field = "allow_negative_stock" """)

@frappe.whitelist()
def diskon_sn_ste(self,method):
	frappe.db.sql(""" UPDATE `tabSingles` SET value = 1 WHERE field = "allow_negative_stock" """)
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
		check = 0
		for p in po:
			# print(i['purchase_order'])
			prec = frappe.db.sql(""" 
				SELECT 
					pri.name,pri.parent,pri.item_code,pri.serial_no,
					pri.amount,pri.rate,pri.purchase_order,pri.purchase_order_item,
					pri.warehouse,prec.posting_date,prec.posting_time,prec.cost_center
				from `tabPurchase Receipt` prec 
				join `tabPurchase Receipt Item` pri on pri.parent = prec.name
				where prec.docstatus = 1 and pri.purchase_order = '{}' and pri.purchase_order_item = '{}' """.format(p['purchase_order'],p['po_detail']),as_dict=1)
			
			
			for i in self.items:
				for item in prec:
					# print(item.cost_center, ' item.item.cost_center')
					if i.po_detail == item.purchase_order_item:
						if i.rate != item.rate:
							if item['serial_no']:
								print('masuk sini  xxxxxxxx')
								for serial in item['serial_no'].split('\n'):
									sn = frappe.get_doc('Serial No',serial)
									if sn.status == 'Active' and sn.purchase_document_type != 'Purchase Receipt':
										print(sn.name, ' sn_namexxx')
										# frappe.throw('Item sudah berpindah Gudang / Dokumen !')

									# if sn.status == 'Active' and sn.purchase_document_type == 'Purchase Receipt':
									if sn.status == 'Active':
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
										# if sn.name == 'KC02E1253206--MH1KC0216RK253731':
										# 	frappe.throw(str(sn.purchase_rate)+ ' sn.purchase_ratexx111')
										sn.db_update()
										ste = frappe.new_doc('Stock Entry')
										ste.purchase_invoice = self.name
										ste.stock_entry_type = 'Repack'
										ste.posting_date = posting_date
										ste.posting_time = posting_time
										ste.set_posting_time = 1
										ste.append('items',{
												's_warehouse': item.warehouse,
												# 's_warehouse': sn.warehouse,
												'item_code': item.item_code,
												'serial_no': sn.name,
												'cost_center': item.cost_center,
												'qty': 1
											})

										ste.append('items',{
												't_warehouse': item.warehouse,
												# 't_warehouse': sn.warehouse,
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
										check = 1
										print(ste.name, ' sn_name')
										# sn_a = frappe.get_doc('Serial No',serial)
										# sn_a.purchase_rate = i.rate
										# if sn_a.name == 'KC02E1253206--MH1KC0216RK253731':
										# 	print(sn_a.purchase_rate)
										# 	# frappe.throw(str(sn_a.purchase_rate)+ ' sn_a.purchase_ratexx111')
										# sn_a.db_update()
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
			cek = frappe.db.sql(""" SELECT name from `tabJournal Entry` where purchase_invoice = '{}' and docstatus < 2 """.format(self.name),as_dict=1)
			if cek:
				frappe.throw("Document JE is Exsit !")
			else:
				pass
				# je = frappe.new_doc('Journal Entry')
				# je.posting_date = posting_date
				# je.purchase_invoice = self.name
				# deb = {
				# 	'account' : frappe.get_doc('Company',self.company).je_debit, # '21600.01 - BARANG BELUM DITAGIH - MOTOR - W',
				# 	'debit': selisih,
				# 	'debit_in_account_currency': selisih,
				# 	'cost_center': self.cost_center
				# } 

				# cre = {
				# 	'account' : frappe.get_doc('Company',self.company).je_credit, # '71000.01 - BIAYA KERUGIAN STOCK - W',
				# 	'credit': selisih,
				# 	'credit_in_account_currency': selisih,
				# 	'cost_center': self.cost_center
				# } 

				# je.append('accounts',deb)
				# je.append('accounts',cre)
				# je.save()
				# je.submit()
				# je.flags.ignore_permission=True
				# print(je.name, ' je_name')

	frappe.db.sql(""" UPDATE `tabSingles` SET value = 0 WHERE field = "allow_negative_stock" """)

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
	for p in po:
		# print(i['purchase_order'])
		prec = frappe.db.sql(""" 
			SELECT 
				pri.name,pri.parent,pri.item_code,pri.serial_no,
				pri.amount,pri.rate,pri.purchase_order,pri.purchase_order_item,
				pri.warehouse,prec.posting_date,prec.posting_time,prec.cost_center
			from `tabPurchase Receipt` prec 
			join `tabPurchase Receipt Item` pri on pri.parent = prec.name
			where prec.docstatus = 1 and pri.purchase_order = '{}' and pri.purchase_order_item = '{}' """.format(p['purchase_order'],p['po_detail']),as_dict=1)

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
		# print(sn, ' sn')
		self.append('list_sn',sn)
	self.db_update()
	self.update_children()
	

def udpate_rate_sn(self):
	print('masuk diskon_sn !!!')
	po = []
	for i in self.items:
		po.append({
				'purchase_order': i.purchase_order,
				'po_detail': i.po_detail
			})

	dict_sn = []
	for p in po:
		# print(i['purchase_order'])
		prec = frappe.db.sql(""" 
			SELECT 
				pri.name,pri.parent,pri.item_code,pri.serial_no,
				pri.amount,pri.rate,pri.purchase_order,pri.purchase_order_item,
				pri.warehouse,prec.posting_date,prec.posting_time,prec.cost_center
			from `tabPurchase Receipt` prec 
			join `tabPurchase Receipt Item` pri on pri.parent = prec.name
			where prec.docstatus = 1 and pri.purchase_order = '{}' and pri.purchase_order_item = '{}' """.format(p['purchase_order'],p['po_detail']),as_dict=1)

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

	for sn in dict_sn:
		if sn['status'] == 'Active':
			doc = frappe.get_doc('Serial No',sn['serial_no'])
			doc.update_serial_no_reference()
			doc.db_update()

	print(dict_sn, ' dict_sn')


def debug_repost():
	# bench --site ainew.digitalasiasolusindo.com execute alam_inrotama.helper_tool.debug_repost
	from rq.timeouts import JobTimeoutException
	from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost_sl_entries, repost_gl_entries, notify_error_to_stock_managers

	list_repost = frappe.db.sql(""" SELECT name FROM `tabRepost Item Valuation` WHERE status = "Queued" """)
	# list_repost = frappe.db.sql(""" SELECT name FROM `tabRepost Item Valuation` WHERE name = 'REPOST-ITEM-VAL-064360' """)
	print(len(list_repost))
	counter = 1
	for row in list_repost:
		print(str(counter)+" "+row[0])
		counter+=1
		doc = frappe.get_doc("Repost Item Valuation",row[0])
		try:
			check_bypass = frappe.db.sql(""" UPDATE `tabSingles` set value = 1 WHERE `field` = "bypass" """)
			if not frappe.db.exists("Repost Item Valuation", doc.name):
				return

			doc.set_status('In Progress')
			if not frappe.flags.in_test:
				frappe.db.commit()

			repost_sl_entries(doc)
			repost_gl_entries(doc)

			doc.set_status('Completed')
			check_bypass = frappe.db.sql(""" UPDATE `tabSingles` set value = 0 WHERE `field` = "bypass" """)
			
		except (Exception, JobTimeoutException):
			check_bypass = frappe.db.sql(""" UPDATE `tabSingles` set value = 0 WHERE `field` = "bypass" """)
			frappe.db.rollback()
			traceback = frappe.get_traceback()
			frappe.log_error(traceback)

			message = frappe.message_log.pop()
			if traceback:
				message += "<br>" + "Traceback: <br>" + traceback
			frappe.db.set_value(doc.doctype, doc.name, 'error_log', message)

			notify_error_to_stock_managers(doc, message)
			doc.set_status('Failed')
			raise
		finally:
			frappe.db.commit()

@erpnext.allow_regional
def make_regional_gl_entries(gl_entries, doc):
	return gl_entries