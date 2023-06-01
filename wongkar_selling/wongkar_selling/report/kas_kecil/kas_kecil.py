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
		where ec.docstatus = 1 {} and ecd.expense_date between '{}' and '{}' order by ecd.expense_date asc """.format(kondisi,from_date,to_date),as_list = 1,debug=1)

	saldo_awal = frappe.db.sql(""" SELECT sum(debit)-sum(credit) as debit 
		from `tabGL Entry` gl where gl.account = '11.0104.01.00.00.001 - Petty Cash - CITY1 - HND' 
		and gl.is_cancelled = 0 and gl.posting_date < '{}' 
		and gl.voucher_type = "Journal Entry" """.format(from_date))

	cek_je = frappe.db.sql(""" SELECT posting_date,remarks,debit
		from `tabGL Entry` gl where gl.account = '11.0104.01.00.00.001 - Petty Cash - CITY1 - HND' 
		and gl.is_cancelled = 0 and gl.debit > 0 
		and gl.voucher_type = "Journal Entry" and gl.posting_date between '{}' and '{}' """.format(from_date,to_date))
	
	# frappe.msgprint(str(cek_je)+ " cek_je")

	tampil = [[
				"",
				"",
				"",
				"Saldo Awal",
				"",
				"",
				"",
				saldo_awal[0][0]
			]]
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
				0,
				i[4],
				d-k
			])
	
	# frappe.msgprint(str(tampil)+ " tampil")
	output = []
	if cek_je:
		for c in cek_je:
			tampil.append(["","",c[0],c[1],"",c[2],0,0])

	# for t in tampil[0:]:
	# 	frappe.msgprint(str(t[1][8])+'+'+str(t[6])+"-"+str(t[7]))

	# frappe.msgprint(str(output)+ " output")
	sort = sorted(tampil[1:], key= lambda x: x[2])
	sort.insert(0, tampil[0])
	
	# frappe.msgprint(str(sort)+ " sort")
	conter = 0
	conter2 = 1
	debet = 0 
	kredit = 0
	con = 1
	frappe.msgprint(str(len(sort))+' len sort')
	# for s in sort:
	# 	# frappe.msgprint(str(sort[conter][8])+"wkwkwk")
	# 	# sort[conter][8] = 9999
	# 	sort[conter2][7] = sort[conter][7] + sort[conter2][5] - sort[conter2][6]
		
	# 	if conter2 != len(sort)-1:
	# 		conter = conter + 1
	# 		conter2 = conter2 + 1
	# 		frappe.msgprint(str(sort[conter][5]) + " sort[conter][5]")

	for i in range(len(sort)-1):
		debet = debet + sort[i+1][5]
		kredit = kredit + sort[i+1][6]
		
		sort[i+1][7] = sort[i][7]+sort[i+1][5] - sort[i+1][6]

		# sort[14][7] = 9999
	# 	frappe.msgprint(str(conter2)+ " conter2")
	# 	frappe.msgprint(str(conter)+ " conter")
	# frappe.msgprint(str(sort[1:][1:])+ " conterxx")
	# frappe.msgprint(str(sort[15][7])+'jjj')
	sort.append(
		[
			"",
			"",
			"",
			"Total",
			"",
			debet,
			kredit,
			""
		]
		)
	return sort

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
			"width": 200
		},
		{
			"label": _("Kredit"),
			"fieldname": "kredit",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Saldo"),
			"fieldname": "saldo",
			"fieldtype": "Currency",
			"width": 200
		},

	]

	return columns

