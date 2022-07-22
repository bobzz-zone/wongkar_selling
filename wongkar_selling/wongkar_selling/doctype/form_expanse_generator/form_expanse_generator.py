# Copyright (c) 2022, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FormExpanseGenerator(Document):
	def on_submit(self):
		total = 0
		for d in self.expanse_table:
			total = total + d.biaya

		if total>100:
			frappe.throw("Biaya lebih dari 100!")
		if total<100:
			frappe.throw("Biaya kurang dari 100!")

		for d in self.expanse_table:
			doc = frappe.new_doc("Journal Entry")
			doc.voucher_type = "Journal Entry"
			doc.ket = d.idx
			doc.posting_date = d.tanggal_posting
			doc.form_expanse_generator = self.name
			row = doc.append('accounts', {})
			row.account = d.coa_expanse
			row.debit_in_account_currency = d.nilai
			row2 = doc.append('accounts', {})
			row2.account = d.coa_cb
			row2.credit_in_account_currency = d.nilai
			
			doc.flags.ignore_permissions = True
			doc.save()
			doc.submit()

			index = d.idx
			je = frappe.get_value("Journal Entry",{"form_expanse_generator": self.name,"ket": d.idx},"name")
			frappe.db.sql(""" UPDATE `tabExpanse Table` set no_je = '{0}' where parent='{1}' and idx={2} """.format(je,self.name,index))

		for i in self.list_invoice:
			frappe.db.sql(""" UPDATE `tabSales Invoice` set je_expanse = 1 where name='{0}' """.format(i.sales_invoice))

	def on_cancel(self):
		for i in self.list_invoice:
			frappe.db.sql(""" UPDATE `tabExpanse Table` set no_je = '' where parent='{0}' """.format(self.name))
			frappe.db.sql(""" UPDATE `tabSales Invoice` set je_expanse = 0 where name='{0}' """.format(i.sales_invoice))
			# doc = frappe.get_doc("Journal Entry",i['no_je'])
			# doc.flags.ignore_permissions = True
			# doc.cancel()

			
			# frappe.db.sql(""" UPDATE `tabJournal Entry` set form_expanse_generator = "" where name='{0}' """.format(i.no_je))
			
			
	
@frappe.whitelist()
def coba(name,from_date,to_date,coa_inc):
	frappe.msgprint("coba 123")
	# from_date = frappe.get_value("Form Expanse Generator",{"name":name}, "from_date")
	# to_date = frappe.get_value("Form Expanse Generator",{"name":name}, "to_date")
	# coa_inc = frappe.get_value("Form Expanse Generator",{"name":name}, "coa_income")

	data = frappe.db.sql(""" SELECT sit.amount,si.name  from `tabSales Invoice` si
		join `tabSales Invoice Item` sit on si.name = sit.parent where si.docstatus = 1 and sit.income_account = '{0}'  and si.je_expanse = 0 and sit.income_account = '{0}' and si.posting_date >= '{1}' and si.posting_date <= '{2}' """.format(coa_inc,from_date,to_date),as_dict=1)

	return data

def cencel_form(doc,method):
	if doc.form_expanse_generator:
		frappe.db.sql(""" UPDATE `tabExpanse Table` set no_je = '' where parent='{0}' and no_je='{1}' """.format(doc.form_expanse_generator,doc.name))