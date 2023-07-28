# Copyright (c) 2013, w and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date

def execute(filters=None):
	# columns, data = [], []
	# return columns, data

	return get_columns(filters), get_data(filters)

def get_data(filters):
	data = frappe.db.sql(""" 
		SELECT 
			prec.`posting_date` as tanggal,
			prec.`supplier`,
			prec.`name`,
			prec.supplier_delivery_order,
			prec.`status`,
			prec.`set_warehouse`,
			pinv.`due_date` as tgl_jth_tempo,
			SUM(pri.qty) as tot_unit,
			SUM(pri.`amount`) as tot_amount,
			pe.posting_date as tgl_pembayaran,
			IFNULL(SUM(per.`allocated_amount`),0),
			pinv.`status` as status
		FROM `tabPurchase Receipt` prec
		LEFT JOIN `tabPurchase Receipt Item` pri ON pri.parent = prec.`name`
		LEFT JOIN `tabPurchase Invoice Item` pii ON pii.`purchase_receipt` = prec.`name` AND pii.pr_detail = pri.`name`
		LEFT JOIN `tabPurchase Invoice` pinv ON pinv.`name` = pii.`parent`
		LEFT JOIN `tabPayment Entry Reference` per ON per.`docstatus` = 1 AND per.`reference_name` = pinv.`name`
		LEFT JOIN `tabPayment Entry` pe ON pe.name = per.`parent`
		WHERE prec.`docstatus` = 1 and prec.`posting_date` between '{}' and '{}'
		GROUP BY prec.`supplier_delivery_order` ORDER BY prec.`posting_date` ASC """.format(filters.get('from_date'),filters.get('to_date')), as_dict=1)

	return data


def get_columns(filters):
	columns = [
		{
			"label": _("Tanggal"),
			"fieldname": "tanggal",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 180
		},
		{
			"label": _("Supplier Delivery Order"),
			"fieldname": "supplier_delivery_order",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Accepted Ware Haouse"),
			"fieldname": "set_warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 200
		},
		{
			"label": _("Tot Unit"),
			"fieldname": "tot_unit",
			"fieldtype": "Int",
			"width": 70
		},
		{
			"label": _("Tot Amount"),
			"fieldname": "tot_amount",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tgl Jth Tempo"),
			"fieldname": "tgl_jth_tempo",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Tgl Pembayaran"),
			"fieldname": "tgl_pembayaran",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},

	]

	return columns