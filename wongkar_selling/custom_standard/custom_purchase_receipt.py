import frappe
from frappe import _
from frappe.utils import cint, flt
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt,get_item_account_wise_additional_cost

import erpnext
from erpnext.accounts.utils import get_account_currency

class PurchaseReceiptCustom(PurchaseReceipt):
	def cek_item_saprepart(self,item_code):
		item_group = frappe.get_doc('Item',item_code).item_group
		if item_group in ['H3 - Sparepart','HGA','Oli','Sparepart','Tools']:
			print(item_group, ' cek_igxxx2321323')
			return True
		else:
			return False
			
	def make_item_gl_entries(self, gl_entries, warehouse_account=None):
		if erpnext.is_perpetual_inventory_enabled(self.company):
			stock_rbnb = self.get_company_default("stock_received_but_not_billed")
			landed_cost_entries = get_item_account_wise_additional_cost(self.name)
			expenses_included_in_valuation = self.get_company_default("expenses_included_in_valuation")

		warehouse_with_no_account = []
		stock_items = self.get_stock_items()
		provisional_accounting_for_non_stock_items = cint(
			frappe.db.get_value(
				"Company", self.company, "enable_provisional_accounting_for_non_stock_items"
			)
		)

		for d in self.get("items"):
			cek_stock_rbnb = self.cek_item_saprepart(d.item_code)
			if cek_stock_rbnb:
				stock_rbnb = self.get_company_default("stock_received_but_not_billed_sparepart")
			
			print(stock_rbnb, ' stock_rbnbxxx')
			if d.item_code in stock_items and flt(d.valuation_rate) and flt(d.qty):
				if warehouse_account.get(d.warehouse):
					stock_value_diff = frappe.db.get_value(
						"Stock Ledger Entry",
						{
							"voucher_type": "Purchase Receipt",
							"voucher_no": self.name,
							"voucher_detail_no": d.name,
							"warehouse": d.warehouse,
							"is_cancelled": 0,
						},
						"stock_value_difference",
					)

					warehouse_account_name = warehouse_account[d.warehouse]["account"]
					warehouse_account_currency = warehouse_account[d.warehouse]["account_currency"]
					supplier_warehouse_account = warehouse_account.get(self.supplier_warehouse, {}).get("account")
					supplier_warehouse_account_currency = warehouse_account.get(self.supplier_warehouse, {}).get(
						"account_currency"
					)
					remarks = self.get("remarks") or _("Accounting Entry for Stock")

					# If PR is sub-contracted and fg item rate is zero
					# in that case if account for source and target warehouse are same,
					# then GL entries should not be posted
					if (
						flt(stock_value_diff) == flt(d.rm_supp_cost)
						and warehouse_account.get(self.supplier_warehouse)
						and warehouse_account_name == supplier_warehouse_account
					):
						continue

					self.add_gl_entry(
						gl_entries=gl_entries,
						account=warehouse_account_name,
						cost_center=d.cost_center,
						debit=stock_value_diff,
						credit=0.0,
						remarks=remarks,
						against_account=stock_rbnb,
						account_currency=warehouse_account_currency,
						item=d,
					)

					# GL Entry for from warehouse or Stock Received but not billed
					# Intentionally passed negative debit amount to avoid incorrect GL Entry validation
					credit_currency = (
						get_account_currency(warehouse_account[d.from_warehouse]["account"])
						if d.from_warehouse
						else get_account_currency(stock_rbnb)
					)

					credit_amount = (
						flt(d.base_net_amount, d.precision("base_net_amount"))
						if credit_currency == self.company_currency
						else flt(d.net_amount, d.precision("net_amount"))
					)

					outgoing_amount = d.base_net_amount
					if self.is_internal_transfer() and d.valuation_rate:
						outgoing_amount = abs(
							frappe.db.get_value(
								"Stock Ledger Entry",
								{
									"voucher_type": "Purchase Receipt",
									"voucher_no": self.name,
									"voucher_detail_no": d.name,
									"warehouse": d.from_warehouse,
									"is_cancelled": 0,
								},
								"stock_value_difference",
							)
						)
						credit_amount = outgoing_amount

					if credit_amount:
						account = warehouse_account[d.from_warehouse]["account"] if d.from_warehouse else stock_rbnb

						self.add_gl_entry(
							gl_entries=gl_entries,
							account=account,
							cost_center=d.cost_center,
							debit=-1 * flt(outgoing_amount, d.precision("base_net_amount")),
							credit=0.0,
							remarks=remarks,
							against_account=warehouse_account_name,
							debit_in_account_currency=-1 * credit_amount,
							account_currency=credit_currency,
							item=d,
						)

					# Amount added through landed-cos-voucher
					if d.landed_cost_voucher_amount and landed_cost_entries:
						for account, amount in iteritems(landed_cost_entries[(d.item_code, d.name)]):
							account_currency = get_account_currency(account)
							credit_amount = (
								flt(amount["base_amount"])
								if (amount["base_amount"] or account_currency != self.company_currency)
								else flt(amount["amount"])
							)

							self.add_gl_entry(
								gl_entries=gl_entries,
								account=account,
								cost_center=d.cost_center,
								debit=0.0,
								credit=credit_amount,
								remarks=remarks,
								against_account=warehouse_account_name,
								credit_in_account_currency=flt(amount["amount"]),
								account_currency=account_currency,
								project=d.project,
								item=d,
							)

					# sub-contracting warehouse
					if flt(d.rm_supp_cost) and warehouse_account.get(self.supplier_warehouse):
						self.add_gl_entry(
							gl_entries=gl_entries,
							account=supplier_warehouse_account,
							cost_center=d.cost_center,
							debit=0.0,
							credit=flt(d.rm_supp_cost),
							remarks=remarks,
							against_account=warehouse_account_name,
							account_currency=supplier_warehouse_account_currency,
							item=d,
						)

					# divisional loss adjustment
					valuation_amount_as_per_doc = (
						flt(outgoing_amount, d.precision("base_net_amount"))
						+ flt(d.landed_cost_voucher_amount)
						+ flt(d.rm_supp_cost)
						+ flt(d.item_tax_amount)
					)

					divisional_loss = flt(
						valuation_amount_as_per_doc - flt(stock_value_diff), d.precision("base_net_amount")
					)

					if divisional_loss:
						if self.is_return or flt(d.item_tax_amount):
							loss_account = expenses_included_in_valuation
						else:
							loss_account = (
								self.get_company_default("default_expense_account", ignore_validation=True) or stock_rbnb
							)

						cost_center = d.cost_center or frappe.get_cached_value(
							"Company", self.company, "cost_center"
						)

						self.add_gl_entry(
							gl_entries=gl_entries,
							account=loss_account,
							cost_center=cost_center,
							debit=divisional_loss,
							credit=0.0,
							remarks=remarks,
							against_account=warehouse_account_name,
							account_currency=credit_currency,
							project=d.project,
							item=d,
						)

				elif (
					d.warehouse not in warehouse_with_no_account
					or d.rejected_warehouse not in warehouse_with_no_account
				):
					warehouse_with_no_account.append(d.warehouse)
			elif (
				d.item_code not in stock_items
				and not d.is_fixed_asset
				and flt(d.qty)
				and provisional_accounting_for_non_stock_items
				and d.get("provisional_expense_account")
			):
				self.add_provisional_gl_entry(
					d, gl_entries, self.posting_date, d.get("provisional_expense_account")
				)

		if warehouse_with_no_account:
			frappe.msgprint(
				_("No accounting entries for the following warehouses")
				+ ": \n"
				+ "\n".join(warehouse_with_no_account)
			)