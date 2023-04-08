# Copyright (c) 2021, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CategoryDiscountLeasing(Document):
	def validate(self):
		# pass
		if self.disabled:
			frappe.db.sql(""" UPDATE `tabRule Discount Leasing` set disable = 1 where nama_promo = '{}' """.format(self.name))
		else:
			frappe.db.sql(""" UPDATE `tabRule Discount Leasing` set disable = 0 where nama_promo = '{}' """.format(self.name))
