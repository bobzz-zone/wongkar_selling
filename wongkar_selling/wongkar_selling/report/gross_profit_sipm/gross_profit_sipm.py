# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
def execute(filters=None):
	columns, data = [], []
	columns=["Date:Date:100","Invoice:Link/Sales Invoice Penjualan Motor:150","Leasing:Link/Customer:100","No Mesin:Link/Serial No:200","Nama Type:Data:150","Item:Link/Item:150","Harga Jual:Currency:150",
		"COGS:Currency:150","Gross Profit:Currency:150","Cost STNK:Currency:150","Cost BPKB:Currency:150","GP Percentage:Percent:100","ROI:Percent:100"]
#	columns=["Date:Date:100","Invoice:Link/Sales Invoice Penjualan Motor:150","Leasing:Link/Customer:100","Item:Link/Item:150","Harga Jual:Currency:150",
#               "COGS:Currency:150","Gross Profit:Currency:150","GP Percentage:Percent:100","ROI:Percent:100"]
	#dapatkan data salesinvoice yang related
#sum(gl.credit) as "sales",sum(gl.debit) as "cogs" ,sum(gl.credit-gl.debit) as "profit"
#,sum(if(gl.account like '%STNK%',gl.debit),0) as "stnk",sum(if(gl.account like '%BPKB%',gl.debit),0) as "bpkb"
	data=frappe.db.sql("""select sipm.posting_date,sipm.name,sipm.customer,sn.name,i.item_group,sipm.item_code,
			sum(if(a.root_type !="Liability", gl.credit,0)) as "sales",sum(if(a.root_type !="Liability", gl.debit,0)) as "cogs" , sum(if(a.root_type !="Liability", gl.credit-gl.debit,0)) as "profit",
			sum(if(a.root_type="Liability",	if(gl.account like '%STNK%' ,gl.credit,0),0)) as "stnk",sum(if(a.root_type="Liability",if(gl.account like '%BPKB%' ,gl.credit,0),0)) as "bpkb"
			from `tabGL Entry` gl
	join tabAccount a on gl.account=a.name 
	join `tabSales Invoice Penjualan Motor` sipm on sipm.name=gl.voucher_no
	join `tabItem` i on i.name = sipm.item_code
	join `tabSerial No` sn on sn.name = sipm.no_rangka
	where gl.voucher_type="Sales Invoice Penjualan Motor" and gl.is_cancelled=0 and sipm.docstatus=1 and a.root_type IN ("Income","Expense","Liability")
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
		try:
			row.append(100*(flt(row[6])/flt(row[4])))
		except:
			row.append(0)
		try:
			row.append(100*(flt(row[6])/flt(row[5])))
		except:
			row.append(0)
	try:
		data.append(["","","","",total_sales,total_cogs,total_gp,"","",100*(total_gp/total_sales) or 0,100*(total_gp/total_cogs) or 0])
	except:
		pass
	return columns, data
