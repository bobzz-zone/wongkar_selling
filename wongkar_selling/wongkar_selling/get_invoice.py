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
def get_invd_l(leasing,customer):
	data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={'nama_promo':  leasing,'cara_bayar': 'Credit',"docstatus": ["=",1],"tertagih": 0,'nama_leasing': customer},fields=['*'])

	return data


@frappe.whitelist()
def get_invc(leasing,nama_promo):
	data = frappe.db.get_list('Sales Invoice Penjualan Motor',filters={'nama_leasing': leasing,'cara_bayar': 'Credit',"docstatus": ["=",1],"tertagih": 0,'nama_promo': nama_promo,'outstanding_amount':['!=',0]},fields=['*'])

	return data