# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def cek_akun_return(self,method):
	if self.is_return:
		for i in self.items:
			cek_i = frappe.get_doc("Item",i.item_code)
			if frappe.db.exists("Item Default", {'parent':cek_i.item_group}):
				cek_ig = frappe.get_doc("Item Default", {'parent':cek_i.item_group})
				if cek_ig.default_return_account:
					i.income_account = cek_ig.default_return_account
				else:
					cek_ig = frappe.get_doc("Item Default", {'parent':i.item_code})
					if cek_ig.default_return_account:
						i.income_account = cek_ig.default_return_account
			elif frappe.db.exists("Item Default", {'parent':i.item_code}):
				cek_ig = frappe.get_doc("Item Default", {'parent':i.item_code})
				if cek_ig.default_return_account:
					i.income_account = cek_ig.default_return_account
	else:
		for i in self.items:
			cek_i = frappe.get_doc("Item",i.item_code)
			if frappe.db.exists("Item Default", {'parent':cek_i.item_group}):
				cek_ig = frappe.get_doc("Item Default", {'parent':cek_i.item_group})
				if cek_ig.income_account:
					i.income_account = cek_ig.income_account
				else:
					cek_ig = frappe.get_doc("Item Default", {'parent':i.item_code})
					if cek_ig.income_account:
						i.income_account = cek_ig.income_account
			elif frappe.db.exists("Item Default", {'parent':i.item_code}):
				cek_ig = frappe.get_doc("Item Default", {'parent':i.item_code})
				if cek_ig.income_account:
					i.income_account = cek_ig.income_account
			
