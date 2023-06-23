# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AdvanceLeasing(Document):
	def validate(self):
		self.sisa = self.nilai - self.terpakai


@frappe.whitelist()
def make_pe(name_fp,sisa):
	doc_pe = frappe.new_doc("Payment Entry")
	doc_pe.advance_leasing = name_fp
	doc_pe.payment_type = "Internal Transfer"
	doc_pe.down_payment = 0
	doc_pe.cek_adv_leasing = 1
	doc_pe.paid_amount = sisa
	doc_pe.received_amount = sisa
	doc_pe.flags.ignore_permissions = True
	

	return doc_pe.as_dict()
