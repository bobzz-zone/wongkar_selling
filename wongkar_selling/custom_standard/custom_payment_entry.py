# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import date
import datetime
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.invoice_discounting.invoice_discounting import get_party_account_based_on_invoice_discounting
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
from frappe import _, scrub, ValidationError
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account, get_bank_account_details
from erpnext.accounts.utils import get_outstanding_invoices, get_account_currency, get_balance_on
import frappe, erpnext, json
from six import string_types, iteritems
from erpnext.setup.utils import get_exchange_rate

# ACC-SINV-2021-00017-8
def custom_get_gl_entries(self, warehouse_account=None):
	from erpnext.accounts.general_ledger import merge_similar_entries

	gl_entries = []

	make_customer_gl_entry_custom(self,gl_entries)
	make_disc_gl_entry_custom(self,gl_entries)
	make_disc_gl_entry_custom_leasing(self, gl_entries)
	# make_sales_gl_entry_custom(self, gl_entries)
	# make_vat_gl_entry_custom(self, gl_entries)
	make_biaya_gl_entry_custom(self, gl_entries)
	# make_utama_gl_entry_custom(self, gl_entries)
	# make_disc_gl_entry_custom_credit(self,gl_entries)f
	# make_tax_gl_entries_custom(self, gl_entries)
	make_adj_disc_gl_entry(self, gl_entries)

	self.make_tax_gl_entries(gl_entries)
	self.make_internal_transfer_gl_entries(gl_entries)

	make_item_gl_entries(self,gl_entries)

	# merge gl entries before adding pos entries
	gl_entries = merge_similar_entries(gl_entries)

	self.make_loyalty_point_redemption_gle(gl_entries)
	self.make_pos_gl_entries(gl_entries)
	self.make_gle_for_change_amount(gl_entries)

	self.make_write_off_gl_entry(gl_entries)
	self.make_gle_for_rounding_adjustment(gl_entries)

	return gl_entries

def make_customer_gl_entry_custom(self, gl_entries):
	tot_disc = 0
	for d in self.get('table_discount'):
		tot_disc = tot_disc + d.nominal

	tot_discl = 0	
	for l in self.get('table_discount_leasing'):
		tot_discl = tot_discl + l.nominal

	tot_biaya = 0	
	for b in self.get('tabel_biaya_motor'):
		tot_biaya = tot_biaya + b.amount

	gl_entries.append(
		self.get_gl_dict({
			"account": self.debit_to,
			"party_type": "Customer",
			"party": self.customer,
			"due_date": self.due_date,
			"against": self.against_income_account,
			"debit": ((self.grand_total + tot_biaya) - tot_disc - tot_discl) + self.adj_discount,
			"debit_in_account_currency": ((self.grand_total + tot_biaya) - tot_disc - tot_discl) + self.adj_discount,
			"against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
			"against_voucher_type": self.doctype,
			"cost_center": self.cost_center,
			"project": self.project,
			"remarks": "coba Lutfi xxxxx!"
		}, self.party_account_currency, item=self)
	)

def make_item_gl_entries(self, gl_entries):
	# income account gl entries
	for item in self.get("items"):
		if flt(item.base_net_amount, item.precision("base_net_amount")):
			if item.is_fixed_asset:
				asset = frappe.get_doc("Asset", item.asset)

				if (len(asset.finance_books) > 1 and not item.finance_book
					and asset.finance_books[0].finance_book):
					frappe.throw(_("Select finance book for the item {0} at row {1}")
						.format(item.item_code, item.idx))

				fixed_asset_gl_entries = get_gl_entries_on_asset_disposal(asset,
					item.base_net_amount, item.finance_book)

				for gle in fixed_asset_gl_entries:
					gle["against"] = self.customer
					gl_entries.append(self.get_gl_dict(gle, item=item))

				asset.db_set("disposal_date", self.posting_date)
				asset.set_status("Sold" if self.docstatus==1 else None)
			else:
				# Do not book income for transfer within same company
				if not self.is_internal_transfer():
					income_account = (item.income_account
						if (not item.enable_deferred_revenue or self.is_return) else item.deferred_revenue_account)

					account_currency = get_account_currency(income_account)
					gl_entries.append(
						self.get_gl_dict({
							"account": income_account,
							"against": self.customer,
							"credit": flt(item.base_net_amount, item.precision("base_net_amount")),
							"credit_in_account_currency": (flt(item.base_net_amount, item.precision("base_net_amount"))
								if account_currency==self.company_currency
								else flt(item.net_amount, item.precision("net_amount"))),
							"cost_center": item.cost_center,
							"project": item.project or self.project,
							"remarks": "coba Lutfi xxxxx 12345!"
						}, account_currency, item=item)
					)

	# expense account gl entries
	if cint(self.update_stock) and \
		erpnext.is_perpetual_inventory_enabled(self.company):
		gl_entries += super(SalesInvoice, self).get_gl_entries()

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
	if self.type_penjualan == "Penjualan Motor":
		SalesInvoice.get_gl_entries = custom_get_gl_entries



# pe 
def set_missing_values_custom(self):
	# frappe.msgprint("masuk sini set_missing_values_custom")
	if self.payment_type == "Internal Transfer":
		for field in ("party", "party_balance", "total_allocated_amount",
			"base_total_allocated_amount", "unallocated_amount"):
				self.set(field, None)
		self.references = []
	else:
		if not self.party_type:
			frappe.throw(_("Party Type is mandatory"))

		if not self.party:
			frappe.throw(_("Party is mandatory"))

		_party_name = "title" if self.party_type in ("Student", "Shareholder") else self.party_type.lower() + "_name"
		self.party_name = frappe.db.get_value(self.party_type, self.party, _party_name)
		# test = frappe.db.get_value(self.party_type, self.party, _party_name)
		# frappe.msgprint(_party_name)
		# frappe.msgprint(test)

	if self.party:
		if not self.party_balance:
			self.party_balance = get_balance_on(party_type=self.party_type,
				party=self.party, date=self.posting_date, company=self.company)

		if not self.party_account:
			party_account = get_party_account(self.party_type, self.party, self.company)
			self.set(self.party_account_field, party_account)
			self.party_account = party_account

	if self.paid_from and not (self.paid_from_account_currency or self.paid_from_account_balance):
		acc = get_account_details(self.paid_from, self.posting_date, self.cost_center)
		self.paid_from_account_currency = acc.account_currency
		self.paid_from_account_balance = acc.account_balance

	if self.paid_to and not (self.paid_to_account_currency or self.paid_to_account_balance):
		acc = get_account_details(self.paid_to, self.posting_date, self.cost_center)
		self.paid_to_account_currency = acc.account_currency
		self.paid_to_account_balance = acc.account_balance

	self.party_account_currency = self.paid_from_account_currency \
		if self.payment_type=="Receive" else self.paid_to_account_currency

	set_missing_ref_details_custom(self)

def set_missing_ref_details_custom(self, force=False):
	# frappe.msgprint("set_missing_ref_details_custom masu sini")
	for d in self.get("references"):
		if d.allocated_amount:
			ref_details = get_reference_details_custom(d.reference_doctype,
				d.reference_name, self.party_account_currency)

			for field, value in iteritems(ref_details):
				if field == 'exchange_rate' or not d.get(field) or force:
					d.set(field, value)

@frappe.whitelist()
def change_value(dt,dn):
	# frappe.msgprint("111")
	frappe.db.sql(""" UPDATE `tabTagihan Discount Leasing` set tagihan_sipm=1 where name='{}' """.format(dn))
	frappe.db.commit()

@frappe.whitelist()
def change_value_reverse(dt,dn):
	# frappe.msgprint("222")
	frappe.db.sql(""" UPDATE `tabTagihan Discount Leasing` set tagihan_sipm=0 where name='{}' """.format(dn))	
	frappe.db.commit()

