# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import date
import datetime
# from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
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
from frappe.utils import flt, comma_or, nowdate, getdate
from frappe.frappeclient import FrappeClient
from erpnext.setup.utils import get_exchange_rate


class InvalidPaymentEntry(ValidationError):
	pass

@frappe.whitelist()
def cancel_doc():
	doc = frappe.get_doc("Sales Invoice Penjualan Motor","ACC-SINVM-2022-00881")
	doc.cancel()


@frappe.whitelist()
def test_connection():

	print("https://wongkarpjk.digitalasiasolusindo.com/")
	producer_site = FrappeClient(
		url="https://wongkarpjk.digitalasiasolusindo.com",
		api_key="73379ff8b42a48f",
		api_secret="c1f8382a677fcaf"
		)
	# data = {"event_consumer": "http://hondatax.digitalasiasolusindo.com", "consumer_doctypes": "[{\"doctype\": \"Item\", \"condition\": null}]", "user": "sync@das.com", "api_key": "087612f0ae2a33b", "api_secret": "30a9e7a6deecf18"}
	# try:
	# 	response = producer_site.post_api(
	# 		'frappe.event_streaming.doctype.event_consumer.event_consumer.register_consumer',
	# 		params={'data': data}
	# 	)
	# except:
	# 	print(str(producer_site.session['user']))

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

	outstanding_invoices = get_outstanding_invoices_cutom(args.get("party_type"), args.get("party"),
		args.get("party_account"), filters=args, condition=condition)
	# frappe.msgprint("coba oa"+str(outstanding_invoices))

	outstanding_invoices = split_invoices_based_on_payment_terms(outstanding_invoices)

	for d in outstanding_invoices:
		d["exchange_rate"] = 1
		if party_account_currency != company_currency:
			if d.voucher_type in ("Sales Invoice", "Purchase Invoice", "Expense Claim","Sales Invoice Penjualan Motor"):
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

def split_invoices_based_on_payment_terms(outstanding_invoices):
	invoice_ref_based_on_payment_terms = {}
	for idx, d in enumerate(outstanding_invoices):
		if d.voucher_type in ['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor']:
			payment_term_template = frappe.db.get_value(d.voucher_type, d.voucher_no, 'payment_terms_template')
			if payment_term_template:
				allocate_payment_based_on_payment_terms = frappe.db.get_value(
					'Payment Terms Template', payment_term_template, 'allocate_payment_based_on_payment_terms')
				if allocate_payment_based_on_payment_terms:
					payment_schedule = frappe.get_all('Payment Schedule', filters={'parent': d.voucher_no}, fields=["*"])

					for payment_term in payment_schedule:
						if payment_term.outstanding > 0.1:
							invoice_ref_based_on_payment_terms.setdefault(idx, [])
							invoice_ref_based_on_payment_terms[idx].append(frappe._dict({
								'due_date': d.due_date,
								'currency': d.currency,
								'voucher_no': d.voucher_no,
								'voucher_type': d.voucher_type,
								'posting_date': d.posting_date,
								'invoice_amount': flt(d.invoice_amount),
								'outstanding_amount': flt(d.outstanding_amount),
								'payment_amount': payment_term.payment_amount,
								'payment_term': payment_term.payment_term,
								'allocated_amount': payment_term.outstanding
							}))

