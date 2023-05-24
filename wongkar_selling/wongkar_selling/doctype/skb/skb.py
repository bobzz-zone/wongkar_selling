# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SKB(Document):
	def validate(self):
		self.biaya_stnk = frappe.get_doc("Tabel Biaya Motor",{"parent":self.sales_invoice_penjualan_motor,"type":"STNK"}).amount
		self.biaya_bpkb = frappe.get_doc("Tabel Biaya Motor",{"parent":self.sales_invoice_penjualan_motor,"type":"BPKB"}).amount
