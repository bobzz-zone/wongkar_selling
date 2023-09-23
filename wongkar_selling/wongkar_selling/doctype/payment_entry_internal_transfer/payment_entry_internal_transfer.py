# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentEntryInternalTransfer(Document):
	def validate(self):
		total = 0
		total_fp = 0
		if self.list_penerimaan_dp:
			if len(self.list_penerimaan_dp) > 0:
				for i in self.list_penerimaan_dp:
					total = total + i.total

		# list_form_pembayaran
		# if self.list_form_pembayaran:
		# 	if len(self.list_form_pembayaran) > 0:
		# 		for i in self.list_form_pembayaran:
		# 			total_fp += i.total

		self.total = total + total_fp
		self.validasi_get()

	def validasi_get(self):
		for i in self.list_penerimaan_dp:
			cek = frappe.db.sql(""" SELECT a.name,b.penerimaan_dp from `tabPayment Entry Internal Transfer` a 
				join `tabList Penerimaan DP` b on a.name = b.parent
				where b.penerimaan_dp = '{}' and a.docstatus = 0 """.format(i.penerimaan_dp),as_dict=1)
			if cek:
				for c in cek:
					if c['name'] != self.name:
						frappe.throw("No Penerimaan DP "+c['penerimaan_dp']+" Sudah ada di "+c['name']+" !")

	def on_submit(self):
		if self.list_penerimaan_dp:
			if len(self.list_penerimaan_dp) > 0:
				for i in self.list_penerimaan_dp:
					frappe.db.sql(""" UPDATE `tabPenerimaan DP` set cek_transfer = 1 where name = '{}' """.format(i.penerimaan_dp))

		# list_form_pembayaran
		# if self.list_form_pembayaran:
		# 	if len(self.list_form_pembayaran) > 0:
		# 		for i in self.list_form_pembayaran:
		# 			frappe.db.sql(""" UPDATE `tabForm Pembayaran` set cek_transfer = 1 where name = '{}' """.format(i.form_pembayaran))
		
		doc_pe = frappe.new_doc("Payment Entry")
		doc_pe.payment_entry_internal_transfer = self.name
		doc_pe.posting_date = self.date
		doc_pe.payment_type = "Internal Transfer"
		doc_pe.paid_from = self.account_paid_from
		doc_pe.paid_to = self.account_paid_to
		doc_pe.cost_center = self.cost_center
		doc_pe.paid_amount = self.total
		doc_pe.received_amount = self.total
		doc_pe.flags.ignore_permissions = True
		doc_pe.save()
		doc_pe.submit()

	def on_cancel(self):
		self.ignore_linked_doctypes = ('Payment Entry')
		if self.list_penerimaan_dp:
			if len(self.list_penerimaan_dp) > 0:
				for i in self.list_penerimaan_dp:
					frappe.db.sql(""" UPDATE `tabPenerimaan DP` set cek_transfer = 0 where name = '{}' """.format(i.penerimaan_dp))

		# list_form_pembayaran
		# if self.list_form_pembayaran:
		# 	if len(self.list_form_pembayaran) > 0:
		# 		for i in self.list_form_pembayaran:
		# 			frappe.db.sql(""" UPDATE `tabForm Pembayaran` set cek_transfer = 0 where name = '{}' """.format(i.form_pembayaran))
		
		data = frappe.db.sql(""" SELECT name from `tabPayment Entry` where payment_entry_internal_transfer = "{}" """.format(self.name),as_dict=1)

		if data:
			for d in data:
				frappe.db.sql(""" UPDATE `tabPayment Entry` set payment_entry_internal_transfer = null where name = '{}' """.format(d['name']),debug=1)
				doc_pe = frappe.get_doc("Payment Entry",d['name'])
				if doc_pe.docstatus == 1:
					# doc_pe.ignore_linked_doctypes = ('Payment Entry Internal Transfer')
					doc_pe.ignore_linked_doctypes = ('Payment Entry Internal Transfer',"GL Entry", "Stock Ledger Entry")
					print(doc_pe.payment_entry_internal_transfer,' payment_entry_internal_transfer')
					doc_pe.cancel()
					doc_pe = frappe.get_doc("Payment Entry",d['name'])
					if doc_pe.docstatus == 2:
						doc_pe.delete()
				else:
					doc_pe.delete()

@frappe.whitelist()
def get_pe(name_pe,paid_from,from_date,to_date):
	# data_pe = frappe.get_doc("Payment Entry Internal Transfer",name_pe)
	data = frappe.db.sql(""" SELECT pe.name,pe.paid_amount,pe.posting_date,c.customer_name
		from `tabPayment Entry` pe 
		left join `tabCustomer` c on c.name = pe.pemilik
		where pe.mode_of_payment like 'Cash%' and pe.paid_to = '{}' and 
		pe.docstatus = 1 and pe.internal_transfer = 0 and pe.posting_date between '{}' and '{}' order by pe.posting_date asc """.format(paid_from,from_date,to_date),as_dict=1,debug=1)

	return data

@frappe.whitelist()
def get_dp(name_pe,paid_from,from_date,to_date):
	# data_pe = frappe.get_doc("Payment Entry Internal Transfer",name_pe)
	data = frappe.db.sql(""" SELECT 
				name,
				cara_bayar,
				tanggal,
				IF(cara_bayar='Cash',customer,pemilik) AS pemilik,
				IF(cara_bayar='Cash',customer_name,nama_pemilik) AS nama_pemilik,
				IF(cara_bayar='Cash',piutang_bpkb_stnk+piutang_motor,piutang_motor) AS total
				FROM `tabPenerimaan DP` WHERE docstatus = 1 AND cek_transfer = 0 AND paid_to = '{}'
				AND tanggal BETWEEN '{}' AND '{}' ORDER BY tanggal ASC 
			""".format(paid_from,from_date,to_date),as_dict=1,debug=1)

	return data

@frappe.whitelist()
def get_fp(name_pe,paid_from,from_date,to_date):
	# data_pe = frappe.get_doc("Payment Entry Internal Transfer",name_pe)
	data = frappe.db.sql(""" SELECT 
				fp.name,
				fp.customer,
				fp.posting_date as tanggal,
				sum(tpt.nilai) as total
				FROM `tabForm Pembayaran` fp join
				`tabTagihan Payment Table` tpt on tpt.parent = fp.name
				WHERE fp.docstatus = 1 AND fp.cek_transfer = 0 AND fp.paid_to = '{}'
				AND fp.customer is not null
				AND fp.posting_date BETWEEN '{}' AND '{}' 
				group by fp.name
				ORDER BY tanggal ASC 
			""".format(paid_from,from_date,to_date),as_dict=1,debug=1)

	return data