@frappe.whitelist()
def get_payment_entry_custom_tl(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	# frappe.msgprint("get_payment_entry_custom")
	test2 =[]
	reference_doc = None
	frappe.db.sql(""" UPDATE `tabTagihan Discount Leasing` set tagihan_sipm=0 where name='{}' """.format(dn))	
	frappe.db.commit()
	doc = frappe.get_doc(dt, dn)
	# frappe.msgprint(str(doc.tagihan_sipm)+"tagihan_sipm")
	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	party_type = set_party_type_custom(dt)
	party_account = set_party_account(dt, dn, doc, party_type)
	party_account_currency = set_party_account_currency(dt, party_account, doc)
	payment_type = set_payment_type(dt, doc)
	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc)

	paid_amount, received_amount, discount_amount = apply_early_payment_discount(paid_amount, received_amount, doc)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.tagihan = 1
	pe.tagihan_diskon_l = 1
	pe.tagihan_sipm = doc.tagihan_sipm
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.get(scrub(party_type))
	coba = doc.get(scrub(party_type))
	# frappe.msgprint(party_type)
	# frappe.msgprint(coba)
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type=="Receive" else bank.account
	pe.paid_to = party_account if payment_type=="Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
		frappe.msgprint(_('{0} is on hold till {1}').format(doc.name, doc.release_date))
	else:
		if (doc.doctype in ('Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor')
			and frappe.get_value('Payment Terms Template',
			{'name': doc.payment_terms_template}, 'allocate_payment_based_on_payment_terms')):

			for reference in get_reference_as_per_payment_terms(doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount):
				pe.append('references', reference)
		else:
			if dt == "Dunning":
				pe.append("references", {
					'reference_doctype': 'Sales Invoice',
					'reference_name': doc.get('sales_invoice'),
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('outstanding_amount'),
					'outstanding_amount': doc.get('outstanding_amount'),
					'allocated_amount': doc.get('outstanding_amount')
				})
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('dunning_amount'),
					'outstanding_amount': doc.get('dunning_amount'),
					'allocated_amount': doc.get('dunning_amount')
				})
			else:
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': grand_total,
					'outstanding_amount': outstanding_amount,
					'allocated_amount': outstanding_amount
				})
	# tagihan
	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Daftar Tagihan',filters={'parent': dn},fields=['*'])
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_sinv,
				'nilai': d.terbayarkan
			})

	if pe.references[0].reference_doctype == dt and not doc.tagihan_sipm:
		data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.terbayarkan,
				'doc_type': dt,
				'doc_name': dn
				
			})
	elif pe.references[0].reference_doctype == dt and doc.tagihan_sipm:
		data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.outstanding_sipm,
				'doc_type': dt,
				'doc_name': dn
			})
	
	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': dn},fields=['*'])
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'nilai': d.terbayarkan
			})

	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Daftar Credit Motor',filters={'parent': dn},fields=['*'])
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'nilai': d.terbayarkan
			})

	pe.setup_party_account_field()
	# docpe = frappe.new_doc("Payment Entry")
	# meta = frappe.get_meta('Payment Entry')
	# test = ({'payment_type': pe.payment_type})
	# test2.append(test)
	# coba=set_party_type_custom(dt)
	# coba2= set_payment_type(dt, doc)
	# frappe.msgprint(str(test['payment_type']))
	set_missing_values_custom(pe) # = set_missing_values_custom()

	if party_account and bank:
		if dt == "Employee Advance":
			reference_doc = doc
		set_exchange_rate(pe,ref_doc=reference_doc)
		pe.set_amounts()
		if discount_amount:
			pe.set_gain_or_loss(account_details={
				'account': frappe.get_cached_value('Company', pe.company, "default_discount_account"),
				'cost_center': pe.cost_center or frappe.get_cached_value('Company', pe.company, "cost_center"),
				'amount': discount_amount * (-1 if payment_type == "Pay" else 1)
			})
			pe.set_difference_amount()

	return pe

@frappe.whitelist()
def get_payment_entry_custom_bpkb(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	test2 =[]
	reference_doc = None
	frappe.db.sql(""" UPDATE `tabPembayaran Tagihan Motor` set tagihan_bpkb=1,tagihan_stnk=0 where name='{}' """.format(dn))	
	frappe.db.commit()
	doc = frappe.get_doc(dt, dn)
	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	party_type = set_party_type_custom(dt)
	party_account = set_party_account(dt, dn, doc, party_type)
	party_account_currency = set_party_account_currency(dt, party_account, doc)
	payment_type = set_payment_type(dt, doc)
	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc)

	paid_amount, received_amount, discount_amount = apply_early_payment_discount(paid_amount, received_amount, doc)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.tagihan = 1
	pe.down_payment = 0
	pe.tagihan_bpkb = doc.tagihan_bpkb
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.supplier_bpkb
	coba = doc.get(scrub(party_type))
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type=="Receive" else bank.account
	pe.paid_to = party_account if payment_type=="Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else bank.account_currency
	pe.paid_amount = doc.outstanding_amount_bpkb
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
		frappe.msgprint(_('{0} is on hold till {1}').format(doc.name, doc.release_date))
	else:
		if (doc.doctype in ('Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor')
			and frappe.get_value('Payment Terms Template',
			{'name': doc.payment_terms_template}, 'allocate_payment_based_on_payment_terms')):

			for reference in get_reference_as_per_payment_terms(doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount):
				pe.append('references', reference)
		else:
			if dt == "Dunning":
				pe.append("references", {
					'reference_doctype': 'Sales Invoice',
					'reference_name': doc.get('sales_invoice'),
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('outstanding_amount'),
					'outstanding_amount': doc.get('outstanding_amount'),
					'allocated_amount': doc.get('outstanding_amount')
				})
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('dunning_amount'),
					'outstanding_amount': doc.get('dunning_amount'),
					'allocated_amount': doc.get('dunning_amount')
				})
			else:
				# frappe.msgprint("hjsbdbsadas")
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.total_bpkb,
					'outstanding_amount': doc.outstanding_amount_bpkb,
					'allocated_amount': doc.outstanding_amount_bpkb
				})
	# tagihan
	
	if pe.references[0].reference_doctype == dt and doc.tagihan_bpkb:
		data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.outstanding_bpkb,
				'doc_type': dt,
				'doc_name': dn
			})

	pe.setup_party_account_field()
	set_missing_values_custom(pe) # = set_missing_values_custom()

	if party_account and bank:
		if dt == "Employee Advance":
			reference_doc = doc
		set_exchange_rate(pe,ref_doc=reference_doc)
		pe.set_amounts()
		if discount_amount:
			pe.set_gain_or_loss(account_details={
				'account': frappe.get_cached_value('Company', pe.company, "default_discount_account"),
				'cost_center': pe.cost_center or frappe.get_cached_value('Company', pe.company, "cost_center"),
				'amount': discount_amount * (-1 if payment_type == "Pay" else 1)
			})
			pe.set_difference_amount()

	return pe

