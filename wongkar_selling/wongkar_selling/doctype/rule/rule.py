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
		#check kalo ada yang lbh future start date nya
		cek = frappe.db.sql("""select name from `tabRule` where disable=0 and valid_from>"{}" and valid_to>"{}" and item_code="{}" and category_discount="{}" and territory="{}" and customer="{}"
                        """.format(self.valid_from,self.valid_from,self.item_code,self.category_discount,self.territory,self.customer),as_list=1)
		if cek and len(cek)>0:
			frappe.msgprint("Error Sudah ada Rule yang lebih baru")
			self.disable=1
		else:
			frappe.db.sql("""update `tabRule` set disable=1 where disable=0 and valid_from<"{}" and valid_to>"{}" and item_code="{}" and category_discount="{}" and territory="{}" and customer="{}"
                                """.format(self.valid_from,self.valid_from,self.item_code,self.category_discount,self.territory,self.customer),as_list=1)
		# if self.valid_from >= self.valid_to:
		# 	frappe.throw("Tanggal valid from harus lebih dari Valid to")

	# 	if not self.type:
	# 		frappe.throw("Pilih Type terlebih dahulu")
	# 	if not self.get("daftar_biaya") and self.type == "Biaya Penjualan Kendaraan":
	# 		frappe.throw("Masukkan Biaya")
	# 	if self.type != "Biaya Penjualan Kendaraan":
	# 		if not self.discount:
	# 			frappe.throw("Pilih discount terlebih dahulu")
	# 	if self.type == "Dealer":
	# 		if not self.coa_cash or not self.coa_discount:
	# 			frappe.throw("Cek COA Cash / Discount")
	# 	if self.type != "Dealer" or self.type != "Biaya Penjualan Kendaraan":
	# 		if not self.coa_expense or not self.coa_receivable:
	# 			frappe.throw("Cek COA Expanse / Recivable")


	def before_insert(self):
		# frappe.msgprint("before_insert")

		cek = frappe.db.get_value("Rule",{"item_code": self.item_code,"category_discount": self.category_discount,"territory": self.territory,
			"customer":self.customer,"valid_to":self.valid_to}, "name")
		if cek:
			frappe.throw("Disconut Item "+cek+" sudah ada !")

#		cek2 = frappe.db.get_value("Rule",{"item_code": self.item_code,"category_discount": self.category_discount,"territory": self.territory,
#			"customer":self.customer,"valid_to":self.valid_to}, "name")
#		if cek2:
#			frappe.throw("Disconut Item "+cek+" sudah ada !")

		# if self.type == "Leasing" and self.besar_dp == "":
		# 	frappe.throw("Masukkan besar DP !")
		# if self.type == "Leasing" and self.tenor == "":
		# 	frappe.throw("Masukkan besar Tenor !")

		

		

