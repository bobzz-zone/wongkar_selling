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
import erpnext

class PembayaranTagihanMotor(Document):
	def before_cancel(self):
		# cek = frappe.db.sql(""" SELECT pe.name from `tabPayment Entry Reference` per 
		# 	join `tabPayment Entry` pe on pe.name = per.parent
		# 	where per.reference_name = '{}' and pe.docstatus != 2 GROUP by pe.name """.format(self.name),as_dict=1)
		
		cek = frappe.db.sql(""" SELECT fp.name from `tabList Doc Name` l 
			join `tabForm Pembayaran` fp on fp.name = l.parent
			where l.docname = '{}' and fp.docstatus != 2 GROUP by fp.name """.format(self.name),as_dict=1)
		
		if cek:
			frappe.throw("Tida Bisa Cancel karena terrhubung dengan Form Pembayaran "+cek[0]['name'])
			
	def validasi_supplier(self):
		if self.type == "STNK dan BPKB":
			stnk = self.supplier_stnk.split("-")
			bpkb = self.supplier_bpkb.split("-")
			if stnk[1] not in bpkb[1]:
				frappe.throw("Supplier STNK dan BPKB TIdak Sama !")


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
			'remarks': self.get("remarks") or self.get("remark"),
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
		
		# merge gl entries before adding pos entries
		gl_entries = merge_similar_entries(gl_entries)

		return gl_entries

	def make_gl_debit(self, gl_entries):
		cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
		if self.type == "Diskon Dealer":
			for d in self.get('tagihan_biaya_motor'):
				account = frappe.get_value("Tabel Biaya Motor",{"parent" : d.no_invoice,'type': self.type}, "coa")
				cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
				gl_entries.append(
					self.get_gl_dict({
						"account": account,
						# "party_type": "Supplier",
						# "party": self.supplier,
						# "due_date": self.due_date,
						"against": self.coa_biaya_motor,
						"debit": d.nilai,
						"debit_in_account_currency": d.nilai,
						"against_voucher": d.no_invoice,
						"against_voucher_type": "Sales Invoice Penjualan Motor",
						# "cost_center": cost_center
						# "project": self.project,
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)
		elif self.type == "STNK dan BPKB":
			for d in self.get('tagihan_biaya_motor'):
				account = frappe.get_value("Tabel Biaya Motor",{"parent" : d.no_invoice,'type': "STNK"}, "coa")
				cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
				gl_entries.append(
					self.get_gl_dict({
						"account": account,
						# "party_type": "Supplier",
						# "party": self.supplier_stnk,
						# "due_date": self.due_date,
						"against": self.coa_biaya_motor_stnk,
						"debit": d.nilai_stnk,
						"debit_in_account_currency": d.nilai_stnk,
						"against_voucher": d.no_invoice,
						"against_voucher_type": "Sales Invoice Penjualan Motor",
						# "cost_center": cost_center
						# "project": self.project,
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)

				account = frappe.get_value("Tabel Biaya Motor",{"parent" : d.no_invoice,'type': "BPKB"}, "coa")
				gl_entries.append(
					self.get_gl_dict({
						"account": account,
						# "party_type": "Supplier",
						# "party": self.supplier_bpkb,
						# "due_date": self.due_date,
						"against": self.coa_biaya_motor_bpkb,
						"debit": d.nilai_bpkb,
						"debit_in_account_currency": d.nilai_bpkb,
						"against_voucher": d.no_invoice,
						"against_voucher_type": "Sales Invoice Penjualan Motor",
						# "cost_center": cost_center
						# "project": self.project,
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)

			# for d in self.get('tagihan_biaya_motor'):
			# 	account = frappe.get_value("Tabel Biaya Motor",{"parent" : d.no_invoice,'type': "BPKB"}, "coa")
			# 	cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
			# 	gl_entries.append(
			# 		self.get_gl_dict({
			# 			"account": account,
			# 			"party_type": "Supplier",
			# 			"party": self.supplier_bpkb,
			# 			# "due_date": self.due_date,
			# 			"against": self.coa_biaya_motor_bpkb,
			# 			"debit": d.nilai_bpkb,
			# 			"debit_in_account_currency": d.nilai_bpkb,
			# 			"against_voucher": d.no_invoice,
			# 			"against_voucher_type": "Sales Invoice Penjualan Motor",
			# 			"cost_center": cost_center
			# 			# "project": self.project,
			# 			# "remarks": "coba Lutfi yyyyy!"
			# 		}, item=None)
			# 	)
		
	def make_gl_credit(self, gl_entries):
		# frappe.msgprint("MASuk make_gl_debit")
		if self.type == "Diskon Dealer":
			account = frappe.get_value("Rule Biaya",{"name" : self.vendor}, "coa")
			cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
			data = frappe.db.sql(""" SELECT SUM(nilai) AS nilai,cost_center FROM `tabChild Tagihan Biaya Motor` cd
				JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_invoice` WHERE cd.parent = '{}' GROUP BY cost_center """.format(self.name),as_dict=1)
			
			for d in data:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.coa_biaya_motor,
						"party_type": "Supplier",
						"party": self.supplier,
						# "due_date": self.due_date,
						"against": self.supplier,
						"credit": d.nilai,
						"credit_in_account_currency": d.nilai,
						# "against_voucher": d.no_sinv,
						# "against_voucher_type": "Sales Invoice Penjualan Motor",
						# "cost_center": d.cost_center
						# "project": self.project,
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)
		elif self.type == "STNK dan BPKB":
			account = frappe.get_value("Rule Biaya",{"name" : self.vendor}, "coa")
			cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
			data_stnk = frappe.db.sql(""" SELECT SUM(nilai_stnk) AS nilai,cost_center FROM `tabChild Tagihan Biaya Motor` cd
				JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_invoice` WHERE cd.parent = '{}' GROUP BY cost_center """.format(self.name),as_dict=1)
			
			for d in data_stnk:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.coa_biaya_motor_stnk,
						"party_type": "Supplier",
						"party": self.supplier_stnk,
						# "due_date": self.due_date,
						"against": self.supplier_stnk,
						"credit": d.nilai,
						"credit_in_account_currency": d.nilai,
						# "against_voucher": d.no_sinv,
						# "against_voucher_type": "Sales Invoice Penjualan Motor",
						# "cost_center": d.cost_center
						# "project": self.project,
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)

			data_bpkb = frappe.db.sql(""" SELECT SUM(nilai_bpkb) AS nilai,cost_center FROM `tabChild Tagihan Biaya Motor` cd
				JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_invoice` WHERE cd.parent = '{}' GROUP BY cost_center """.format(self.name),as_dict=1)
			
			for d in data_bpkb:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.coa_biaya_motor_bpkb,
						"party_type": "Supplier",
						"party": self.supplier_bpkb,
						# "due_date": self.due_date,
						"against": self.supplier_bpkb,
						"credit": d.nilai,
						"credit_in_account_currency": d.nilai,
						# "against_voucher": d.no_sinv,
						# "against_voucher_type": "Sales Invoice Penjualan Motor",
						# "cost_center": d.cost_center
						# "project": self.project,
						# "remarks": "coba Lutfi yyyyy!"
					}, item=None)
				)

	def get_serial_no(self):
		for i in self.tagihan_biaya_motor:
			doc = frappe.get_doc("Serial No",i.no_rangka)

			row = doc.append('list_status_serial_no', {})
			row.list = "Tagihan "+self.type
			row.date = self.date
			row.ket = self.name
			doc.flags.ignore_permissions = True
			print(doc.name)
			doc.save()

	def get_serial_no_cancel(self):
		for i in self.tagihan_biaya_motor:
			# doc = frappe.get_doc("Serial No",i.no_rangka)
			frappe.db.sql(""" DELETE FROM `tabList Status Serial No` where parent='{}' and ket = '{}' """.format(i.no_rangka,self.name))
			frappe.db.commit()

	def on_submit(self):
		self.get_serial_no()
		self.make_gl_entries()
		if self.type == "Diskon Dealer":
			data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': self.name,'type': self.type},fields=['*'])
			for i in data:
				doc = frappe.get_doc('Tabel Biaya Motor',{'parent': i['no_invoice'],'vendor': self.supplier,'type': self.type})
				doc.tertagih = 1
				doc.db_update()
				frappe.db.commit()
		elif self.type == "STNK dan BPKB":
			# data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': self.name,'type': self.type},fields=['*'])
			for i in self.tagihan_biaya_motor:
				frappe.db.sql(""" UPDATE `tabTabel Biaya Motor` set tertagih = 1 
					where parent = '{}' and (type = 'STNK' or type = "BPKB") 
					and (vendor = '{}' or vendor = '{}') """.format(i.no_invoice,self.supplier_stnk,self.supplier_bpkb))
				frappe.db.commit()
		self.set_status()

	def on_cancel(self):
		self.get_serial_no_cancel()
		self.ignore_linked_doctypes = ('GL Entry')
		self.make_gl_entries(cancel=1)
		if self.type == "Diskon Dealer":
			data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': self.name,'type': self.type},fields=['*'])
			for i in data:
				doc = frappe.get_doc('Tabel Biaya Motor',{'parent': i['no_invoice'],'vendor': self.supplier,'type': self.type})
				doc.tertagih = 0
				doc.db_update()
				frappe.db.commit()
				# frappe.msgprint('Berhasil !')
		elif self.type == "STNK dan BPKB":
			# data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': self.name,'type': self.type},fields=['*'])
			for i in self.tagihan_biaya_motor:
				frappe.db.sql(""" UPDATE `tabTabel Biaya Motor` set tertagih = 0 
					where parent = '{}' and (type = 'STNK' or type = "BPKB") 
					and (vendor = '{}' or vendor = '{}') """.format(i.no_invoice,self.supplier_stnk,self.supplier_bpkb))
				frappe.db.commit()
		
		self.set_status()
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(self.name,self.doctype))
		frappe.db.commit()

	def validate(self):
		self.set_status()
		self.validasi_supplier()
		self.validasi_get()

	def validasi_get(self):
		for i in self.tagihan_biaya_motor:
			cek = frappe.db.sql(""" SELECT a.name,b.no_invoice from `tabPembayaran Tagihan Motor` a 
				join `tabChild Tagihan Biaya Motor` b on a.name = b.parent
				where b.no_invoice = '{}' and a.docstatus = 0 and a.supplier_stnk = '{}' and a.supplier_bpkb = '{}' """.format(i.no_invoice,self.supplier_stnk,self.supplier_bpkb),as_dict=1)
			if cek:
				for c in cek:
					if c['name'] != self.name:
						frappe.throw("No Sinv "+c['no_invoice']+" Sudah ada di "+c['name']+" !")


