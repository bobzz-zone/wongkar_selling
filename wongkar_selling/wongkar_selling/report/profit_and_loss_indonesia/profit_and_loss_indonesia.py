# Copyright (c) 2013, w and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
def execute(filters=None):
	columns, source = ["Title:Data:500","Amount:Currency:200"], [{},{},{},{},{},{},{}]
	source_gl = frappe.db.sql("""select account,credit-debit from `tabGL Entry` where is_cancelled=0 and 
		company="{}" and posting_date >= "{}" and posting_date <="{}" """.format(filters.get("company"),filters.get("from_date"),filters.get("to_date")),as_list=1)
	source[0]={"title":"40.0000.00.00.00.000 - Sales & Revenue Element","amount":0}
	source[1]={"title":"50.0000.00.00.00.000 - Cost of Goods Sold / Manufactured","amount":0}
	source[2]={"title":"60.0000.00.00.00.000 - Operational Expenses","amount":0}
	source[3]={"title":"70.0000.00.00.00.000 - Non-Operating Income","amount":0}
	source[4]={"title":"80.0000.00.00.00.000 - Non-Operating Expense","amount":0}
	source[5]={"title":"80.0400.00.00.00.000 - Tax Expenses","amount":0}
	source[6]={"title":"90.0000.00.00.00.000 - Other Comperhensive Income","amount":0}
	for gl in source_gl:
		if gl[0].startswith("40"):
			source[0]['amount']=flt(source[0]['amount'])+flt(gl[1])
		if gl[0].startswith("50"):
			source[1]['amount']=flt(source[1]['amount'])+flt(gl[1])
		if gl[0].startswith("60"):
			source[2]['amount']=flt(source[2]['amount'])+flt(gl[1])
		if gl[0].startswith("70"):
			source[3]['amount']=flt(source[3]['amount'])+flt(gl[1])
		if gl[0].startswith("90"):
			source[6]['amount']=flt(source[6]['amount'])+flt(gl[1])
		if gl[0].startswith("80"):
			if gl[0].startswith("80.0400"):
				source[5]['amount']=flt(source[5]['amount'])+flt(gl[1])
			else:
				source[4]['amount']=flt(source[4]['amount'])+flt(gl[1])
	data=[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]
	data[0]=source[0]
	data[1]=source[1]
	laba_kotor=source[0]['amount']+source[1]['amount']
	data[2]={"title":"<strong>Laba kotor</strong>","amount":laba_kotor}
	data[3]={"title":"","amount":""}
	data[4]=source[2]
	laba_kotor=laba_kotor+source[2]['amount']
	data[5]={"title":"<strong>Laba Operational</strong>","amount":laba_kotor}
	data[6]={"title":"","amount":""}
	data[7]=source[3]
	data[8]=source[4]
	laba_kotor=laba_kotor+source[3]['amount']+source[4]['amount']
	data[9]={"title":"<strong>Laba Sebelum Pajak</strong>","amount":laba_kotor}
	data[10]={"title":"","amount":""}
	data[11]=source[5]
	laba_kotor=laba_kotor+source[5]['amount']
	data[12]={"title":"<strong>Laba Bersih</strong>","amount":laba_kotor}
	data[13]={"title":"","amount":""}
	data[14]=source[6]

	return columns, data
