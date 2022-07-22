import frappe

def make_serial_no(doc,method):
	if doc.purpose == "Repack":

		for item in doc.items:
			if item.t_warehouse and item.serial_no:
				# JBK3E1408377--MH1JBK315NK410006-Repack
				doc = frappe.new_doc("Serial No")
				doc.save()