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
	kondisi = ""
	if filters.get("leasing"):
		kondisi = " and al.leasing = '{}' ".format(filters.get("leasing"))

	data = frappe.db.sql(""" SELECT
		al.tanggal,
		al.name as advance_leasing,
		al.nilai as advance_distburse,
		pe.posting_date as tgl_pencairan,
		IFNULL(sum(pe.paid_amount),0) as tot_pencairan
		from `tabAdvance Leasing` al 
		left join `tabPayment Entry` pe on pe.advance_leasing = al.name
		where al.docstatus = 1 {} and al.tanggal between '{}' and '{}' 
		group by al.name,pe.name order by al.tanggal asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)

	frappe.msgprint(str(data[0]['tanggal']))
	frappe.msgprint(str(data))
	for i in range(len(data)-1):
		data[i].update({
				'saldo_akhir': 0
			})
		data[i]['saldo_akhir'] = data[i]['advance_distburse'] - data[i]['tot_pencairan']
		data[i+1]['advance_distburse'] = data[i]['saldo_akhir']
		data[i+1]['saldo_akhir'] = data[i+1]['advance_distburse'] - data[i+1]['tot_pencairan']

	previous_al = None
	for i in data:
		current_al = i['advance_leasing']
		if (previous_al != current_al):
			i['advance_leasing'] = i['advance_leasing']
			i['tanggal'] = i['tanggal']
		else:
			i['advance_leasing'] = ""
			i['tanggal'] = ""
		previous_al = current_al
	
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Tanggal"),
			"fieldname": "tanggal",
			"fieldtype": "Date",
			"width": 200
		},
		{
			"label": _("Advance Leasing"),
			"fieldname": "advance_leasing",
			"fieldtype": "Link",
			"options": 'Advance Leasing',
			"width": 200
		},
		{
			"label": _("Advance Distburse"),
			"fieldname": "advance_distburse",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tgl Pencairan"),
			"fieldname": "tgl_pencairan",
			"fieldtype": "Date",
			"width": 200
		},
		{
			"label": _("Tot Pencairan"),
			"fieldname": "tot_pencairan",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Saldo Akhir"),
			"fieldname": "saldo_akhir",
			"default": 0,
			"fieldtype": "Currency",
			"width": 200
		},
	]

	return columns


