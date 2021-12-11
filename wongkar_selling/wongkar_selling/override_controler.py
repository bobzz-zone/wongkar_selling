# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import date
import datetime
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.invoice_discounting.invoice_discounting import get_party_account_based_on_invoice_discounting
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
from frappe import _, scrub, ValidationError
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account, get_bank_account_details
from erpnext.accounts.utils import get_outstanding_invoices, get_account_currency, get_balance_on
import frappe, erpnext, json
from six import string_types, iteritems

def calculate_totals_custom(self):
		frappe.throw("test")
		self.doc.grand_total = flt(self.doc.get("taxes")[-1].total) + flt(self.doc.rounding_adjustment) \
			if self.doc.get("taxes") else flt(self.doc.net_total)

		self.doc.total_taxes_and_charges = flt(self.doc.grand_total - self.doc.net_total
			- flt(self.doc.rounding_adjustment), self.doc.precision("total_taxes_and_charges"))

		self._set_in_company_currency(self.doc, ["total_taxes_and_charges", "rounding_adjustment"])

		if self.doc.doctype in ["Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "POS Invoice"]:
			self.doc.base_grand_total = flt(self.doc.grand_total * self.doc.conversion_rate, self.doc.precision("base_grand_total")) \
				if self.doc.total_taxes_and_charges else self.doc.base_net_total
		else:
			self.doc.taxes_and_charges_added = self.doc.taxes_and_charges_deducted = 0.0
			for tax in self.doc.get("taxes"):
				if tax.category in ["Valuation and Total", "Total"]:
					if tax.add_deduct_tax == "Add":
						self.doc.taxes_and_charges_added += flt(tax.tax_amount_after_discount_amount)
					else:
						self.doc.taxes_and_charges_deducted += flt(tax.tax_amount_after_discount_amount)

			self.doc.round_floats_in(self.doc, ["taxes_and_charges_added", "taxes_and_charges_deducted"])

			self.doc.base_grand_total = flt(self.doc.grand_total * self.doc.conversion_rate) \
				if (self.doc.taxes_and_charges_added or self.doc.taxes_and_charges_deducted) \
				else self.doc.base_net_total

			self._set_in_company_currency(self.doc,
				["taxes_and_charges_added", "taxes_and_charges_deducted"])

		self.doc.round_floats_in(self.doc, ["grand_total", "base_grand_total"])

		self.set_rounded_total()