# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import date
import datetime
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
# from wongkar_selling.wongkar_selling.doctype.sales_invoice_penjualan_motor.sales_invoice_penjualan_motor import SalesInvoicePenjualanMotor
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.accounts.utils import get_account_currency

# ACC-SINV-2021-00017-8
def custom_get_gl_entries(self, warehouse_account=None):
	from erpnext.accounts.general_ledger import merge_similar_entries

	gl_entries = []

	make_customer_gl_entry_custom(self,gl_entries)
	# make_disc_gl_entry_custom(self,gl_entries)
	# make_disc_gl_entry_custom_leasing(self, gl_entries)
	# # make_sales_gl_entry_custom(self, gl_entries)
	# # make_vat_gl_entry_custom(self, gl_entries)
	# make_biaya_gl_entry_custom(self, gl_entries)
	# # make_utama_gl_entry_custom(self, gl_entries)
	# # make_disc_gl_entry_custom_credit(self,gl_entries)
	# # make_tax_gl_entries_custom(self, gl_entries)
	# make_adj_disc_gl_entry(self, gl_entries)

	self.make_tax_gl_entries(gl_entries)
	self.make_internal_transfer_gl_entries(gl_entries)

	self.make_item_gl_entries(gl_entries)

	# merge gl entries before adding pos entries
	gl_entries = merge_similar_entries(gl_entries)

	self.make_loyalty_point_redemption_gle(gl_entries)
	self.make_pos_gl_entries(gl_entries)
	self.make_gle_for_change_amount(gl_entries)

	self.make_write_off_gl_entry(gl_entries)
	self.make_gle_for_rounding_adjustment(gl_entries)

	return gl_entries

def make_customer_gl_entry_custom(self, gl_entries):
	# Checked both rounding_adjustment and rounded_total
	# because rounded_total had value even before introcution of posting GLE based on rounded total
	grand_total = self.rounded_total if (self.rounding_adjustment and self.rounded_total) else self.grand_total
	if grand_total:
		# Didnot use base_grand_total to book rounding loss gle
		grand_total_in_company_currency = flt(grand_total * self.conversion_rate,
			self.precision("grand_total"))

		gl_entries.append(
			self.get_gl_dict({
				"account": self.debit_to,
				"party_type": "Customer",
				"party": self.customer,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"debit": grand_total_in_company_currency,
				"debit_in_account_currency": grand_total_in_company_currency \
					if self.party_account_currency==self.company_currency else grand_total,
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi xxx!"
			}, self.party_account_currency, item=self)
		)

def make_disc_gl_entry_custom(self, gl_entries):
	for d in self.get('table_discount'):
		gl_entries.append(
			self.get_gl_dict({
				"account": d.coa_receivable,
				"party_type": "Customer",
				"party": d.customer,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"debit": d.nominal,
				"debit_in_account_currency": d.nominal,
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi yyyyy!"
			}, self.party_account_currency, item=self)
		)

def make_disc_gl_entry_custom_leasing(self, gl_entries):
	for d in self.get('table_discount_leasing'):
		gl_entries.append(
			self.get_gl_dict({
				"account": d.coa,
				"party_type": "Customer",
				"party": self.nama_leasing,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"debit": d.nominal,
				"debit_in_account_currency": d.nominal,
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi zzzzz!"
			}, self.party_account_currency, item=self)
		)

def make_vat_gl_entry_custom(self, gl_entries):
	for d in self.get('items'):
		gl_entries.append(
			self.get_gl_dict({
				"account": "1111.001 - Kas Kecil - DAS",
				"party_type": "Customer",
				"party": self.customer,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"credit": d.amount * 0.1,
				"credit_in_account_currency": d.amount * 0.1,
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi aaaaa!"
			}, self.party_account_currency, item=self)
		)

def make_sales_gl_entry_custom(self, gl_entries):
	for d in self.get('taxes'):
		gl_entries.append(
			self.get_gl_dict({
				"account": d.account_head,
				"party_type": "Customer",
				"party": self.customer,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"credit": d.total,
				"credit_in_account_currency": d.total,
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi bbbbbb!"
			}, self.party_account_currency, item=self)
		)

def make_biaya_gl_entry_custom(self, gl_entries):
	for d in self.get('tabel_biaya_motor'):
		gl_entries.append(
			self.get_gl_dict({
				"account": d.coa,
				"party_type": "Customer",
				"party": d.vendor,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"credit": d.amount ,
				"credit_in_account_currency": d.amount,
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi cccccc!"
			}, self.party_account_currency, item=self)
		)

