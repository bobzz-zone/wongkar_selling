import frappe
from six import iteritems, string_types
import json
import erpnext
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, get_link_to_form, nowdate

@frappe.whitelist()
def get_adv_leasing(self,method):
	# if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if self.advance_leasing:
			cek = frappe.get_doc("Advance Leasing",self.advance_leasing).journal_entry
			if cek:
				frappe.throw("Sudah ada No Je di "+self.advance_leasing+" !s")
			else:
				frappe.db.sql(""" UPDATE `tabAdvance Leasing` set journal_entry = '{}' where name= '{}' """.format(self.name,self.advance_leasing))
				

@frappe.whitelist()
def get_adv_leasing_cancel(self,method):
	# if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if self.advance_leasing:
			frappe.db.sql(""" UPDATE `tabAdvance Leasing` set journal_entry = '{}' where name= '{}' """.format("",self.advance_leasing))

@frappe.whitelist()
def get_penerimaan_dp(self,method):
	# self.ignore_linked_doctypes = ('Penerimaan DP')
	if self.penerimaan_dp:
		cek = frappe.get_doc("Penerimaan DP",self.penerimaan_dp).docstatus
		if cek == 1:
			frappe.throw("Dokeumen Peneriamaan DP "+self.penerimaan_dp+" masih SUbmit !")

@frappe.whitelist()
def cek_cancel_adv_leasing(self,method):
	if self.advance_leasing:
		cek = frappe.get_doc("Advance Leasing",self.advance_leasing)

		if cek.sisa <= 0:
			frappe.throw("Sisa di advance Leasing "+self.advance_leasing+" sudah di tansfer !!")
		elif cek.terpakai > 0:
			frappe.throw("Advance Leasing "+self.advance_leasing+" sudah terpakai !!")

@frappe.whitelist()
def get_outstanding_custom(args):
	# frappe.msgprint("test !")
	if not frappe.has_permission("Account"):
		frappe.msgprint(_("No Permission"), raise_exception=1)

	if isinstance(args, string_types):
		args = json.loads(args)

	company_currency = erpnext.get_company_currency(args.get("company"))

	if args.get("doctype") == "Journal Entry":
		condition = " and party=%(party)s" if args.get("party") else ""

		against_jv_amount = frappe.db.sql(
			"""
			select sum(debit_in_account_currency) - sum(credit_in_account_currency)
			from `tabJournal Entry Account` where parent=%(docname)s and account=%(account)s {0}
			and (reference_type is null or reference_type = '')""".format(
				condition
			),
			args,
		)

		against_jv_amount = flt(against_jv_amount[0][0]) if against_jv_amount else 0
		amount_field = (
			"credit_in_account_currency" if against_jv_amount > 0 else "debit_in_account_currency"
		)
		return {amount_field: abs(against_jv_amount)}
	elif args.get("doctype") in ("Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor","Invoice Penagihan Garansi"):
		party_type = "Customer" if args.get("doctype") in ["Sales Invoice","Sales Invoice Penjualan Motor","Invoice Penagihan Garansi"] else "Supplier"
		if args.get("doctype") in ("Invoice Penagihan Garansi"):
			pass
		else:
			invoice = frappe.db.get_value(
				args["doctype"],
				args["docname"],
				["outstanding_amount", "conversion_rate", scrub(party_type)],
				as_dict=1,
			)

		exchange_rate = (
			invoice.conversion_rate if (args.get("account_currency") != company_currency) else 1
		)

		if args["doctype"] == "Sales Invoice":
			amount_field = (
				"credit_in_account_currency"
				if flt(invoice.outstanding_amount) > 0
				else "debit_in_account_currency"
			)
		else:
			amount_field = (
				"debit_in_account_currency"
				if flt(invoice.outstanding_amount) > 0
				else "credit_in_account_currency"
			)

		return {
			amount_field: abs(flt(invoice.outstanding_amount)),
			"exchange_rate": exchange_rate,
			"party_type": party_type,
			"party": invoice.get(scrub(party_type)),
		}


@frappe.whitelist()
def hitung_total_claim():
	self = frappe.get_doc('Journal Entry','ACC-JV-2024-01369-1')
	tmp = []
	if self.tagihan_payment_table and len(self.tagihan_payment_table) > 0:
		for i in self.tagihan_payment_table:
			for j in self.list_doc_name:
				if i.doc_name == j.docname:
					tmp.append({
							'docname': i.doc_name,
							'nilai': i.nilai
						})

	print(tmp, ' tmpclaim')

@frappe.whitelist()
def hitung_outstanding_claim(self,method):
	if self.docstatus == 1:
		if self.tagihan_payment_table and len(self.tagihan_payment_table) > 0:
			for i in self.tagihan_payment_table:
				nilai = frappe.get_doc('List Invoice Penagihan Garansi',i.id_detail).outstanding_amount_oli
				if nilai < i.nilai:
					frappe.throw('Nilai yang di bayar lebih besar !')
				else:
					hasil = nilai - i.nilai
					frappe.db.sql(""" UPDATE `tabList Invoice Penagihan Garansi` 
						set outstanding_amount_oli = {} where name = '{}' """.format(hasil,i.id_detail),debug=0)
		# frappe.throw('sss')
	elif self.docstatus == 2:
		if self.tagihan_payment_table and len(self.tagihan_payment_table) > 0:
			for i in self.tagihan_payment_table:
				nilai = frappe.get_doc('List Invoice Penagihan Garansi',i.id_detail).outstanding_amount_oli
				if nilai > i.nilai:
					frappe.throw('Nilai yang di bayar lebih besar !')
				else:
					hasil = nilai + i.nilai
					frappe.db.sql(""" UPDATE `tabList Invoice Penagihan Garansi` 
						set outstanding_amount_oli = {} where name = '{}' """.format(hasil,i.id_detail))