@frappe.whitelist()
def get_payment_entry_custom_stnk(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	test2 =[]
	reference_doc = None
	frappe.db.sql(""" UPDATE `tabPembayaran Tagihan Motor` set tagihan_stnk=1,tagihan_bpkb=0 where name='{}' """.format(dn))	
	frappe.db.commit()
	doc = frappe.get_doc(dt, dn)
	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	party_type = set_party_type_custom(dt)
	# frappe.msgprint(str(party_type)+" party_type")
	party_account = set_party_account(dt, dn, doc, party_type)
	party_account_currency = set_party_account_currency(dt, party_account, doc)
	payment_type = set_payment_type(dt, doc)
	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc)

	paid_amount, received_amount, discount_amount = apply_early_payment_discount(paid_amount, received_amount, doc)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.tagihan = 1
	pe.down_payment = 0
	pe.tagihan_stnk = doc.tagihan_stnk
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.supplier_stnk
	coba = doc.get(scrub(party_type))
	# frappe.msgprint(str(scrub(party_type))+"scrub(party_type)2")
	# frappe.msgprint(str(doc.get("supplier"))+"scrub(party_type)")
	# frappe.msgprint(doc.get(scrub(party_type))+"party")
	# frappe.msgprint(coba+"coba")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type=="Receive" else bank.account
	pe.paid_to = party_account if payment_type=="Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else bank.account_currency
	pe.paid_amount = doc.outstanding_amount_stnk
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
		frappe.msgprint(_('{0} is on hold till {1}').format(doc.name, doc.release_date))
	else:
		if (doc.doctype in ('Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor')
			and frappe.get_value('Payment Terms Template',
			{'name': doc.payment_terms_template}, 'allocate_payment_based_on_payment_terms')):

			for reference in get_reference_as_per_payment_terms(doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount):
				pe.append('references', reference)
		else:
			if dt == "Dunning":
				pe.append("references", {
					'reference_doctype': 'Sales Invoice',
					'reference_name': doc.get('sales_invoice'),
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('outstanding_amount'),
					'outstanding_amount': doc.get('outstanding_amount'),
					'allocated_amount': doc.get('outstanding_amount')
				})
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('dunning_amount'),
					'outstanding_amount': doc.get('dunning_amount'),
					'allocated_amount': doc.get('dunning_amount')
				})
			else:
				frappe.msgprint("hjsbdbsadas")
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.total_stnk,
					'outstanding_amount': doc.outstanding_amount_stnk,
					'allocated_amount': doc.outstanding_amount_stnk
				})
	# tagihan
	
	if pe.references[0].reference_doctype == dt and doc.tagihan_stnk:
		# data = frappe.db.sql(""" SELECT * from `tabChild Tagihan Biaya Motor` where parent='{}' order by pemilik asc """.format(dn),as_dict=1)
		data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.outstanding_stnk,
				'doc_type': dt,
				'doc_name': dn
			})

	pe.setup_party_account_field()
	# docpe = frappe.new_doc("Payment Entry")
	# meta = frappe.get_meta('Payment Entry')
	# test = ({'payment_type': pe.payment_type})
	# test2.append(test)
	# coba=set_party_type_custom(dt)
	# coba2= set_payment_type(dt, doc)
	# frappe.msgprint(str(test['payment_type']))
	set_missing_values_custom(pe) # = set_missing_values_custom()

	if party_account and bank:
		if dt == "Employee Advance":
			reference_doc = doc
		set_exchange_rate(pe,ref_doc=reference_doc)
		pe.set_amounts()
		if discount_amount:
			pe.set_gain_or_loss(account_details={
				'account': frappe.get_cached_value('Company', pe.company, "default_discount_account"),
				'cost_center': pe.cost_center or frappe.get_cached_value('Company', pe.company, "cost_center"),
				'amount': discount_amount * (-1 if payment_type == "Pay" else 1)
			})
			pe.set_difference_amount()

	return pe

@frappe.whitelist()
def get_payment_entry_custom(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	test2 =[]
	reference_doc = None
	frappe.db.sql(""" UPDATE `tabTagihan Discount Leasing` set tagihan_sipm=0 where name='{}' """.format(dn))	
	frappe.db.commit()
	doc = frappe.get_doc(dt, dn)
	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	party_type = set_party_type_custom(dt)
	# frappe.msgprint(str(party_type)+" party_type")
	party_account = set_party_account(dt, dn, doc, party_type)
	party_account_currency = set_party_account_currency(dt, party_account, doc)
	payment_type = set_payment_type(dt, doc)
	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc)

	paid_amount, received_amount, discount_amount = apply_early_payment_discount(paid_amount, received_amount, doc)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.tagihan = 1
	# pe.tagihan_sipm = doc.tagihan_sipm
	pe.tagihan_diskon = 1
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.get(scrub(party_type))
	coba = doc.get(scrub(party_type))
	# frappe.msgprint(str(doc.get("supplier"))+"scrub(party_type)")
	# frappe.msgprint(doc.get(scrub(party_type))+"party")
	# frappe.msgprint(coba+"coba")
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type=="Receive" else bank.account
	pe.paid_to = party_account if payment_type=="Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
		frappe.msgprint(_('{0} is on hold till {1}').format(doc.name, doc.release_date))
	else:
		if (doc.doctype in ('Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor')
			and frappe.get_value('Payment Terms Template',
			{'name': doc.payment_terms_template}, 'allocate_payment_based_on_payment_terms')):

			for reference in get_reference_as_per_payment_terms(doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount):
				pe.append('references', reference)
		else:
			if dt == "Dunning":
				pe.append("references", {
					'reference_doctype': 'Sales Invoice',
					'reference_name': doc.get('sales_invoice'),
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('outstanding_amount'),
					'outstanding_amount': doc.get('outstanding_amount'),
					'allocated_amount': doc.get('outstanding_amount')
				})
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('dunning_amount'),
					'outstanding_amount': doc.get('dunning_amount'),
					'allocated_amount': doc.get('dunning_amount')
				})
			else:
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': grand_total,
					'outstanding_amount': outstanding_amount,
					'allocated_amount': outstanding_amount
				})
	# tagihan
	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Daftar Tagihan',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_sinv,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.terbayarkan,
				'doc_type': dt,
				'doc_name': dn
				
			})

	# if pe.references[0].reference_doctype == dt and not doc.tagihan_sipm:
	# 	data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'])
	# 	for d in data:
	# 		pe.append("tagihan_payment_table", {
	# 			'no_sinv': d.no_invoice,
	# 			'nilai': d.terbayarkan
	# 		})
	# elif pe.references[0].reference_doctype == dt and doc.tagihan_sipm:
	# 	data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'])
	# 	for d in data:
	# 		pe.append("tagihan_payment_table", {
	# 			'no_sinv': d.no_invoice,
	# 			'nilai': d.outstanding_sipm
	# 		})
	
	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Child Tagihan Biaya Motor',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.terbayarkan,
				'doc_type': dt,
				'doc_name': dn
			})

	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Daftar Credit Motor',filters={'parent': dn},fields=['*'])
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'nilai': d.terbayarkan
			})

	pe.setup_party_account_field()
	# docpe = frappe.new_doc("Payment Entry")
	# meta = frappe.get_meta('Payment Entry')
	# test = ({'payment_type': pe.payment_type})
	# test2.append(test)
	# coba=set_party_type_custom(dt)
	# coba2= set_payment_type(dt, doc)
	# frappe.msgprint(str(test['payment_type']))
	set_missing_values_custom(pe) # = set_missing_values_custom()

	if party_account and bank:
		if dt == "Employee Advance":
			reference_doc = doc
		set_exchange_rate(pe,ref_doc=reference_doc)
		pe.set_amounts()
		if discount_amount:
			pe.set_gain_or_loss(account_details={
				'account': frappe.get_cached_value('Company', pe.company, "default_discount_account"),
				'cost_center': pe.cost_center or frappe.get_cached_value('Company', pe.company, "cost_center"),
				'amount': discount_amount * (-1 if payment_type == "Pay" else 1)
			})
			pe.set_difference_amount()

	return pe

