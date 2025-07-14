from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date
from collections import OrderedDict

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):
	serial_no = filters.get("serial_no")

	data = frappe.db.sql(""" 
					SELECT 
					  	voucher_type AS reference_doctype,voucher_no AS reference_name 
					FROM `tabStock Ledger Entry` 
					WHERE serial_no LIKE '%{}%' AND is_cancelled = 0
					GROUP BY voucher_no """.format(serial_no),as_dict=1)

	data_tagihan_discount = frappe.db.sql(""" 
									SELECT 
									  'Tagihan Discount' as reference_doctype,
									   td.name as reference_name
									from `tabTagihan Discount` td 
									join `tabDaftar Tagihan` dt on td.name = dt.parent
									where dt.no_rangka = '{}' and td.docstatus = 1 
									group by td.name  """.format(serial_no),as_dict=1)
	
	data_tagihan_discount_leasing = frappe.db.sql(""" 
									SELECT 
									  'Tagihan Discount Leasing' as reference_doctype,
									   tdl.name as reference_name
									from `tabTagihan Discount Leasing` tdl
									join `tabDaftar Tagihan Leasing` dtl on tdl.name = dtl.parent
									where dtl.no_rangka = '{}' and tdl.docstatus = 1 
									group by tdl.name  """.format(serial_no),as_dict=1)
	
	data_pembayaran_tagihan_motor = frappe.db.sql(""" 
									SELECT 
									  'Pembayaran Tagihan Motor' as reference_doctype,
									   tdl.name as reference_name
									from `tabPembayaran Tagihan Motor` tdl
									join `tabChild Tagihan Biaya Motor` dtl on tdl.name = dtl.parent
									where dtl.no_rangka = '{}' and tdl.docstatus = 1 
									group by tdl.name  """.format(serial_no),as_dict=1)
	
	data_tagihan_leasing = frappe.db.sql(""" 
									SELECT 
									  'Tagihan Leasing' as reference_doctype,
									   tdl.name as reference_name
									from `tabTagihan Leasing` tdl
									join `tabList Tagihan Piutang Leasing` dtl on tdl.name = dtl.parent
									where dtl.no_rangka = '{}' and tdl.docstatus = 1 
									group by tdl.name  """.format(serial_no),as_dict=1)


	data.extend(data_tagihan_discount or [])
	data.extend(data_tagihan_discount_leasing or [])
	data.extend(data_tagihan_leasing or [])
	data.extend(data_pembayaran_tagihan_motor or [])
	
	# frappe.msgprint(f'{data}')

	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Reference Doctype"),
			"fieldname": "reference_doctype",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 200
		},
		{
			"label": _("Reference Name"),
			"fieldname": "reference_name",
			"fieldtype": "Dynamic Link",
			"options": "reference_doctype",
			"width": 200
		},

	]

	return columns


