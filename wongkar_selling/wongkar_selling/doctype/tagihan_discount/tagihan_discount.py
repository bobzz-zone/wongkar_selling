# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.controllers.selling_controller import SellingController
from erpnext.controllers.accounts_controller import AccountsController, get_supplier_block_status
from erpnext.accounts.general_ledger import make_gl_entries
from datetime import date
import datetime
from erpnext.accounts.utils import get_fiscal_years, validate_fiscal_year, get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
import erpnext

class TagihanDiscount(Document):
	def before_cancel(self):
		# cek = frappe.db.sql(""" SELECT pe.name from `tabPayment Entry Reference` per 
		# 	join `tabPayment Entry` pe on pe.name = per.parent
		# 	where per.reference_name = '{}' and pe.docstatus != 2 GROUP by pe.name """.format(self.name),as_dict=1)
		
		cek = frappe.db.sql(""" SELECT fp.name from `tabList Doc Name` l 
			join `tabForm Pembayaran` fp on fp.name = l.parent
			where l.docname = '{}' and fp.docstatus != 2 GROUP by fp.name """.format(self.name),as_dict=1)
		
		if cek:
			frappe.throw("Tida Bisa Cancel karena terrhubung dengan Form Pembayaran "+cek[0]['name'])

	def hitung_pph(self):
		total = 0
		if self.cek_pph:
			for d in self.daftar_tagihan:
				rate = frappe.get_doc('Sales Taxes and Charges',{'parent':d.no_sinv,'idx':1}).rate
				tax = (100+rate ) / 100
				hitung_tax = d.nilai_diskon / tax
				pph = hitung_tax * self.pph / 100
				d.nilai = d.nilai_diskon - pph
				d.terbayarkan = d.nilai
				total += d.nilai
		else:
			for d in self.daftar_tagihan:
				d.nilai = d.nilai_diskon
				d.terbayarkan = d.nilai
				total += d.nilai

		self.grand_total = total
		self.base_grand_total = total
		self.outstanding_amount = total
			
	def set_status(self):
		if self.docstatus == 2:
			self.status = 'Cancelled'
		elif self.docstatus == 1:
			self.status = 'Submitted'
		else:
			self.status = 'Draft'

	def validate_account_currency(self, account, account_currency=None):
		currency = 'IDR'
		valid_currency = [currency]
		if self.get("currency") and currency != currency:
			valid_currency.append(currency)

		if account_currency not in valid_currency:
			frappe.throw(_("Account {0} is invalid. Account Currency must be {1}")
				.format(account, (' ' + _("or") + ' ').join(valid_currency)))

	def get_gl_dict(self, args, account_currency=None, item=None):
		"""this method populates the common properties of a gl entry record"""

		posting_date = args.get('date') or self.get('date')
		fiscal_years = get_fiscal_years(posting_date, company=self.company)
		if len(fiscal_years) > 1:
			frappe.throw(_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
				formatdate(posting_date)))
		else:
			fiscal_year = fiscal_years[0][0]

		gl_dict = frappe._dict({
			'company': self.company,
			'posting_date': self.date,
			'fiscal_year': fiscal_year,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			# 'remarks': self.get("remarks") or self.get("remark"),
			'debit': 0,
			'credit': 0,
			'debit_in_account_currency': 0,
			'credit_in_account_currency': 0,
			'is_opening': self.get("is_opening") or "No",
			'party_type': None,
			'party': None,
			'project': self.get("project")
		})

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

		if gl_dict.account and self.doctype not in ["Journal Entry",
			"Period Closing Voucher", "Payment Entry", "Purchase Receipt", "Purchase Invoice", "Stock Entry"]:
			self.validate_account_currency(gl_dict.account, account_currency)

		if gl_dict.account and self.doctype not in ["Journal Entry", "Period Closing Voucher", "Payment Entry"]:
			set_balance_in_account_currency(gl_dict, account_currency, self.get("conversion_rate"),
											"IDR")

		return gl_dict

	def make_gl_entries(self, gl_entries=None, from_repost=False,cancel=None):
		from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

		auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)
		if not gl_entries:
			gl_entries = self.get_gl_entries()

		if gl_entries:
			# if POS and amount is written off, updating outstanding amt after posting all gl entries
			update_outstanding = (
				"No"
			)

			if self.docstatus == 1:
				print(gl_entries, ' gl_entries')
				make_gl_entries(
					gl_entries,
					update_outstanding=update_outstanding,
					merge_entries=False,
					from_repost=from_repost,
				)
			elif self.docstatus == 2:
				make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	def get_gl_entries(self, warehouse_account=None):
		from erpnext.accounts.general_ledger import merge_similar_entries

		gl_entries = []

		self.make_gl_debit(gl_entries)
		self.make_gl_credit(gl_entries)
		self.make_gl_pendapatan(gl_entries)
		# self.make_tax_gl_entries(gl_entries)
		# self.make_pph_gl_entries(gl_entries)
		
		# merge gl entries before adding pos entries
		gl_entries = merge_similar_entries(gl_entries)

		return gl_entries

	def make_gl_pendapatan(self,gl_entries):
		for i in self.daftar_tagihan:
			data = frappe.db.sql(""" SELECT td.name,td.coa_receivable,td.coa_lawan,sipm.cost_center 
				from `tabTable Discount` td
				LEFT JOIN `tabSales Invoice Penjualan Motor` sipm on sipm.name = td.parent
				where td.parent='{}' and td.customer='{}' """.format(i.no_sinv,self.customer),as_dict=1)
			
			for d in data:
				gl_entries.append(
					self.get_gl_dict({
						"account": d.coa_lawan,
						# "party_type": "Customer",
						# "party": self.customer,
						"against": self.coa_pendapatan,
						"debit": i.nilai ,
						"debit_in_account_currency":  i.nilai,
						# "against_voucher": i.no_sinv,
						# "against_voucher_type": "Sales Invoice Penjualan Motor",
						"cost_center": d.cost_center
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)


			for d in data:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.coa_pendapatan,
						# "party_type": "Customer",
						# "party": self.customer,
						"against": d.coa_lawan,
						"credit":  i.nilai ,
						"credit_in_account_currency":  i.nilai,
						# "against_voucher": i.no_sinv,
						# "against_voucher_type": "Sales Invoice Penjualan Motor",
						"cost_center": d.cost_center
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)
		print(gl_entries, ' cost_center')

	def make_pph_gl_entries(self, gl_entries):
		
		for d in self.get('daftar_tagihan'):
			cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_sinv}, "cost_center")
			rate = frappe.get_doc('Sales Taxes and Charges',{'parent':d.no_sinv,'idx':1}).rate
			tax = (100+rate ) / 100
			hitung_tax = d.nilai_diskon / tax
			pph = hitung_tax * self.pph / 100
			pajak = hitung_tax - pph
			gl_entries.append(
				self.get_gl_dict({
					"account": self.pph_account,
					"against": self.customer,
					"debit": pph,
					"debit_in_account_currency": pph,
					"cost_center": cost_center,
					# "remarks": "coba Lutfi pajak!"
				}, item=None)
			)

	def make_tax_gl_entries(self, gl_entries):
		
		for d in self.get('daftar_tagihan'):
			cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_sinv}, "cost_center")
			rate = frappe.get_doc('Sales Taxes and Charges',{'parent':d.no_sinv,'idx':1}).rate
			tax = (100+rate ) / 100
			hitung_tax = d.nilai_diskon / tax
			net = d.nilai_diskon - hitung_tax
			gl_entries.append(
				self.get_gl_dict({
					"account": self.tax_account,
					"against": self.customer,
					"credit": net,
					"credit_in_account_currency": net,
					"against_voucher": d.no_sinv,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": cost_center,
					# "remarks": "coba Lutfi pajak!"
				}, item=None)
			)

	def make_gl_credit(self, gl_entries):
		# frappe.msgprint("MASuk make_gl_credit")
		# account = frappe.get_value("Rule",{"name" : self.customer_rule}, "coa_receivable")
		account = frappe.get_value("Rule",{"customer" : self.customer}, "coa_receivable")
		cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
		# cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
		data = frappe.db.sql(""" SELECT SUM(td.nominal) AS nilai,cost_center,sinv.debit_to,td.coa_receivable,td.coa_lawan,td.rule,td.parent as no_sinv FROM `tabDaftar Tagihan` cd
			JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_sinv` 
			JOIN `tabTable Discount` td on td.parent = sinv.name WHERE cd.parent = '{}' and td.customer = '{}' GROUP BY cost_center,td.customer """.format(self.name,self.customer),as_dict=1)

		for d in data:
			cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_sinv}, "cost_center")
			beban = frappe.get_doc("Rule",d.rule).coa_lawan
			against_income_account = set_against_income_account(d.no_sinv)
			rate = frappe.get_doc('Sales Taxes and Charges',{'parent':d.no_sinv,'idx':1}).rate
			tax = (100+rate ) / 100
			# hitung_tax = flt(d.nilai / tax,0)
			hitung_tax = d.nilai / tax
			net = d.nilai - hitung_tax
			gl_entries.append(
				self.get_gl_dict({
					"account": d.coa_receivable,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.coa_tagihan_discount,
					"credit": d.nilai,
					"credit_in_account_currency": d.nilai,
					"against_voucher": d.no_sinv,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					# "cost_center": d.cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)
		# frappe.msgprint(str(gl_entries))

	def make_gl_debit(self, gl_entries):
		account = frappe.get_value("Rule",{"customer" : self.customer}, "coa_receivable")
		cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
		
		data = frappe.db.sql(""" SELECT SUM(td.nominal) AS nilai,cost_center,sinv.debit_to,td.coa_receivable,td.rule,sinv.name as no_sinv  FROM `tabDaftar Tagihan` cd
			JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_sinv` 
			JOIN `tabTable Discount` td on td.parent = sinv.name WHERE cd.parent = '{}' and td.customer = '{}' GROUP BY cost_center,td.customer """.format(self.name,self.customer),as_dict=1)
		
		for d in data:
			# rate = frappe.get_doc('Sales Taxes and Charges',{'parent':d.no_sinv,'idx':1}).rate
			# tax = (100+rate ) / 100
			# hitung_tax = d.nilai / tax
			# pph = hitung_tax * self.pph /100
			# pajak = d.nilai - pph
			# pph = d.nilai * self.pph / 100
			pendapatan = frappe.get_doc("Rule",d.rule).coa_lawan
			gl_entries.append(
				self.get_gl_dict({
					"account": self.coa_tagihan_discount,
					"party_type": "Customer",
					"party": self.customer,
					"against": d.coa_receivable,
					"debit": d.nilai ,
					"debit_in_account_currency": d.nilai,
					"against_voucher": d.no_sinv,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					# "cost_center": d.cost_center
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)

	def get_serial_no(self):
		for i in self.daftar_tagihan:
			doc = frappe.get_doc("Serial No",i.no_rangka)
			row = doc.append('list_status_serial_no', {})
			row.list = "Tagihan Discount "+self.customer
			row.date = self.date
			row.ket = self.name
			doc.flags.ignore_permissions = True
			doc.save()

	def get_serial_no_cancel(self):
		for i in self.daftar_tagihan:
			# doc = frappe.get_doc("Serial No",i.no_rangka)
			frappe.db.sql(""" DELETE FROM `tabList Status Serial No` where parent='{}' and ket = '{}' """.format(i.no_rangka,self.name))
			# frappe.db.commit()

	def on_submit(self):
		# add_party_gl_entries_custom_tambah(self)
		# add_party_gl_entries_custom(self)
		# self.status = 'Submitted'
		self.make_gl_entries()
		data = frappe.db.get_list('Daftar Tagihan',filters={'parent': self.name},fields=['*'])
		for i in data:
			doc = frappe.get_doc('Table Discount',{'parent': i['no_sinv'],'customer': self.customer})
			doc.tertagih = 1
			doc.db_update()
			# frappe.db.commit()
			# frappe.msgprint('Berhasil !')
		self.set_status()

	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry')
		# self.ignore_linked_doctypes = ('GL Entry', 'Stock Ledger Entry')
		self.make_gl_entries(cancel=1)
		data = frappe.db.get_list('Daftar Tagihan',filters={'parent': self.name},fields=['*'])
		for i in data:
			doc = frappe.get_doc('Table Discount',{'parent': i['no_sinv'],'customer': self.customer})
			doc.tertagih = 0
			doc.db_update()
			# frappe.db.commit()
			# frappe.msgprint('Berhasil update !')
		self.set_status()
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(self.name,self.doctype))
		# frappe.db.commit()

	def on_trash(self):
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(self.name,self.doctype))

	def validate(self):
		self.set_status()
		self.hitung_pph()
		self.validasi_get()

	def validasi_get(self):
		for i in self.daftar_tagihan:
			cek = frappe.db.sql(""" SELECT a.name,b.no_sinv from `tabTagihan Discount` a 
				join `tabDaftar Tagihan` b on a.name = b.parent
				where b.no_sinv = '{}' and a.docstatus = 0 and a.customer = '{}' """.format(i.no_sinv,self.customer),as_dict=1)
			if cek:
				for c in cek:
					if c['name'] != self.name:
						frappe.throw("No Sinv "+c['no_sinv']+" Sudah ada di "+c['name']+" !")


def add_party_gl_entries_custom(self):
	# account = frappe.get_value("Rule",{"name" : self.customer_rule}, "coa_receivable")
	account = frappe.get_value("Rule",{"customer" : self.customer}, "coa_receivable")
	cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
	
	mydate= datetime.date.today()
	docgl = frappe.new_doc('GL Entry')
	docgl.posting_date = date.today()
	docgl.party_type = "Customer"
	docgl.party = self.customer
	docgl.account = account
	docgl.cost_center = cost_center
	docgl.credit = self.grand_total
	docgl.credit_in_account_currency = self.grand_total
	docgl.account_currency = "IDR"
	docgl.against = self.coa_tagihan_discount
	docgl.voucher_type = "Tagihan Discount"
	docgl.voucher_no = self.name
	docgl.remarks = "No Remarks"
	docgl.is_opening = "No"
	docgl.is_advance = "No"
	# docgl.company = "DAS"
	docgl.fiscal_year = mydate.year
	# docgl.due_date = due_date
	docgl.docstatus = 1
	docgl.flags.ignore_permission = True
	docgl.save()

def add_party_gl_entries_custom_tambah(self):
	# account = frappe.get_value("Rule",{"name" : self.customer_rule}, "coa_receivable")
	account = frappe.get_value("Rule",{"customer" : self.customer}, "coa_receivable")
	cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
	
	mydate= datetime.date.today()
	docgl = frappe.new_doc('GL Entry')
	docgl.posting_date = date.today()
	docgl.party_type = "Customer"
	docgl.party = self.customer
	docgl.account = self.coa_tagihan_discount
	docgl.cost_center = cost_center
	docgl.debit = self.grand_total
	docgl.debit_in_account_currency = self.grand_total
	docgl.against = self.customer
	docgl.account_currency = "IDR"
	docgl.voucher_type = "Tagihan Discount"
	docgl.voucher_no = self.name
	docgl.remarks = "No Remarks"
	docgl.is_opening = "No"
	docgl.is_advance = "No"
	# docgl.company = "DAS"
	docgl.fiscal_year = mydate.year
	# docgl.due_date = due_date
	docgl.docstatus = 1
	docgl.flags.ignore_permission = True
	docgl.save()

def set_balance_in_account_currency(gl_dict, account_currency=None, conversion_rate=None, company_currency=None):
	if (not conversion_rate) and (account_currency != company_currency):
		frappe.throw(_("Account: {0} with currency: {1} can not be selected")
					 .format(gl_dict.account, account_currency))

	gl_dict["account_currency"] = company_currency if account_currency == company_currency \
		else account_currency

	# set debit/credit in account currency if not provided
	if flt(gl_dict.debit) and not flt(gl_dict.debit_in_account_currency):
		gl_dict.debit_in_account_currency = gl_dict.debit if account_currency == company_currency \
			else flt(gl_dict.debit / conversion_rate, 2)

	if flt(gl_dict.credit) and not flt(gl_dict.credit_in_account_currency):
		gl_dict.credit_in_account_currency = gl_dict.credit if account_currency == company_currency \
			else flt(gl_dict.credit / conversion_rate, 2)

def set_against_income_account(name):
	"""Set against account for debit to account"""
	against_acc = []
	data = frappe.db.sql(""" SELECT * from `tabSales Invoice Penjualan Motor Item` sipm where parent = '{}'  """.format(name),as_dict=1) 

	for d in data:
		if d['income_account'] and d['income_account'] not in against_acc:
			against_acc.append(d['income_account'])

	against_income_account = ','.join(against_acc)

	return against_income_account


