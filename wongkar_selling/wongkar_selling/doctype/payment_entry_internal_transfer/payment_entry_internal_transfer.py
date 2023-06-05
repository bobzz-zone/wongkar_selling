# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentEntryInternalTransfer(Document):
	def validate(self):
		total = 0
		if self.list_payment_entry:
			if len(self.list_payment_entry) > 0:
				for i in self.list_payment_entry:
					total = total + i.total_allocated_amount

		self.total = total

	def on_submit(self):
		if self.list_payment_entry:
			if len(self.list_payment_entry) > 0:
				for i in self.list_payment_entry:
					frappe.db.sql(""" UPDATE `tabPayment Entry` set internal_transfer = 1 where name = '{}' """.format(i.payment_entry))
		
		doc_pe = frappe.new_doc("Payment Entry")
		doc_pe.payment_entry_internal_transfer = self.name
		doc_pe.payment_type = "Internal Transfer"
		doc_pe.down_payment = 0
		doc_pe.paid_from = self.account_paid_from
		doc_pe.paid_to = self.account_paid_to
		doc_pe.cost_center = self.cost_center
		doc_pe.paid_amount = self.total
		doc_pe.received_amount = self.total
		doc_pe.flags.ignore_permissions = True
		doc_pe.save()
		doc_pe.submit()

	def on_cancel(self):
		if self.list_payment_entry:
			if len(self.list_payment_entry) > 0:
				for i in self.list_payment_entry:
					frappe.db.sql(""" UPDATE `tabPayment Entry` set internal_transfer = 0 where name = '{}' """.format(i.payment_entry))
		
		data = frappe.db.sql(""" SELECT name from `tabPayment Entry` where payment_entry_internal_transfer = "{}" """.format(self.name),as_dict=1)

		if data:
			for d in data:
				doc_pe = frappe.get_doc("Payment Entry",d['name'])
				if doc_pe.docstatus == 1:
					doc_pe.cancel()
					doc_pe.delete()
				else:
					doc_pe.delete()

@frappe.whitelist()
def get_pe(name_pe,paid_from,from_date,to_date):
	# data_pe = frappe.get_doc("Payment Entry Internal Transfer",name_pe)
	data = frappe.db.sql(""" SELECT pe.name,pe.total_allocated_amount,pe.posting_date,c.customer_name
		from `tabPayment Entry` pe 
		left join `tabCustomer` c on c.name = pe.pemilik
		where pe.mode_of_payment like 'Cash%' and pe.paid_to = '{}' and 
		pe.docstatus = 1 and pe.internal_transfer = 0 and pe.total_allocated_amount > 0 and pe.posting_date between '{}' and '{}' order by pe.posting_date asc """.format(paid_from,from_date,to_date),as_dict=1,debug=1)

	return data