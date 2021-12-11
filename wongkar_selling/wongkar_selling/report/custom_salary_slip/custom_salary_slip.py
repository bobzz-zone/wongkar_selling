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
	# columns, data = [], []
	# return columns, data


def get_data(filters):
	print(f"\n\n\n{filters}\n\n\n")


	_from = filters.get('month')
	to = filters.get('year')

	tmp = ''
	if _from == 'Januari':
		tmp = '01'
	if _from == 'Februari':
		tmp = '02'
	if _from == 'Maret':
		tmp = '03'
	if _from == 'April':
		tmp = '04'
	if _from == 'Mei':
		tmp = '05'
	if _from == 'Juni':
		tmp = '06'
	if _from == 'Juli':
		tmp = '07'
	if _from == 'Agustus':
		tmp = '08'
	if _from == 'September':
		tmp = '09'
	if _from == 'Oktober':
		tmp = '10'
	if _from == 'November':
		tmp = '11'
	if _from == 'Desember':
		tmp = '12'

	gabung = to+"-"+tmp+"%"
	# frappe.msgprint(gabung)

	data = frappe.db.sql(f"""
			SELECT ss.bank_name AS 'transfer_type',ss.bank_account_no AS 'credit_account',
			ss.employee_name AS 'receiver_name',ss.gross_pay AS 'amount',
			e.department AS 'dept',SUM(ss.`gross_pay`) AS 'total' FROM `tabSalary Slip` ss JOIN `tabEmployee` e ON ss.employee = e.name 
			WHERE ss.posting_date like '{gabung}' """, as_dict=1)
	# WHERE (ss.posting_date BETWEEN '{_from}' and '{to}')

	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Transaction ID"),
			"fieldname": "transaction_id",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Transfer Type"),
			"fieldname": "transfer_type",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Beneficairy ID"),
			"fieldname": "beneficairy_id",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Credit Account"),
			"fieldname": "credit_account",
			"fieldtype": "int",
			"width": 180
		},
		{
			"label": _("Receiver Name"),
			"fieldname": "receiver_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 180
		},
		{
			"label": _("Dept"),
			"fieldname": "dept",
			"fieldtype": "Data",
			"width": 180
		}
	]

	return columns
