# Copyright (c) 2024, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import erpnext
from frappe.utils import add_days, cint, cstr, flt, formatdate, get_link_to_form, getdate, nowdate
from erpnext.accounts.utils import get_account_currency, get_fiscal_years, validate_fiscal_year
from frappe import _
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from erpnext.controllers.accounts_controller import set_balance_in_account_currency

class InvoicePenagihanGaransi(Document):
	def hitung_total(self):
		if self.list_invoice_penagihan_garansi and len(self.list_invoice_penagihan_garansi) >0:
			total = 0
			for i in self.list_invoice_penagihan_garansi:
				total += i.grand_total

			self.grand_total = total
			self.outstanding_amount = self.grand_total
		if not self.customer or self.customer == '':
			self.customer = frappe.get_doc("Company",self.company).customer
			self.customer_name = frappe.get_doc("Company",self.company).customer_name

	def validate(self):
		self.hitung_total()

	def update_tagihan(self):
		for i in self.list_invoice_penagihan_garansi:
			cek = frappe.get_doc("Sales Invoice Sparepart Garansi",i.sales_invoice_sparepart_garansi)
			if self.docstatus == 1:
				if cek.docstatus == 1:
					if cek.tagihan == 1:
						frappe.throw("Sudah ada Tagihannya")
					else:
						frappe.db.sql(""" UPDATE `tabSales Invoice Sparepart Garansi` set tagihan = 1 where name = '{}' """.format(i.sales_invoice_sparepart_garansi))
				else:
					frappe.throw("Cek dokumen !")
			elif self.docstatus == 2:
				if cek.docstatus == 1:
					frappe.db.sql(""" UPDATE `tabSales Invoice Sparepart Garansi` set tagihan = 0 where name = '{}' """.format(i.sales_invoice_sparepart_garansi))
				else:
					frappe.throw("Cek dokumen !")
				

	def on_submit(self):
		self.make_gl_entries()
		self.update_tagihan()

	def on_cancel(self):
		self.make_gl_entries_on_cancel()
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Repost Item Valuation")
		self.update_tagihan()

	def on_trash(self):
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_type = '{}' and voucher_no = "{}" """.format(self.doctype,self.name))

	def make_gl_entries_on_cancel(self):
		if frappe.db.sql(
			"""select name from `tabGL Entry` where voucher_type=%s
			and voucher_no=%s""",
			(self.doctype, self.name),
		):
			self.make_gl_entries()

	def get_gl_dict(self, args, account_currency=None, item=None):
		"""this method populates the common properties of a gl entry record"""

		posting_date = args.get("posting_date") or self.get("posting_date")
		fiscal_years = get_fiscal_years(posting_date, company=self.company)
		if len(fiscal_years) > 1:
			frappe.throw(
				_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
					formatdate(posting_date)
				)
			)
		else:
			fiscal_year = fiscal_years[0][0]

		gl_dict = frappe._dict(
			{
				"company": self.company,
				"posting_date": posting_date,
				"fiscal_year": fiscal_year,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"remarks": self.get("remarks") or self.get("remark"),
				"debit": 0,
				"credit": 0,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": 0,
				"is_opening": self.get("is_opening") or "No",
				"party_type": None,
				"party": None,
				"project": self.get("project"),
				"post_net_value": args.get("post_net_value"),
			}
		)

		accounting_dimensions = get_accounting_dimensions()
		dimension_dict = frappe._dict()

		for dimension in accounting_dimensions:
			dimension_dict[dimension] = self.get(dimension)
			if item and item.get(dimension):
				dimension_dict[dimension] = item.get(dimension)

		gl_dict.update(dimension_dict)
		gl_dict.update(args)

		if not account_currency:
			account_currency = get_account_currency(gl_dict.account)

		if gl_dict.account and self.doctype not in [
			"Journal Entry",
			"Period Closing Voucher",
			"Payment Entry",
			"Purchase Receipt",
			"Purchase Invoice",
			"Stock Entry",
		]:
			self.validate_account_currency(gl_dict.account, account_currency)

		if gl_dict.account and self.doctype not in [
			"Journal Entry",
			"Period Closing Voucher",
			"Payment Entry",
		]:
			set_balance_in_account_currency(
				gl_dict, account_currency, self.get("conversion_rate"), 'IDR'
			)

		return gl_dict

	def validate_account_currency(self, account, account_currency=None):
		valid_currency = ['IDR']
		if self.get("currency") and self.currency != self.company_currency:
			valid_currency.append(self.currency)

		if account_currency not in valid_currency:
			frappe.throw(
				_("Account {0} is invalid. Account Currency must be {1}").format(
					account, (" " + _("or") + " ").join(valid_currency)
				)
			)

	def get_gl_entries(self, warehouse_account=None):
		from erpnext.accounts.general_ledger import merge_similar_entries

		gl_entries = []

		self.make_customer_gl_entry(gl_entries)
		self.make_item_gl_entries(gl_entries)
		self.make_tax_gl_entries(gl_entries)
		self.make_income_entries(gl_entries)
		
		# merge gl entries before adding pos entries
		gl_entries = merge_similar_entries(gl_entries)

		# frappe.msgprint(str(gl_entries))
		return gl_entries

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

	def make_customer_gl_entry(self, gl_entries):
		# Checked both rounding_adjustment and rounded_total
		# because rounded_total had value even before introcution of posting GLE based on rounded total
		grand_total = (self.grand_total)

		base_grand_total = flt(self.grand_total,self.precision("grand_total"),)

		if grand_total:
			# Did not use base_grand_total to book rounding loss gle
			for i in self.list_invoice_penagihan_garansi:
				sp = frappe.get_doc("Sales Invoice Sparepart Garansi",i.sales_invoice_sparepart_garansi)
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": self.debit_to,
							"party_type": "Customer",
							"party": self.customer,
							# "due_date": self.due_date,
							"against": sp.debit_to,
							"debit": sp.grand_total,
							"debit_in_account_currency": sp.grand_total
							if "IDR" == "IDR"
							else sp.grand_total,
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							# "cost_center": sp.cost_center,
							# "project": self.project,
						},
						'IDR',
						item=self.list_invoice_penagihan_garansi,
					)
				)

	def make_tax_gl_entries(self, gl_entries):
		# pjk = self.grand_total / ((100+self.rate)/100)
		# akhir = self.grand_total - pjk
		# amount = akhir
		# base_amount = akhir

		account_currency = 'IDR'
		for i in self.list_invoice_penagihan_garansi:
			sp = frappe.get_doc("Sales Invoice Sparepart Garansi",i.sales_invoice_sparepart_garansi)
			pjk = i.grand_total / ((100+self.rate)/100)
			akhir = i.grand_total - pjk
			amount = akhir
			base_amount = akhir
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
						"cost_center": sp.cost_center,
					},
					account_currency,
					item=self,
				)
			)


	def make_income_entries(self, gl_entries):
		# pjk = self.grand_total / ((100+self.rate)/100)
		# akhir = self.grand_total - pjk
		# amount = akhir
		# base_amount = akhir

		account_currency = 'IDR'
		for i in self.list_invoice_penagihan_garansi:
			sp = frappe.get_doc("Sales Invoice Sparepart Garansi",i.sales_invoice_sparepart_garansi)
			pjk = i.grand_total / ((100+self.rate)/100)
			akhir = i.grand_total - pjk
			amount = pjk
			base_amount = pjk
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.income,
						"against": self.customer,
						"credit": flt(base_amount, self.precision("grand_total")),
						"credit_in_account_currency": (
							flt(base_amount, self.precision("grand_total"))
							if account_currency == 'IDR'
							else flt(amount, self.precision("grand_total"))
						),
						"cost_center": sp.cost_center,
					},
					account_currency,
					item=self,
				)
			)

	def make_item_gl_entries(self, gl_entries):
		# income account gl entries
		for item in self.get("list_invoice_penagihan_garansi"):
			if flt(item.grand_total, item.precision("grand_total")):
				sp = frappe.get_doc("Sales Invoice Sparepart Garansi",item.sales_invoice_sparepart_garansi)
				# amount, base_amount = self.get_amount_and_base_amount(item, enable_discount_accounting=False)
				amount = item.grand_total
				base_amount = item.grand_total

				account_currency = get_account_currency(sp.debit_to)
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": sp.debit_to,
							# "party_type": "Customer",
							# "party": item.customer,
							"against": self.debit_to,
							"credit": flt(amount, item.precision("grand_total")),
							"credit_in_account_currency": (
								flt(amount, item.precision("grand_total"))
								if account_currency == 'IDR'
								else flt(amount, item.precision("grand_total"))
							),
							"against_voucher": sp.name,
							"against_voucher_type": sp.doctype,
							# "cost_center": sp.cost_center,
							# "project": item.project or self.project,
						},
						account_currency,
						item=self.list_invoice_penagihan_garansi,
					)
				)

				beban = frappe.db.sql(""" SELECT sum(amount) as total,income_account,cost_center 
					from `tabSales Invoice Sparepart Garansi Item` where parent = '{}' """.format(item.sales_invoice_sparepart_garansi),as_dict=1)
				
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": beban[0]['income_account'],
							# "party_type": "Customer",
							# "party": item.customer,
							"against": self.debit_to,
							"debit": flt(beban[0]['total'], item.precision("grand_total")),
							"debit_in_account_currency": (
								flt(beban[0]['total'], item.precision("grand_total"))
								if account_currency == 'IDR'
								else flt(beban[0]['total'], item.precision("grand_total"))
							),
							"against_voucher": sp.name,
							"against_voucher_type": sp.doctype,
							"cost_center": beban[0]['cost_center'],
							# "project": item.project or self.project,
						},
						account_currency,
						item=self.list_invoice_penagihan_garansi,
					)
				)

	def get_amount_and_base_amount(self, item, enable_discount_accounting):
		net_amount = item.grand_total / ((100+self.rate) / 100)
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


@frappe.whitelist()
def get_data(from_date,to_date):
	data = frappe.db.sql(""" SELECT 
		isg.name,isg.customer,isg.customer_name,
		isg.grand_total,isg.outstanding_amount,
		isg.no_rangka_manual_atau_lama, isg.no_mesin
		from `tabSales Invoice Sparepart Garansi` isg
		where isg.docstatus = 1 and isg.tagihan = 0 
		and isg.posting_date between '{}' and '{}' """.format(from_date,to_date),as_dict=1)

	return data