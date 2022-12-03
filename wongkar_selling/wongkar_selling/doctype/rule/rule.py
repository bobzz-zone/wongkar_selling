# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
from frappe.utils import flt, rounded, add_months,add_days, nowdate, getdate
import time
import datetime

class Rule(Document):
	def validate(self):
		# frappe.msgprint("validate")
		today = date.today()
		if self.discount:
			if self.discount == "Amount":
				if not self.amount:
					frappe.throw("Masukkan Amount")
			if self.discount == "Percent":
				if not self.percent:
					frappe.throw("Masukkan Percent")
		elif not self.discount:
			frappe.throw("Pilih discount terlebih dahulu")

		# if not self.coa_expense:
		# 	frappe.throw("Pilih Akun terlebih dahulu")

		if not self.coa_receivable:
			frappe.throw("Pilih Akun terlebih dahulu")
		
		# item_code
		cek = frappe.db.sql("""select name from `tabRule` where disable=0 and valid_from>"{}" and valid_to>"{}" and item_code="{}" and category_discount="{}" and territory="{}" and customer="{}"
			""".format(self.valid_from,self.valid_from,self.item_code,self.category_discount,self.territory,self.customer),as_list=1)

		# item_group
		# cek = frappe.db.sql("""select name from `tabRule` where disable=0 and valid_from>"{}" and valid_to>"{}" and item_group="{}" and category_discount="{}" and territory="{}" and customer="{}"
		# 	""".format(self.valid_from,self.valid_from,self.item_group,self.category_discount,self.territory,self.customer),as_list=1)
		
		if cek and len(cek)>0:
			frappe.msgprint("Error Sudah ada Rule yang lebih baru")
			self.disable=1
		else:
			frappe.db.sql("""update `tabRule` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" and item_code="{}" and category_discount="{}" and territory="{}" and customer="{}" 
				""".format(self.valid_from,self.valid_from,self.item_code,self.category_discount,self.territory,self.customer),as_list=1)
			
			# frappe.db.sql("""update `tabRule` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" and item_group="{}" and category_discount="{}" and territory="{}" and customer="{}" 
			# 	""".format(self.valid_from,self.valid_from,self.item_group,self.category_discount,self.territory,self.customer),as_list=1)


	def before_insert(self):
		cek = frappe.db.get_value("Rule",{"item_code": self.item_code,"category_discount": self.category_discount,"territory": self.territory,
			"customer":self.customer,"valid_to":self.valid_to}, "name")
		if cek:
			frappe.throw("Disconut Item "+cek+" sudah ada !")		

		# cek = frappe.db.get_value("Rule",{"item_group": self.item_group,"category_discount": self.category_discount,"territory": self.territory,
		# 	"customer":self.customer,"valid_to":self.valid_to}, "name")
		# if cek:
		# 	frappe.throw("Disconut Item "+cek+" sudah ada !")

		# cek_valid_to = frappe.db.get_value("Rule",{"item_group": self.item_group,"category_discount": self.category_discount,"territory": self.territory,"valid_from":self.valid_to}, "name")
		
		#item_code
		cek_valid_to = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_from":self.valid_to}, "name")

		if cek_valid_to:
			frappe.throw("Discount Item "+cek_valid_to+" sudah ada !")
		

