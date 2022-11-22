# Copyright (c) 2022, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TagihanLeasing(Document):
	def on_submit(self):
		if self.list__outstanding__tagihan_leasing:
			if len(self.list__outstanding__tagihan_leasing) > 0:
				for i in self.list__outstanding__tagihan_leasing:
					# frappe.throw(i.sipm)
					frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set tagihan_leasing = 1 where name = '{}' """.format(i.sipm))
				frappe.db.commit()

	def on_cancel(self):
		if self.list__outstanding__tagihan_leasing:
			if len(self.list__outstanding__tagihan_leasing) > 0:
				for i in self.list__outstanding__tagihan_leasing:
					frappe.db.sql(""" UPDATE `tabSales Invoice Penjualan Motor` set tagihan_leasing = 0 where name = '{}' """.format(i.sipm))
				frappe.db.commit()
	
	
@frappe.whitelist()
def get_sipm(leasing,from_date,to_date):
	# frappe.msgprint(doc.name)
	data = frappe.db.sql(""" SELECT name,outstanding_amount from `tabSales Invoice Penjualan Motor` 
		where docstatus = 1 and outstanding_amount > 0 
		and tagihan_leasing = 0 and customer='{}' and posting_date between '{}' and '{}' order by name """.format(leasing,from_date,to_date),as_dict=1)

	return data
