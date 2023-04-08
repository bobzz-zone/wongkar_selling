# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RuleBiaya(Document):
	def before_insert(self):
		cek = frappe.db.sql(""" SELECT * from `tabRule Biaya` where item_group = '{0}' 
			and type = '{1}' and territory = '{2}' 
			and (valid_to = '{3}' or valid_from = '{3}') and vendor = '{4}' 
			and name != '{5}' and disable=0 """.format(self.item_group,self.type,self.territory,self.valid_to,self.vendor,self.name),as_dict=1)
		
		tmp_cek = []
		if cek:
			for i in cek:
				tmp_cek.append(i['name'])
			frappe.throw("Discount Item ada di "+str(tmp_cek)+" !")

		# item_code
		# cek = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_to":self.valid_to,"vendor":self.vendor}, "name")
		
		# item_group
		# cek = frappe.db.get_value("Rule Biaya",{"item_group": self.item_group,"type": self.type,"territory": self.territory,"valid_to":self.valid_to,"vendor":self.vendor}, "name")
		
		# if cek:
		# 	frappe.throw("Discount Item "+cek+" sudah ada !")
		
		#item_code
		# cek_valid_to = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_from":self.valid_to,"vendor":self.vendor}, "name")

		# item_group
#		cek_valid_to = frappe.db.get_value("Rule Biaya",{"item_group": self.item_group,"type": self.type,"territory": self.territory,"valid_from":self.valid_to,"vendor":self.vendor}, "name")
		
#		if cek_valid_to:
#			frappe.throw("Discount Item "+cek_valid_to+" sudah ada !")
	
	def validate(self):
		return
		# item_code
		# cek = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_to":self.valid_to,"vendor":self.vendor}, "name")
		
		# item_group
		# cek = frappe.db.get_value("Rule Biaya",{"item_group": self.item_group,"type": self.type,"territory": self.territory,"valid_to":self.valid_to,"vendor":self.vendor}, "name")

		cek = frappe.db.sql(""" SELECT * from `tabRule Biaya` where item_group = '{0}' 
			and type = '{1}' and territory = '{2}' 
			and (valid_to = '{3}' or valid_from = '{3}') and vendor = '{4}' 
			and name != '{5}' and disable=0 """.format(self.item_group,self.type,self.territory,self.valid_to,self.vendor,self.name),as_dict=1)
		
		tmp_cek = []
		if cek:
			for i in cek:
				tmp_cek.append(i['name'])
			frappe.throw("Discount Item ada di "+str(tmp_cek)+" !")
		
		#item_code
		# cek_valid_to = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory,"valid_from":self.valid_to,"vendor":self.vendor}, "name")

		# item_group
#		cek_valid_to = frappe.db.get_value("Rule Biaya",{"item_group": self.item_group,"type": self.type,"territory": self.territory,"valid_from":self.valid_to,"vendor":self.vendor}, "name")
		
#		if cek_valid_to:
#			frappe.throw("Discount Item "+cek_valid_to+" sudah ada !")

		# cek_valid_to = frappe.db.sql(""" SELECT * from `tabRule Biaya` where item_group = '{}' and type = '{}' 
		# 	and territory = '{}' and valid_from	= '{}' 
		# 	and vendor = '{}' and name  != '{}' and disable = 0 """.format(self.item_group,self.type,self.territory,self.valid_to,self.vendor,self.name),as_dict=1)

		# tmp_cek_valid_to = []
		# if cek_valid_to:
		# 	for i in cek_valid_to:
		# 		cek_valid_to.append(i['name'])
		# 	frappe.throw("Valid From sama dengan valid to di Rule "+str(tmp_cek_valid_to)+" !")
		
		if not self.amount:
			frappe.throw("Masukkan Amount terlebih dahulu")

		if not self.coa:
			frappe.throw("Pilih Akun terlebih dahulu")
		
		
		# mematika rule yang lama
		# # item_code
		# # cek = frappe.db.sql("""select name from `tabRule Biaya` where disable=0 and valid_from<"{}" and valid_to>"{}" and item_code="{}" and type="{}" and territory="{}" 
		# 	# and vendor = "{}" """.format(self.valid_from,self.valid_from,self.item_code,self.type,self.territory,self.vendor),as_list=1)

		# #item_group
		# cek = frappe.db.sql("""select name from `tabRule Biaya` where disable=0 and valid_from<"{}" and valid_to>"{}" and item_group="{}" and type="{}" and territory="{}"
		# 	and vendor = "{}" """.format(self.valid_from,self.valid_from,self.item_group,self.type,self.territory,self.vendor),as_list=1)
		
		# if cek and len(cek)>0:
		# 	frappe.msgprint("Error Sudah ada Rule yang lebih baru")
		# 	self.disable=1
		# else:
		# 	# item_code
		# 	# frappe.db.sql("""update `tabRule Biaya` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" and item_code="{}" and type="{}" and territory="{}" 
		# 	# 	and vendor = "{}" """.format(self.valid_from,self.valid_from,self.item_code,self.type,self.territory,self.vendor),as_list=1)
			
		# 	# item_group
		# 	frappe.db.sql("""update `tabRule Biaya` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" and item_group="{}" and type="{}" and territory="{}" 
		# 		and vendor = "{}" """.format(self.valid_from,self.valid_from,self.item_group,self.type,self.territory,self.vendor),as_list=1)
