
# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RuleDiscountLeasing(Document):
	def cek_akun(self):
		if self.coa:
			cek = frappe.get_doc("Account",self.coa).account_type

			if cek == 'Receivable':
				frappe.throw("Tidak boleh menggunkan akun Receivable ! ")
				
	def before_insert(self):
		# pass
		self.cek_akun()
		cek	= frappe.db.sql(""" SELECT * from `tabRule Discount Leasing` where item_group = '{0}' and nama_promo = '{1}' 
			and territory = '{2}' and leasing = '{3}' 
			and (valid_to = '{4}' or valid_from = '{4}')
			and name != '{5}' and disable = 0 """.format(self.item_group,self.nama_promo,self.territory,self.leasing,self.valid_to,self.name),as_dict=1)

		tmp_cek = []
		if cek:
			for i in cek:
				tmp_cek.append(i['name'])
			frappe.throw("RuleDiscountLeasing sudah ada di document "+str(tmp_cek)+" !")
		
		# item_code
		# cek = frappe.db.get_value("Rule Discount Leasing",{"item_code": self.item_code,"nama_promo": self.nama_promo,"territory": self.territory,
		# 	"leasing": self.leasing,"valid_to":self.valid_to}, "name")

		# item_group
		# cek = frappe.db.get_value("Rule Discount Leasing",{"item_group": self.item_group,"nama_promo": self.nama_promo,"territory": self.territory,
		# 	"leasing": self.leasing,"valid_to":self.valid_to}, "name")
		
		# if cek:
		# 	frappe.throw("Disconut Item "+cek+" sudah ada !")
		
		#item_code
		# cek_valid_to = frappe.db.get_value("Rule Discount Leasing",{"item_code": self.item_code,"nama_promo": self.nama_promo,"territory": self.territory,"valid_from":self.valid_to,"leasing": self.leasing}, "name")
		
		# item_group
#		cek_valid_to = frappe.db.get_value("Rule Discount Leasing",{"item_group": self.item_group,"nama_promo": self.nama_promo,"territory": self.territory,"valid_from":self.valid_to,"leasing": self.leasing}, "name")
		
#		if cek_valid_to:
#			frappe.throw("Discount Item "+cek_valid_to+" sudah ada !")

	def validate(self):
		# return
		self.cek_akun()
		# item_code
		# cek = frappe.db.get_value("Rule Discount Leasing",{"item_code": self.item_code,"nama_promo": self.nama_promo,"territory": self.territory,
		# 	"leasing": self.leasing,"valid_to":self.valid_to}, "name")

		# item_group
		# cek = frappe.db.get_value("Rule Discount Leasing",{"item_group": self.item_group,"nama_promo": self.nama_promo,"territory": self.territory,
		# 	"leasing": self.leasing,"valid_to":self.valid_to}, "name")

		# if cek and cek != self.name:
		# 	frappe.throw("Disconut Item "+cek+" sudah ada !")

		cek	= frappe.db.sql(""" SELECT * from `tabRule Discount Leasing` where item_group = '{0}' and nama_promo = '{1}' 
			and territory = '{2}' and leasing = '{3}' 
			and (valid_to = '{4}' or valid_from = '{4}')
			and name != '{5}' and disable = 0 """.format(self.item_group,self.nama_promo,self.territory,self.leasing,self.valid_to,self.name),as_dict=1)

		tmp_cek = []
		if cek:
			for i in cek:
				tmp_cek.append(i['name'])
			frappe.throw("RuleDiscountLeasing sudah ada di document "+str(tmp_cek)+" !")

		#item_code
		# cek_valid_to = frappe.db.get_value("Rule Discount Leasing",{"item_code": self.item_code,"nama_promo": self.nama_promo,"territory": self.territory,"valid_from":self.valid_to,"leasing": self.leasing}, "name")
		
		# item_group
#		cek_valid_to = frappe.db.get_value("Rule Discount Leasing",{"item_group": self.item_group,"nama_promo": self.nama_promo,"territory": self.territory,"valid_from":self.valid_to,"leasing": self.leasing}, "name")
		
#		if cek_valid_to:
#			frappe.throw("Discount Item "+cek_valid_to+" sudah ada !")

		# mematika rule yang lama
		# # item_code
		# # cek = frappe.db.sql("""select name from `tabRule Discount Leasing` 
		# # 	where disable=0 and valid_from>"{}" and valid_to>"{}" and item_code="{}" 
		# # 	and nama_promo="{}" and territory="{}" and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_code,self.nama_promo,self.territory,self.leasing),as_list=1)
		
		# # item_group
		# cek = frappe.db.sql("""select name from `tabRule Discount Leasing` 
		# 	where disable=0 and valid_from>"{}" and valid_to>"{}" and item_group="{}" 
		# 	and nama_promo="{}" and territory="{}" and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_group,self.nama_promo,self.territory,self.leasing),as_list=1)
		
		# if cek and len(cek)>0:
		# 	frappe.msgprint("Error Sudah ada Rule yang lebih baru")
		# 	self.disable=1
		# else:
		# 	#item_code
		# 	# frappe.db.sql("""update `tabRule Discount Leasing` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" 
		# 	# 	and item_code="{}" and nama_promo="{}" and territory="{}" 
		# 	# 	and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_code,self.nama_promo,self.territory,self.leasing),as_list=1)
			
		# 	# item_group
		# 	frappe.db.sql("""update `tabRule Discount Leasing` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" 
		# 		and item_group="{}" and nama_promo="{}" and territory="{}" 
		# 		and leasing="{}" """.format(self.valid_from,self.valid_from,self.item_group,self.nama_promo,self.territory,self.leasing),as_list=1)


		# lama
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