def make_utama_gl_entry_custom(self, gl_entries):
	tot_disc = 0
	for d in self.get('table_discount'):
		tot_disc = tot_disc + d.nominal

	tot_discl = 0	
	for l in self.get('table_discount_leasing'):
		tot_discl = tot_discl + l.nominal
	
	gl_entries.append(
		self.get_gl_dict({
			"account": "1111.002 - Kas Besar - DAS",
			"party_type": "Customer",
			"party": self.nama_leasing,
			"due_date": self.due_date,
			"against": self.against_income_account,
			"debit": (self.harga-tot_disc-tot_discl)-self.grand_total,
			"debit_in_account_currency": (self.harga-tot_disc-tot_discl)-self.grand_total,
			"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
			"against_voucher_type": self.doctype,
			"cost_center": self.cost_center,
			"project": self.project,
			"remarks": "coba Lutfi ddddddd!"
		}, self.party_account_currency, item=self)
	)


def make_adj_disc_gl_entry(self, gl_entries):
	if self.account_adj_discount:
		test = str(self.adj_discount)
		if '-' in test:
			gl_entries.append(
			self.get_gl_dict({
				"account": self.account_adj_discount,
				"party_type": "Customer",
				"party": self.nama_leasing,
				"due_date": self.due_date,
				"against": self.against_income_account,
				"debit": abs(self.adj_discount),
				"debit_in_account_currency": abs(self.adj_discount),
				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
				"against_voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"project": self.project,
				"remarks": "coba Lutfi ffff!"
			}, self.party_account_currency, item=self)
		)
		else:
			gl_entries.append(
				self.get_gl_dict({
					"account": self.account_adj_discount,
					"party_type": "Customer",
					"party": self.nama_leasing,
					"due_date": self.due_date,
					"against": self.against_income_account,
					"credit": abs(self.adj_discount),
					"credit_in_account_currency": abs(self.adj_discount),
					"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"project": self.project,
					"remarks": "coba Lutfi ffff!"
				}, self.party_account_currency, item=self)
			)

# def make_disc_gl_entry_custom_credit(self, gl_entries):
# 	for d in self.get('table_discount'):
# 		gl_entries.append(
# 			self.get_gl_dict({
# 				"account": d.coa_expense,
# 				"party_type": "Customer",
# 				"party": d.customer,
# 				"due_date": self.due_date,
# 				"against": self.against_income_account,
# 				"credit": d.nominal,
# 				"credit_in_account_currency": d.nominal,
# 				"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
# 				"against_voucher_type": self.doctype,
# 				"cost_center": self.cost_center,
# 				"project": self.project,
# 				"remarks": "coba Lutfi !"
# 			}, self.party_account_currency, item=self)
# 		)

# def make_tax_gl_entries_custom(self, gl_entries):
# 	for tax in self.get("tabel_biaya_motor"):
# 		account_currency = get_account_currency(tax.account_head)
# 		gl_entries.append(
# 			self.get_gl_dict({
# 				"account": tax.account_head,
# 				"against": tax.vendor,
# 				"credit": tax.tax_amount,
# 				"credit_in_account_currency": tax.tax_amount,
# 				"cost_center": tax.cost_center
# 			}, account_currency, item=tax)
# 		)


@frappe.whitelist()
def overide_make_gl(self,method):
	frappe.msgprint("Masuk sini !")
	SalesInvoice.get_gl_entries = custom_get_gl_entries




# @frappe.whitelist()
# def get_disc(item_code,dp,tenor):
# 	# frappe.msgprint("masuk fungsi")
# 	data = frappe.db.get_list('Rule',filters={'item_code': item_code},fields=['*'])
# 	harga = frappe.get_value("Item Price",{"item_code": item_code}, "price_list_rate")
# 	nominal = float(harga)
# 	frappe.msgprint(str(data))
# 	disc=[]
# 	today = date.today()
# 	dm = 0.0
# 	dl = 0.0
# 	dd = 0.0
# 	dd = 0.0
# 	dmd = 0.0
# 	bs = 0.0
# 	bb = 0.0
# 	bg = 0.0
# 	cbj = ""
# 	cbb = ""
# 	cbg = ""

# 	for i in data:
# 		# amount
# 		if i ['discount'] == 'Amount':
# 			if i['type'] == 'Manufacture':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					frappe.msgprint("benar")
# 					dm = i['amount']
# 			if i['type'] == 'Leasing':
# 				if i['valid_from'] <= today and i['valid_to'] >= today and i['besar_dp'] == dp and i['tenor'] == tenor:
# 					dl = i['amount']
# 			if i['type'] == 'Dealer':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					dd = i['amount']
# 			if i['type'] == 'Main Dealer':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					dmd = i['amount']

