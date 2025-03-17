# Copyright (c) 2023, w and contributors
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
from frappe import _, bold, qb, throw

class FormPembayaran(Document):
	def cek_double_list_docname(self):
		tmp= []
		for i in self.list_doc_name:
			tmp.append(i.docname)
		duplikat = set()
		unique_tagihan = set()

		for item in tmp:
			if item in unique_tagihan:
				duplikat.add(item)
			else:
				unique_tagihan.add(item)
		print(unique_tagihan, 'sadsd')
		# Buang tagihan duplikat ke Frappe
		for item in duplikat:
			frappe.throw(f"Melempar {item} ke Frappe.")
		# print(tmp)



	def on_submit(self):
		self.cek_outstanding()
		self.make_gl_entries()
		self.calcutale_outstanding()
		self.calculate_advance_leasing()
		self.add_tanggalcair()

	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry')
		self.make_gl_entries(cancel=1)
		self.calcutale_outstanding()
		self.calculate_advance_leasing()

	def validate(self):
		self.hitung_total()
		self.cek_double_list_docname()

	# def onload(self):
	# 	if self.total == 0 and self.docstatus == 1:
	# 		self.hitung_total()
	# 		self.db_set("total",self.total)
	# 		frappe.db.commit()

	def hitung_total(self):
		total = 0
		for i in self.tagihan_payment_table:
			total += i.nilai
		self.total = total
		
	def add_tanggalcair(self):
		if self.type == 'Pembayaran Tagihan Leasing':
			for i in self.tagihan_payment_table:
				# frappe.msgprint(self.posting_date+i.no_sinv)
				frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set tanggal_cair = '{}' where name='{}' """.format(self.posting_date,i.no_sinv))
				frappe.db.commit()


	def calculate_advance_leasing(self):
		# if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
			total = 0
			for i in self.tagihan_payment_table:
				total += i.nilai

			if self.advance_leasing and self.docstatus == 1:
				doc = frappe.get_doc("Advance Leasing",self.advance_leasing)
				doc.terpakai = doc.terpakai + total
				sisa = doc.nilai - doc.terpakai
				# frappe.msgprint(str(sisa)+ "sisa")
				# frappe.msgprint(str(doc.nilai - doc.terpakai)+ "sisa2")
				if sisa < doc.nilai - doc.terpakai:
					frappe.throw("Sisa di advance leasing kurang !")
				else:
					doc.sisa = sisa
				doc.db_update()
				frappe.db.commit()
			elif self.advance_leasing and self.docstatus == 2:
				doc = frappe.get_doc("Advance Leasing",self.advance_leasing)
				doc.terpakai = doc.terpakai - total
				doc.sisa = doc.nilai  - doc.terpakai
				doc.db_update()
				frappe.db.commit()

	def cek_outstanding(self):
		for i in self.tagihan_payment_table:
			if i.doc_type == 'Tagihan Discount':
				doctype = 'Daftar Tagihan'
				outstanding = frappe.get_doc(doctype,i.id_detail).terbayarkan
			elif i.doc_type == 'Tagihan Discount Leasing':
				doctype = 'Daftar Tagihan Leasing'
				outstanding = frappe.get_doc(doctype,i.id_detail).outstanding_discount
			elif i.doc_type == 'Tagihan Leasing':
				doctype = 'List Tagihan Piutang Leasing'
				outstanding = frappe.get_doc(doctype,i.id_detail).outstanding_sipm
			elif i.doc_type == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran STNK':
				doctype = 'Child Tagihan Biaya Motor'
				outstanding = frappe.get_doc(doctype,i.id_detail).outstanding_stnk
			elif i.doc_type == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran BPKB':
				doctype = 'Child Tagihan Biaya Motor'
				outstanding = frappe.get_doc(doctype,i.id_detail).outstanding_bpkb
			elif i.doc_type == 'Invoice Penagihan Garansi' and self.type == 'Pembayaran Invoice Garansi':
				doctype = 'List Invoice Penagihan Garansi'
				outstanding = frappe.get_doc(doctype,i.id_detail).outstanding_amount

			if i.nilai > outstanding:
				frappe.throw("Nilai yang dimasukkan lebih besar dari outstanding "+i.no_sinv+' !') 

	def on_trash(self):
		delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" and voucher_type = "{}" """.format(self.name,self.doctype))
		frappe.db.commit()

	def calcutale_outstanding(self):
		for d in self.tagihan_payment_table:
			if d.doc_type == 'Tagihan Discount':
				doc_type = 'Daftar Tagihan'
				field = 'terbayarkan'
				outstanding = frappe.get_doc(doc_type,d.id_detail).terbayarkan
			elif d.doc_type == 'Tagihan Discount Leasing':
				doc_type = 'Daftar Tagihan Leasing'
				field = 'outstanding_discount'
				nilai = frappe.get_doc(doc_type,d.id_detail).nilai
				outstanding = frappe.get_doc(doc_type,d.id_detail).outstanding_discount
			elif d.doc_type == 'Tagihan Leasing':
				doc_type = 'List Tagihan Piutang Leasing'
				field = 'outstanding_sipm'
				nilai = frappe.get_doc(doc_type,d.id_detail).tagihan_sipm
				outstanding = frappe.get_doc(doc_type,d.id_detail).outstanding_sipm
			elif d.doc_type == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran STNK':
				doc_type = 'Child Tagihan Biaya Motor'
				field = 'outstanding_stnk'
				outstanding = frappe.get_doc(doc_type,d.id_detail).outstanding_stnk
			elif d.doc_type == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran BPKB':
				doc_type = 'Child Tagihan Biaya Motor'
				field = 'outstanding_bpkb'
				outstanding = frappe.get_doc(doc_type,d.id_detail).outstanding_bpkb
			elif d.doc_type == 'Invoice Penagihan Garansi' and self.type == 'Pembayaran Invoice Garansi':
				doc_type = 'List Invoice Penagihan Garansi'
				field = 'outstanding_amount'
				outstanding = frappe.get_doc(doc_type,d.id_detail).outstanding_amount
			
			if self.docstatus == 1:
				hitung = outstanding - d.nilai
				if doc_type == 'Daftar Tagihan Leasing':
					hitung_t = nilai - hitung
					if d.nilai > 0:
						frappe.db.sql(""" UPDATE `tab{}` set {} = '{}',terbayarkan = '{}',mode_of_payment_discount = '{}' where name = '{}' """.format(doc_type,field,hitung,hitung_t,self.mode_of_payment,d.id_detail))
				elif doc_type == 'List Tagihan Piutang Leasing':
					hitung_t = nilai - hitung
					if d.nilai > 0:
						frappe.db.sql(""" UPDATE `tab{}` set {} = '{}',terbayarkan_sipm = '{}',mode_of_payment_sipm = '{}' where name = '{}' """.format(doc_type,field,hitung,hitung_t,self.mode_of_payment,d.id_detail)) 
				else:
					frappe.db.sql(""" UPDATE `tab{}` set {} = '{}' where name = '{}' """.format(doc_type,field,hitung,d.id_detail))
			elif self.docstatus == 2:
				hitung = outstanding + d.nilai
				if doc_type == 'Daftar Tagihan Leasing':
					hitung_t = nilai - hitung
					frappe.db.sql(""" UPDATE `tab{}` set {} = '{}',terbayarkan = '{}' where name = '{}' """.format(doc_type,field,hitung,hitung_t,d.id_detail))
				elif doc_type == 'List Tagihan Piutang Leasing':
					hitung_t = nilai - hitung
					frappe.db.sql(""" UPDATE `tab{}` set {} = '{}',terbayarkan_sipm = '{}' where name = '{}' """.format(doc_type,field,hitung,hitung_t,d.id_detail))
				else:
					frappe.db.sql(""" UPDATE `tab{}` set {} = '{}' where name = '{}' """.format(doc_type,field,hitung,d.id_detail))

		for i in self.list_doc_name:
			if i.reference_doctype == 'Tagihan Discount':
				doc_type = 'Daftar Tagihan'
				field = 'terbayarkan'
			elif i.reference_doctype == 'Tagihan Discount Leasing':
				doc_type = 'Daftar Tagihan Leasing'
				field = 'outstanding_discount'
			elif i.reference_doctype == 'Tagihan Leasing':
				doc_type = 'List Tagihan Piutang Leasing'
				field = 'outstanding_sipm'
			elif i.reference_doctype == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran STNK':
				doc_type = 'Child Tagihan Biaya Motor'
				field = 'outstanding_stnk'
			elif i.reference_doctype == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran BPKB':
				doc_type = 'Child Tagihan Biaya Motor'
				field = 'outstanding_bpkb'
			elif i.reference_doctype == 'Invoice Penagihan Garansi' and self.type == 'Pembayaran Invoice Garansi':
				doc_type = 'List Invoice Penagihan Garansi'
				field = 'outstanding_amount'

			data = frappe.db.sql(""" SELECT sum({}) as total from `tab{}` where parent = '{}' """.format(field,doc_type,i.docname),as_dict=1)
			if i.reference_doctype == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran STNK':
				frappe.db.set_value(i.reference_doctype, i.docname, "outstanding_amount_stnk", data[0]['total']);
			elif i.reference_doctype == 'Pembayaran Tagihan Motor' and self.type == 'Pembayaran BPKB':
				frappe.db.set_value(i.reference_doctype, i.docname, "outstanding_amount_bpkb", data[0]['total']);
			else:
				frappe.db.set_value(i.reference_doctype, i.docname, "outstanding_amount", data[0]['total']);

	def get_gl_dict(self, args, account_currency=None, item=None):
		"""this method populates the common properties of a gl entry record"""

		posting_date = self.posting_date
		fiscal_years = get_fiscal_years(posting_date, company=self.company)
		if len(fiscal_years) > 1:
			frappe.throw(_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
				formatdate(posting_date)))
		else:
			fiscal_year = fiscal_years[0][0]

		gl_dict = frappe._dict({
			'company': self.company,
			'posting_date': self.posting_date,
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
		if self.customer  and self.type != 'Pembayaran Invoice Garansi':		
			tmp = []
			for d in self.list_doc_name:
				tmp.append({
					'docname': d.docname,
					'reference_doctype': d.reference_doctype
				})

			unique_data = list({frozenset(item.items()): item for item in tmp}.values())

			for u in unique_data:
				data = frappe.db.sql(""" SELECT SUM(nilai) as total from `tabTagihan Payment Table` tpt 
					where tpt.doc_name = '{}' and tpt.parent = '{}' """.format(u['docname'],self.name),as_dict=1,debug=1)
				print(f'{data} --dataxx')
				gl_entries.append(
					self.get_gl_dict({
						"account": self.paid_from,
						"against": self.paid_to,
						"credit": data[0]['total'],
						"party_type": "Customer",
						"party": self.customer,
						"credit_in_account_currency": data[0]['total'],
						"against_voucher": u['docname'],
						"against_voucher_type": u['reference_doctype'],
						# "cost_center": self.cost_center
					}, item=None)
				)
		# if self.customer  and self.type != 'Pembayaran Invoice Garansi':		
		# 	for d in self.tagihan_payment_table:
		# 		# data = frappe.db.sql(""" SELECT SUM(nilai) as total from `tabTagihan Payment Table` tpt 
		# 		# 	where tpt.doc_name = '{}' and tpt.parent = '{}' """.format(d.docname,self.name),as_dict=1)
		# 		sp = frappe.get_doc("Sales Invoice Pen",d.sales_invoice_sparepart_garansi)
		# 		gl_entries.append(
		# 			self.get_gl_dict({
		# 				"account": self.paid_from,
		# 				"against": self.paid_to,
		# 				"credit": data[0]['total'],
		# 				"party_type": "Customer",
		# 				"party": self.customer,
		# 				"credit_in_account_currency": data[0]['total'],
		# 				"against_voucher": d.docname,
		# 				"against_voucher_type": d.reference_doctype,
		# 				"cost_center": self.cost_center
		# 			}, item=None)
		# 		)
		elif self.vendor:
			tmp = []
			for d in self.list_doc_name:
				tmp.append({
					'docname': d.docname,
					'reference_doctype': d.reference_doctype
				})

			unique_data = list({frozenset(item.items()): item for item in tmp}.values())

			for u in unique_data:
				data = frappe.db.sql(""" SELECT SUM(nilai) as total from `tabTagihan Payment Table` tpt 
					where tpt.doc_name = '{}' and tpt.parent = '{}' """.format(u['docname'],self.name),as_dict=1)
				
				gl_entries.append(
					self.get_gl_dict({
						"account": self.paid_from,
						"against": self.vendor,
						"credit": data[0]['total'],
						# "party_type": "Customer",
						# "party": self.customer,
						"credit_in_account_currency": data[0]['total'],
						# "against_voucher": d.docname,
						# "against_voucher_type": d.reference_doctype,
						"cost_center": self.cost_center
					}, item=None)
				)
		elif self.customer and self.type == 'Pembayaran Invoice Garansi':
			for d in self.tagihan_payment_table:
				# data = frappe.db.sql(""" SELECT SUM(nilai) as total from `tabTagihan Payment Table` tpt 
				# 	where tpt.doc_name = '{}' and tpt.parent = '{}' """.format(d.docname,self.name),as_dict=1)
				sp = frappe.get_doc("Sales Invoice Sparepart Garansi",d.sales_invoice_sparepart_garansi)
				gl_entries.append(
					self.get_gl_dict({
						"account": self.paid_from,
						"against": self.customer,
						"credit": d.nilai,
						"credit_in_account_currency": d.nilai,
						"party_type": "Customer",
						"party": self.customer,
						"against_voucher": d.doc_name,
						"against_voucher_type": d.doc_type,
						# "cost_center": sp.cost_center
					}, item=None)
				)		

	def make_gl_debit(self, gl_entries):
		if self.customer:
			tmp = []
			for d in self.list_doc_name:
				tmp.append({
					'docname': d.docname,
					'reference_doctype': d.reference_doctype
				})

			unique_data = list({frozenset(item.items()): item for item in tmp}.values())

			for u in unique_data:
				data = frappe.db.sql(""" SELECT SUM(nilai) as total from `tabTagihan Payment Table` tpt 
					where tpt.doc_name = '{}' and tpt.parent = '{}' """.format(u['docname'],self.name),as_dict=1)
				
				gl_entries.append(
					self.get_gl_dict({
						"account": self.paid_to,
						"against": self.customer,
						"debit": data[0]['total'],
						"debit_in_account_currency": data[0]['total'],
						# "against_voucher": '',
						# "against_voucher_type": '',
						"cost_center": self.cost_center
					}, item=None)
				)
		elif self.vendor:
			tmp = []
			for d in self.list_doc_name:
				tmp.append({
					'docname': d.docname,
					'reference_doctype': d.reference_doctype
				})

			unique_data = list({frozenset(item.items()): item for item in tmp}.values())

			for u in unique_data:
				data = frappe.db.sql(""" SELECT SUM(nilai) as total from `tabTagihan Payment Table` tpt 
					where tpt.doc_name = '{}' and tpt.parent = '{}' """.format(u['docname'],self.name),as_dict=1)
				
				gl_entries.append(
					self.get_gl_dict({
						"account": self.paid_to,
						"against": self.paid_from,
						"party_type": "Supplier",
						"party": self.vendor,
						"debit": data[0]['total'],
						"debit_in_account_currency": data[0]['total'],
						"against_voucher": u['docname'],
						"against_voucher_type": u['reference_doctype'],
						# "cost_center": self.cost_center
					}, item=None)
				)	



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

@frappe.whitelist()
def get_form_pemabayaran(dt, dn, type_bayar = None):
	doc = frappe.get_doc(dt, dn)
	if dt == 'Tagihan Discount':
		type_fp = 'Pembayaran Diskon'
		grand_total = doc.grand_total
		outstanding = doc.outstanding_amount
		data = frappe.db.get_list('Daftar Tagihan',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
	elif dt == 'Tagihan Discount Leasing':
		type_fp = 'Pembayaran Diskon Leasing'
		grand_total = doc.grand_total
		outstanding = doc.outstanding_amount
		data = frappe.db.get_list('Daftar Tagihan Leasing',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
	elif dt == 'Tagihan Leasing':
		type_fp = 'Pembayaran Tagihan Leasing'
		grand_total = doc.grand_total
		outstanding = doc.outstanding_amount
		data = frappe.db.get_list('List Tagihan Piutang Leasing',filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
	elif dt == 'Pembayaran Tagihan Motor' and type_bayar == 'STNK':
		type_fp = 'Pembayaran STNK'
		grand_total = doc.total_stnk
		outstanding = doc.outstanding_amount_stnk
		data = frappe.db.get_list("Child Tagihan Biaya Motor",filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
	elif dt == 'Pembayaran Tagihan Motor' and type_bayar == 'BPKB':
		type_fp = 'Pembayaran BPKB'
		grand_total = doc.total_bpkb
		outstanding = doc.outstanding_amount_bpkb
		data = frappe.db.get_list("Child Tagihan Biaya Motor",filters={'parent': dn},fields=['*'],order_by='nama_pemilik asc')
	elif dt == 'Invoice Penagihan Garansi':
		type_fp = 'Pembayaran Invoice Garansi'
		grand_total = doc.grand_total
		outstanding = doc.outstanding_amount
		data = frappe.db.get_list("List Invoice Penagihan Garansi",filters={'parent': dn},fields=['*'],order_by='customer asc')

	fp = frappe.new_doc("Form Pembayaran")
	fp.type = type_fp
	if dt == 'Tagihan Discount':
		fp.customer = doc.customer
		fp.paid_from = doc.coa_tagihan_discount
	elif dt == 'Tagihan Discount Leasing':
		fp.customer = doc.customer
		fp.paid_from = doc.coa_tagihan_discount_leasing
	elif dt == 'Tagihan Leasing':
		fp.customer = doc.customer
		fp.paid_from = doc.coa_lawan
	elif dt == 'Pembayaran Tagihan Motor' and type_bayar == 'STNK':
		fp.vendor = doc.supplier_stnk
		fp.paid_to = doc.coa_biaya_motor_stnk
	elif dt == 'Pembayaran Tagihan Motor' and type_bayar == 'BPKB':
		fp.vendor = doc.supplier_bpkb
		fp.paid_to = doc.coa_biaya_motor_bpkb
	elif dt == 'Invoice Penagihan Garansi':
		fp.customer = doc.customer
		fp.paid_from = doc.debit_to

	fp.append("list_doc_name",{
		'reference_doctype': dt,
		'docname': dn,
		'grand_total': grand_total,
		'outstanding': outstanding
	})

	for d in data:
		if d.parenttype == 'Tagihan Discount':
			no_sinv = d.no_sinv
			nilai = d.terbayarkan
		elif d.parenttype == 'Tagihan Discount Leasing':
			no_sinv = d.no_invoice
			nilai = d.outstanding_discount
		elif d.parenttype == 'Tagihan Leasing':
			no_sinv = d.no_invoice
			nilai = d.outstanding_sipm
		elif d.parenttype  == 'Pembayaran Tagihan Motor' and type_bayar == 'STNK':
			no_sinv = d.no_invoice
			nilai = d.outstanding_stnk
		elif d.parenttype  == 'Pembayaran Tagihan Motor' and type_bayar == 'BPKB':
			no_sinv = d.no_invoice
			nilai = d.outstanding_bpkb
		elif d.parenttype  == 'Invoice Penagihan Garansi':
			no_sinv = d.sales_invoice_sparepart_garansi
			nilai = d.outstanding_amount
			no_rangka = d.no_rangka+"--"+d.no_mesin

		if d.parenttype != 'Invoice Penagihan Garansi':
			fp.append("tagihan_payment_table", {
				'no_sinv': no_sinv,
				'pemilik': d.pemilik,
				'nama_pemilik': d.nama_pemilik,
				'item': d.item,
				'no_rangka': d.no_rangka,
				'nilai': nilai,
				'doc_type': dt,
				'doc_name': dn,
				'id_detail': d.name
			})
		elif d.parenttype == 'Invoice Penagihan Garansi':
			fp.append("tagihan_payment_table", {
				'sales_invoice_sparepart_garansi': no_sinv,
				'pemilik': d.customer,
				'nama_pemilik': d.customer_name,
				'item': None,
				'no_rangka2': no_rangka,
				'nilai': nilai,
				'doc_type': dt,
				'doc_name': dn,
				'id_detail': d.name
			})

	return fp