@frappe.whitelist()
def get_payment_entry_custom_sipm(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	# frappe.msgprint("get_payment_entry_custom")
	test2 =[]
	reference_doc = None
	frappe.db.sql(""" UPDATE `tabTagihan Discount Leasing` set tagihan_sipm=1 where name='{}' """.format(dn))
	frappe.db.commit()
	doc = frappe.get_doc(dt, dn)
	# frappe.msgprint(str(doc.tagihan_sipm)+"tagihan_sipm")
	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	party_type = set_party_type_custom(dt)
	party_account = set_party_account(dt, dn, doc, party_type)
	party_account_currency = set_party_account_currency(dt, party_account, doc)
	payment_type = set_payment_type(dt, doc)
	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc)

	# bank or cash
	bank = get_bank_cash_account(doc, bank_account)

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc)

	paid_amount, received_amount, discount_amount = apply_early_payment_discount(paid_amount, received_amount, doc)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.tagihan = 1
	pe.tagihan_sipm = doc.tagihan_sipm
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.get(scrub(party_type))
	coba = doc.get(scrub(party_type))
	# frappe.msgprint(party_type)
	# frappe.msgprint(coba)
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type=="Receive" else bank.account
	pe.paid_to = party_account if payment_type=="Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
		frappe.msgprint(_('{0} is on hold till {1}').format(doc.name, doc.release_date))
	else:
		if (doc.doctype in ('Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor')
			and frappe.get_value('Payment Terms Template',
			{'name': doc.payment_terms_template}, 'allocate_payment_based_on_payment_terms')):

			for reference in get_reference_as_per_payment_terms(doc.payment_schedule, dt, dn, doc, grand_total, outstanding_amount):
				pe.append('references', reference)
		else:
			if dt == "Dunning":
				frappe.msgprint("masuk sini")
				pe.append("references", {
					'reference_doctype': 'Sales Invoice',
					'reference_name': doc.get('sales_invoice'),
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('outstanding_amount'),
					'outstanding_amount': doc.get('outstanding_amount'),
					'allocated_amount': doc.get('outstanding_amount')
				})
				pe.append("references", {
					'reference_doctype': dt,
					'reference_name': dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					'total_amount': doc.get('dunning_amount'),
					'outstanding_amount': doc.get('dunning_amount'),
					'allocated_amount': doc.get('dunning_amount')
				})
			else:
				# frappe.msgprint("masuk sini222222222xxx")
				pe.references=[]
				row = pe.append('references', {})
				row.reference_doctype = dt
				row.reference_name = dn
				row.total_amount = doc.total_tagihan_sipm
				row.outstanding_amount = doc.total_outstanding_tagihan_sipm
				row.allocated_amount = doc.total_outstanding_tagihan_sipm
				# pe.append("references", {
				# 	'reference_doctype': dt,
				# 	'reference_name': dn,
				# 	"bill_no": doc.get("bill_no"),
				# 	"due_date": doc.get("due_date"),
				# 	'total_amount': doc.total_tagihan_sipm,
				# 	'outstanding_amount': doc.total_outstanding_tagihan_sipm,
				# 	'allocated_amount': doc.total_outstanding_tagihan_sipm
				# })
				# pe.references=[]
	# tagihan

	# if pe.references[0].reference_doctype == dt and not doc.tagihan_sipm:
	# 	data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'])
	# 	for d in data:
	# 		pe.append("tagihan_payment_table", {
	# 			'no_sinv': d.no_invoice,
	# 			'pemilik': d.pemilik,
	# 			'item': d.item,
	# 			'no_rangka': d.no_rangka,
	# 			'nilai': d.terbayarkan
	# 			'doc_type': dt,
	# 			'doc_name': dn
				
	# 		})
	# elif pe.references[0].reference_doctype == dt and doc.tagihan_sipm:
	# 	data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'])
	# 	for d in data:
	# 		pe.append("tagihan_payment_table", {
	# 			'no_sinv': d.no_invoice,
	# 			'pemilik': d.pemilik,
	# 			'item': d.item,
	# 			'no_rangka': d.no_rangka,
	# 			'nilai': d.outstanding_sipm
	# 			'doc_type': dt,
	# 			'doc_name': dn
	# 		})
	if pe.references[0].reference_doctype == dt:
		data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
		for d in data:
			pe.append("tagihan_payment_table", {
				'no_sinv': d.no_invoice,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': d.outstanding_sipm,
				'doc_type': dt,
				'doc_name': dn
			})

	pe.setup_party_account_field()
	# docpe = frappe.new_doc("Payment Entry")
	# meta = frappe.get_meta('Payment Entry')
	# test = ({'payment_type': pe.payment_type})
	# test2.append(test)
	# coba=set_party_type_custom(dt)
	# coba2= set_payment_type(dt, doc)
	# frappe.msgprint(str(test['payment_type']))
	set_missing_values_custom(pe) # = set_missing_values_custom()

	if party_account and bank:
		if dt == "Employee Advance":
			reference_doc = doc
		set_exchange_rate(pe,ref_doc=reference_doc)
		pe.set_amounts()
		if discount_amount:
			pe.set_gain_or_loss(account_details={
				'account': frappe.get_cached_value('Company', pe.company, "default_discount_account"),
				'cost_center': pe.cost_center or frappe.get_cached_value('Company', pe.company, "cost_center"),
				'amount': discount_amount * (-1 if payment_type == "Pay" else 1)
			})
			pe.set_difference_amount()

	return pe



def set_exchange_rate(self, ref_doc=None):
	# frappe.msgprint("set_exchange_rate sini")
	self.set_source_exchange_rate(ref_doc)
	self.set_target_exchange_rate(ref_doc)

# @frappe.whitelist()
def set_party_type_custom(dt):
	# frappe.msgprint("masuk custom sini lutfi")
	if dt in ("Sales Invoice", "Sales Order", "Dunning","Sales Invoice Penjualan Motor","Tagihan Discount","Tagihan Discount Leasing","Pembayaran Credit Motor"):
		party_type = "Customer"
	elif dt in ("Purchase Invoice", "Purchase Order","Pembayaran Tagihan Motor"):
		party_type = "Supplier"
	elif dt in ("Expense Claim", "Employee Advance", "Gratuity"):
		party_type = "Employee"
	elif dt == "Fees":
		party_type = "Student"
	elif dt == "Donation":
		party_type = "Donor"
	return party_type

def set_party_account(dt, dn, doc, party_type):
	if dt == "Sales Invoice" or dt == "Sales Invoice Penjualan Motor":
		party_account = get_party_account_based_on_invoice_discounting(dn) or doc.debit_to
	elif dt == "Purchase Invoice":
		party_account = doc.credit_to
	elif dt == "Fees":
		party_account = doc.receivable_account
	elif dt == "Employee Advance":
		party_account = doc.advance_account
	elif dt == "Expense Claim":
		party_account = doc.payable_account
	elif dt == "Gratuity":
		party_account = doc.payable_account
	elif dt == "Tagihan Discount":
		debit_to = frappe.get_doc("Sales Invoice Penjualan Motor",doc.daftar_tagihan[0].no_sinv).debit_to
		party_account = debit_to
	elif dt == "Tagihan Discount Leasing":
		debit_to = frappe.get_doc("Sales Invoice Penjualan Motor",doc.daftar_tagihan_leasing[0].no_invoice).debit_to
		party_account = doc.coa_tagihan_sipm
	elif dt == "Pembayaran Credit Motor":
		party_account = doc.coa_credit_motor
	elif dt == "Pembayaran Tagihan Motor" and doc.type == "Diskon Dealer":
		party_account = doc.coa_biaya_motor
	elif dt == "Pembayaran Tagihan Motor" and doc.type == "STNK dan BPKB" and "STNK" in doc.supplier_stnk:
		party_account = doc.coa_biaya_motor_stnk
	elif dt == "Pembayaran Tagihan Motor" and doc.type == "STNK dan BPKB" and "BPKB" in doc.supplier_bpkb:
		party_account = doc.coa_biaya_motor_bpkb
	else:
		party_account = get_party_account(party_type, doc.get(party_type.lower()), doc.company)
	return party_account

def set_party_account_currency(dt, party_account, doc):
	if dt not in ("Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"):
		party_account_currency = get_account_currency(party_account)
	else:
		party_account_currency = doc.get("party_account_currency") or get_account_currency(party_account)
	return party_account_currency

def set_payment_type(dt, doc):
	if (dt in ("Sales Order", "Donation","Tagihan Discount","Tagihan Discount Leasing","Pembayaran Credit Motor") or (dt in ("Sales Invoice", "Fees", "Dunning","Sales Invoice Penjualan Motor") and doc.outstanding_amount > 0)) \
		or (dt=="Purchase Invoice" and doc.outstanding_amount < 0):
			payment_type = "Receive"
	else:
		payment_type = "Pay"
	return payment_type

