# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
def execute(filters=None):
	columns, source = ["Title:Data:200","Debit:Currency:200","Credit:Currency:200"], [{},{},{},{},{},{},{}]
	source_gl = frappe.db.sql("""select account,debit,credit from `tabGL Entry` where is_cancelled=0 and 
		company="{}" and posting_date >= "{}" and posting_date <="{}" """.format(filters.get("company"),filters.get("from_date"),filters.get("to_date")),as_list=1)
	source[0]={"title":"40.0000.00.00.00.000 - Sales & Revenue Element","debit":0,"credit":0}
	source[1]={"title":"50.0000.00.00.00.000 - Cost of Goods Sold / Manufactured","debit":0,"credit":0}
	source[2]={"title":"60.0000.00.00.00.000 - Operational Expenses","debit":0,"credit":0}
	source[3]={"title":"70.0000.00.00.00.000 - Non-Operating Income","debit":0,"credit":0}
	source[4]={"title":"80.0000.00.00.00.000 - Non-Operating Expense","debit":0,"credit":0}
	source[5]={"title":"80.0400.00.00.00.000 - Tax Expenses","debit":0,"credit":0}
	source[6]={"title":"90.0000.00.00.00.000 - Other Comperhensive Income","debit":0,"credit":0}
	for gl in source_gl:
		if gl[0].startswith("40"):
			source[0]['debit']=flt(source[0]['debit'])+flt(gl[1])
			source[0]['credit']=flt(source[0]['credit'])+flt(gl[2])
		if gl[0].startswith("50"):
			source[1]['debit']=flt(source[1]['debit'])+flt(gl[1])
			source[1]['credit']=flt(source[1]['credit'])+flt(gl[2])
		if gl[0].startswith("60"):
			source[2]['debit']=flt(source[2]['debit'])+flt(gl[1])
			source[2]['credit']=flt(source[2]['credit'])+flt(gl[2])
		if gl[0].startswith("70"):
			source[3]['debit']=flt(source[3]['debit'])+flt(gl[1])
			source[3]['credit']=flt(source[3]['credit'])+flt(gl[2])
		if gl[0].startswith("90"):
			source[6]['debit']=flt(source[6]['debit'])+flt(gl[1])
			source[6]['credit']=flt(source[6]['credit'])+flt(gl[2])
		if gl[0].startswith("80"):
			if gl[0].startswith("80.0400"):
				source[5]['debit']=flt(source[5]['debit'])+flt(gl[1])
				source[5]['credit']=flt(source[5]['credit'])+flt(gl[2])
			else:
				source[4]['debit']=flt(source[4]['debit'])+flt(gl[1])
				source[4]['credit']=flt(source[4]['credit'])+flt(gl[2])
	data=[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]
	data[0]=source[0]
	data[1]=source[1]
	laba_kotor=source[0]['credit']-source[0]['debit']+source[1]['credit']-source[1]['debit']
	if laba_kotor<0:
		data[2]={"title":"<strong>Laba kotor</strong>","debit":laba_kotor*-1,"credit":0}
	else:
		data[2]={"title":"<strong>Laba kotor</strong>","debit":0,"credit":laba_kotor}
	data[3]={"title":"","debit":"","credit":""}
	data[4]=source[2]
	laba_kotor=laba_kotor+source[2]['credit']-source[2]['debit']
	if laba_kotor<0:
		data[5]={"title":"<strong>Laba Operational</strong>","debit":laba_kotor*-1,"credit":0}
	else:
		data[5]={"title":"<strong>Laba Operational</strong>","debit":0,"credit":laba_kotor}
	data[6]={"title":"","debit":"","credit":""}
	data[7]=source[3]
	data[8]=source[4]
	laba_kotor=laba_kotor+source[3]['credit']-source[3]['debit']+source[4]['credit']-source[4]['debit']
	if laba_kotor<0:
		data[9]={"title":"<strong>Laba Sebelum Pajak</strong>","debit":laba_kotor*-1,"credit":0}
	else:
		data[9]={"title":"Laba Sebelum Pajak</strong>","debit":0,"credit":laba_kotor}
	data[10]={"title":"","<strong>debit":"","credit":""}
	data[11]=source[5]
	laba_kotor=laba_kotor+source[5]['credit']-source[5]['debit']
	if laba_kotor<0:
		data[12]={"title":"<strong>Laba Bersih</strong>","debit":laba_kotor*-1,"credit":0}
	else:
		data[12]={"title":"<strong>Laba Bersih</strong>","debit":0,"credit":laba_kotor}
	data[13]={"title":"","debit":"","credit":""}
	data[14]=source[6]

	return columns, data