# 		# Percent
# 		if i ['discount'] == 'Percent':
# 			if i['type'] == 'Manufacture':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					frappe.msgprint("benar")
# 					dm = i['percent'] * nominal / 100
# 			if i['type'] == 'Leasing':
# 				if i['valid_from'] <= today and i['valid_to'] >= today and i['besar_dp'] == dp and i['tenor'] == tenor:
# 					frappe.msgprint("percent"+str(i['percent']))
# 					dl = i['percent'] * nominal / 100
# 			if i['type'] == 'Dealer':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					dd = i['percent'] * nominal / 100
# 			if i['type'] == 'Main Dealer':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					dmd = i['percent'] * nominal / 100
# 		# Biaya
# 		if i['discount'] == "":
# 			if i['type'] == 'Biaya Penjualan Kendaraan':
# 				if i['valid_from'] <= today and i['valid_to'] >= today:
# 					biaya = frappe.db.get_list('Daftar Biaya',filters={'parent': i['name']},fields=['*'])
# 					for j in biaya:
# 						if j['jenis_biaya'] == 'BPKB':
# 							bs = j['nominal']
# 							cbj = j['coa']
# 						if j['jenis_biaya'] == 'STNK':
# 							bb = j['nominal']
# 							cbb = j['coa']
# 						if j['jenis_biaya'] == 'Gift':
# 							bg = j['nominal']
# 							cbg = j['coa']


# 	return dm,dd,dmd,dl,bs,bb,bg,harga,cbj,cbb,cbg
# 	# dl = frappe.get_value("Rule",{"item_code": item_code,"type": "Leasing"}, "amount")

# @frappe.whitelist()
# def buat_gl(doc,method):
# 	if doc.type_penjualan == "Penjualan Motor":
# 		cost_center = frappe.get_value("Sales Invoice Item",{"parent": doc.name}, "cost_center")
		
# 		if doc.nama_leasing:
# 			coa_receivable = frappe.get_value("Rule Discount Leasing",{"leasing": doc.nama_leasing,"nama_promo": doc.promo}, "coa_receivable")
# 			coa_expense = frappe.get_value("Rule Discount Leasing",{"leasing": doc.nama_leasing,"nama_promo": doc.promo}, "coa_expense")
# 			amount = frappe.get_value("Rule Discount Leasing",{"leasing": doc.nama_leasing,"nama_promo": doc.promo}, "amount")
# 			buat_gl2(coa_receivable,amount,0,amount,0,doc.customer,doc.name,cost_center,doc.due_date) # debit
# 			buat_gl2(coa_expense,0,amount,0,amount,doc.customer,doc.name,cost_center,doc.due_date) # kredit
		
# 		disc = frappe.db.get_list('Table Discount',filters={'parent': doc.name},fields=['*'])
# 		for i in disc:
# 			data = frappe.db.get_list('Rule',filters={'name': i['rule']},fields=['*'])
# 			for d in data:
# 				coa_receivable = frappe.get_value("Rule",{"name": d['name']}, "coa_receivable")
# 				coa_expense = frappe.get_value("Rule",{"name": d['name']}, "coa_expense")
# 				amount = frappe.get_value("Rule",{"name": d['name']}, "amount")
# 				buat_gl2(coa_receivable,amount,0,amount,0,doc.customer,doc.name,cost_center,doc.due_date) # debit
# 				buat_gl2(coa_expense,0,amount,0,amount,doc.customer,doc.name,cost_center,doc.due_date) # kredit
			
# @frappe.whitelist()
# def buat_gl2(akun,debit,kredit,debitcr,kreditcr,customer,name,cost_center,due_date):	
# 	mydate= datetime.date.today()
# 	docgl = frappe.new_doc('GL Entry')
# 	docgl.posting_date = date.today()
# 	docgl.party_type = "Customer"
# 	docgl.party = customer
# 	docgl.account = akun
# 	docgl.cost_center = cost_center
# 	docgl.debit = debit
# 	docgl.credit = kredit
# 	docgl.debit_in_account_currency = debitcr
# 	docgl.credit_in_account_currency = kreditcr
# 	docgl.against = "4110.000 - Penjualan - DAS"
# 	docgl.against_voucher_type = "Sales Invoice"
# 	docgl.against_voucher = name
# 	docgl.voucher_type = "Sales Invoice"
# 	docgl.voucher_no = name
# 	docgl.remarks = "No Remarks"
# 	docgl.is_opening = "No"
# 	docgl.is_advance = "No"
# 	# docgl.company = "DAS"
# 	docgl.fiscal_year = mydate.year
# 	docgl.due_date = due_date
# 	docgl.docstatus = 1
# 	docgl.flags.ignore_permission = True
# 	docgl.save()
# 	frappe.msgprint("buat GL akun berhasil !")

