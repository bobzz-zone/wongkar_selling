# Copyright (c) 2013, w and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):

	bulan = filters.get('month')
	tahun = filters.get('year')

	if bulan == "Januari":
		bulan = "01"
	elif bulan == "Februari":
		bulan = '02'
	elif bulan == "Maret":
		bulan = '03'
	elif bulan == "April":
		bulan = '04'
	elif bulan == "Mei":
		bulan = '05'
	elif bulan == "Juni":
		bulan = '06'
	elif bulan == "Juli":
		bulan = '07'
	elif bulan == "Agustus":
		bulan = '08'
	elif bulan == "September":
		bulan = '09'
	elif bulan == "Oktober":
		bulan = '10'
	elif bulan == "November":
		bulan = '11'
	elif bulan == "Desember":
		bulan = '12'

	gabung = tahun+'-'+bulan

	data = frappe.db.sql(""" SELECT 
		ec.cost_center,
		ecd.expense_date,
		ecd.expense_type,
		ecd.description,
		ecd.amount,
		ec.status,
		cc.parent_cost_center
		from `tabExpense Claim` ec 
		left join `tabExpense Claim Detail` ecd on ecd.parent = ec.name
		left join `tabCost Center` cc on cc.name = ec.cost_center
		where ec.docstatus = 1 and ecd.expense_date like "{}%" order by ecd.expense_date asc """.format(gabung),as_list = 1,debug=1)
	

	tampil = []
	if data:
		for i in data:
			if i[5] == "Paid":
				d = 0
				k = i[4]
			else:
				d=i[4]
				k=0

			tampil.append([
				i[6],
				i[0],
				i[1],
				i[2],
				i[3],
				i[5],
				d,
				k,
				d-k
			])

	return tampil

def get_columns(filters):
	columns = [
		{
			"label": _("Cab"),
			"fieldname": "cab",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 200
		},
		{
			"label": _("Area"),
			"fieldname": "area",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 200
		},
		{
			"label": _("Tgl Transaksi"),
			"fieldname": "tgl_tanasaksi",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Expanse Claim Type"),
			"fieldname": "type",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Description"),
			"fieldname": "desc",
			"fieldtype": "Text Editor",
			"width": 100
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Text Editor",
			"width": 100
		},
		{
			"label": _("Debet"),
			"fieldname": "debet",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Kredit"),
			"fieldname": "kredit",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Saldo"),
			"fieldname": "saldo",
			"fieldtype": "Currency",
			"width": 100
		},

	]

	return columns

