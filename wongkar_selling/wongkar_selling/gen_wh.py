# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe


@frappe.whitelist()
def gen_warehouse(doc,method):
	#frappe.throw("test")
	docw = frappe.new_doc('Warehouse')
	docw.warehouse_name = doc.territory_name

	docw.flags.ignore_permission = True
	docw.save()

@frappe.whitelist()
def get_ter():
	#frappe.throw("test")
	data = frappe.db.get_list('Territory')

	return data