def get_outstanding_invoices_cutom(party_type, party, account, condition=None, filters=None):
	# frappe.msgprint("mauk get_outstanding_invoices_cutom")
	outstanding_invoices = []
	precision = frappe.get_precision("Sales Invoice", "outstanding_amount") or 2
	# precision = frappe.get_precision("Sales Invoice Penjualan Motor", "outstanding_amount") or 2
	if account:
		root_type, account_type = frappe.get_cached_value("Account", account, ["root_type", "account_type"])
		party_account_type = "Receivable" if root_type == "Asset" else "Payable"
		party_account_type = account_type or party_account_type
	else:
		party_account_type = erpnext.get_party_account_type(party_type)

	if party_account_type == 'Receivable':
		dr_or_cr = "debit_in_account_currency - credit_in_account_currency"
		payment_dr_or_cr = "credit_in_account_currency - debit_in_account_currency"
	else:
		dr_or_cr = "credit_in_account_currency - debit_in_account_currency"
		payment_dr_or_cr = "debit_in_account_currency - credit_in_account_currency"

	held_invoices = get_held_invoices(party_type, party)

	invoice_list = frappe.db.sql("""
		select
			voucher_no, voucher_type, posting_date, due_date,
			ifnull(sum({dr_or_cr}), 0) as invoice_amount,
			account_currency as currency
		from
			`tabGL Entry`
		where
			party_type = %(party_type)s and party = %(party)s
			and account = %(account)s and {dr_or_cr} > 0
			and is_cancelled=0
			{condition}
			and ((voucher_type = 'Journal Entry'
					and (against_voucher = '' or against_voucher is null))
				or (voucher_type not in ('Journal Entry', 'Payment Entry')))
		group by voucher_type, voucher_no
		order by posting_date, name""".format(
			dr_or_cr=dr_or_cr,
			condition=condition or ""
		), {
			"party_type": party_type,
			"party": party,
			"account": account,
		}, as_dict=True)

	payment_entries = frappe.db.sql("""
		select against_voucher_type, against_voucher,
			ifnull(sum({payment_dr_or_cr}), 0) as payment_amount
		from `tabGL Entry`
		where party_type = %(party_type)s and party = %(party)s
			and account = %(account)s
			and {payment_dr_or_cr} > 0
			and against_voucher is not null and against_voucher != ''
			and is_cancelled=0
		group by against_voucher_type, against_voucher
	""".format(payment_dr_or_cr=payment_dr_or_cr), {
		"party_type": party_type,
		"party": party,
		"account": account
	}, as_dict=True)

	pe_map = frappe._dict()
	for d in payment_entries:
		pe_map.setdefault((d.against_voucher_type, d.against_voucher), d.payment_amount)

	for d in invoice_list:
		payment_amount = pe_map.get((d.voucher_type, d.voucher_no), 0)
		outstanding_amount = flt(d.invoice_amount - payment_amount, precision)
		if outstanding_amount > 0.5 / (10**precision):
			if (filters and filters.get("outstanding_amt_greater_than") and
				not (outstanding_amount >= filters.get("outstanding_amt_greater_than") and
				outstanding_amount <= filters.get("outstanding_amt_less_than"))):
				continue

			if not d.voucher_type == "Purchase Invoice" or d.voucher_no not in held_invoices:
				outstanding_invoices.append(
					frappe._dict({
						'voucher_no': d.voucher_no,
						'voucher_type': d.voucher_type,
						'posting_date': d.posting_date,
						'invoice_amount': flt(d.invoice_amount),
						'payment_amount': payment_amount,
						'outstanding_amount': outstanding_amount,
						'due_date': d.due_date,
						'currency': d.currency
					})
				)

	outstanding_invoices = sorted(outstanding_invoices, key=lambda k: k['due_date'] or getdate(nowdate()))
	return outstanding_invoices

def get_held_invoices(party_type, party):
	"""
	Returns a list of names Purchase Invoices for the given party that are on hold
	"""
	held_invoices = None

	if party_type == 'Supplier':
		held_invoices = frappe.db.sql(
			'select name from `tabPurchase Invoice` where release_date IS NOT NULL and release_date > CURDATE()',
			as_dict=1
		)
		held_invoices = set([d['name'] for d in held_invoices])

	return held_invoices

