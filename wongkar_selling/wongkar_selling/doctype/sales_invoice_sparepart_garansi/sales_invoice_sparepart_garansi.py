# Copyright (c) 2024, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import add_days, cint, cstr, flt, formatdate, get_link_to_form, getdate, nowdate
from erpnext.accounts.utils import get_account_currency
import erpnext
from erpnext.stock import get_warehouse_account_map
from frappe import _
from erpnext.accounts.general_ledger import (
	make_gl_entries,
	make_reverse_gl_entries,
	process_gl_map,
)

class SalesInvoiceSparepartGaransi(SalesInvoice):
	def ubah_akun(self):
		beban_titipan_ahas_account = frappe.get_doc("Company",self.company).beban_titipan_ahas_account
		titipan_ahas_account = frappe.get_doc("Company",self.company).titipan_ahas_account
		if self.items and len(self.items) > 0:
			for i in self.items:
				i.income_account = beban_titipan_ahas_account
				i.cost_center = self.cost_center
		
	def hitung_total(self):
		piutang_oli = 0
		piutang_jasa = 0
		if self.items and len(self.items) > 0:
			for i in self.items:
				if i.titipan_account == self.debit_to:
					piutang_jasa += i.amount
				elif i.titipan_account == self.debit_to_oli:
					piutang_oli += i.amount

		self.grand_total = piutang_jasa
		self.grand_total_oli = piutang_oli
		self.outstanding_amount = self.grand_total
		self.outstanding_amount_oli = self.grand_total_oli

	def validate(self):
		self.hitung_total()
		self.set_item_amount()
		self.ubah_akun()

	def on_update(self):
		pass

	def before_save(self):
		pass

	def before_cancel(self):
		pass

	def on_submit(self):
		self.update_stock_ledger()
		self.make_gl_entries()
		self.repost_future_sle_and_gle()

	def on_cancel(self):
		self.update_stock_ledger()
		self.make_gl_entries_on_cancel()
		self.repost_future_sle_and_gle()
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Repost Item Valuation")

	def update_stock_ledger(self):
		# SalesInvoice.update_reserved_qty(self)

		sl_entries = []
		# Loop over items and packed items table
		for d in self.get_item_list():
			if frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1 and flt(d.qty):
				if flt(d.conversion_factor) == 0.0:
					d.conversion_factor = (
						get_conversion_factor(d.item_code, d.uom).get("conversion_factor") or 1.0
					)

				# On cancellation or return entry submission, make stock ledger entry for
				# target warehouse first, to update serial no values properly

				if d.warehouse and (
					(not  self.docstatus == 1)
					or ( self.docstatus == 2)
				):
					sl_entries.append(self.get_sle_for_source_warehouse(d))

				if d.target_warehouse:
					sl_entries.append(self.get_sle_for_target_warehouse(d))

				if d.warehouse and (
					(not self.docstatus == 2)
					or ( self.docstatus == 1)
				):
					sl_entries.append(self.get_sle_for_source_warehouse(d))

		self.make_sl_entries(sl_entries)

	def get_item_list(self):
		il = []
		for d in self.get("items"):
			if d.qty is None:
				frappe.throw(_("Row {0}: Qty is mandatory").format(d.idx))

			if SalesInvoice.has_product_bundle(self,d.item_code):
				for p in self.get("packed_items"):
					if p.parent_detail_docname == d.name and p.parent_item == d.item_code:
						# the packing details table's qty is already multiplied with parent's qty
						il.append(
							frappe._dict(
								{
									"warehouse": p.warehouse or d.warehouse,
									"item_code": p.item_code,
									"qty": flt(p.qty),
									"uom": p.uom,
									"batch_no": cstr(p.batch_no).strip(),
									"serial_no": cstr(p.serial_no).strip(),
									"name": d.name,
									"target_warehouse": p.target_warehouse,
									"company": self.company,
									"voucher_type": self.doctype,
									"allow_zero_valuation": d.allow_zero_valuation_rate,
									"sales_invoice_item": d.get("sales_invoice_item"),
									"dn_detail": d.get("dn_detail"),
									"incoming_rate": p.get("incoming_rate"),
								}
							)
						)
			else:
				il.append(
					frappe._dict(
						{
							"warehouse": d.warehouse,
							"item_code": d.item_code,
							"qty": d.qty,
							"uom": d.uom,
							"stock_uom": d.uom,
							"conversion_factor": 1,
							# "batch_no": cstr(d.get("batch_no")).strip(),
							# "serial_no": cstr(d.get("serial_no")).strip(),
							"name": d.name,
							# "target_warehouse": d.target_warehouse,
							"company": self.company,
							"voucher_type": self.doctype,
							# "allow_zero_valuation": d.allow_zero_valuation_rate,
							# "sales_invoice_item": d.get("sales_invoice_item"),
							# "dn_detail": d.get("dn_detail"),
							# "incoming_rate": d.get("incoming_rate"),
						}
					)
				)
		return il

	def set_item_amount(self):
		if self.items and len(self.items) > 0:
			for i in self.items:
				i.amount = i.rate * i.qty

	def get_sle_for_source_warehouse(self, item_row):
		sle = self.get_sl_entries(
			item_row,
			{
				"actual_qty": -1 * flt(item_row.qty),
				"incoming_rate": item_row.incoming_rate,
				# "recalculate_rate": cint(self.is_return),
			},
		)
		if item_row.target_warehouse:
			sle.dependant_sle_voucher_detail_no = item_row.name

		return sle


	def make_customer_gl_entry(self, gl_entries):
		# Checked both rounding_adjustment and rounded_total
		# because rounded_total had value even before introcution of posting GLE based on rounded total
		grand_total = (self.grand_total)

		base_grand_total = flt(self.grand_total,self.precision("grand_total"),)

		if grand_total and not self.is_internal_transfer():
			# Did not use base_grand_total to book rounding loss gle
			for i in self.items:
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": i.titipan_account,
							# "party_type": "Customer",
							# "party": self.customer,
							# "due_date": self.due_date,
							"against": i.income_account,
							"debit": i.amount,
							"debit_in_account_currency": i.amount,
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							# "cost_center": self.cost_center,
							# "project": self.project,
						},
						'IDR',
						item=self,
					)
				)

			# lama	
			# gl_entries.append(
			# 	self.get_gl_dict(
			# 		{
			# 			"account": self.debit_to,
			# 			# "party_type": "Customer",
			# 			# "party": self.customer,
			# 			# "due_date": self.due_date,
			# 			"against": self.against_income_account,
			# 			"debit": base_grand_total,
			# 			"debit_in_account_currency": base_grand_total
			# 			if "IDR" == "IDR"
			# 			else grand_total,
			# 			"against_voucher": self.name,
			# 			"against_voucher_type": self.doctype,
			# 			# "cost_center": self.cost_center,
			# 			# "project": self.project,
			# 		},
			# 		'IDR',
			# 		item=self,
			# 	)
			# )

	def get_gl_entries(self, warehouse_account=None):
		from erpnext.accounts.general_ledger import merge_similar_entries

		gl_entries = []

		self.make_customer_gl_entry(gl_entries)

		# self.make_tax_gl_entries(gl_entries)
		self.make_exchange_gain_loss_gl_entries(gl_entries)
		self.make_internal_transfer_gl_entries(gl_entries)

		self.make_item_gl_entries(gl_entries)
		self.make_discount_gl_entries(gl_entries)

		# merge gl entries before adding pos entries
		gl_entries = merge_similar_entries(gl_entries)

		# self.make_loyalty_point_redemption_gle(gl_entries)
		# self.make_pos_gl_entries(gl_entries)

		# self.make_write_off_gl_entry(gl_entries)
		# self.make_gle_for_rounding_adjustment(gl_entries)

		return gl_entries

	def get_tax_amounts(self, tax, enable_discount_accounting):
		amount = tax.tax_amount_after_discount_amount
		base_amount = tax.base_tax_amount_after_discount_amount

		if (
			enable_discount_accounting
			and self.get("discount_amount")
			and self.get("additional_discount_account")
			and self.get("apply_discount_on") == "Grand Total"
		):
			amount = tax.tax_amount
			base_amount = tax.base_tax_amount

		return amount, base_amount

	def make_tax_gl_entries(self, gl_entries):
		pjk = self.grand_total / ((100+self.rate)/100)
		akhir = self.grand_total - pjk
		amount = akhir
		base_amount = akhir

		account_currency = 'IDR'
		gl_entries.append(
			self.get_gl_dict(
				{
					"account": self.tax_account,
					"against": self.customer,
					"credit": flt(base_amount, self.precision("grand_total")),
					"credit_in_account_currency": (
						flt(base_amount, self.precision("grand_total"))
						if account_currency == 'IDR'
						else flt(amount, self.precision("grand_total"))
					),
					"cost_center": self.cost_center,
				},
				account_currency,
				item=self,
			)
		)

	def make_item_gl_entries(self, gl_entries):
		# income account gl entries
		for item in self.get("items"):
			if flt(item.amount, item.precision("amount")):
				if not self.is_internal_transfer():
					income_account = (
						item.income_account
					)

					amount, base_amount = self.get_amount_and_base_amount(item, self.enable_discount_accounting)

					account_currency = get_account_currency(income_account)
					gl_entries.append(
						self.get_gl_dict(
							{
								"account": income_account,
								"against": self.customer,
								"credit": flt(amount, item.precision("amount")),
								"credit_in_account_currency": (
									flt(amount, item.precision("amount"))
									if account_currency == 'IDR'
									else flt(amount, item.precision("amount"))
								),
								"cost_center": item.cost_center,
								# "project": item.project or self.project,
							},
							account_currency,
							item=item,
						)
					)

		# expense account gl entries
		if erpnext.is_perpetual_inventory_enabled(self.company):
			gl_entries += self.get_gl_entries_stock()

	def get_amount_and_base_amount(self, item, enable_discount_accounting):
		net_amount = item.amount / ((100+self.rate) / 100)
		amount = net_amount
		base_amount = net_amount

		if (
			enable_discount_accounting
			and self.get("discount_amount")
			and self.get("additional_discount_account")
		):
			amount = net_amount
			base_amount = net_amount

		return amount, base_amount

	def get_gl_entries_stock(
		self, warehouse_account=None, default_expense_account=None, default_cost_center=None
	):

		if not warehouse_account:
			warehouse_account = get_warehouse_account_map(self.company)

		sle_map = self.get_stock_ledger_details()
		voucher_details = self.get_voucher_details(default_expense_account, default_cost_center, sle_map)

		gl_list = []
		warehouse_with_no_account = []
		precision = self.get_debit_field_precision()
		for item_row in voucher_details:
			sle_list = sle_map.get(item_row.name)
			sle_rounding_diff = 0.0
			if sle_list:
				for sle in sle_list:
					if warehouse_account.get(sle.warehouse):
						# from warehouse account

						sle_rounding_diff += flt(sle.stock_value_difference)

						self.check_expense_account(item_row)

						# expense account/ target_warehouse / source_warehouse
						if item_row.get("target_warehouse"):
							warehouse = item_row.get("target_warehouse")
							expense_account = warehouse_account[warehouse]["account"]
						else:
							expense_account = item_row.expense_account

						gl_list.append(
							self.get_gl_dict(
								{
									"account": warehouse_account[sle.warehouse]["account"],
									"against": expense_account,
									"cost_center": item_row.cost_center,
									# "project": item_row.project or self.get("project"),
									"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
									"debit": flt(sle.stock_value_difference, precision),
									"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
								},
								warehouse_account[sle.warehouse]["account_currency"],
								item=item_row,
							)
						)

						gl_list.append(
							self.get_gl_dict(
								{
									"account": expense_account,
									"against": warehouse_account[sle.warehouse]["account"],
									"cost_center": item_row.cost_center,
									"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
									"debit": -1 * flt(sle.stock_value_difference, precision),
									# "project": item_row.get("project") or self.get("project"),
									"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
								},
								item=item_row,
							)
						)
					elif sle.warehouse not in warehouse_with_no_account:
						warehouse_with_no_account.append(sle.warehouse)

			if abs(sle_rounding_diff) > (1.0 / (10**precision)) and self.is_internal_transfer():
				warehouse_asset_account = ""
				if self.get("is_internal_customer"):
					warehouse_asset_account = warehouse_account[item_row.get("target_warehouse")]["account"]
				elif self.get("is_internal_supplier"):
					warehouse_asset_account = warehouse_account[item_row.get("warehouse")]["account"]

				expense_account = frappe.db.get_value("Company", self.company, "default_expense_account")

				gl_list.append(
					self.get_gl_dict(
						{
							"account": expense_account,
							"against": warehouse_asset_account,
							"cost_center": item_row.cost_center,
							"project": item_row.project or self.get("project"),
							"remarks": _("Rounding gain/loss Entry for Stock Transfer"),
							"debit": sle_rounding_diff,
							"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
						},
						warehouse_account[sle.warehouse]["account_currency"],
						item=item_row,
					)
				)

				gl_list.append(
					self.get_gl_dict(
						{
							"account": warehouse_asset_account,
							"against": expense_account,
							"cost_center": item_row.cost_center,
							"remarks": _("Rounding gain/loss Entry for Stock Transfer"),
							"credit": sle_rounding_diff,
							"project": item_row.get("project") or self.get("project"),
							"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
						},
						item=item_row,
					)
				)

		if warehouse_with_no_account:
			for wh in warehouse_with_no_account:
				if frappe.db.get_value("Warehouse", wh, "company"):
					frappe.throw(
						_(
							"Warehouse {0} is not linked to any account, please mention the account in the warehouse record or set default inventory account in company {1}."
						).format(wh, self.company)
					)

		return process_gl_map(gl_list, precision=precision)

	def make_gl_entries(self, gl_entries=None, from_repost=False):
		from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

		auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)
		if not gl_entries:
			gl_entries = self.get_gl_entries()

		if gl_entries:
			# if POS and amount is written off, updating outstanding amt after posting all gl entries
			update_outstanding = (
				"Yes"
			)

			if self.docstatus == 1:
				make_gl_entries(
					gl_entries,
					update_outstanding=update_outstanding,
					merge_entries=False,
					from_repost=from_repost,
				)
			elif self.docstatus == 2:
				make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

			if update_outstanding == "No":
				from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt

				update_outstanding_amt(
					self.debit_to,
					"Customer",
					self.customer,
					self.doctype,
					self.return_against if cint(self.is_return) and self.return_against else self.name,
				)

		elif self.docstatus == 2 and cint(self.update_stock) and cint(auto_accounting_for_stock):
			make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

