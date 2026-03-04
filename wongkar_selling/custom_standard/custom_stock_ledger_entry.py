import frappe

from frappe.query_builder.functions import CombineDatetime
from frappe.utils import get_link_to_form
from frappe import _, _dict, bold

def check_future_entries_exists(self,method):
    # wongkar_selling.custom_standard.custom_stock_ledger_entry.check_future_entries_exists
    # self = frappe.get_doc("Stock Ledger Entry",'MAT-SLE-2025-26756')
    if not frappe.flags.repair:
        if self.is_cancelled == 0:
            if self.serial_no:
                serial_no = self.serial_no.split('\n')
                for sn in serial_no:
                    if sn != '':
                        future_entries = frappe.db.sql(""" 
                                    SELECT 
                                        sle.posting_date,sle.posting_time,sle.serial_no,voucher_type,voucher_no FROM `tabStock Ledger Entry` sle
                                    WHERE serial_no LIKE '%{0}%' AND `is_cancelled`=0 
                                    AND TIMESTAMP(sle.`posting_date`,sle.`posting_time`) > TIMESTAMP('{1}','{2}')
                                    """.format(sn,self.posting_date,self.posting_time),as_dict=1)
                        if future_entries:
                            msg = """The serial nos has been used in the future
                                transactions so you need to cancel them first.
                                The list of serial nos and their respective
                                transactions are as below."""

                            msg += "<br><br><ul>"

                            for d in future_entries:
                                msg += f"<li>{d.serial_no} in {get_link_to_form(d.voucher_type, d.voucher_no)}</li>"
                            msg += "</li></ul>"

                            title = "Serial No Exists In Future Transaction(s)"

                            frappe.throw(_(msg), title=_(title),)
