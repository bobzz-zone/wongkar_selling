import frappe

def make_serial_no(doc,method):
	pass
	# if doc.purpose == "Repack":

	# 	for item in doc.items:
	# 		if item.t_warehouse and item.serial_no:
	# 			# JBK3E1408377--MH1JBK315NK410006-Repack
	# 			doc = frappe.new_doc("Serial No")
	# 			doc.save()

@frappe.whitelist()
def cek_diskon_pinv(self,method):
	if self.purchase_invoice:
		frappe.throw('Tidak Bisa Cancel Disini !')