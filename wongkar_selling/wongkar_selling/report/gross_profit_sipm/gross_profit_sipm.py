# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
def execute(filters=None):
	columns, data = [], []
	columns=["Date:Date:100","Invoice:Link/Sales Invoice Penjualan Motor:150","Leasing:Data:100","No Mesin:Link/Serial No:200","Nama Type:Data:150","Item:Link/Item:150","ID Jual:Data:150","Cabang Jual:Data:150","OTR:Currency:150","Potongan:Currency:150","Adjustment:Currency:150","Harga Jual:Currency:150",
		"COGS:Currency:150","Gross Profit:Currency:150","Cost STNK:Currency:150","Cost BPKB:Currency:150","GP Percentage:Percent:100","ROI:Percent:100"]
#	columns=["Date:Date:100","Invoice:Link/Sales Invoice Penjualan Motor:150","Leasing:Link/Customer:100","Item:Link/Item:150","Harga Jual:Currency:150",
#               "COGS:Currency:150","Gross Profit:Currency:150","GP Percentage:Percent:100","ROI:Percent:100"]
	#dapatkan data salesinvoice yang related
#sum(gl.credit) as "sales",sum(gl.debit) as "cogs" ,sum(gl.credit-gl.debit) as "profit"
#,sum(if(gl.account like '%STNK%',gl.debit),0) as "stnk",sum(if(gl.account like '%BPKB%',gl.debit),0) as "bpkb"
	#update columns
	data=frappe.db.sql("""select sipm.posting_date,sipm.name,if(c.customer_group="Leasing",sipm.customer,"CASH"),SUBSTRING_INDEX(sn.name,'--', 1) AS first_name,i.item_name,sipm.item_group,pc.parent_cost_center,sipm.cost_center,sipm.harga,sipm.nominal_diskon,sipm.adj_discount,
			sum(if(a.name like "40.0101.%", gl.credit,if(a.name like "40.0199.%",gl.credit,0))) as "sales",sum(if(account_type ="Cost of Goods Sold", gl.debit,0)) as "cogs" ,
			sum(if(a.root_type="Liability",	if(gl.account like '%STNK%' ,gl.credit,0),0)) as "stnk",sum(if(a.root_type="Liability",if(gl.account like '%BPKB%' ,gl.credit,0),0)) as "bpkb"
			from `tabGL Entry` gl
	join tabAccount a on gl.account=a.name 
	join `tabSales Invoice Penjualan Motor` sipm on sipm.name=gl.voucher_no
	join `tabItem` i on i.name = sipm.item_code
	join `tabSerial No` sn on sn.name = sipm.no_rangka
	left join `tabCustomer` c on c.name=sipm.customer
	left join `tabCost Center` cc on sipm.cost_center=cc.name
	left join `tabCost Center` pc on cc.parent_cost_center=pc.name

	where gl.voucher_type="Sales Invoice Penjualan Motor" and gl.is_cancelled=0 and sipm.docstatus=1 and a.root_type IN ("Income","Expense","Liability")
	and gl.posting_date >= "{}" and gl.posting_date <="{}" and gl.company="{}"
	group by sipm.name
	 """.format(filters.get("from_date"),filters.get("to_date"),filters.get("company")),as_list=1)
	total_sales=0
	total_cogs=0
	total_gp=0
	result=[]
	for row in data:
		total_sales+=flt(row[11])+flt(row[13])+flt(row[14])
		total_cogs+=flt(row[12])
		total_gp+=flt(row[11])-flt(row[12])
		row8=0
		row9=0
		try:
			row8=(100*(flt(row[11])-flt(row[12]))/flt(row[11]))
		except:
			row8=0
		try:
			row9=(100*((flt(row[11])-flt(row[12]))/flt(row[12])))
		except:
			row9=0
		result.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],flt(row[11])+flt(row[13])+flt(row[14]),row[12],flt(row[11])-flt(row[12]),row[13],row[14],row8,row9])
	try:
		result.append(["","","","","","","","","","","",total_sales,total_cogs,total_gp,"","",100*(total_gp/total_sales) or 0,100*(total_gp/total_cogs) or 0])
	except:
		pass
	return columns,result