@frappe.whitelist()
def repair_gl_entry_tagihan_motor(doctype,docname):
	docu = frappe.get_doc(doctype, docname)
	print(docu.name)
	delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(docname,doctype))
	frappe.db.commit()
	docu.make_gl_entries()
	


def add_party_gl_entries_custom(self):
	account = frappe.get_value("Rule Biaya",{"name" : self.vendor}, "coa")
	cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
	
	mydate= datetime.date.today()
	docgl = frappe.new_doc('GL Entry')
	docgl.posting_date = date.today()
	docgl.party_type = "Supplier"
	docgl.party = self.supplier
	docgl.account = account
	docgl.cost_center = cost_center
	docgl.debit = self.grand_total
	docgl.debit_in_account_currency = self.grand_total
	docgl.account_currency = "IDR"
	docgl.against = self.coa_biaya_motor
	docgl.voucher_type = "Pembayaran Tagihan Motor"
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
	account = frappe.get_value("Rule Biaya",{"name" : self.vendor}, "coa")
	cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
	
	mydate= datetime.date.today()
	docgl = frappe.new_doc('GL Entry')
	docgl.posting_date = date.today()
	docgl.party_type = "Supplier"
	docgl.party = self.supplier
	docgl.account = self.coa_biaya_motor
	docgl.cost_center = cost_center
	docgl.credit = self.grand_total
	docgl.credit_in_account_currency = self.grand_total
	docgl.against = self.supplier
	docgl.account_currency = "IDR"
	docgl.voucher_type = "Pembayaran Tagihan Motor"
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

			