@frappe.whitelist()
def get_reference_details_chandra(reference_doctype, tipe_pembayaran,reference_name, party_account_currency):
	# frappe.msgprint("MASUK KE METHOD GANTI@")
	# frappe.msgprint(tipe_pembayaran+" tipe_pembayaran")
	total_amount = outstanding_amount = exchange_rate = bill_no = None
	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)
	# frappe.msgprint(reference_doctype+" reference_doctype")
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
			# frappe.msgprint('masuk Sales Invoice Penjualan Motor')
			outstanding_amount = ref_doc.get("outstanding_amount")
			bill_no = ref_doc.get("bill_no")
			# frappe.msgprint("oa "+str(outstanding_amount))
			# frappe.msgprint("bill "+str(bill_no))
		elif reference_doctype == "Tagihan Discount":
			total_amount = ref_doc.grand_total
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.grand_total
		elif reference_doctype == "Tagihan Discount Leasing" and not ref_doc.tagihan_sipm and not tipe_pembayaran:
			# frappe.msgprint("Tagihan Discount Leasing 1ab")
			total_amount = ref_doc.grand_total
			outstanding_amount = ref_doc.outstanding_amount
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Tagihan Discount Leasing" and ref_doc.tagihan_sipm and not tipe_pembayaran:
			# frappe.msgprint("Tagihan Discount Leasing 2sdsdcd")
			total_amount = ref_doc.total_tagihan_sipm
			outstanding_amount = ref_doc.total_outstanding_tagihan_sipm
			bill_no = ref_doc.get("bill_no")
		elif reference_doctype == "Pembayaran Credit Motor":
			total_amount = ref_doc.grand_total
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount
		elif reference_doctype == "Pembayaran Tagihan Motor" and not ref_doc.tagihan_stnk and not tipe_pembayaran and not ref_doc.tagihan_bpkb:
			total_amount = ref_doc.grand_total
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount
		elif reference_doctype == "Pembayaran Tagihan Motor" and ref_doc.tagihan_stnk and not ref_doc.tagihan_bpkb:
			total_amount = ref_doc.total_stnk
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount_stnk
		elif reference_doctype == "Pembayaran Tagihan Motor" and ref_doc.tagihan_bpkb and not ref_doc.tagihan_stnk:
			total_amount = ref_doc.total_bpkb
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount_bpkb
		elif reference_doctype == "Pembayaran Tagihan Motor" and tipe_pembayaran == "Pembayaran STNK":
			# frappe.msgprint("sksksksks")
			total_amount = ref_doc.total_stnk
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount_stnk
		elif reference_doctype == "Pembayaran Tagihan Motor" and tipe_pembayaran == "Pembayaran BPKB":
			# frappe.msgprint("sksksksks")
			total_amount = ref_doc.total_bpkb
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount_bpkb
		elif reference_doctype == "Pembayaran Tagihan Motor" and tipe_pembayaran == "Pembayaran Diskon Dealer":
			# frappe.msgprint("sksksksks")
			total_amount = ref_doc.grand_total
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount
		elif reference_doctype == "Tagihan Discount Leasing" and tipe_pembayaran == "Pembayaran Diskon Leasing":
			# frappe.msgprint("sksksksks")
			total_amount = ref_doc.grand_total
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.outstanding_amount
		elif reference_doctype == "Tagihan Discount Leasing" and tipe_pembayaran == "Pembayaran SIPM":
			# frappe.msgprint("sksksksks")
			total_amount = ref_doc.total_tagihan_sipm
			bill_no = ref_doc.get("bill_no")
			outstanding_amount = ref_doc.total_outstanding_tagihan_sipm
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
			# frappe.msgprint('masuk Sales Invoice Penjualan Motor else')
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

def on_submit_chandra(self):
	# frappe.msgprint("mausk on_submit_chandra")
	self.setup_party_account_field()
	if self.difference_amount:
		frappe.throw(_("Difference Amount must be zero"))
	self.make_gl_entries()
	update_outstanding_amounts_chandra(self)
	update_advance_paid_lutfi(self)
	# get_outstanding_reference_documents_custom(self)
	self.update_expense_claim()
	self.update_donation()
	update_payment_schedule_lutfi(self)
	self.set_status()

def on_cancel_chandra(self):
	# frappe.msgprint("on_cancel_chandra")
	self.ignore_linked_doctypes = ('GL Entry', 'Stock Ledger Entry')
	self.setup_party_account_field()
	self.make_gl_entries(cancel=1)
	update_outstanding_amounts_chandra(self)
	update_advance_paid_lutfi(self)
	self.update_expense_claim()
	self.update_donation(cancel=1)
	self.delink_advance_entry_references()
	update_payment_schedule_lutfi(self,cancel=1)
	self.set_payment_req_status()
	self.set_status()

