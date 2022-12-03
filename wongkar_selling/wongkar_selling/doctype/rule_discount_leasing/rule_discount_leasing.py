# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RuleDiscountLeasing(Document):
	def before_insert(self):
#		pass
		# frappe.msgprint("before_insert")
		cek = frappe.db.get_value("Rule Discount Leasing",{"item_code": self.item_code,"nama_promo": self.nama_promo,"territory": self.territory,
			"leasing": self.leasing,"valid_to":self.valid_to}, "name")
		
		# cek = frappe.db.get_value("Rule Discount Leasing",{"item_group": self.item_group,"nama_promo": self.nama_promo,"territory": self.territory,
		# 	"leasing": self.leasing,"valid_to":self.valid_to}, "name")
		
		if cek:
			frappe.throw("Disconut Item "+cek+" sudah ada !")

		# cek_valid_to = frappe.db.get_value("Rule Discount Leasing",{"item_group": self.item_group,"nama_promo": self.nama_promo,"territory": self.territory,"valid_from":self.valid_to}, "name")
		
		#item_code
		cek_valid_to = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_from":self.valid_to}, "name")

		if cek_valid_to:
			frappe.throw("Discount Item "+cek_valid_to+" sudah ada !")

	def validate(self):
		cek = frappe.db.sql("""select name from `tabRule Discount Leasing` 
			where disable=0 and valid_from>"{}" and valid_to>"{}" and item_code="{}" 
			and nama_promo="{}" and territory="{}" and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_code,self.nama_promo,self.territory,self.leasing),as_list=1)
		
		# cek = frappe.db.sql("""select name from `tabRule Discount Leasing` 
		# 	where disable=0 and valid_from>"{}" and valid_to>"{}" and item_group="{}" 
		# 	and nama_promo="{}" and territory="{}" and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_group,self.nama_promo,self.territory,self.leasing),as_list=1)
		
		if cek and len(cek)>0:
			frappe.msgprint("Error Sudah ada Rule yang lebih baru")
			self.disable=1
		else:
			frappe.db.sql("""update `tabRule Discount Leasing` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" 
				and item_code="{}" and nama_promo="{}" and territory="{}" 
				and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_code,self.nama_promo,self.territory,self.leasing),as_list=1)
			
			# frappe.db.sql("""update `tabRule Discount Leasing` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" 
			# 	and item_group="{}" and nama_promo="{}" and territory="{}" 
			# 	and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_group,self.nama_promo,self.territory,self.leasing),as_list=1)
		
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

		# if not self.coa_expense:
		# 	frappe.throw("Pilih Akun terlebih dahulu")

		# if not self.coa_receivable:
		# 	frappe.throw("Pilih Akun terlebih dahulu")
