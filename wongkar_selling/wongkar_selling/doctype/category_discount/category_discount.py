# Copyright (c) 2021, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CategoryDiscount(Document):
	def validate(self):
		if self.disabled:
			frappe.db.sql(""" UPDATE `tabRule` set disable = 1 where category_discount = '{}' """.format(self.name))
		else:
			frappe.db.sql(""" UPDATE `tabRule` set disable = 0 where category_discount = '{}' """.format(self.name))
