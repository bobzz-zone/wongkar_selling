# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wongkar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Rule(Document):
	pass
	# def validate(self):
	# 	frappe.msgprint("validate")
	# 	if not self.type:
	# 		frappe.throw("Pilih Type terlebih dahulu")
	# 	if not self.get("daftar_biaya") and self.type == "Biaya Penjualan Kendaraan":
	# 		frappe.throw("Masukkan Biaya")
	# 	if self.type != "Biaya Penjualan Kendaraan":
	# 		if not self.discount:
	# 			frappe.throw("Pilih discount terlebih dahulu")
	# 	if self.discount == "Amount" and self.type != "Biaya Penjualan Kendaraan":
	# 		if not self.amount:
	# 			frappe.throw("Masukkan Amount")
	# 	if self.discount == "Percent" and self.type != "Biaya Penjualan Kendaraan":
	# 		if not self.percent:
	# 			frappe.throw("Masukkan Percent")
	# 	if self.type == "Dealer":
	# 		if not self.coa_cash or not self.coa_discount:
	# 			frappe.throw("Cek COA Cash / Discount")
	# 	if self.type != "Dealer" or self.type != "Biaya Penjualan Kendaraan":
	# 		if not self.coa_expense or not self.coa_receivable:
	# 			frappe.throw("Cek COA Expanse / Recivable")



	# def before_insert(self):
	# 	frappe.msgprint("before_insert")

	# 	leasing = frappe.db.get_value("Rule",{"item_code": self.item_code, "besar_dp" : self.besar_dp, "tenor": self.tenor}, "item_code")
	# 	if leasing:
	# 		frappe.throw("Disconut Item "+leasing+" sudah ada !")
		
	# 	if self.type == "Leasing" and self.besar_dp == "":
	# 		frappe.throw("Masukkan besar DP !")
	# 	if self.type == "Leasing" and self.tenor == "":
	# 		frappe.throw("Masukkan besar Tenor !")

		

		

