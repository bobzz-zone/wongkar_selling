# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.reportview import get_match_cond, get_filters_cond

from erpnext.accounts.doctype.payment_entry.payment_entry import get_account_details


class AdvanceLeasing(Document):
	def validate(self):
		self.sisa = self.nilai - self.terpakai

	def on_submit(self):
		pass
		# if not self.journal_entry:
		# 	frappe.throw("Journal Belum Terbentuk !")


@frappe.whitelist()
def make_pe(name_fp,sisa,account_debit):
	doc_pe = frappe.new_doc("Payment Entry")
	doc_pe.advance_leasing = name_fp
	doc_pe.payment_type = "Internal Transfer"
	doc_pe.down_payment = 0
	doc_pe.cek_adv_leasing = 1
	doc_pe.paid_from = account_debit
	doc_pe.paid_amount = sisa
	doc_pe.received_amount = sisa
	acc = get_account_details(doc_pe.paid_from, doc_pe.posting_date, doc_pe.cost_center)
	doc_pe.paid_from_account_currency = acc.account_currency
	doc_pe.paid_from_account_balance = acc.account_balance
	doc_pe.flags.ignore_permissions = True
	

	return doc_pe.as_dict()

@frappe.whitelist()
def make_je(name_fp,nilai,tanggal,account_debit,account_credit,leasing):
	doc_je = frappe.new_doc("Journal Entry")
	doc_je.advance_leasing = name_fp
	doc_je.posting_date = tanggal
	doc_je.flags.ignore_permissions = True
	row = doc_je.append('accounts', {})
	row.debit_in_account_currency = nilai
	row.account = account_debit

	row_c = doc_je.append('accounts', {})
	row_c.credit_in_account_currency = nilai
	# row_c.party_type = "Customer"
	# row_c.party = leasing
	row_c.account = account_credit
	
	return doc_je.as_dict()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def je_query(doctype, txt, searchfield, start, page_len, filters):
	conditions = []
	
	# fields = get_fields("Journal Entry", fields)

	searchfields = frappe.get_meta("Journal Entry").get_search_fields()
	searchfields = " or ".join(field + " like %(txt)s" for field in searchfields)

	return frappe.db.sql("""select `tabJournal Entry`.name from `tabJournal Entry`
		join `tabJournal Entry Account`  on `tabJournal Entry Account`.parent = `tabJournal Entry`.name
		where `tabJournal Entry`.docstatus = 1 {fcond}
		group by `tabJournal Entry`.name
		order by
			if(locate(%(_txt)s, `tabJournal Entry`.name), locate(%(_txt)s, `tabJournal Entry`.name), 99999),
			`tabJournal Entry`.name desc
		limit %(start)s, %(page_len)s""".format(**{
			"scond": searchfields,
			"mcond": get_match_cond(doctype),
			"fcond": get_filters_cond(doctype, filters, conditions).replace('%', '%%'),
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		},debug=1)

@frappe.whitelist()
def get_je(name):
	data = frappe.db.sql(""" SELECT jea.debit,jea.account,je.posting_date
		from `tabJournal Entry` je 
		join `tabJournal Entry Account` jea on jea.parent = je.name
		where je.name = '{}' and jea.debit > 0 """.format(name),as_dict=1)

	return data