def validate_lutfi(self):
	# frappe.msgprint("masuk validate_lutfi")
	self.setup_party_account_field()
	set_missing_values_lutfi(self)
	cek_payment(self)
	# bagi_alocated(self)
	# get_data_tagihan(self)
	self.validate_payment_type()
	self.validate_party_details()
	self.validate_bank_accounts()
	self.set_exchange_rate()
	self.validate_mandatory()
	validate_reference_documents_lutfi(self)
	# kalkulasi_oa_cancel(self)
	self.set_amounts()
	self.clear_unallocated_reference_document_rows()
	validate_payment_against_negative_invoice(self)
	# self.validate_payment_against_negative_invoice()
	self.validate_transaction_reference()
	self.set_title()
	self.set_remarks()
	self.validate_duplicate_entry()
	self.validate_allocated_amount()
	self.validate_paid_invoices()
	self.ensure_supplier_is_not_blocked()
	self.set_status()


def cek_payment(self):
	# if frappe.local.site in ["honda.digitalasiasolusindo.com","hondapjk.digitalasiasolusindo.com"]:
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com"]:
		if self.doc_type:
			if self.doc_type == "Pembayaran Tagihan Motor":
				if self.payment_type != "Pay":
					frappe.throw("Salah Memilih Payment Tyepe")
			else:
				if self.payment_type != "Receive":
					frappe.throw("Salah Memilih Payment Tyepe")
	
# def get_data_tagihan(self):
# 	tmp = []
# 	for i in self.references:
# 		frappe.msgprint(i.reference_name)
# 		data = frappe.db.sql(""" SELECT 
# 			pemilik,
# 			item,
# 			no_rangka,
# 			outstanding_stnk,
# 			parenttype,
# 			parent 
# 			from `tabChild Tagihan Biaya Motor` where parent = '{}' """.format(i.reference_name),as_dict=1)
# 		if data:
# 			tmp.append(data)
	
# 	for t in tmp:
# 		frappe.msgprint(t)


def bagi_alocated(self):
	# res = {}
	# for item in self.tagihan_payment_table:
	# 	res.setdefault(item['doc_name'], []).append(item)
	# frappe.msgprint(str(res)+" res")
	# frappe.msgprint(str(self.name)+ " self.name")
	# frappe.msgprint(str(self.tagihan_payment_table)+ " self.tagihan_payment_table")
	tmp = []
	for i in self.tagihan_payment_table:
		tmp.append(i)

	# frappe.msgprint(str(tmp)+ "tmp")




def update_payment_schedule_lutfi(self, cancel=0):
	# frappe.msgprint("masuk update_payment_schedule_lutfi")
	invoice_payment_amount_map = {}
	invoice_paid_amount_map = {}

	for ref in self.get('references'):
		if ref.payment_term and ref.reference_name:
			key = (ref.payment_term, ref.reference_name)
			invoice_payment_amount_map.setdefault(key, 0.0)
			invoice_payment_amount_map[key] += ref.allocated_amount

			if not invoice_paid_amount_map.get(key):
				payment_schedule = frappe.get_all(
					'Payment Schedule',
					filters={'parent': ref.reference_name},
					fields=['paid_amount', 'payment_amount', 'payment_term', 'discount', 'outstanding']
				)
				for term in payment_schedule:
					invoice_key = (term.payment_term, ref.reference_name)
					invoice_paid_amount_map.setdefault(invoice_key, {})
					invoice_paid_amount_map[invoice_key]['outstanding'] = term.outstanding
					invoice_paid_amount_map[invoice_key]['discounted_amt'] = ref.total_amount * (term.discount / 100)

	for key, allocated_amount in iteritems(invoice_payment_amount_map):
		outstanding = flt(invoice_paid_amount_map.get(key, {}).get('outstanding'))
		discounted_amt = flt(invoice_paid_amount_map.get(key, {}).get('discounted_amt'))

		if cancel:
			frappe.db.sql("""
				UPDATE `tabPayment Schedule`
				SET
					paid_amount = `paid_amount` - %s,
					discounted_amount = `discounted_amount` - %s,
					outstanding = `outstanding` + %s
				WHERE parent = %s and payment_term = %s""",
				(allocated_amount - discounted_amt, discounted_amt, allocated_amount, key[1], key[0]))
		else:
			if allocated_amount > outstanding:
				frappe.throw(_('Cannot allocate more than {0} against payment term {1}').format(outstanding, key[0]))

			if allocated_amount and outstanding:
				frappe.db.sql("""
					UPDATE `tabPayment Schedule`
					SET
						paid_amount = `paid_amount` + %s,
						discounted_amount = `discounted_amount` + %s,
						outstanding = `outstanding` - %s
					WHERE parent = %s and payment_term = %s""",
				(allocated_amount - discounted_amt, discounted_amt, allocated_amount, key[1], key[0]))

