# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RuleBiaya(Document):
	def before_insert(self):
		# frappe.msgprint("before_insert")

		cek = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_to":self.valid_to,"amount":self.amount}, "name")
		if cek:
			frappe.throw("Discount Item "+cek+" sudah ada !")
	def validate(self):
		# frappe.msgprint("validate")
		# if self.discount:
		# 	if self.discount == "Amount":
		# 		if not self.amount:
		# 			frappe.throw("Masukkan Amount")
		# 	if self.discount == "Percent":
		# 		if not self.percent:
		# 			frappe.throw("Masukkan Percent")
		# elif not self.discount:
		# 	frappe.throw("Pilih discount terlebih dahulu")

		if not self.amount:
			frappe.throw("Masukkan Amount terlebih dahulu")

		if not self.coa:
			frappe.throw("Pilih Akun terlebih dahulu")
		#check kalo ada yang lbh future start date nya
		cek = frappe.db.sql("""select name from `tabRule Biaya` where disable=0 and valid_from>"{}" and valid_to>"{}" and item_code="{}" and type="{}" and territory="{}" 
			""".format(self.valid_from,self.valid_from,self.item_code,self.type,self.territory),as_list=1)
		if cek and len(cek)>0:
			frappe.msgprint("Error Sudah ada Rule yang lebih baru")
			self.disable=1
		else:
			frappe.db.sql("""update `tabRule Biaya` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" and item_code="{}" and type="{}" and territory="{}" 
				""".format(self.valid_from,self.valid_from,self.item_code,self.type,self.territory),as_list=1)