def set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc):
	#frappe.msgprint('set_grand_total_and_outstanding_amount')
	grand_total = outstanding_amount = 0
	# tdl = frappe.get_doc(dt,dn)
	if party_amount:
		grand_total = outstanding_amount = party_amount
	elif dt in ("Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"):
		if party_account_currency == doc.company_currency:
			#frappe.throw("wahyu lutfi y123")
			grand_total = doc.base_rounded_total or doc.base_grand_total
		else:
			#frappe.throw("wahyu lutfi y")
			grand_total = doc.rounded_total or doc.grand_total
		outstanding_amount = doc.outstanding_amount
	elif dt in ("Expense Claim"):
		grand_total = doc.total_sanctioned_amount + doc.total_taxes_and_charges
		outstanding_amount = doc.grand_total \
			- doc.total_amount_reimbursed
	elif dt == "Employee Advance":
		grand_total = flt(doc.advance_amount)
		outstanding_amount = flt(doc.advance_amount) - flt(doc.paid_amount)
		if party_account_currency != doc.currency:
			grand_total = flt(doc.advance_amount) * flt(doc.exchange_rate)
			outstanding_amount = (flt(doc.advance_amount) - flt(doc.paid_amount)) * flt(doc.exchange_rate)
	elif dt == "Fees":
		grand_total = doc.grand_total
		outstanding_amount = doc.outstanding_amount
	elif dt == "Dunning":
		grand_total = doc.grand_total
		outstanding_amount = doc.grand_total
	elif dt == "Donation":
		grand_total = doc.amount
		outstanding_amount = doc.amount
	elif dt == "Gratuity":
		grand_total = doc.amount
		outstanding_amount = flt(doc.amount) - flt(doc.paid_amount)
	elif dt == "Tagihan Discount":
		grand_total = doc.grand_total
		outstanding_amount = doc.outstanding_amount
	elif dt == "Tagihan Discount Leasing" and not doc.tagihan_sipm:
		grand_total = doc.grand_total
		outstanding_amount = doc.outstanding_amount
	elif dt == "Tagihan Discount Leasing" and doc.tagihan_sipm:
		# frappe.msgprint(str(doc.total_tagihan_sipm)+str(doc.total_outstanding_tagihan_sipm)+"mauskkkkk")
		grand_total = doc.total_tagihan_sipm
		outstanding_amount = doc.total_outstanding_tagihan_sipm
	elif dt == "Pembayaran Credit Motor":
		grand_total = doc.grand_total
		outstanding_amount = doc.outstanding_amount
	elif dt == "Pembayaran Tagihan Motor":
		grand_total = doc.grand_total
		outstanding_amount = doc.outstanding_amount
	else:
		if party_account_currency == doc.company_currency:
			grand_total = flt(doc.get("base_rounded_total") or doc.base_grand_total)
		else:
			grand_total = flt(doc.get("rounded_total") or doc.grand_total)
		outstanding_amount = grand_total - flt(doc.advance_paid)
	return grand_total, outstanding_amount

def get_bank_cash_account(doc, bank_account):
	if doc.company:
		bank = get_default_bank_cash_account(doc.company, "Bank", mode_of_payment=doc.get("mode_of_payment"),
			account=bank_account)

		if not bank:
			bank = get_default_bank_cash_account(doc.company, "Cash", mode_of_payment=doc.get("mode_of_payment"),
				account=bank_account)
	else:
		bank = get_default_bank_cash_account("DAS", "Bank", mode_of_payment=doc.get("mode_of_payment"),
			account=bank_account)

		if not bank:
			bank = get_default_bank_cash_account("DAS", "Cash", mode_of_payment=doc.get("mode_of_payment"),
				account=bank_account)

	return bank

def set_paid_amount_and_received_amount(dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc):
	paid_amount = received_amount = 0
	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)
	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get('conversion_rate', 1)
			if dt == "Employee Advance":
				received_amount = paid_amount * doc.get('exchange_rate', 1)
	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			paid_amount = received_amount * doc.get('conversion_rate', 1)
			if dt == "Employee Advance":
				paid_amount = received_amount * doc.get('exchange_rate', 1)
	return paid_amount, received_amount

def apply_early_payment_discount(paid_amount, received_amount, doc):
	total_discount = 0
	if doc.doctype in ['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor'] and doc.payment_schedule:
		for term in doc.payment_schedule:
			if not term.discounted_amount and term.discount and getdate(nowdate()) <= term.discount_date:
				if term.discount_type == 'Percentage':
					discount_amount = flt(doc.get('grand_total')) * (term.discount / 100)
				else:
					discount_amount = term.discount

				discount_amount_in_foreign_currency = discount_amount * doc.get('conversion_rate', 1)

				if doc.doctype == 'Sales Invoice':
					paid_amount -= discount_amount
					received_amount -= discount_amount_in_foreign_currency
				else:
					received_amount -= discount_amount
					paid_amount -= discount_amount_in_foreign_currency

				total_discount += discount_amount

		if total_discount:
			money = frappe.utils.fmt_money(total_discount, currency=doc.get('currency'))
			frappe.msgprint(_("Discount of {} applied as per Payment Term").format(money), alert=1)

	return paid_amount, received_amount, total_discount

@frappe.whitelist()
def get_reference_details_custom(reference_doctype, reference_name, party_account_currency):
	# frappe.msgprint("coba-coba")
	total_amount = outstanding_amount = exchange_rate = bill_no = None
	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)

	if reference_doctype == "Fees":
		total_amount = ref_doc.get("grand_total")
		exchange_rate = 1
		outstanding_amount = ref_doc.get("outstanding_amount")
	elif reference_doctype == "Donation":
		total_amount = ref_doc.get("amount")
		exchange_rate = 1
	elif reference_doctype == "Dunning":
		total_amount = ref_doc.get("dunning_amount")
		exchange_rate = 1
		outstanding_amount = ref_doc.get("dunning_amount")
	elif reference_doctype == "Journal Entry" and ref_doc.docstatus == 1:
		total_amount = ref_doc.get("total_amount")
		if ref_doc.multi_currency:
			exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
		else:
			exchange_rate = 1
			outstanding_amount = get_outstanding_on_journal_entry(reference_name)
	elif reference_doctype != "Journal Entry":
		if ref_doc.doctype == "Expense Claim":
				total_amount = flt(ref_doc.total_sanctioned_amount) + flt(ref_doc.total_taxes_and_charges)
		elif ref_doc.doctype == "Employee Advance":
			total_amount = ref_doc.advance_amount
			exchange_rate = ref_doc.get("exchange_rate")
			if party_account_currency != ref_doc.currency:
				total_amount = flt(total_amount) * flt(exchange_rate)
		elif ref_doc.doctype == "Gratuity":
				total_amount = ref_doc.amount
		if not total_amount:
			if party_account_currency == company_currency:
				total_amount = ref_doc.base_grand_total
				exchange_rate = 1
			else:
				total_amount = ref_doc.grand_total
		if not exchange_rate:
			# Get the exchange rate from the original ref doc
			# or get it based on the posting date of the ref doc.
			exchange_rate = ref_doc.get("conversion_rate") or \
				get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
		if reference_doctype in ("Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"):
			outstanding_amount = ref_doc.get("outstanding_amount")
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Tagihan Discount":
			# frappe.msgprint("Tagihan Discount")
			total_amount = ref_doc.grand_total
			outstanding_amount = ref_doc.outstanding_amount
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Tagihan Discount Leasing" and not ref_doc.tagihan_sipm:
			# frappe.msgprint("Tagihan Discount Leasing 1")
			total_amount = ref_doc.grand_total
			outstanding_amount = ref_doc.outstanding_amount
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Tagihan Discount Leasing" and ref_doc.tagihan_sipm:
			# frappe.msgprint("Tagihan Discount Leasing 2sdsd")
			total_amount = ref_doc.total_tagihan_sipm
			outstanding_amount = ref_doc.total_outstanding_tagihan_sipm
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Pembayaran Credit Motor":
			# frappe.msgprint("Pembayaran Credit Motor")
			total_amount = ref_doc.grand_total
			outstanding_amount = ref_doc.outstanding_amount
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Pembayaran Tagihan Motor":
			# frappe.msgprint("Pembayaran Tagihan Motor")
			total_amount = ref_doc.grand_total
			outstanding_amount = ref_doc.outstanding_amount
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Expense Claim":
			outstanding_amount = flt(ref_doc.get("total_sanctioned_amount")) + flt(ref_doc.get("total_taxes_and_charges"))\
				- flt(ref_doc.get("total_amount_reimbursed")) - flt(ref_doc.get("total_advance_amount"))
		elif reference_doctype == "Employee Advance":
			outstanding_amount = (flt(ref_doc.advance_amount) - flt(ref_doc.paid_amount))
			if party_account_currency != ref_doc.currency:
				outstanding_amount = flt(outstanding_amount) * flt(exchange_rate)
				if party_account_currency == company_currency:
					exchange_rate = 1
		elif reference_doctype == "Gratuity":
			outstanding_amount = ref_doc.amount - flt(ref_doc.paid_amount)
		else:
			outstanding_amount = flt(total_amount) - flt(ref_doc.advance_paid)
	else:
		# Get the exchange rate based on the posting date of the ref doc.
		exchange_rate = get_exchange_rate(party_account_currency,
			company_currency, ref_doc.posting_date)

	return frappe._dict({
		"due_date": ref_doc.get("due_date"),
		"total_amount": total_amount,
		"outstanding_amount": outstanding_amount,
		"exchange_rate": exchange_rate,
		"bill_no": bill_no
	})

