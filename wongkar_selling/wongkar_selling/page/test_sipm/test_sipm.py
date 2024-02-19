# Copyright (c) 2021, Patrick Stuhlmüller and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json

@frappe.whitelist()
def get_data(filters):
	filters = json.loads(filters)
	# frappe.msgprint(filters['from_date'] + ' filters')
	data = frappe.db.sql("""  SELECT * FROM `tabSales Invoice Penjualan Motor` 
		WHERE docstatus = 1 and posting_date between '{}' and '{}' """.format(filters['from_date'],filters['to_date']),as_dict=1,debug=1)

	con = 1
	for i in data:
		i['no'] = con
		con += 1
		# i['name'] = '<a href="'+frappe.utils.get_url()+'/app/sales-invoice-penjualan-motor/'+i['name']+'">'+i['name']+'</a>'

	return data