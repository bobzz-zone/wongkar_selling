# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RuleBiaya(Document):
	def before_insert(self):
		# frappe.msgprint("before_insert")

		cek = frappe.db.get_value("Rule Biaya",{"item_code": self.item_code,"type": self.type,"territory": self.territory}, "item_code")
		if cek:
			frappe.throw("Disconut Item "+cek+" sudah ada !")

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