def validate_reference_documents_custom(self):
	# frappe.msgprint('masuk valiasi custom')
	if self.party_type == "Student":
		valid_reference_doctypes = ("Fees")
	elif self.party_type == "Customer":
		valid_reference_doctypes = ("Sales Order", "Sales Invoice", "Journal Entry", "Dunning","Sales Invoice Penjualan Motor")
	elif self.party_type == "Supplier":
		valid_reference_doctypes = ("Purchase Order", "Purchase Invoice", "Journal Entry")
	elif self.party_type == "Employee":
		valid_reference_doctypes = ("Expense Claim", "Journal Entry", "Employee Advance", "Gratuity")
	elif self.party_type == "Shareholder":
		valid_reference_doctypes = ("Journal Entry")
	elif self.party_type == "Donor":
		valid_reference_doctypes = ("Donation")

	for d in self.get("references"):
		if not d.allocated_amount:
			continue
		if d.reference_doctype not in valid_reference_doctypes:
			frappe.throw(_("Reference Doctype must be one of {0}")
				.format(comma_or(valid_reference_doctypes)))

		elif d.reference_name:
			if not frappe.db.exists(d.reference_doctype, d.reference_name):
				frappe.throw(_("{0} {1} does not exist").format(d.reference_doctype, d.reference_name))
			else:
				ref_doc = frappe.get_doc(d.reference_doctype, d.reference_name)

				if d.reference_doctype != "Journal Entry":
					if self.party != ref_doc.get(scrub(self.party_type)):
						frappe.throw(_("{0} {1} is not associated with {2} {3}")
							.format(d.reference_doctype, d.reference_name, self.party_type, self.party))
				else:
					self.validate_journal_entry()

				if d.reference_doctype in ("Sales Invoice", "Purchase Invoice", "Expense Claim", "Fees","Sales Invoice Penjualan Motor"):
					if self.party_type == "Customer":
						ref_party_account = get_party_account_based_on_invoice_discounting(d.reference_name) or ref_doc.debit_to
					elif self.party_type == "Student":
						ref_party_account = ref_doc.receivable_account
					elif self.party_type=="Supplier":
						ref_party_account = ref_doc.credit_to
					elif self.party_type=="Employee":
						ref_party_account = ref_doc.payable_account

					if ref_party_account != self.party_account:
							frappe.throw(_("{0} {1} is associated with {2}, but Party Account is {3}")
								.format(d.reference_doctype, d.reference_name, ref_party_account, self.party_account))

				if ref_doc.docstatus != 1:
					frappe.throw(_("{0} {1} must be submitted")
						.format(d.reference_doctype, d.reference_name))

@frappe.whitelist()
def overide_make_pe(self,method):
	# frappe.msgprint("overide_make_pe sini")
	# PaymentEntry.validate_reference_documents = validate_reference_documents_custom
	PaymentEntry.get_reference_details = get_reference_details_custom
	# PaymentEntry.get_payment_entry = get_payment_entry_custom
	# PaymentEntry.set_missing_ref_details = set_missing_ref_details_custom

@frappe.whitelist()
def get_outstanding_reference_documents_custom(args):
	# frappe.msgprint("masuk get_outstanding_reference_documents_custom")
	if isinstance(args, string_types):
		args = json.loads(args)

	if args.get('party_type') == 'Member':
		return

	# confirm that Supplier is not blocked
	if args.get('party_type') == 'Supplier':
		supplier_status = get_supplier_block_status(args['party'])
		if supplier_status['on_hold']:
			if supplier_status['hold_type'] == 'All':
				return []
			elif supplier_status['hold_type'] == 'Payments':
				if not supplier_status['release_date'] or getdate(nowdate()) <= supplier_status['release_date']:
					return []

	party_account_currency = get_account_currency(args.get("party_account"))
	company_currency = frappe.get_cached_value('Company',  args.get("company"),  "default_currency")

	# Get negative outstanding sales /purchase invoices
	negative_outstanding_invoices = []
	if args.get("party_type") not in ["Student", "Employee"] and not args.get("voucher_no"):
		negative_outstanding_invoices = get_negative_outstanding_invoices(args.get("party_type"), args.get("party"),
			args.get("party_account"), args.get("company"), party_account_currency, company_currency)

	# Get positive outstanding sales /purchase invoices/ Fees
	condition = ""
	if args.get("voucher_type") and args.get("voucher_no"):
		condition = " and voucher_type={0} and voucher_no={1}"\
			.format(frappe.db.escape(args["voucher_type"]), frappe.db.escape(args["voucher_no"]))

	# Add cost center condition
	if args.get("cost_center"):
		condition += " and cost_center='%s'" % args.get("cost_center")

	date_fields_dict = {
		'posting_date': ['from_posting_date', 'to_posting_date'],
		'due_date': ['from_due_date', 'to_due_date']
	}

	for fieldname, date_fields in date_fields_dict.items():
		if args.get(date_fields[0]) and args.get(date_fields[1]):
			condition += " and {0} between '{1}' and '{2}'".format(fieldname,
				args.get(date_fields[0]), args.get(date_fields[1]))

	if args.get("company"):
		condition += " and company = {0}".format(frappe.db.escape(args.get("company")))

	outstanding_invoices = get_outstanding_invoices(args.get("party_type"), args.get("party"),
		args.get("party_account"), filters=args, condition=condition)

	outstanding_invoices = split_invoices_based_on_payment_terms(outstanding_invoices)

	for d in outstanding_invoices:
		d["exchange_rate"] = 1
		if party_account_currency != company_currency:
			if d.voucher_type in ("Sales Invoice", "Purchase Invoice", "Expense Claim"):
				d["exchange_rate"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "conversion_rate")
			elif d.voucher_type == "Journal Entry":
				d["exchange_rate"] = get_exchange_rate(
					party_account_currency,	company_currency, d.posting_date
				)
		if d.voucher_type in ("Purchase Invoice"):
			d["bill_no"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "bill_no")

	# Get all SO / PO which are not fully billed or aginst which full advance not paid
	orders_to_be_billed = []
	if (args.get("party_type") != "Student"):
		orders_to_be_billed =  get_orders_to_be_billed(args.get("posting_date"),args.get("party_type"),
			args.get("party"), args.get("company"), party_account_currency, company_currency, filters=args)

	data = negative_outstanding_invoices + outstanding_invoices + orders_to_be_billed

	if not data:
		frappe.msgprint(_("No outstanding invoices found for the {0} {1} which qualify the filters you have specified.")
			.format(args.get("party_type").lower(), frappe.bold(args.get("party"))))

	return data

def get_negative_outstanding_invoices(party_type, party, party_account,
	company, party_account_currency, company_currency, cost_center=None):
	voucher_type = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
	# voucher_type = "Sales Invoice Penjualan Motor" if party_type == "Customer" else "Purchase Invoice"
	supplier_condition = ""
	if voucher_type == "Purchase Invoice":
		supplier_condition = "and (release_date is null or release_date <= CURDATE())"
	if party_account_currency == company_currency:
		grand_total_field = "base_grand_total"
		rounded_total_field = "base_rounded_total"
	else:
		grand_total_field = "grand_total"
		rounded_total_field = "rounded_total"

	return frappe.db.sql("""
		select
			"{voucher_type}" as voucher_type, name as voucher_no,
			if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) as invoice_amount,
			outstanding_amount, posting_date,
			due_date, conversion_rate as exchange_rate
		from
			`tab{voucher_type}`
		where
			{party_type} = %s and {party_account} = %s and docstatus = 1 and
			company = %s and outstanding_amount < 0
			{supplier_condition}
		order by
			posting_date, name
		""".format(**{
			"supplier_condition": supplier_condition,
			"rounded_total_field": rounded_total_field,
			"grand_total_field": grand_total_field,
			"voucher_type": voucher_type,
			"party_type": scrub(party_type),
			"party_account": "debit_to" if party_type == "Customer" else "credit_to",
			"cost_center": cost_center
		}), (party, party_account, company), as_dict=True)


