import frappe

def rem_sinv(self,method):
	if self.delivery_document_type == 'Sales Invoice Penjualan Motor' and self.delivery_document_no:
		data = frappe.get_doc("Sales Invoice Penjualan Motor",self.delivery_document_no)
		# self.sales_invoice_penjualan_motor = self.delivery_document_no
		# self.seles_invoice = None
		if not self.pemilik or self.pemilik == "":
			self.pemilik = data.pemilik
			self.customer = data.pemilik
			self.customer_name = data.nama_pemilik
			self.nama_pemilik = data.nama_pemilik

	if not self.delivery_document_no:
		self.pemilik = ""
		self.customer = ""
		self.customer_name = ""
		self.nama_pemilik = ""
		# self.sales_invoice_penjualan_motor = None
		# self.seles_invoice = None