def update_advance_paid_lutfi(self):
	if self.payment_type in ("Receive", "Pay") and self.party:
		for d in self.get("references"):
			if d.allocated_amount \
				and d.reference_doctype in ("Sales Order", "Purchase Order", "Employee Advance", "Gratuity"):
					frappe.get_doc(d.reference_doctype, d.reference_name).set_total_advance_paid()

def set_missing_values_lutfi(self):
	# frappe.throw("lutfi")
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

	set_missing_ref_details_chandra(self,force=True)

def update_outstanding_amounts_chandra(self):
	# frappe.msgprint("masuk update_outstanding_amounts_chandra")
	set_missing_ref_details_chandra(self,force=True)

def set_missing_ref_details_chandra(self, force=False):
	# frappe.msgprint("masuk set_missing_ref_details_chandra")

	tipe_pembayaran=None
	try:
		tipe_pembayaran=self.tipe_pembayaran
	except:
		tipe_pembayaran=None
	for d in self.get("references"):
		if d.allocated_amount:
			ref_details = get_reference_details_chandra(d.reference_doctype,tipe_pembayaran,
				d.reference_name, self.party_account_currency)
			for field, value in iteritems(ref_details):
				if field == 'exchange_rate' or not d.get(field) or force:
					d.set(field, value)
def validate_reference_documents_lutfi(self):
	if self.party_type == "Student":
		valid_reference_doctypes = ("Fees")
	elif self.party_type == "Customer":
		valid_reference_doctypes = ("Sales Order", "Sales Invoice", "Journal Entry", "Dunning","Sales Invoice Penjualan Motor","Tagihan Discount","Tagihan Discount Leasing","Pembayaran Credit Motor")
	elif self.party_type == "Supplier":
		valid_reference_doctypes = ("Purchase Order", "Purchase Invoice", "Journal Entry","Pembayaran Tagihan Motor")
	elif self.party_type == "Employee":
		valid_reference_doctypes = ("Expense Claim", "Journal Entry", "Employee Advance", "Gratuity")
	elif self.party_type == "Shareholder":
		valid_reference_doctypes = ("Journal Entry")
	elif self.party_type == "Donor":
		valid_reference_doctypes = ("Donation")

	for d in self.references:
		if not d.allocated_amount:
			# frappe.msgprint("masuk sini ssss")
			continue
		if d.reference_doctype not in valid_reference_doctypes:
			frappe.throw(_("Reference Doctype must be one of {0}")
				.format(comma_or(valid_reference_doctypes)))

		elif d.reference_name:
			if not frappe.db.exists(d.reference_doctype, d.reference_name):
				frappe.throw(_("{0} {1} does not exist").format(d.reference_doctype, d.reference_name))
			else:
				ref_doc = frappe.get_doc(d.reference_doctype, d.reference_name)
				if d.reference_doctype == "Pembayaran Tagihan Motor":
					return
				if d.reference_doctype != "Journal Entry":
					if self.party != ref_doc.get(scrub(self.party_type)):
						frappe.throw(_("{0} {1} is not associated with {2} {3}")
							.format(d.reference_doctype, d.reference_name, self.party_type, self.party))
				else:
					self.validate_journal_entry()

				if d.reference_doctype in ("Sales Invoice", "Purchase Invoice", "Expense Claim", "Fees"):
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

