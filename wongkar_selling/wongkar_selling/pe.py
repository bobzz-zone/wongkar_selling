from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
import frappe

# # 
# class CustomPaymentEntry(PaymentEntry):
# 	def validate(self):
#         self.my_custom_code()
#         super(PaymentEntry, self).validate()

#     def my_custom_code(self):
# 		frappe.msgprint("Wahyu Lutfi")

@frappe.whitelist()
def get_reference_details_custom2(reference_doctype, reference_name, party_account_currency):
    frappe.msgprint("coba-coba")
    total_amount = outstanding_amount = exchange_rate = bill_no = None
    ref_doc = frappe.get_doc(reference_doctype, reference_name)
    company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)

    if reference_doctype == "Fees":
        total_amount = ref_doc.get("grand_total")
        exchange_rate = 1
        outstanding_amount = ref_doc.get("outstanding_amount")
    elif reference_doctype == "Donation":
        total_amount = ref_doc.get("amount")
        exchange_rate = 1
    elif reference_doctype == "Dunning":
        total_amount = ref_doc.get("dunning_amount")
        exchange_rate = 1
        outstanding_amount = ref_doc.get("dunning_amount")
    elif reference_doctype == "Journal Entry" and ref_doc.docstatus == 1:
        total_amount = ref_doc.get("total_amount")
        if ref_doc.multi_currency:
            exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
        else:
            exchange_rate = 1
            outstanding_amount = get_outstanding_on_journal_entry(reference_name)
    elif reference_doctype != "Journal Entry":
        if ref_doc.doctype == "Expense Claim":
                total_amount = flt(ref_doc.total_sanctioned_amount) + flt(ref_doc.total_taxes_and_charges)
        elif ref_doc.doctype == "Employee Advance":
            total_amount = ref_doc.advance_amount
            exchange_rate = ref_doc.get("exchange_rate")
            if party_account_currency != ref_doc.currency:
                total_amount = flt(total_amount) * flt(exchange_rate)
        elif ref_doc.doctype == "Gratuity":
                total_amount = ref_doc.amount
        if not total_amount:
            if party_account_currency == company_currency:
                total_amount = ref_doc.base_grand_total
                exchange_rate = 1
            else:
                total_amount = ref_doc.grand_total
        if not exchange_rate:
            # Get the exchange rate from the original ref doc
            # or get it based on the posting date of the ref doc.
            exchange_rate = ref_doc.get("conversion_rate") or \
                get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
        if reference_doctype in ("Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"):
            outstanding_amount = ref_doc.get("outstanding_amount")
            bill_no = ref_doc.get("bill_no")
        elif reference_doctype == "Expense Claim":
            outstanding_amount = flt(ref_doc.get("total_sanctioned_amount")) + flt(ref_doc.get("total_taxes_and_charges"))\
                - flt(ref_doc.get("total_amount_reimbursed")) - flt(ref_doc.get("total_advance_amount"))
        elif reference_doctype == "Employee Advance":
            outstanding_amount = (flt(ref_doc.advance_amount) - flt(ref_doc.paid_amount))
            if party_account_currency != ref_doc.currency:
                outstanding_amount = flt(outstanding_amount) * flt(exchange_rate)
                if party_account_currency == company_currency:
                    exchange_rate = 1
        elif reference_doctype == "Gratuity":
            outstanding_amount = ref_doc.amount - flt(ref_doc.paid_amount)
        else:
            outstanding_amount = flt(total_amount) - flt(ref_doc.advance_paid)
    else:
        # Get the exchange rate based on the posting date of the ref doc.
        exchange_rate = get_exchange_rate(party_account_currency,
            company_currency, ref_doc.posting_date)

    return frappe._dict({
        "due_date": ref_doc.get("due_date"),
        "total_amount": total_amount,
        "outstanding_amount": outstanding_amount,
        "exchange_rate": exchange_rate,
        "bill_no": bill_no
    })


@frappe.whitelist()
def overide_make_pe2(self,method):
    frappe.msgprint("overide_make_pe sini 22")
    # PaymentEntry.validate_reference_documents = validate_reference_documents_custom
    PaymentEntry.get_reference_details = get_reference_details_custom2