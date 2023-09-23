import frappe

@frappe.whitelist()
def get_kelurahan(kel):
	return frappe.get_doc("Kelurahan",kel).kelurahan