def validate_payment_against_negative_invoice(self):
	if ((self.payment_type=="Pay" and self.party_type=="Customer")
			or (self.payment_type=="Receive" and self.party_type=="Supplier")):

		total_negative_outstanding = sum([abs(flt(d.outstanding_amount))
			for d in self.get("references") if flt(d.outstanding_amount) < 0])
			#for d in self.get("references") if d.reference_doctype == "Tagihan Discount" and flt(d.outstanding_amount) > 0 or flt(d.outstanding_amount) < 0])
		
		paid_amount = self.paid_amount if self.payment_type=="Receive" else self.received_amount
		additional_charges = sum([flt(d.amount) for d in self.deductions])
		# frappe.msgprint(str(total_negative_outstanding))

		if not total_negative_outstanding:
			# frappe.msgprint("tes llutfi")
			frappe.throw(_("Cannot {0} {1} {2} without any negative outstanding invoice")
				.format(self.payment_type, ("to" if self.party_type=="Customer" else "from"),
					self.party_type), InvalidPaymentEntry)

		elif paid_amount - additional_charges > total_negative_outstanding:
			frappe.throw(_("Paid Amount cannot be greater than total negative outstanding amount {0}")
				.format(total_negative_outstanding), InvalidPaymentEntry)

PaymentEntry.on_submit = on_submit_chandra
PaymentEntry.on_cancel = on_cancel_chandra
PaymentEntry.validate = validate_lutfi


def kalkulasi_oa(doc,method):
	# frappe.msgprint("kalkulasi_oa")
	# cek = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	# for c in cek:
	# 	if c['reference_doctype'] == 'Sales Invoice Penjualan Motor'
	total = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	name = ''
	for i in total:
		if i['reference_doctype'] == 'Sales Invoice Penjualan Motor':
			hasil = doc.paid_amount - i['outstanding_amount']
			docs = frappe.get_doc("Sales Invoice Penjualan Motor",i['reference_name'])
			docs.outstanding_amount = hasil
			# docs.flags.ignore_permission = True
			# docs.save()
			docs.status = 'Paid'
			docs.db_update()
			frappe.db.commit()

def kalkulasi_oa_cancel(doc,method):
	# frappe.msgprint("kalkulasi_oa_cancel")
	# cek = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	# for c in cek:
	# 	if c['reference_doctype'] == 'Sales Invoice Penjualan Motor'
	total = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	name = ''
	for i in total:
		if i['reference_doctype'] == 'Sales Invoice Penjualan Motor':
			# hasil = doc.paid_amount + i['outstanding_amount']
			hasil = doc.paid_amount
			docs = frappe.get_doc("Sales Invoice Penjualan Motor",i['reference_name'])
			docs.outstanding_amount = hasil
			# docs.flags.ignore_permission = True
			# docs.save()
			docs.status = 'Unpaid'
			docs.db_update()
			frappe.db.commit()

def kalkulasi_tagihan(doc,method):
	# frappe.msgprint("kalkulasi_oa")
	# cek = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	# for c in cek:
	# 	if c['reference_doctype'] == 'Sales Invoice Penjualan Motor'
	total = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	name = ''
	for i in total:
		if i['reference_doctype'] == 'Tagihan Discount':
			hasil = doc.paid_amount - i['outstanding_amount']
			docs = frappe.get_doc("Tagihan Discount",i['reference_name'])
			docs.grand_total = hasil
			# docs.flags.ignore_permission = True
			# docs.save()
			docs.status = 'Paid'
			docs.db_update()
			frappe.db.commit()

		# tagihan discoun leasing
		if i['reference_doctype'] == 'Tagihan Discount Leasing':
			hasil = doc.paid_amount - i['outstanding_amount']
			docs = frappe.get_doc("Tagihan Discount Leasing",i['reference_name'])
			docs.grand_total = hasil
			# docs.flags.ignore_permission = True
			# docs.save()
			docs.status = 'Paid'
			docs.db_update()
			frappe.db.commit()

		# Pembayaran tagihan Motor
		if i['reference_doctype'] == 'Pembayaran Tagihan Motor':
			hasil = doc.paid_amount - i['outstanding_amount']
			docs = frappe.get_doc("Pembayaran Tagihan Motor",i['reference_name'])
			docs.grand_total = hasil
			# docs.flags.ignore_permission = True
			# docs.save()
			docs.status = 'Paid'
			docs.db_update()
			frappe.db.commit()

		# Pembayaran Credit Motor
		if i['reference_doctype'] == 'Pembayaran Credit Motor':
			hasil = doc.paid_amount - i['outstanding_amount']
			docs = frappe.get_doc("Pembayaran Credit Motor",i['reference_name'])
			docs.grand_total = hasil
			# docs.flags.ignore_permission = True
			# docs.save()
			docs.status = 'Paid'
			docs.db_update()
			frappe.db.commit()

