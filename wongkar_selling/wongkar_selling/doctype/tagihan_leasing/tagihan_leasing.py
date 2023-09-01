# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_account_currency, get_fiscal_years, validate_fiscal_year
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from erpnext.controllers.accounts_controller import set_balance_in_account_currency
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate

class TagihanLeasing(Document):
	def on_submit(self):
		# frappe.throw("Submitted")
		self.add_tagihan()
		self.make_gl_entries()
		for i in self.list_tagihan_piutang_leasing:
			# doc = frappe.get_doc('Sales Invoice Penjualan Motor',{'name': i['no_invoice'],'nama_leasing': self.customer,'nama_promo': self.nama_promo})
			doc = frappe.get_doc('Sales Invoice Penjualan Motor',i.no_invoice) 
			doc.tertagih = 1
			doc.outstanding_amount = doc.outstanding_amount - i.tagihan_sipm
			doc.db_update()
			# frappe.db.commit()
			# frappe.msgprint('Berhasil !')
		self.set_status()
		

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

	def validate_account_currency(self, account, account_currency=None):
		currency = 'IDR'
		valid_currency = [currency]
		if self.get("currency") and currency != currency:
			valid_currency.append(currency)

		if account_currency not in valid_currency:
			frappe.throw(_("Account {0} is invalid. Account Currency must be {1}")
				.format(account, (' ' + _("or") + ' ').join(valid_currency)))

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
		

		for ds in self.get('list_tagihan_piutang_leasing'):
			print(ds.no_invoice, ' ds.no_invoice')
			# cost_center = frappe.get_value("Company",{"name" : ds.no_invoice}, "round_off_cost_center")
			cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "cost_center")
			account = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "debit_to")
			account_bpkb_stnk = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "coa_bpkb_stnk")
			advance = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "total_advance")
			harga = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : ds.no_invoice}, "harga")
			tot_biaya = frappe.db.sql(""" SELECT IFNULL(SUM(tbm.`amount`),0) AS total_biaya 
				FROM `tabTabel Biaya Motor` tbm 
				WHERE tbm.parent = '{}' AND tbm.`type` IN ('BPKB','STNK') """.format(ds.no_invoice),as_dict=1)
			rate = frappe.get_doc('Sales Taxes and Charges',{'parent':ds.no_invoice,'idx':1}).rate
			tax = (100+rate ) / 100
			nominal_diskon =  frappe.get_doc("Sales Invoice Penjualan Motor",ds.no_invoice).nominal_diskon
			nominal_diskon_setelah_pajak = 0
			if nominal_diskon != 0:
				nominal_diskon_setelah_pajak = flt(nominal_diskon / 1.11,0)	
			pajak_nominal_diskon = nominal_diskon - nominal_diskon_setelah_pajak
			print(pajak_nominal_diskon, " pajak_nominal_diskon")
			# piutang_motor = harga - tot_biaya[0]['total_biaya'] - advance - nominal_diskon_setelah_pajak
			piutang_motor = harga - tot_biaya[0]['total_biaya'] - advance - nominal_diskon_setelah_pajak - pajak_nominal_diskon


			gl_entries.append(
				self.get_gl_dict({
					"account": account,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.coa_lawan,
					"credit": piutang_motor,
					"credit_in_account_currency": piutang_motor,
					"against_voucher": ds.no_invoice,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)

			gl_entries.append(
				self.get_gl_dict({
					"account": account_bpkb_stnk,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": self.coa_lawan,
					"credit": tot_biaya[0]['total_biaya'],
					"credit_in_account_currency": tot_biaya[0]['total_biaya'],
					"against_voucher": ds.no_invoice,
					"against_voucher_type": "Sales Invoice Penjualan Motor",
					"cost_center": cost_center
					# "project": self.project,
					# "remarks": "coba Lutfi yyyyy!"
				}, item=None)
			)
		print(gl_entries, ' ds')


	def make_gl_debit(self, gl_entries):
		# frappe.msgprint("MASuk make_gl_debit")
		# account = frappe.get_list("Table Disc Leasing",{"parent" : self.leasing,'nama_leasing': self.customer},"*")
		cash = frappe.get_value("Company",{"name" : self.company}, "default_cash_account")
		

		data_sipm = frappe.db.sql(""" SELECT SUM(outstanding_sipm) AS outstanding_sipm,cost_center,sinv.debit_to,sinv.coa_bpkb_stnk,sinv.total_advance FROM `tabList Tagihan Piutang Leasing` cd
			JOIN `tabSales Invoice Penjualan Motor` sinv ON sinv.name = cd.`no_invoice` WHERE cd.parent = '{}' GROUP BY cost_center """.format(self.name),as_dict=1)

		
		for ds in data_sipm:
			# cost_center = frappe.get_value("Company",{"name" : self.company}, "round_off_cost_center")
			# cost_center = frappe.get_value("Sales Invoice Penjualan Motor",{"name" : d.no_invoice}, "cost_center")
			gl_entries.append(
				self.get_gl_dict({
					"account": self.coa_lawan,
					"party_type": "Customer",
					"party": self.customer,
					# "due_date": self.due_date,
					"against": ds.debit_to+' '+ds.coa_bpkb_stnk,
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

	def add_tagihan(self):
		for i in self.list_tagihan_piutang_leasing:
			frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set tanggal_tagih='{}',status='Billed' where name='{}' """.format(self.date,i.no_invoice))

	def set_status(self):
		if self.docstatus == 2:
			self.status = 'Cancelled'
		elif self.docstatus == 1:
			self.status = 'Submitted'
		else:
			self.status = 'Draft'

	def before_cancel(self):
		# cek = frappe.db.sql(""" SELECT pe.name from `tabPayment Entry Reference` per 
		# 	join `tabPayment Entry` pe on pe.name = per.parent
		# 	where per.reference_name = '{}' and pe.docstatus != 2 GROUP by pe.name """.format(self.name),as_dict=1)
		
		cek = frappe.db.sql(""" SELECT fp.name from `tabList Doc Name` l 
			join `tabForm Pembayaran` fp on fp.name = l.parent
			where l.docname = '{}' and fp.docstatus != 2 GROUP by fp.name """.format(self.name),as_dict=1)
		
		if cek:
			frappe.throw("Tida Bisa Cancel karena terrhubung dengan Form Pembayaran "+cek[0]['name'])
			
	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry')
		self.make_gl_entries(cancel=1)
		data = frappe.db.get_list('List Tagihan Piutang Leasing',filters={'parent': self.name},fields=['*'])
		for i in self.list_tagihan_piutang_leasing:
			# doc = frappe.get_doc('Sales Invoice Penjualan Motor',{'name': i['no_invoice'],'nama_leasing': self.customer,'nama_promo': self.nama_promo})
			doc = frappe.get_doc('Sales Invoice Penjualan Motor',i.no_invoice) 
			doc.tertagih = 0
			doc.outstanding_amount = doc.outstanding_amount + i.tagihan_sipm
			doc.db_update()
			frappe.db.commit()

			# frappe.msgprint('Berhasil update !')
		self.set_status()
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(self.name,self.doctype))
		frappe.db.commit()

	def validate(self):
		self.set_status()
		self.validasi_get()

	def validasi_get(self):
		for i in self.list_tagihan_piutang_leasing:
			cek = frappe.db.sql(""" SELECT a.name,b.no_invoice from `tabTagihan Leasing` a 
				join `tabList Tagihan Piutang Leasing` b on a.name = b.parent
				where b.no_invoice = '{}' and a.docstatus = 0 and a.customer = '{}' """.format(i.no_invoice,self.customer),as_dict=1)
			if cek:
				for c in cek:
					if c['name'] != self.name:
						frappe.throw("No Sinv "+c['no_invoice']+" Sudah ada di "+c['name']+" !")
