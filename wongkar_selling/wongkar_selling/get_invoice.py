# -*- coding: utf-8 -*-
# Copyright (c) 2021, w and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
import datetime
from erpnext.accounts.utils import get_fiscal_years, validate_fiscal_year, get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.accounts.general_ledger import make_gl_entries

# pembayaran Motor
@frappe.whitelist()
def get_inv(supplier,types):
	data = frappe.db.get_list('Tabel Biaya Motor',filters={'tertagih': 0,'vendor': supplier,'type': types,'parenttype': 'Sales Invoice Penjualan Motor'},fields=['*'])

	return data

@frappe.whitelist()
def get_invd(customer):
	data = frappe.db.get_list('Table Discount',filters={'customer': customer,"tertagih": 0,'parenttype': 'Sales Invoice Penjualan Motor'},fields=['*'])

	return data

@frappe.whitelist()
def get_invd_l(customer):
	# data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={'cara_bayar': 'Credit',"docstatus": ["=",1],"tertagih": 0,'nama_leasing': customer},fields=['*'])

	# return data
	data = frappe.db.sql(""" SELECT sinv.name,sinv.posting_date,sinv.no_rangka,sinv.nama_promo,sinv.item_code,sinv.pemilik,tdl.nama_leasing,sum(tdl.nominal) as nominal from `tabSales Invoice Penjualan Motor` sinv
		join `tabTable Disc Leasing` tdl on sinv.name = tdl.parent where tdl.nama_leasing = '{0}' and tdl.tertagih = 0 and sinv.docstatus = 1  """.format(customer),as_dict=1)
	return data

@frappe.whitelist()
def get_invc(leasing):
	data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={"customer": leasing,'cara_bayar': 'Credit',"docstatus": ["=",1],'outstanding_amount':['!=',0]},fields=['*'])

	return data

@frappe.whitelist()
def get_item_price(item_code,price_list,posting_date):
	"""
		Get name, price_list_rate from Item Price based on conditions
			Check if the desired qty is within the increment of the packing list.
		:param args: dict (or frappe._dict) with mandatory fields price_list, uom
			optional fields transaction_date, customer, supplier
		:param item_code: str, Item Doctype field item_code
	"""

	# args['item_code'] = item_code

	# conditions = """where item_code=%(item_code)s
	# 	and price_list=%(price_list)s
	# 	and ifnull(uom, '') in ('', %(uom)s)"""

	# conditions += "and ifnull(batch_no, '') in ('', %(batch_no)s)"

	# if not ignore_party:
	# 	if args.get("customer"):
	# 		conditions += " and customer=%(customer)s"
	# 	elif args.get("supplier"):
	# 		conditions += " and supplier=%(supplier)s"
	# 	else:
	# 		conditions += "and (customer is null or customer = '') and (supplier is null or supplier = '')"

	# if args.get('transaction_date'):
	# 	conditions += """ and %(transaction_date)s between
	# 		ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""

	# if args.get('posting_date'):
	# 	conditions += """ and %(posting_date)s between
	# 		ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""
	data = frappe.db.sql(""" select name, price_list_rate, uom from `tabItem Price` where item_code='{0}' and price_list='{1}' and (valid_from is NULL or valid_from <='{2}') and (valid_upto is NULL or valid_upto >='{2}') order by valid_from desc, batch_no desc, uom desc """.format(item_code,price_list,posting_date),as_dict=1)
	
	return data
#(posting_date between ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31'))

@frappe.whitelist()
def get_leasing(item_code,nama_promo,territory_real,posting_date):
	data = frappe.db.sql(""" SELECT rdl.leasing,tdl.coa,tdl.amount  from `tabRule Discount Leasing` rdl 
		join `tabTable Discount Leasing` tdl on rdl.name = tdl.parent
		where rdl.item_code='{0}' and rdl.nama_promo='{1}' and rdl.territory='{2}' and (rdl.valid_from is NULL or rdl.valid_from <='{3}') and (rdl.valid_to is NULL or rdl.valid_to >='{3}') AND rdl.disable = 0 """.format(item_code,nama_promo,territory_real,posting_date),as_dict=1)
	return data
