import frappe
from erpnext.accounts.doctype.gl_entry.gl_entry import GLEntry,validate_balance_type,validate_frozen_account
from frappe.utils import flt, fmt_money

class custom_advance(GLEntry):
	def on_update(self):
		adv_adj = self.flags.adv_adj
		if not self.flags.from_repost and self.voucher_type != "Period Closing Voucher":
			self.validate_account_details(adv_adj)
			self.validate_dimensions_for_pl_and_bs()
			self.validate_allowed_dimensions()
			validate_balance_type(self.account, adv_adj)
			validate_frozen_account(self.account, adv_adj)

			# Update outstanding amt on against voucher menambahkan voucher untuk sipm
			if (
				self.against_voucher_type in ["Journal Entry", "Sales Invoice", "Purchase Invoice", "Fees","Sales Invoice Penjualan Motor","Sales Invoice Sparepart Garansi"]
				and self.against_voucher
				and self.flags.update_outstanding == "Yes"
				and not frappe.flags.is_reverse_depr_entry
			):
				# frappe.throw("masuk sini")
				update_outstanding_amt_custom(
					self.account, self.party_type, self.party, self.against_voucher_type, self.against_voucher
				)

def update_outstanding_amt_custom(
	account, party_type, party, against_voucher_type, against_voucher, on_cancel=False
):
	# frappe.throw("masuk sinin vvv")
	if party_type and party:
		party_condition = " and party_type={0} and party={1}".format(
			frappe.db.escape(party_type), frappe.db.escape(party)
		)
	else:
		party_condition = ""

	# menambahkan voucher untuk sipm
	if against_voucher_type in ["Sales Invoice","Sales Invoice Penjualan Motor","Sales Invoice Sparepart Garansi"]:
		# frappe.msgprint("aaaaa")
		party_account = frappe.db.get_value(against_voucher_type, against_voucher, "debit_to")
		if against_voucher_type == "Sales Invoice Penjualan Motor":
			account_bpkb_stnk = frappe.db.get_value(against_voucher_type, against_voucher, "coa_bpkb_stnk")
			
			account_condition = "and account in ({0}, {1},{2})".format(
				frappe.db.escape(account), frappe.db.escape(party_account), frappe.db.escape(account_bpkb_stnk)
			)
		else:
			account_condition = "and account in ({0}, {1})".format(
				frappe.db.escape(account), frappe.db.escape(party_account)
			)
	else:
		account_condition = " and account = {0}".format(frappe.db.escape(account))

	# get final outstanding amt
	bal = flt(
		frappe.db.sql(
			"""
		select sum(debit_in_account_currency) - sum(credit_in_account_currency)
		from `tabGL Entry`
		where against_voucher_type=%s and against_voucher=%s
		and voucher_type != 'Invoice Discounting'
		{0} {1}""".format(
				party_condition, account_condition
			),
			(against_voucher_type, against_voucher),
		)[0][0]
		or 0.0
	)

	if against_voucher_type == "Purchase Invoice":
		bal = -bal
	elif against_voucher_type == "Journal Entry":
		against_voucher_amount = flt(
			frappe.db.sql(
				"""
			select sum(debit_in_account_currency) - sum(credit_in_account_currency)
			from `tabGL Entry` where voucher_type = 'Journal Entry' and voucher_no = %s
			and account = %s and (against_voucher is null or against_voucher='') {0}""".format(
					party_condition
				),
				(against_voucher, account),
			)[0][0]
		)

		if not against_voucher_amount:
			frappe.throw(
				_("Against Journal Entry {0} is already adjusted against some other voucher").format(
					against_voucher
				)
			)

		bal = against_voucher_amount + bal
		if against_voucher_amount < 0:
			bal = -bal

		# Validation : Outstanding can not be negative for JV
		if bal < 0 and not on_cancel:
			frappe.throw(
				_("Outstanding for {0} cannot be less than zero ({1})").format(against_voucher, fmt_money(bal))
			)

	if against_voucher_type in ["Sales Invoice", "Purchase Invoice", "Fees","Sales Invoice Penjualan Motor","Sales Invoice Sparepart Garansi"]:
		# frappe.msgprint("bbbb")
		ref_doc = frappe.get_doc(against_voucher_type, against_voucher)

		# Didn't use db_set for optimization purpose
		ref_doc.outstanding_amount = bal
		# frappe.msgprint(str(bal)+against_voucher_type+against_voucher)
		frappe.db.set_value(against_voucher_type, against_voucher, "outstanding_amount", bal)
		if against_voucher_type != "Sales Invoice Sparepart Garansi":
			ref_doc.set_status(update=True)