def get_terbayarkan_multi(doc,method):
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if doc.doc_type:
			if doc.tipe_pembayaran == "Pembayaran STNK":
				for i in doc.references:
					data = frappe.get_doc("Pembayaran Tagihan Motor",i.reference_name)
					data.outstanding_amount_stnk = data.outstanding_amount_stnk - i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Child Tagihan Biaya Motor",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.outstanding_stnk = data.outstanding_stnk - t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran BPKB":
				for i in doc.references:
					data = frappe.get_doc("Pembayaran Tagihan Motor",i.reference_name)
					data.outstanding_amount_bpkb = data.outstanding_amount_bpkb - i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Child Tagihan Biaya Motor",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.outstanding_bpkb = data.outstanding_bpkb - t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran Diskon Dealer":
				for i in doc.references:
					data = frappe.get_doc("Pembayaran Tagihan Motor",i.reference_name)
					data.outstanding_amount = data.outstanding_amount - i.allocated_amount
					data.db_update()
					frappe.db.commit()
				# 	if i.allocated_amount <= data.outstanding_amount:
				# 		data.outstanding_amount = data.outstanding_amount - i.allocated_amount
				# 		data.db_update()
				# 		# frappe.db.commit()
				# 	else:
				# 		frappe.throw(i.reference_name+" lebih besar dari yang terbayarkan !")
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Child Tagihan Biaya Motor",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.terbayarkan = data.terbayarkan - t.nilai
					data.db_update()
					frappe.db.commit()
					# if t.nilai <= data.terbayarkan:
					# 	data.terbayarkan = data.terbayarkan - t.nilai
					# 	data.db_update()
					# 	# frappe.db.commit()
					# else:
					# 	frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
			elif doc.tipe_pembayaran == "Pembayaran Diskon Leasing":
				for i in doc.references:
					data = frappe.get_doc("Tagihan Discount Leasing",i.reference_name)
					data.outstanding_amount = data.outstanding_amount - i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Daftar Tagihan Leasing",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.terbayarkan = data.terbayarkan - t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran SIPM":
				for i in doc.references:
					data = frappe.get_doc("Tagihan Discount Leasing",i.reference_name)
					data.total_outstanding_tagihan_sipm = data.total_outstanding_tagihan_sipm - i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Daftar Tagihan Leasing",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.outstanding_sipm = data.outstanding_sipm - t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran Diskon":
					for i in doc.references:
						data = frappe.get_doc("Tagihan Discount",i.reference_name)
						data.outstanding_amount = data.outstanding_amount - i.allocated_amount
						data.db_update()
						frappe.db.commit()
					for t in doc.tagihan_payment_table:
						data = frappe.get_doc("Daftar Tagihan",{'parent':t.doc_name,"no_sinv":t.no_sinv})
						data.terbayarkan = data.terbayarkan - t.nilai
						data.db_update()
						frappe.db.commit()

def get_terbayarkan_multi_cancel(doc,method):
	# if frappe.local.site in ["honda.digitalasiasolusindo.com","hondapjk.digitalasiasolusindo.com"]:
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if doc.doc_type:
			if doc.tipe_pembayaran == "Pembayaran STNK":
				for i in doc.references:
					data = frappe.get_doc("Pembayaran Tagihan Motor",i.reference_name)
					data.outstanding_amount_stnk = data.outstanding_amount_stnk + i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Child Tagihan Biaya Motor",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.outstanding_stnk = data.outstanding_stnk + t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran BPKB":
				for i in doc.references:
					data = frappe.get_doc("Pembayaran Tagihan Motor",i.reference_name)
					data.outstanding_amount_bpkb = data.outstanding_amount_bpkb + i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Child Tagihan Biaya Motor",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.outstanding_bpkb = data.outstanding_bpkb + t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran Diskon Dealer":
				for i in doc.references:
					data = frappe.get_doc("Pembayaran Tagihan Motor",i.reference_name)
					data.outstanding_amount = data.outstanding_amount + i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Child Tagihan Biaya Motor",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.terbayarkan = data.terbayarkan + t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran Diskon Leasing":
				for i in doc.references:
					data = frappe.get_doc("Tagihan Discount Leasing",i.reference_name)
					data.outstanding_amount = data.outstanding_amount + i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Daftar Tagihan Leasing",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.terbayarkan = data.terbayarkan + t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran SIPM":
				for i in doc.references:
					data = frappe.get_doc("Tagihan Discount Leasing",i.reference_name)
					data.total_outstanding_tagihan_sipm = data.total_outstanding_tagihan_sipm + i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Daftar Tagihan Leasing",{'parent':t.doc_name,"no_invoice":t.no_sinv})
					data.outstanding_sipm = data.outstanding_sipm + t.nilai
					data.db_update()
					frappe.db.commit()
			elif doc.tipe_pembayaran == "Pembayaran Diskon":
				for i in doc.references:
					data = frappe.get_doc("Tagihan Discount",i.reference_name)
					data.outstanding_amount = data.outstanding_amount + i.allocated_amount
					data.db_update()
					frappe.db.commit()
				for t in doc.tagihan_payment_table:
					data = frappe.get_doc("Daftar Tagihan",{'parent':t.doc_name,"no_sinv":t.no_sinv})
					data.terbayarkan = data.terbayarkan + t.nilai
					data.db_update()
					frappe.db.commit()


