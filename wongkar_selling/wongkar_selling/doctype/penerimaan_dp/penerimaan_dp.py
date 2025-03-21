# Copyright (c) 2023, w and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from datetime import datetime

class PenerimaanDP(Document):
	def on_submit(self):
		self.make_je()

	def validate(self):
		self.hitung_bayar()
		self.missing_value()

	@frappe.whitelist()
	def hitung_bayar(self):
		# frappe.msgprint(str(getdate(self.tanggal)))
		from wongkar_selling.wongkar_selling.get_invoice import get_item_price, get_leasing, get_biaya,get_rule
		if not self.nominal_diskon:
			self.nominal_diskon=0
		if self.paid_amount > 0 and not self.dp_ke_2:
			list_tabel_biaya = get_biaya(self.item_code,self.territory,self.tanggal,1)
			total_biaya_tanpa_dealer = 0
			if list_tabel_biaya:
				for row in list_tabel_biaya:
					if row.valid_from <= getdate(self.tanggal) and row.valid_to >= getdate(self.tanggal):
						if row.type in ['STNK','BPKB']:
							total_biaya_tanpa_dealer += row.amount
			if self.paid_amount < self.harga - total_biaya_tanpa_dealer:
				self.piutang_motor = self.paid_amount
				self.piutang_bpkb_stnk = 0
			elif self.paid_amount > self.harga - total_biaya_tanpa_dealer and not self.off_the_road:
				self.piutang_motor = self.paid_amount - total_biaya_tanpa_dealer
				self.piutang_bpkb_stnk = total_biaya_tanpa_dealer
			elif self.paid_amount > self.harga - total_biaya_tanpa_dealer and self.off_the_road:
				self.piutang_motor = (self.harga - total_biaya_tanpa_dealer) - self.nominal_diskon
				self.piutang_bpkb_stnk = total_biaya_tanpa_dealer
			elif self.paid_amount == self.harga - total_biaya_tanpa_dealer:
				self.piutang_motor = self.harga - total_biaya_tanpa_dealer - self.nominal_diskon
				self.piutang_bpkb_stnk = total_biaya_tanpa_dealer
		if self.off_the_road:
			self.piutang_bpkb_stnk = 0
			# frappe.msgprint(str(total_biaya_tanpa_dealer)+" total_biaya_tanpa_dealer")


	def missing_value(self):
		if self.piutang_motor <= 0:
			frappe.throw("Silahkan Cek apakaha Harga Motor sudah Ter set atau paid amount sudah terisi !!")

	def on_cancel(self):
		data = frappe.db.sql(""" SELECT name,docstatus from `tabJournal Entry` where penerimaan_dp = '{}' """.format(self.name),as_dict=1)
		for i in data:
			doc = frappe.get_doc('Journal Entry',i['name'])
			if doc.docstatus == 1:
				doc.cancel()
			else:
				doc.delete()

	def before_cancel(self):
		data = frappe.db.sql(""" SELECT name,docstatus from `tabJournal Entry` where penerimaan_dp = '{}' """.format(self.name),as_dict=1)
		for i in data:
			if i.docstatus == 1:
				cek_sipm = frappe.db.sql(""" SELECT sipm.name from `tabSales Invoice Penjualan Motor` sipm 
					join `tabSales Invoice Advance` a on a.parent = sipm.name where a.reference_name = '{}' and sipm.docstatus = 1 """.format(i['name']),as_dict=1)
				if cek_sipm:
					frappe.throw("Masih di pakai di sipm "+ cek_sipm[0]['name']+" !")
		# frappe.throw("wkwkwk")

	def on_trash(self):
		data = frappe.db.sql(""" SELECT name,docstatus from `tabJournal Entry` where penerimaan_dp = '{}' """.format(self.name),as_dict=1)
		for i in data:
			doc = frappe.get_doc('Journal Entry',i['name'])
			if doc.docstatus == 1:
				doc.cancel()
				doc.delete()
			else:
				doc.delete()

	def make_je(self):
		doc = frappe.new_doc("Journal Entry")
		doc.posting_date = self.tanggal
		doc.penerimaan_dp = self.name
		row_pm = doc.append('accounts', {})

		if self.cara_bayar == 'Cash':	
			row_pm.account = self.debit_to
			row_pm.credit_in_account_currency = self.piutang_motor
			row_pm.is_advance = 'Yes'
			row_pm.party_type = "Customer"
			row_pm.party = self.customer

			if self.piutang_bpkb_stnk > 0:
				row_pb = doc.append('accounts', {})
				row_pb.account = self.coa_bpkb_stnk
				row_pb.credit_in_account_currency = self.piutang_bpkb_stnk
				row_pb.is_advance = 'Yes'
				row_pb.party_type = "Customer"
				row_pb.party = self.customer

			row = doc.append('accounts', {})
			row.account = self.paid_to
			row.debit_in_account_currency = self.piutang_motor + self.piutang_bpkb_stnk
		else:
			row_pm.account = self.debit_to
			row_pm.credit_in_account_currency = self.piutang_motor
			row_pm.is_advance = 'Yes'
			row_pm.party_type = "Customer"
			row_pm.party = self.customer

			row = doc.append('accounts', {})
			row.account = self.paid_to
			row.debit_in_account_currency = self.piutang_motor + self.piutang_bpkb_stnk


		doc.flags.ignore_permission = True
		doc.save() 
		doc.submit()


