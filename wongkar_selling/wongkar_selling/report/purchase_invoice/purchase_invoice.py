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
	data = frappe.db.sql(""" SELECT
		prec.supplier_delivery_note,
		pinv.supplier,
		pinv.posting_date,
		pinv.due_date,
		pinv.cost_center,
		sum(pii.qty),
		pinv.grand_total,
		pinv.status,
		pinv.atchement_tagihan,
		pinv.atchement_pelunasan,
		if(pinv.outstanding_amount-sum(per.allocated_amount)<0,DATEDIFF(pe.posting_date,pinv.due_date)+1,DATEDIFF(current_date(),pinv.due_date)+1)
		from `tabPurchase Invoice` pinv
		join `tabPurchase Invoice Item` pii on pii.parent = pinv.name
		join `tabPurchase Receipt` prec on pii.purchase_receipt = prec.name
		left join `tabPayment Entry Reference` per on per.reference_name = pinv.name
		left join `tabPayment Entry` pe on pe.name = per.parent
		where pe.docstatus = 1 or pinv.docstatus = 1 and pinv.posting_date between '{}' and '{}' group by prec.name,pinv.name order by pinv.posting_date asc """.format(filters.get('from_date'),filters.get('to_date')),as_list = 1)
	
	
	

	tampil = []
	if data:
		
		for i in data:
			att_tag = ""
			att_pel = ""

			if i[8]:
				att_tag = "<a href='"+frappe.utils.get_url()+i[8]+"'>"+frappe.utils.get_url()+i[8]+"</a>"
			if i[9]:
				att_pel = "<a href='"+frappe.utils.get_url()+i[9]+"'>"+frappe.utils.get_url()+i[9]+"</a>"
			
			tampil.append([
				i[0],
				i[1],
				i[2],
				i[3],
				i[4],
				i[5],
				i[6],
				i[7],
				i[10],
				att_tag,
				att_pel
			])

	return tampil

def get_columns(filters):
	columns = [
		{
			"label": _("No DO"),
			"fieldname": "no_do",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tgl DO"),
			"fieldname": "tgl_do",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Tgl Jth Tempo"),
			"fieldname": "tgl_jt",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Cabang Beli"),
			"fieldname": "cabang_beli",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Jumlah Unit"),
			"fieldname": "jumlah_unit",
			"fieldtype": "int",
			"width": 100
		},
		{
			"label": _("Total Tagihan"),
			"fieldname": "total_tagihan",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Status Pembayaran"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Lama Overdue"),
			"fieldname": "lama",
			"fieldtype": "int",
			"width": 150
		},
		{
			"label": _("Atchement Tagihan"),
			"fieldname": "att_tagihan",
			"fieldtype": "HTML",
			"width": 150
		},
		{
			"label": _("Atchement Pelunasan"),
			"fieldname": "att_pelunasan",
			"fieldtype": "HTML",
			"width": 150
		},
		

	]

	return columns