def get_terbayarkan(doc,method):
	# if frappe.local.site in ["honda.digitalasiasolusindo.com","hondapjk.digitalasiasolusindo.com"]:
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if doc.tagihan == 1 and not doc.doc_type:
			# frappe.throw(doc.references[0].reference_name)
			if doc.references[0].reference_doctype == "Tagihan Discount":
				td_doc = frappe.get_doc("Tagihan Discount",doc.references[0].reference_name)
				for d in td_doc.daftar_tagihan:
					for t in doc.tagihan_payment_table:
						if d.no_sinv == t.no_sinv:
							baru = d.terbayarkan - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabDaftar Tagihan` SET terbayarkan= {} WHERE parent='{}' and no_sinv= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount - doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()
				
				# td_doc.flags.ignore_permissions = True
				# td_doc.save()

			if doc.references[0].reference_doctype == "Tagihan Discount Leasing" and not doc.tagihan_sipm:
				td_doc = frappe.get_doc("Tagihan Discount Leasing",doc.references[0].reference_name)
				for d in td_doc.daftar_tagihan_leasing:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.terbayarkan - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabDaftar Tagihan Leasing` SET terbayarkan= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount - doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()
			elif doc.references[0].reference_doctype == "Tagihan Discount Leasing" and doc.tagihan_sipm:
				td_doc = frappe.get_doc("Tagihan Discount Leasing",doc.references[0].reference_name)
				for d in td_doc.daftar_tagihan_leasing:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.outstanding_sipm - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.outstanding_sipm:
								frappe.db.sql("""UPDATE `tabDaftar Tagihan Leasing` SET outstanding_sipm= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.total_outstanding_tagihan_sipm - doc.paid_amount
				td_doc.total_outstanding_tagihan_sipm = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			# if doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and ('STNK' not in doc.party or 'BPKB' not in doc.party):
			if doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and not doc.tagihan_stnk and not doc.tagihan_bpkb:
				td_doc = frappe.get_doc("Pembayaran Tagihan Motor",doc.references[0].reference_name)
				for d in td_doc.tagihan_biaya_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.terbayarkan - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabChild Tagihan Biaya Motor` SET terbayarkan= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount - doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()
			elif doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and doc.tagihan_stnk:
				td_doc = frappe.get_doc("Pembayaran Tagihan Motor",doc.references[0].reference_name)
				for d in td_doc.tagihan_biaya_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.outstanding_stnk - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.outstanding_stnk:
								frappe.db.sql("""UPDATE `tabChild Tagihan Biaya Motor` SET outstanding_stnk= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount_stnk - doc.paid_amount
				td_doc.outstanding_amount_stnk = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			elif doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and doc.tagihan_bpkb:
				td_doc = frappe.get_doc("Pembayaran Tagihan Motor",doc.references[0].reference_name)
				for d in td_doc.tagihan_biaya_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.outstanding_bpkb - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.outstanding_bpkb:
								frappe.db.sql("""UPDATE `tabChild Tagihan Biaya Motor` SET outstanding_bpkb= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount_bpkb - doc.paid_amount
				td_doc.outstanding_amount_bpkb = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			if doc.references[0].reference_doctype == "Pembayaran Credit Motor":
				td_doc = frappe.get_doc("Pembayaran Credit Motor",doc.references[0].reference_name)
				for d in td_doc.daftar_credit_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.terbayarkan - t.nilai
							# d.terbayarkan = baru
							if t.nilai <= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabDaftar Credit Motor` SET terbayarkan= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount - doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()

def get_terbayarkan_cancel(doc,method):
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
	# if frappe.local.site in ["honda.digitalasiasolusindo.com","hondapjk.digitalasiasolusindo.com"]:
		if doc.tagihan == 1 and not doc.doc_type:
			# frappe.throw(doc.references[0].reference_name)
			if doc.references[0].reference_doctype == "Tagihan Discount":
				td_doc = frappe.get_doc("Tagihan Discount",doc.references[0].reference_name)
				for d in td_doc.daftar_tagihan:
					for t in doc.tagihan_payment_table:
						if d.no_sinv == t.no_sinv:
							baru = d.terbayarkan + t.nilai
							# d.terbayarkan = baru
							if t.nilai >= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabDaftar Tagihan` SET terbayarkan= {} WHERE parent='{}' and no_sinv= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount + doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()
				
				# td_doc.flags.ignore_permissions = True
				# td_doc.save()

			if doc.references[0].reference_doctype == "Tagihan Discount Leasing" and not doc.tagihan_sipm:
				td_doc = frappe.get_doc("Tagihan Discount Leasing",doc.references[0].reference_name)
				for d in td_doc.daftar_tagihan_leasing:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.terbayarkan + t.nilai
							# d.terbayarkan = baru
							if t.nilai >= d.terbayarkan:
								# frappe.throw("masek inis")
								frappe.db.sql("""UPDATE `tabDaftar Tagihan Leasing` SET terbayarkan= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							# else:
							# 	frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount + doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()
			elif doc.references[0].reference_doctype == "Tagihan Discount Leasing" and doc.tagihan_sipm:
				td_doc = frappe.get_doc("Tagihan Discount Leasing",doc.references[0].reference_name)
				for d in td_doc.daftar_tagihan_leasing:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.outstanding_sipm + t.nilai
							# d.terbayarkan = baru
							if t.nilai != d.outstanding_sipm:
								frappe.db.sql("""UPDATE `tabDaftar Tagihan Leasing` SET outstanding_sipm= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.total_outstanding_tagihan_sipm + doc.paid_amount
				td_doc.total_outstanding_tagihan_sipm = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			if doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and not doc.tagihan_stnk and not doc.tagihan_bpkb:
			# if doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and ('STNK' not in doc.party or 'BPKB' not in doc.party):
				td_doc = frappe.get_doc("Pembayaran Tagihan Motor",doc.references[0].reference_name)
				for d in td_doc.tagihan_biaya_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.terbayarkan + t.nilai
							# d.terbayarkan = baru
							print(t.nilai, d.terbayarkan, t.no_sinv)
							if t.nilai >= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabChild Tagihan Biaya Motor` SET terbayarkan= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount + doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			if doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and doc.tagihan_stnk:
				td_doc = frappe.get_doc("Pembayaran Tagihan Motor",doc.references[0].reference_name)
				for d in td_doc.tagihan_biaya_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.outstanding_stnk + t.nilai
							# d.terbayarkan = baru
							print(t.nilai, d.terbayarkan, t.no_sinv)
							if t.nilai >= d.outstanding_stnk:
								frappe.db.sql("""UPDATE `tabChild Tagihan Biaya Motor` SET outstanding_stnk= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount_stnk + doc.paid_amount
				td_doc.outstanding_amount_stnk = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			if doc.references[0].reference_doctype == "Pembayaran Tagihan Motor" and doc.tagihan_bpkb:
				td_doc = frappe.get_doc("Pembayaran Tagihan Motor",doc.references[0].reference_name)
				for d in td_doc.tagihan_biaya_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.outstanding_bpkb + t.nilai
							# d.terbayarkan = baru
							if t.nilai >= d.outstanding_bpkb:
								frappe.db.sql("""UPDATE `tabChild Tagihan Biaya Motor` SET outstanding_bpkb= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount_bpkb + doc.paid_amount
				td_doc.outstanding_amount_bpkb = oa_baru
				td_doc.db_update()
				frappe.db.commit()

			if doc.references[0].reference_doctype == "Pembayaran Credit Motor":
				td_doc = frappe.get_doc("Pembayaran Credit Motor",doc.references[0].reference_name)
				for d in td_doc.daftar_credit_motor:
					for t in doc.tagihan_payment_table:
						if d.no_invoice == t.no_sinv:
							baru = d.terbayarkan + t.nilai
							# d.terbayarkan = baru
							if t.nilai >= d.terbayarkan:
								frappe.db.sql("""UPDATE `tabDaftar Credit Motor` SET terbayarkan= {} WHERE parent='{}' and no_invoice= '{}' """.format(baru,doc.references[0].reference_name,t.no_sinv))
								frappe.db.commit()
							else:
								frappe.throw(t.no_sinv+" lebih besar dari yang terbayarkan !")
				oa_baru = td_doc.outstanding_amount + doc.paid_amount
				td_doc.outstanding_amount = oa_baru
				td_doc.db_update()
				frappe.db.commit()
				
				# td_doc.flags.ignore_permissions = True
				# td_doc.save()

def add_tanggalcair(self,method):
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
	# if frappe.local.site in ["honda.digitalasiasolusindo.com","hondapjk.digitalasiasolusindo.com"]:
		if self.tagihan_diskon_l or self.tipe_pembayaran == "Pembayaran Diskon Leasing":
			for i in self.tagihan_payment_table:
				frappe.msgprint(self.posting_date+i.no_sinv)
				frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set tanggal_cair = '{}' where name='{}' """.format(self.posting_date,i.no_sinv),debug=1)
				frappe.db.commit()

@frappe.whitelist()
def make_sipm(name_pe):
	cek = frappe.get_value("Sales Invoice Advance",{"reference_name": name_pe,"docstatus": ["!=",2]}, "parent")
	pemilik = frappe.get_doc("Payment Entry",name_pe).pemilik
	party = frappe.get_doc("Payment Entry",name_pe).party
	unallocated_amount = frappe.get_doc("Payment Entry",name_pe).unallocated_amount
	territory = frappe.get_doc("Customer",pemilik).territory
	customer_group = frappe.get_doc("Customer",pemilik).customer_group
	debit_to = frappe.get_doc("Party Account",{"parent":customer_group}).account

	if pemilik == party:
		cara_bayar = "Cash"
	else:
		cara_bayar = "Credit"

	if not cek:
		target_doc = frappe.new_doc("Sales Invoice Penjualan Motor")
		target_doc.pemilik = pemilik
		target_doc.customer = party
		target_doc.cara_bayar = cara_bayar
		target_doc.territory_real = territory
		target_doc.territory_biaya = territory
		target_doc.debit_to = debit_to
		row = target_doc.append('advances', {})
		row.reference_type = "Payment Entry"
		row.reference_name = name_pe
		row.advance_amount = unallocated_amount
		row.allocated_amount = unallocated_amount
		return target_doc.as_dict()
	else:
		frappe.throw(_(' Sudah ada di {0} !').format(frappe.utils.get_link_to_form('Sales Invoice Penjualan Motor', cek)))