@frappe.whitelist()
def make_sipm(name_dp):
	name_je = frappe.get_doc('Journal Entry',{'penerimaan_dp':name_dp,"docstatus":1}).name
	cek = frappe.get_value("Sales Invoice Advance",{"reference_name": name_je,"docstatus": ["!=",2]}, "parent")
	# pemilik = frappe.get_doc("Penerimaan DP",name_dp).pemilik
	# customer = frappe.get_doc("Penerimaan DP",name_dp).customer
	# debit_to = frappe.get_doc("Penerimaan DP",name_dp).debit_to
	# cara_bayar = frappe.get_doc("Penerimaan DP",name_dp).cara_bayar
	# item_code = frappe.get_doc("Penerimaan DP",name_dp).item_code
	# price_list = frappe.get_doc("Penerimaan DP",name_dp).price_list
	# item_group = frappe.get_doc("Penerimaan DP",name_dp).item_group
	# territory = frappe.get_doc("Penerimaan DP",name_dp).territory
	data = frappe.db.sql(""" SELECT * from `tabPenerimaan DP` where name = '{}' """.format(name_dp),as_dict=1)
	# frappe.throw(data[0].customer)


	if data[0].cara_bayar == "Cash":
		pemilik = data[0].pemilik
		customer = data[0].customer
	else:
		pemilik = data[0].pemilik
		customer = data[0].customer
	# territory = frappe.get_doc("Customer",pemilik).territory

	if not cek:
		target_doc = frappe.new_doc("Sales Invoice Penjualan Motor")
		target_doc.pemilik = pemilik
		target_doc.customer = customer
		target_doc.off_the_road = data[0].off_the_road
		target_doc.cara_bayar = data[0].cara_bayar
		target_doc.territory_real = frappe.get_doc("Customer",pemilik).territory
		target_doc.territory_biaya = data[0].territory
		target_doc.debit_to = data[0].debit_to
		target_doc.item_code = data[0].item_code
		target_doc.item_group = data[0].item_group
		target_doc.selling_price_list = data[0].price_list
		target_doc.nominal_diskon = data[0].nominal_diskon
		target_doc.debit_to = data[0].debit_to
		target_doc.coa_bpkb_stnk = data[0].coa_bpkb_stnk
		target_doc.set_posting_time = 1
		target_doc.posting_date = data[0].tanggal
		target_doc.nama_promo = data[0].nama_promo

		from wongkar_selling.wongkar_selling.get_invoice import get_item_price, get_leasing, get_biaya,get_rule
		total_discount_leasing = 0

		list_table_discount_leasing = get_leasing(target_doc.item_code,target_doc.nama_promo,target_doc.territory_real,target_doc.posting_date,target_doc.from_group)
		# get_leasing(self.item_code,self.nama_promo,self.territory_real,self.posting_date)
		frappe.msgprint(str(list_table_discount_leasing)+ ' list_table_discount_leasing')
		nominal_diskon = 0
		if list_table_discount_leasing:
			for row in list_table_discount_leasing:
				target_doc.append("table_discount_leasing",{
						"rule":row.name,
						"coa":row.coa,
						"coa_lawan":row.coa_lawan,
						"nominal":row.amount,
						"nama_leasing":row.leasing
					})
				total_discount_leasing += row.amount
                
        
		target_doc.total_discoun_leasing = total_discount_leasing

		# target_doc.set_advances()
		return target_doc.as_dict()
	else:
		frappe.throw((' Sudah ada di {0} !').format(frappe.utils.get_link_to_form('Sales Invoice Penjualan Motor', cek)))

