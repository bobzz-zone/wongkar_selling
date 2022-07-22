# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
def execute(filters=None):
	columns, data = [], []
	columns=["Date:Date:100","Invoice:Link/Sales Invoice Penjualan Motor:150","Leasing:Link/Customer:100","Item:Link/Item:150","Harga Jual:Currency:150",
		"COGS:Currency:150","Gross Profit:Currency:150","GP Percentage:Percent:100","ROI:Percent:100"]
	#dapatkan data salesinvoice yang related
	data=frappe.db.sql("""select sipm.posting_date,sipm.name,sipm.customer,sipm.item_code,sum(gl.credit) as "sales",sum(gl.debit) as "cogs" , sum(gl.credit-gl.debit) as "profit"
			from `tabGL Entry` gl
	join tabAccount a on gl.account=a.name 
	join `tabSales Invoice Penjualan Motor` sipm on sipm.name=gl.voucher_no
	where gl.voucher_type="Sales Invoice Penjualan Motor" and gl.is_cancelled=0 and sipm.docstatus=1 and a.root_type IN ("Income","Expense")
	and gl.posting_date >= "{}" and gl.posting_date <="{}" and gl.company="{}"
	group by sipm.name
	 """.format(filters.get("from_date"),filters.get("to_date"),filters.get("company")),as_list=1)
	total_sales=0
	total_cogs=0
	total_gp=0
	for row in data:
		total_sales+=flt(row[4])
		total_cogs+=flt(row[5])
		total_gp+=flt(row[6])
		row.append(100*(flt(row[6])/flt(row[4])))
		row.append(100*(flt(row[6])/flt(row[5])))
	data.append(["","","","",total_sales,total_cogs,total_gp,100*(total_gp/total_sales) or 0,100*(total_gp/total_cogs) or 0])
	return columns, data
