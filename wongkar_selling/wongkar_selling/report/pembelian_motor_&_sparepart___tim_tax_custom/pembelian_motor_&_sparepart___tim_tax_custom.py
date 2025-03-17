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
	kondisi = ""
	if filters.get("purchase_invoice"):
		kondisi = " and pinv.name = '{}' ".format(filters.get("purchase_invoice"))

	data = frappe.db.sql(""" 
					SELECT
					  	pinv.name as id,
					  	pinv.bill_no,
					  	pinv.faktur_pajak,
					  	pinv.company,
					  	pinv.posting_date,
					  	pinv.supplier,
					  	pinv.bill_date,
					  	pinv.currency,
					  	pinv.supplier_name,
					  	pinv.base_grand_total,
						pinv.status,
						pinv.due_date,
					  	pinv.is_return,
					  	pinv.release_date,
					  	pinv.on_hold,
					  	pinv.represents_company,
					  	pinv.grand_total,
						pii.item_code,
					  	pii.item_name,
					  	pinv.party_account_currency,
					  	pri.serial_no as serial_no,
					  	pinv.outstanding_amount,
					  	pii.rate,
					  	pii.amount,
					  	pii.net_amount,
					  	pii.qty,
					  	pii.description,
					  	pinv.is_internal_supplier
					from `tabPurchase Invoice` pinv
					join `tabPurchase Invoice Item` pii on pii.parent = pinv.name
					left join `tabPurchase Receipt Item` pri on pri.purchase_order_item = pii.po_detail 
					where pinv.docstatus = 1 {} and pinv.posting_date between '{}' and '{}' 
					  """.format(kondisi,filters.get("from_date"),filters.get("to_date")),as_dict=1,debug=1)

	# frappe.msgprint(str(data)+ ' dataxx')
	# for i in data:
	# 	if i['serial_no']:
	# 		if '\n' in i['serial_no']:
	# 			i['serial_no'] = i['serial_no'].replace('\n',' ')

	tampil2 = []
	tampil = []
	for i in range(len(data)):
		if data[i]["serial_no"]:
			if "\n" in data[i]["serial_no"]:
				# frappe.msgprint(str(data[i])+ ' dataxx')
				tmp_sn = data[i]["serial_no"].split('\n')
				if len(tmp_sn) > 1:
					for t in tmp_sn:
						data[i].update({'serial_no' : t})
						tes = data[i]
						# frappe.msgprint(str(tes)+ ' teszz')
						tampil.append({
							"id": data[i]['id'],
							"bill_no": data[i]['bill_no'],
							"faktur_pajak": data[i]['faktur_pajak'],
							"company": data[i]['company'],
							"posting_date": data[i]['posting_date'],
							"supplier": data[i]['supplier'],
							"bill_date": data[i]['bill_date'],
							"currency": data[i]['currency'],
							"supplier_name": data[i]['supplier_name'],
							"base_grand_total": data[i]['base_grand_total'],
							"status": data[i]['status'],
							"due_date": data[i]['due_date'],
							"is_return": data[i]['is_return'],
							"release_date": data[i]['release_date'],
							"on_hold": data[i]['on_hold'],
							"represents_company": data[i]['represents_company'],
							"grand_total": data[i]['grand_total'],
							"item_code": data[i]['item_code'],
							"item_name": data[i]['item_name'],
							"party_account_currency": data[i]['party_account_currency'],
							"outstanding_amount": data[i]['outstanding_amount'],
							"rate":data[i]['rate'],
							"amount": data[i]['amount'],
							"net_amount": data[i]['net_amount'],
							"qty": data[i]['qty'],
							"description": data[i]['description'],
							"is_internal_supplier": data[i]['is_internal_supplier'],
							'serial_no' : t
						})
			else:
				tampil.append(data[i])
		else:
			tampil.append(data[i])
		# frappe.msgprint(str(data[i])+ ' dataxx')
	# data = []
	return tampil

def get_columns(filters):
	columns = [
		{
			"label": _("ID"),
			"fieldname": "id",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			# "width": 200
		},
		{
			"label": _("Supplier Invoice No"),
			"fieldname": "bill_no",
			"fieldtype": "Data",
			# "width": 200
		},
		{
			"label": _("Faktur Pajak"),
			"fieldname": "faktur_pajak",
			"fieldtype": "Data",
			# "width": 200
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			# "width": 200
		},
		{
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			# "width": 200
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			# "width": 200
		},
		{
			"label": _("Supplier Invoice Date"),
			"fieldname": "bill_date",
			"fieldtype": "Date",
			# "width": 200
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			# "width": 200
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			# "width": 200
		},
		{
			"label": _("Grand Total (Company Currency)"),
			"fieldname": "base_grand_total",
			"fieldtype": "Currency",
			# "width": 200
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			# "width": 200
		},
		{
			"label": _("Due Date"),
			"fieldname": "due_date",
			"fieldtype": "Date",
			# "width": 200
		},
		{
			"label": _("Is Return (Debit Note)"),
			"fieldname": "is_return",
			"fieldtype": "Check",
			# "width": 200
		},
		{
			"label": _("Is Return (Debit Note)"),
			"fieldname": "is_return",
			"fieldtype": "Check",
			# "width": 200
		},
		{
			"label": _("Release Date"),
			"fieldname": "release_date",
			"fieldtype": "Date",
			# "width": 200
		},
		{
			"label": _("Hold Invoice"),
			"fieldname": "on_hold",
			"fieldtype": "Check",
			# "width": 200
		},
		{
			"label": _("Represents Company"),
			"fieldname": "represents_company",
			"fieldtype": "Link",
			"options": "Company",
			# "width": 200
		},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			# "width": 200
		},
		{
			"label": _("Item (Purchase Invoice Item)"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			# "width": 200
		},
		{
			"label": _("Item Name (Purchase Invoice Item)"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			# "width": 200
		},
		{
			"label": _("Party Account Currency"),
			"fieldname": "party_account_currency",
			"fieldtype": "Link",
			"options": "Currency",
			# "width": 200
		},
		{
			"label": _("Serial No"),
			"fieldname": "serial_no",
			"fieldtype": "Text",
			"width": 200
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			# "width": 200
		},
		{
			"label": _("Rate (Purchase Invoice Item)"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			# "width": 200
		},
		{
			"label": _("Amount (Purchase Invoice Item)"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			# "width": 200
		},
		{
			"label": _("Net Amount (Purchase Invoice Item)"),
			"fieldname": "net_amount",
			"fieldtype": "Currency",
			# "width": 200
		},
		{
			"label": _("Accepted Qty (Purchase Invoice Item)"),
			"fieldname": "qty",
			"fieldtype": "Float",
			# "width": 200
		},
		{
			"label": _("Description (Purchase Invoice Item)"),
			"fieldname": "description",
			"fieldtype": "Text Editor",
			# "width": 200
		},
		{
			"label": _("Is Internal Supplier"),
			"fieldname": "is_internal_supplier",
			"fieldtype": "Check",
			# "width": 200
		},
	]

	return columns

