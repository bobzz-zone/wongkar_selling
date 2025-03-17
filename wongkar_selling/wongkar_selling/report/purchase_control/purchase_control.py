# Copyright (c) 2024, w and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	columns = get_columns(filters)

	condition = ''
	if filters.get("po"):
		condition = "and po.name = '{}'".format(filters.get("po"))
	if filters.get("pinv"):
		condition = "and pinv.name = '{}'".format(filters.get("pinv"))
	
	if filters.get("pt") == 'Motor':
		data = frappe.db.sql(""" 
			SELECT 
				po.name as po,
				poi.item_code as item,
				pri.parent as prec,
				pii.parent as pinv
			from `tabPurchase Order` po
			join `tabPurchase Order Item` poi on po.name = poi.parent
			left join `tabPurchase Receipt Item` pri on pri.purchase_order_item = poi.name and pri.docstatus = 1
			left join `tabPurchase Invoice Item` pii on pii.po_detail = poi.name and pii.docstatus = 1
			where po.docstatus = 1 and po.transaction_date between '{}' and '{}' 
			{} """.format(from_date,to_date,condition),as_dict=1,debug=1)
	elif filters.get("pt") == 'Sperepart':
		data = frappe.db.sql(""" 
			SELECT 
				pinv.name as pinv,
				pii.item_code as item,
				pri.parent as prec
			from `tabPurchase Invoice` pinv
			join `tabPurchase Invoice Item` pii on pinv.name = pii.parent
			left join `tabPurchase Receipt Item` pri on pri.purchase_invoice_item = pii.name and pri.docstatus = 1
			where pinv.docstatus = 1 and pinv.posting_date between '{}' and '{}' and pinv.bill_no like '%INV%'
			{} """.format(from_date,to_date,condition),as_dict=1,debug=1)
	
	return columns, data


def get_columns(filters):
	"""return columns"""
	if filters.get("pt") == 'Motor':
		columns = [
			{
				"label": _("Purchase Order"),
				"fieldname": "po",
				"fieldtype": "Link",
				"options": "Purchase Order",
				"width": 200,
			},
			{
				"label": _("Item"),
				"fieldname": "item",
				"fieldtype": "Link",
				"options": "Item",
				"width": 200,
			},
			{
				"label": _("Purchase Receipt"),
				"fieldname": "prec",
				"fieldtype": "Link",
				"options": "Purchase Receipt",
				"width": 200,
			},
			{
				"label": _("Purchase Invoice"),
				"fieldname": "pinv",
				"fieldtype": "Link",
				"options": "Purchase Invoice",
				"width": 200,
			}
		]
	elif filters.get("pt") == 'Sperepart':
		columns = [
			{
				"label": _("Purchase Invoice"),
				"fieldname": "pinv",
				"fieldtype": "Link",
				"options": "Purchase Invoice",
				"width": 200,
			},
			{
				"label": _("Item"),
				"fieldname": "item",
				"fieldtype": "Link",
				"options": "Item",
				"width": 200,
			},
			{
				"label": _("Purchase Receipt"),
				"fieldname": "prec",
				"fieldtype": "Link",
				"options": "Purchase Receipt",
				"width": 200,
			},
			
		]
	return columns

