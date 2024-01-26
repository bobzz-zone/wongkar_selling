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

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	kondisi = ""
	if filters.get("area"):
		kondisi = " and ec.cost_center = '{}' ".format(filters.get("area"))

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

	# gabung = tahun+'-'+bulan

	# ec = frappe.db.sql(""" SELECT 
	# 	ec.cost_center as area,
	# 	ecd.expense_date as tgl_tanasaksi,
	# 	ecd.expense_type as type,
	# 	ecd.description as description,
	# 	ecd.amount as kredit,
	# 	ec.status,
	# 	cc.parent_cost_center as cab,
	# 	ec.name as dokumen
	# 	from `tabExpense Claim` ec 
	# 	left join `tabExpense Claim Detail` ecd on ecd.parent = ec.name
	# 	left join `tabCost Center` cc on cc.name = ec.cost_center
	# 	where ec.docstatus = 1 and ecd.expense_date between '{}' and '{}' 
	# 	and ec.cost_center = '{}' order by ecd.expense_date asc """.format(from_date,to_date,filters.get("area")),as_dict=1,debug=1)

	ec = frappe.db.sql(""" SELECT
		gl.`posting_date` AS tgl_tanasaksi,
		gl.`voucher_type`,
		gl.`voucher_no` AS dokumen,
		IF(gl.voucher_type='Expense Claim',gl.`debit`,0) AS kredit,
		IF(gl.voucher_type='Payment Entry',gl.`debit`,0) AS debet,
		gl.cost_center as area,
		cc.parent_cost_center as cab,
		gl.remarks as description
		FROM `tabGL Entry` gl 
		left join `tabCost Center` cc on cc.name = gl.cost_center
		WHERE gl.is_cancelled = 0 AND gl.voucher_type IN ('Expense Claim','Payment Entry') 
		AND gl.docstatus = 1 AND gl.posting_date BETWEEN '{}' AND '{}' AND gl.debit > 0 
		AND gl.cost_center = '{}' ORDER BY  gl.posting_date ASC """.format(from_date,to_date,filters.get("area")),as_dict=1,debug=1)

	# 11.0104.01.00.00.001 - Petty Cash - CITY1 - HND
	
	saldo_awal = frappe.db.sql(""" SELECT sum(debit)-sum(credit) as saldo,"Saldo Awal" as description
		from `tabGL Entry` gl where gl.account = '{}' 
		and gl.is_cancelled = 0 and gl.posting_date > '{}' 
		and gl.voucher_type = "Journal Entry" """.format(filters.get("akun"),from_date),as_dict=1,debug=1)

	cek_je = frappe.db.sql(""" SELECT posting_date,remarks,debit
		from `tabGL Entry` gl where gl.account = '{}' 
		and gl.is_cancelled = 0 and gl.debit > 0 
		and gl.voucher_type = "Journal Entry" and gl.posting_date between '{}' and '{}' """.format(filters.get("akun"),from_date,to_date),debug=1)
	
	data = []
	data.extend(saldo_awal or [])
	saldo = data[0]['saldo']
	tot_deb = 0
	tot_kre = 0
	for i in ec:
		saldo = saldo + i['debet'] - i['kredit'] 
		tot_deb += i['debet']
		tot_kre += i['kredit']
		i.update({
				'saldo': saldo
			})
	data.extend(ec or [])

	

	total = [{
		'description' : 'Total',
		'debet': tot_deb,
		'kredit': tot_kre
	}]

	# data.extend(total or [])

	# frappe.msgprint(str(data)+' dataxxx')
	
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Cab"),
			"fieldname": "cab",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 100
		},
		{
			"label": _("Area"),
			"fieldname": "area",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 100
		},
		{
			"label": _("Tgl Transaksi"),
			"fieldname": "tgl_tanasaksi",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Description"),
			"fieldname": "description",
			"fieldtype": "Text Editor",
			"width": 250
		},
		# {
		# 	"label": _("Expanse Claim Type"),
		# 	"fieldname": "type",
		# 	"fieldtype": "Data",
		# 	"width": 100
		# },
		# {
		# 	"label": _("Dokumen"),
		# 	"fieldname": "dokumen",
		# 	"fieldtype": "Data",
		# 	"width": 100
		# },
		# {
		# 	"label": _("Status"),
		# 	"fieldname": "status",
		# 	"fieldtype": "Text Editor",
		# 	"width": 100
		# },
		{
			"label": _("Debet"),
			"fieldname": "debet",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": _("Kredit"),
			"fieldname": "kredit",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"label": _("Saldo"),
			"fieldname": "saldo",
			"fieldtype": "Currency",
			"width": 150
		},

	]

	return columns

