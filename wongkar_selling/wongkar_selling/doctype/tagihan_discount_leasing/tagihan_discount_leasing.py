# -*- coding: utf-8 -*-
# Copyright (c) 2021, w and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
import datetime
from erpnext.accounts.utils import get_fiscal_years, validate_fiscal_year, get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.accounts.general_ledger import make_gl_entries

class TagihanDiscountLeasing(Document):
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

	def make_gl_entries(self, cancel=0, adv_adj=0):
		# frappe.msgprint("MAsuk make_gl_entries")
		from erpnext.accounts.general_ledger import merge_similar_entries

		gl_entries = []
		self.make_gl_credit(gl_entries)
		self.make_gl_debit(gl_entries)
		# return gl_entries
		print(gl_entries, ' gl_entries')
		make_gl_entries(gl_entries, cancel=cancel, adv_adj=adv_adj)

	def make_gl_credit(self, gl_entries):
		# frappe.msgprint("MASuk make_gl_credit")
		cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
		# cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
		
		for d in self.get('daftar_tagihan_leasing'):
			print(d.no_invoice, " no_invoice")
			account = frappe.db.get_list('Table Disc Leasing',filters={'parent' : d.no_invoice,'nama_leasing': self.customer},fields=['*'])
			# account = frappe.db.sql(""" SELECT coa,sum(nominal),name,parent from `tabTable Disc Leasing` where parent='{}' and nama_leasing='{}' GROUP by nama_leasing,parent """.format(d.no_invoice,self.customer),as_dict=1)
			print(account, ' account')
			cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
			total = [0]
			for d2 in account:
				print( d2.name, d2.parent, ' d2')
				total.append(d2.nominal)
				# print(sum(total), " total")
			gl_entries.append(
				self.get_gl_dict({
					"account": d2.coa,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.coa_tagihan_discount_leasing,
					"credit": sum(total),
					"credit_in_account_currency": sum(total),
					"against_voucher": d.no_invoice,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)

		print(gl_entries, ' d')

		for ds in self.get('daftar_tagihan_leasing'):
			print(ds.no_invoice, ' ds.no_invoice')
			# cost_center = frappe.get_value("Company",{"name" : ds.no_invoice}, "round_off_cost_center")
			cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "cost_center")
			account = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "debit_to")
			gl_entries.append(
				self.get_gl_dict({
					"account": account,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.coa_tagihan_sipm,
					"credit": ds.outstanding_sipm,
					"credit_in_account_currency": ds.outstanding_sipm,
					"against_voucher": ds.no_invoice,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)
		# frappe.msgprint(str(gl_entries)+ " credit")
		print(gl_entries, ' ds')

	def make_gl_debit(self, gl_entries):
		# frappe.msgprint("MASuk make_gl_debit")
		account = frappe.get_list("Table Disc Leasing",{"parent" : self.leasing,'nama_leasing': self.customer},"*")
		cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
		
		data = frappe.db.sql(""" SELECT SUM(nilai) AS nilai,cost_center FROM `tabDaftar Tagihan Leasing` cd
			JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_invoice` WHERE cd.parent = '{}' GROUP BY cost_center """.format(self.name),as_dict=1)

		data_sipm = frappe.db.sql(""" SELECT SUM(outstanding_sipm) AS outstanding_sipm,cost_center FROM `tabDaftar Tagihan Leasing` cd
			JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_invoice` WHERE cd.parent = '{}' GROUP BY cost_center """.format(self.name),as_dict=1)

		# frappe.msgprint(str(data_sipm)+"data_sipm")
		
		for d in data:
			# cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
			# cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
			gl_entries.append(
				self.get_gl_dict({
					"account": self.coa_tagihan_discount_leasing,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.customer,
					"debit": d.nilai,
					"debit_in_account_currency": d.nilai,
					# "against_voucher": d.no_sinv,
					# "against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": d.cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)

		for ds in data_sipm:
			# cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
			# cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
			gl_entries.append(
				self.get_gl_dict({
					"account": self.coa_tagihan_sipm,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.customer,
					"debit": ds.outstanding_sipm,
					"debit_in_account_currency": ds.outstanding_sipm,
					# "against_voucher": d.no_sinv,
					# "against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": ds.cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)
		# frappe.msgprint(str(gl_entries)+ " debit")

		# cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
		# # for d in self.get('daftar_tagihan'):
		# gl_entries.append(
		# 	self.get_gl_dict({
		# 		"account": self.coa_tagihan_discount_leasing,
		# 		"party_type": "Customer",
		# 		"party": self.customer,
		# 		# "due_date": self.due_date,
		# 		"against": self.customer,
		# 		"debit": self.grand_total,
		# 		"debit_in_account_currency": self.grand_total,
		# 		# "against_voucher": d.no_sinv,
		# 		# "against_voucher_type": "Sales Invoice Penjualan Motor",
		# 		"cost_center": cost_center
		# 		# "project": self.project,
		# 		# "remarks": "coba Lutfi yyyyy!"
		# 	}, item=None)
		# )

		# frappe.msgprint(str(gl_entries))

	def get_serial_no(self):
		for i in self.daftar_tagihan_leasing:
			doc = frappe.get_doc("Serial No",i.no_rangka)
			row = doc.append('list_status_serial_no', {})
			row.list = "Tagihan Discount Leasing dan SIPM "
			row.date = self.date
			row.ket = self.name
			doc.flags.ignore_permissions = True
			doc.save()

	def get_serial_no_cancel(self):
		for i in self.daftar_tagihan_leasing:
			# doc = frappe.get_doc("Serial No",i.no_rangka)
			frappe.db.sql(""" DELETE FROM `tabList Status Serial No` where parent='{}' and ket = '{}' """.format(i.no_rangka,self.name))
			frappe.db.commit()

	def on_submit(self):
		# add_party_gl_entries_custom_tambah(self)
		# add_party_gl_entries_custom(self)
		self.make_gl_entries()
		# frappe.throw("jhasdbhjasbgd")
		data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': self.name},fields=['*'])
		for i in data:
			# doc = frappe.get_doc('Sales Invoice Penjualan Motor',{'name': i['no_invoice'],'nama_leasing': self.customer,'nama_promo': self.nama_promo})
			doc = frappe.get_doc('Table Disc Leasing',{'parent': i['no_invoice'],'nama_leasing': self.customer}) 
			
			doc.tertagih = 1
			doc.db_update()
			frappe.db.commit()
			# frappe.msgprint('Berhasil !')
		self.set_status()

	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry')
		self.make_gl_entries(cancel=1)
		data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': self.name},fields=['*'])
		for i in data:
			# doc = frappe.get_doc('Sales Invoice Penjualan Motor',{'name': i['no_invoice'],'nama_leasing': self.customer,'nama_promo': self.nama_promo})
			doc = frappe.get_doc('Table Disc Leasing',{'parent': i['no_invoice'],'nama_leasing': self.customer}) 
			doc.tertagih = 0
			doc.db_update()
			frappe.db.commit()
			# frappe.msgprint('Berhasil update !')
		self.set_status()
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(self.name,self.doctype))
		frappe.db.commit()

	def validate(self):
		self.set_status()


def add_party_gl_entries_custom(self):
	account = frappe.get_list("Table Discount Leasing",{"parent" : self.leasing},"coa")
	cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
	for d in account:
		mydate= datetime.date.today()
		docgl = frappe.new_doc('GL Entry')
		docgl.posting_date = date.today()
		docgl.party_type = "Customer"
		docgl.party = self.customer
		docgl.account = d.coa
		docgl.cost_center = cost_center
		docgl.credit = self.grand_total
		docgl.credit_in_account_currency = self.grand_total
		docgl.account_currency = "IDR"
		docgl.against = self.coa_tagihan_discount_leasing
		docgl.voucher_type = "Tagihan Discount Leasing"
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
	account = frappe.get_list("Table Discount Leasing",{"parent" : self.leasing},"coa")
	cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
	for d in account:
		mydate= datetime.date.today()
		docgl = frappe.new_doc('GL Entry')
		docgl.posting_date = date.today()
		docgl.party_type = "Customer"
		docgl.party = self.customer
		docgl.account = self.coa_tagihan_discount_leasing
		docgl.cost_center = cost_center
		docgl.debit = self.grand_total
		docgl.debit_in_account_currency = self.grand_total
		docgl.against = self.customer
		docgl.account_currency = "IDR"
		docgl.voucher_type = "Tagihan Discount Leasing"
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