def kalkulasi_tagihan_cancel(doc,method):
	pass
	# # frappe.msgprint("kalkulasi_oa")
	# # cek = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	# # for c in cek:
	# # 	if c['reference_doctype'] == 'Sales Invoice Penjualan Motor'
	# total = frappe.db.get_list('Payment Entry Reference',filters={'parent': doc.name},fields=['*'])
	# name = ''
	# for i in total:
	# 	if i['reference_doctype'] == 'Tagihan Discount':
	# 		hasil = doc.paid_amount
	# 		docs = frappe.get_doc("Tagihan Discount",i['reference_name'])
	# 		docs.grand_total = hasil
	# 		# docs.flags.ignore_permission = True
	# 		# docs.save()
	# 		docs.status = 'Submitted'
	# 		docs.db_update()
	# 		frappe.db.commit()

	# 	# tagihan discoun leasing
	# 	if i['reference_doctype'] == 'Tagihan Discount Leasing':
	# 		hasil = doc.paid_amount
	# 		docs = frappe.get_doc("Tagihan Discount Leasing",i['reference_name'])
	# 		docs.grand_total = hasil
	# 		# docs.flags.ignore_permission = True
	# 		# docs.save()
	# 		docs.status = 'Submitted'
	# 		docs.db_update()
	# 		frappe.db.commit()

	# 	# Pembayaran tagihan Motor
	# 	if i['reference_doctype'] == 'Pembayaran Tagihan Motor':
	# 		hasil = doc.paid_amount
	# 		docs = frappe.get_doc("Pembayaran Tagihan Motor",i['reference_name'])
	# 		docs.grand_total = hasil
	# 		# docs.flags.ignore_permission = True
	# 		# docs.save()
	# 		docs.status = 'Submitted'
	# 		docs.db_update()
	# 		frappe.db.commit()

	# 	# Pembayaran Credit Motor
	# 	if i['reference_doctype'] == 'Pembayaran Credit Motor':
	# 		hasil = doc.paid_amount
	# 		docs = frappe.get_doc("Pembayaran Credit Motor",i['reference_name'])
	# 		docs.grand_total = hasil
	# 		# docs.flags.ignore_permission = True
	# 		# docs.save()
	# 		docs.status = 'Submitted'
	# 		docs.db_update()
	# 		frappe.db.commit()

def override_on_submit_on_cancel(self,method):
	# if frappe.local.site in ["honda.digitalasiasolusindo.com","hondapjk.digitalasiasolusindo.com"]:
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com"]:
		PaymentEntry.validate = validate_lutfi
	
def coba():
	frappe.throw("Coba cencel")


@frappe.whitelist()
def get_account_details(account, date, cost_center=None):
	frappe.has_permission('Payment Entry', throw=True)

	# to check if the passed account is accessible under reference doctype Payment Entry
	account_list = frappe.get_list('Account', {
		'name': account
	}, reference_doctype='Payment Entry', limit=1)

	# There might be some user permissions which will allow account under certain doctypes
	# except for Payment Entry, only in such case we should throw permission error
	if not account_list:
		frappe.throw(_('Account: {0} is not permitted under Payment Entry').format(account))

	account_balance = get_balance_on(account, date, cost_center=cost_center,
		ignore_account_permission=True)

	return frappe._dict({
		"account_currency": get_account_currency(account),
		"account_balance": account_balance,
		"account_type": frappe.db.get_value("Account", account, "account_type")
	})
