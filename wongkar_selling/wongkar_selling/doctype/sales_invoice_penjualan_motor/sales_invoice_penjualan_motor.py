import frappe
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, get_link_to_form, nowdate
from six import iteritems

# from erpnext.controllers.account_controller import AccountsController
import erpnext
from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
    SalesInvoice, check_if_return_invoice_linked_with_payment_entry, unlink_inter_company_doc,validate_inter_company_party,
    validate_service_stop_date,update_linked_doc
)
from erpnext.setup.doctype.company.company import update_company_current_month_sales
from erpnext.healthcare.utils import manage_invoice_submit_cancel
# from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
#     get_party_tax_withholding_details,
# )
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from frappe.utils import cint, flt, round_based_on_smallest_currency_fraction
from erpnext.accounts.utils import get_account_currency
from erpnext.stock import get_warehouse_account_map
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries, process_gl_map
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.controllers.accounts_controller import get_advance_journal_entries,get_advance_journal_entries,get_advance_payment_entries
from erpnext.accounts.utils import check_if_advance_entry_modified,validate_allocated_amount,update_reference_in_journal_entry,update_reference_in_payment_entry
# from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
from erpnext.stock.doctype.serial_no.serial_no import (
    get_delivery_note_serial_no,
    get_serial_nos,
    update_serial_nos_after_submit,
)
from frappe import _, scrub, ValidationError

# from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from wongkar_selling.custom_standard.custom_taxes_and_total import calculate_taxes_and_totals_custom

class SalesInvoicePenjualanMotor(SalesInvoice):
    def get_advance_entries(self, include_unallocated=True):
        if self.doctype == "Sales Invoice Penjualan Motor":
            # frappe.msgprint("masuk Sales Invoice Penjualan Motor")
            # tambahan
            # name = self.name
            pemilik = self.pemilik
            party_account = self.debit_to
            party_bpkb_stnk = self.coa_bpkb_stnk
            party_type = "Customer"
            party = self.customer
            amount_field = "credit_in_account_currency"
            order_field = "sales_order"
            order_doctype = "Sales Order"
        else:
            party_account = self.credit_to
            party_type = "Supplier"
            party = self.supplier
            amount_field = "debit_in_account_currency"
            order_field = "purchase_order"
            order_doctype = "Purchase Order"

        order_list = list(set([d.get(order_field)
            for d in self.get("items") if d.get(order_field)]))

        # frappe.msgprint(str(order_list)+"order_list")
        journal_entries = get_advance_journal_entries_custom(party_type, party, party_account,party_bpkb_stnk,self.cara_bayar,self.pemilik,
            amount_field, order_doctype, order_list, include_unallocated)

        # payment_entries = get_advance_payment_entries(party_type, party, party_account,
        #   order_doctype, order_list, include_unallocated)

        #edit
        payment_entries = get_advance_payment_entries(pemilik,party_type, party, party_account,
            order_doctype, order_list, include_unallocated)

        res = journal_entries + payment_entries

        # frappe.msgprint(str(journal_entries)+"journal_entries")
        # frappe.msgprint(str(payment_entries)+"payment_entries")
        # frappe.msgprint(str(res)+"res2222")
        return res

    @frappe.whitelist()
    def set_advances(self):
        """Returns list of advances against Account, Party, Reference"""
        # frappe.msgprint("set_advances")
        res = self.get_advance_entries()
        # frappe.msgprint(str(res)+"res")
        self.set("advances", [])
        advance_allocated = 0
        for d in res:
            if d.against_order:
                allocated_amount = flt(d.amount)
            else:
                if self.get('party_account_currency') == self.company_currency:
                    amount = self.get('base_rounded_total') or self.base_grand_total
                else:
                    amount = self.get('rounded_total') or self.grand_total

                allocated_amount = min(amount - advance_allocated, d.amount)
            advance_allocated += flt(allocated_amount)

            self.append("advances", {
                #"doctype": self.doctype + " Advance",
                "doctype": "Sales Invoice" + " Advance",
                "reference_type": d.reference_type,
                "reference_name": d.reference_name,
                "reference_row": d.reference_row,
                "remarks": d.remarks,
                "advance_amount": flt(d.amount),
                "allocated_amount": allocated_amount
            })
        # self.reload()

    def onload(self):
        # frappe.msgprint("asas")
        # if len(self.items) > 0:
        #     self.calculate_totals()
        #     self.calculate_total_advance()
        self.set_status()

    def set_status(self, update=False, status=None, update_modified=True):
        # tambahan
        # frappe.msgprint("masuk sini status")
        if self.is_new():
            if self.get('amended_from'):
                self.status = 'Draft'
            return

        precision = self.precision("outstanding_amount")
        outstanding_amount = flt(self.outstanding_amount, precision)
        due_date = getdate(self.due_date)
        nowdate = getdate()

        discounting_status = None
        if self.is_discounted:
            discountng_status = get_discounting_status(self.name)

        if not status:
            if self.docstatus == 2:
                status = "Cancelled"
            elif self.docstatus == 1:
                # if self.is_internal_transfer():
                #   self.status = 'Internal Transfer'
                # frappe.msgprint("masuk sini status xxx")
                if outstanding_amount > 0 and due_date < nowdate and self.is_discounted and discountng_status=='Disbursed':
                    self.status = "Overdue and Discounted"
                if outstanding_amount > 0 and due_date < nowdate:
                    # frappe.msgprint("masuk sini status 444")
                    self.status = "Overdue"
                if outstanding_amount > 0 and due_date >= nowdate and self.is_discounted and discountng_status=='Disbursed':
                    self.status = "Unpaid and Discounted"
                if outstanding_amount > 0 and due_date >= nowdate and not self.tertagih:
                    # frappe.msgprint("masuk sini status 222")
                    self.status = "Unpaid"
                #Check if outstanding amount is 0 due to credit note issued against invoice
                if outstanding_amount <= 0 and self.is_return == 0 and frappe.db.get_value('Sales Invoice Penjualan Motor', {'is_return': 1, 'return_against': self.name, 'docstatus': 1}):
                    self.status = "Credit Note Issued"
                if self.is_return == 1:
                    self.status = "Return"
                if outstanding_amount<=0:
                    if self.customer_group=="Leasing":
                        update = True
                        # frappe.msgprint("masuk sini status 333")
                        self.status="Billed"
                    else:
                        self.status = "Paid"
                # else:
                #   self.status = "Submitted coba"
            elif self.docstatus == 0:
                self.status = "Draft"
        
        # frappe.msgprint(str(update_modified)+ "update_modified")
        if update:
            # frappe.msgprint("masuk update")
            # frappe.msgprint(self.status+ " self.status")
            self.db_set('status', self.status, update_modified = update_modified)
            # frappe.db.commit()

    def cek_rdl(self):
        # if len(self.items) > 1 or self.from_group:
        if self.nama_promo and self.cara_bayar=="Credit":
            if not self.table_discount_leasing or len(self.table_discount_leasing) == 0:
                frappe.throw("Table Discount Leasing harus ada isinya !")
            # if self.table_discount_leasing:
            #   if len(self.table_discount_leasing) == 0:
            #       frappe.throw("Table Discount Leasing harus ada isinya !")
    def cek_rule(self):
        # if len(self.items) > 1 or self.from_group:
        if self.nama_diskon:
            if not self.table_discount or len(self.table_discount) == 0:
                frappe.throw("Table Discount harus ada isinya !")
            # if self.table_discount:
            #   if len(self.table_discount) == 0:
            #       frappe.throw("Table Discount harus ada isinya !")

    def add_pemilik(self):
        try:
            frappe.db.sql(""" UPDATE `tabSerial No` set pemilik="{}",nama_pemilik="{}" where name="{}" """.format(self.pemilik,self.nama_pemilik,self.no_rangka))
            for i in self.tabel_biaya_motor:
                if i.type == "STNK":
                    frappe.db.sql(""" UPDATE `tabSerial No` set biaya_stnk='{}' where name = '{}' """.format(i.amount,self.no_rangka))
                elif i.type == "BPKB":
                    frappe.db.sql(""" UPDATE `tabSerial No` set biaya_bpkb='{}' where name = '{}' """.format(i.amount,self.no_rangka))
                else:
                    frappe.db.sql(""" UPDATE `tabSerial No` set biaya_dealer='{}' where name = '{}' """.format(i.amount,self.no_rangka))
        except Exception as e:
            frappe.throw(str(e))
        
        # doc = frappe.get_doc("Serial No",self.no_rangka)
        # doc.pemilik = self.pemilik
        # doc.nama_pemilik = self.nama_pemilik
        # doc.flags.ignore_permissions = True
        # doc.save()

    def remove_pemilik(self):
        frappe.db.sql(""" UPDATE `tabSerial No` set pemilik="",nama_pemilik="",biaya_stnk=0,biaya_bpkb=0,biaya_dealer=0  where name='{}' """.format(self.no_rangka))

    def cek_no_po_leasing(self):
        if self.no_po_leasing:
            cek = frappe.db.sql(""" SELECT name from `tabSales Invoice Penjualan Motor` where no_po_leasing = '{}' and docstatus != 2 """.format(self.no_po_leasing),as_dict=1)

            if cek:
                if len(cek) > 1:
                    frappe.throw("No Po sudah ada di "+str(cek))

    def dp_gross_h(self):
        rule = 0
        rdl = 0
        if self.table_discount:
            if len(self.table_discount) > 0:
                for r in self.table_discount:
                    rule = rule + r.nominal

        if self.table_discount_leasing:
            if len(self.table_discount_leasing) > 0:
                for rd in self.table_discount_leasing:
                    rdl = rdl + rd.nominal

        dp = self.total_advance + rule + rdl
        print(dp)
        self.dp_gross_hitung = dp

    def cek_off(self):
        if self.off_the_road:
            self.coa_bpkb_stnk = None
            self.tabel_biaya_motor = []
            self.total_biaya = 0
            if (self.adjustment_harga <= 0 or self.adjustment_harga == None) and self.territory_biaya == 'ZZZ_Kosongan' and 'Antar Entitas' in self.selling_price_list:
                frappe.throw("Masukkan Nilai adjusment otr tanpa biya bpkb dan stnk !!!")

    # @frappe.whitelist()
    def cek_advance(self):
        if self.antar_entitas == 1:
            pass
        elif self.advances:
            if len(self.advances) <= 0:
                frappe.throw("Advance Belum Ada !")
            else:
                if self.nama_promo:
                    for i in self.advances:
                        cek = frappe.get_doc("Journal Entry",i.reference_name).penerimaan_dp
                        cek_promo = frappe.get_doc("Penerimaan DP",cek)
                        if not cek_promo.dp_ke_2:
                            if self.nama_promo != cek_promo.nama_promo:
                                frappe.throw(_(' Nama Promo tidak sama di {0} !').format(frappe.utils.get_link_to_form('Penerimaan DP', cek_promo.name)))
        else:
            frappe.throw("Advance Belum Ada !")

    def validate(self):
        # frappe.msgprint('sads')
        self.cek_no_po_leasing()
        self.cek_rdl()
        self.cek_rule()
        self.cek_off()
        # self.cek_advance()

        if self.no_rangka != self.items[0].serial_no:
            frappe.throw("No rangka tidak sama dengan item !")
        #validate rule biaya harus ada 3
        if not self.bypass_biaya:
            if len(self.tabel_biaya_motor)<=1:
                frappe.throw("Error ada biaya yang belum di set")

        # super(SalesInvoice, self).validate()
        self.validate_auto_set_posting_time()
        # self.calculate_taxes_and_totals()
        if len(self.items) > 0:
            calculate_taxes_and_totals_custom(self)
            # self.calculate_totals()
            # self.calculate_total_advance()
        # doc = self.doc
        # calculate_taxes_and_totals.calculate_totals(self, doc)
        # if not self.is_pos:
        #     self.so_dn_required()

        self.set_tax_withholding()

        self.validate_proj_cust()
        self.validate_pos_return()
        self.validate_with_previous_doc()
        self.validate_uom_is_integer("stock_uom", "stock_qty")
        self.validate_uom_is_integer("uom", "qty")
        self.check_sales_order_on_hold_or_close("sales_order")
        self.validate_debit_to_acc()
        self.clear_unallocated_advances("Sales Invoice Advance", "advances")
        self.add_remarks()
        self.validate_write_off_account()
        self.validate_account_for_change_amount()
        self.validate_fixed_asset()
        self.set_income_account_for_fixed_assets()
        self.validate_item_cost_centers()
        self.validate_income_account()
        self.check_conversion_rate()

        validate_inter_company_party(
            self.doctype, self.customer, self.company, self.inter_company_invoice_reference
        )

        if cint(self.is_pos):
            self.validate_pos()

        if cint(self.update_stock):
            self.validate_dropship_item()
            self.validate_item_code()
            self.validate_warehouse()
            self.update_current_stock()
            self.validate_delivery_note()

        # validate service stop date to lie in between start and end date
        validate_service_stop_date(self)

        if not self.is_opening:
            self.is_opening = "No"

        if self._action != "submit" and self.update_stock and not self.is_return:
            set_batch_nos(self, "warehouse", True)

        if self.redeem_loyalty_points:
            lp = frappe.get_doc("Loyalty Program", self.loyalty_program)
            self.loyalty_redemption_account = (
                lp.expense_account if not self.loyalty_redemption_account else self.loyalty_redemption_account
            )
            self.loyalty_redemption_cost_center = (
                lp.cost_center
                if not self.loyalty_redemption_cost_center
                else self.loyalty_redemption_cost_center
            )

        self.set_against_income_account()
        self.validate_c_form()
        self.validate_time_sheets_are_submitted()
        self.validate_multiple_billing("Delivery Note", "dn_detail", "amount", "items")
        if not self.is_return:
            self.validate_serial_numbers()
        else:
            self.timesheets = []
        self.update_packing_list()
        self.set_billing_hours_and_amount()
        self.update_timesheet_billing_for_project()
        self.set_status()
        if self.is_pos and not self.is_return:
            self.verify_payment_amount_is_positive()

        # validate amount in mode of payments for returned invoices for pos must be negative
        if self.is_pos and self.is_return:
            self.verify_payment_amount_is_negative()

        if (
            self.redeem_loyalty_points
            and self.loyalty_program
            and self.loyalty_points
            and not self.is_consolidated
        ):
            validate_loyalty_points(self, self.loyalty_points)

        self.reset_default_field_value("set_warehouse", "items", "warehouse")

    def set_tax_withholding(self):
        tax_withholding_details = get_party_tax_withholding_details(self)

        if not tax_withholding_details:
            return

        accounts = []
        tax_withholding_account = tax_withholding_details.get("account_head")

        for d in self.taxes:
            if d.account_head == tax_withholding_account:
                d.update(tax_withholding_details)
            accounts.append(d.account_head)

        if not accounts or tax_withholding_account not in accounts:
            self.append("taxes", tax_withholding_details)

        to_remove = [
            d
            for d in self.taxes
            if not d.tax_amount and d.charge_type == "Actual" and d.account_head == tax_withholding_account
        ]

        for d in to_remove:
            self.remove(d)

        # calculate totals again after applying TDS
        self.calculate_taxes_and_totals()


    def on_cancel(self):
        super(SalesInvoicePenjualanMotor, self).on_cancel()
        from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries

        if self.doctype in ["Sales Invoice", "Sales Invoice Penjualan Motor","Purchase Invoice"]:
            if frappe.db.get_single_value("Accounts Settings", "unlink_payment_on_cancellation_of_invoice"):
                unlink_ref_doc_from_payment_entries(self)

        if not self.is_return:
            self.update_serial_no(in_cancel=True)

        self.remove_pemilik()
        self.add_dpp_sn()              

    def before_submit(self):
        self.dp_gross_h()

    def before_insert(self):
        # pass
        if len(self.items) == 0:
            # frappe.msgprint('tes')
            self.custom_missing_values()

    def custom_missing_values(self):
        # validasi field
        if not self.cara_bayar:
            frappe.throw("Silahkan mengisi Cara Bayar")
        
        if not self.item_code:
            frappe.throw("Silahkan mengisi Kode Item")

        if not self.item_group:
            frappe.throw("Silahkan mengisi item_group")

        if not self.nama_diskon:
            frappe.throw("Silahkan mengisi Nama Diskon")
        
        if self.cara_bayar == "Credit":
            if not self.nama_promo:
                frappe.throw("Silahkan mengisi Nama Promo")

        if not self.no_rangka:
            frappe.throw("Silahkan mengisi No Rangka")

        if not self.selling_price_list:
            frappe.throw("Silahkan mengisi Price List")
        
        if self.diskon == 1:
            if self.nominal_diskon == 0:
                pass
                # frappe.throw("Silahkan mengisi Nominal Diskon")
        else:
            self.nominal_diskon = 0

        if not self.territory_real:
            frappe.throw("Silahkan mengisi Territory Real")
        
        if not self.territory_biaya:
            frappe.throw("Silahkan mengisi Territory Biaya")

        today = frappe.utils.nowdate()

        if self.posting_date != today:
            self.set_posting_time = 1 

        # cari nilai
        from wongkar_selling.wongkar_selling.get_invoice import get_item_price, get_leasing, get_biaya,get_rule
        if not self.harga:
            self.harga = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"]
            self.otr = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"]
        else:
            self.harga = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"]
            self.otr = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"]

        # reset semua table
        self.tabel_biaya_motor = []
        self.table_discount_leasing= []
        self.table_discount = []

        # generate tabel biaya
        list_tabel_biaya = get_biaya(self.item_code,self.territory_biaya,self.posting_date,self.from_group)
        
        total_biaya = 0
        total_discount = 0
        total_discount_leasing = 0
        total_biaya_tanpa_dealer = 0
        # generate tabel biaya
        # frappe.msgprint(str(self.posting_date.date()))
        print(self.posting_date)
        if list_tabel_biaya:
            for row in list_tabel_biaya:
                if row.valid_from <= self.posting_date.date() and row.valid_to >= self.posting_date.date():
                # if row.valid_from <= self.posting_date and row.valid_to >= self.posting_date:
                    self.append("tabel_biaya_motor",{
                            "rule":row.name,
                            "vendor":row.vendor,
                            "type": row.type,
                            "amount" : row.amount,
                            "coa" : row.coa
                        })
                    total_biaya += row.amount
                    if row.type in ['STNK','BPKB']:
                        total_biaya_tanpa_dealer += row.amount

        # generate tabel discount
        # list_table_discount = frappe.db.get_list('Rule',filters={ 'item_code': self.item_code, 'territory' : self.territory_real, 'category_discount': self.nama_diskon , 'disable': 0 }, fields=['*'])
        list_table_discount = get_rule(self.item_code,self.territory_real,self.posting_date,self.nama_diskon,self.from_group)
        if list_table_discount:
            for row in list_table_discount:
                if row.valid_from <= self.posting_date.date() and row.valid_to >= self.posting_date.date():
                # if row.valid_from <= self.posting_date and row.valid_to >= self.posting_date:
                    if row.discount == "Percent":
                        row.amount = row.percent * self.harga / 100

                    self.append("table_discount",{
                        "rule": row.name,
                        "customer":row.customer,
                        "category_discount": row.category_discount,
                        "coa_receivable": row.coa_receivable,
                        "coa_lawan": row.coa_lawan,
                        "nominal": row.amount
                        })

                    total_discount += row.amount

        # generate table discount leasing
        list_table_discount_leasing = get_leasing(self.item_code,self.nama_promo,self.territory_real,self.posting_date,self.from_group)
        # get_leasing(self.item_code,self.nama_promo,self.territory_real,self.posting_date)
        nominal_diskon = 0
        if list_table_discount_leasing:
            for row in list_table_discount_leasing:
                self.append("table_discount_leasing",{
                        "rule":row.name,
                        "coa":row.coa,
                        "coa_lawan":row.coa_lawan,
                        "nominal":row.amount,
                        "nama_leasing":row.leasing
                    })
                total_discount_leasing += row.amount
                
                self.nominal_diskon = row.beban_dealer

        self.total_biaya = total_biaya

        self.total_discoun_leasing = total_discount_leasing

        # if self.taxes_and_charges:
        #   data_tax = frappe.db.sql(""" SELECT * from `tabSales Taxes and Charges` where parent='{}' """.format(self.taxes_and_charges),as_dict=1)

        # if data_tax:
        #   for i in data_tax:

        tax_template = frappe.db.get_list("Sales Taxes and Charges Template",{"is_default":1},"name")[0]
        tax = frappe.get_doc("Sales Taxes and Charges Template",tax_template)


        ppn_rate = tax.taxes[0].rate
        # self.taxes[0].rate
        ppn_div = (100+ppn_rate)/100
        print(ppn_div)
        # cara mencari grand total
        
        # total2 = ( self.harga - self.total_biaya ) / ppn_div
        total2 = ( self.harga - total_biaya_tanpa_dealer ) / ppn_div
        
        print(total2)
        hasil2 = self.harga - total2
        akhir2 = self.harga - hasil2

        income_account = frappe.db.get_list("Item Default",filters={"parent":self.item_code},fields=["income_account"])[0]["income_account"]
        expense_account = frappe.db.get_list("Item Default",filters={"parent":self.item_code},fields=["expense_account"])[0]["expense_account"]

        company = frappe.db.get_single_value("Global Defaults","default_company")
        if not income_account:
            income_account = frappe.db.get_value("Company",company,"default_income_account")
            
        if not expense_account:
            expense_account = frappe.db.get_value("Company",company,"default_expense_account")

        from erpnext.stock.get_item_details import get_item_details
        
        # frappe.msgprint(str(args)+ ' args')
        tax = frappe.get_doc("Sales Taxes and Charges Template",self.taxes_and_charges)
        doc = self
        total_biaya_tanpa_dealer = 0
        if self.tabel_biaya_motor:
            if len(self.tabel_biaya_motor) > 0:
                for i in self.tabel_biaya_motor:
                    if i.type in ['STNK','BPKB']:
                        total_biaya_tanpa_dealer += i.amount

        ppn_rate = tax.taxes[0].rate
        ppn_div = (100+ppn_rate)/100
       
        total_diskon_setelah_pajak = 0
        if self.table_discount:
            if len(self.table_discount):
                for i in self.table_discount:
                    # diskon_setelah_pajak = flt(i.nominal / ppn_div,0)
                    diskon_setelah_pajak = i.nominal / ppn_div
                    total_diskon_setelah_pajak += diskon_setelah_pajak
                    print(diskon_setelah_pajak)
        
        total_diskon_leasing_setelah_pajak = 0
        if self.table_discount_leasing:
            if len(self.table_discount_leasing):
                for i in self.table_discount_leasing:
                    # diskon_leasing_setelah_pajak = flt(i.nominal / ppn_div,0)
                    diskon_leasing_setelah_pajak = i.nominal / ppn_div
                    total_diskon_leasing_setelah_pajak += diskon_leasing_setelah_pajak

        
        # nominal_diskon_sp = flt(self.nominal_diskon / ppn_div,0)
        nominal_diskon_sp = self.nominal_diskon / ppn_div
        pajak_diskon_sp = self.nominal_diskon - nominal_diskon_sp
        args = {
            "item_code": self.item_code,
            "company": self.company,
            "doctype": self.doctype,
            "currency": self.currency,
            "conversion_rate": self.conversion_rate,
            "warehouse": self.set_warehouse,
            "price_list": self.selling_price_list
        }
        out = get_item_details(args,self,overwrite_warehouse=False)
        # frappe.msgprint(str(out)+ ' out')
        # harga_asli = self.harga - total_biaya_tanpa_dealer - total_diskon_setelah_pajak - total_diskon_leasing_setelah_pajak - nominal_diskon_sp
        harga_asli = self.harga - total_biaya_tanpa_dealer
        
        # menambah tabel item

        out.update({
                'serial_no':self.no_rangka,
                'cost_center': self.cost_center,
                # 'price_list_rate':harga_asli,
                'rate':harga_asli,
                'stock_uom_rate':harga_asli,
                'amount': harga_asli
            })

        self.append("items",out)
        
        self.adj_discount = 0 if not self.adj_discount else self.adj_discount

        tax_template = frappe.db.get_list("Sales Taxes and Charges Template",{"is_default":1},"name")[0]
        # frappe.throw(str(tax_template))
        

        if not self.taxes:
            # frappe.throw('asdsad')
            self.taxes = []
            self.taxes_and_charges = tax_template["name"]

            tax = frappe.get_doc("Sales Taxes and Charges Template",self.taxes_and_charges)
            # self.grand_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.rounded_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount

            self.grand_total = (self.harga) - self.nominal_diskon
            # self.rounded_total = (self.harga) + self.adj_discount

            # for row in tax.taxes:
            #   self.append("taxes",{
            #           "charge_type":row.charge_type,
            #           "account_head": row.account_head,
            #           "description": row.description,
            #           "currency": row.currency,
            #           "included_in_print_rate": row.included_in_print_rate,
            #           "rate":row.rate,
            #           "tax_amount": (self.grand_total - total_biaya) / ((100+row.rate)/100),
            #           "base_tax_amount": (self.grand_total - total_biaya) / ((100+row.rate)/100),
            #           "total": (self.grand_total - total_biaya),
            #           "tax_amount_after_discount_amount": (self.grand_total - total_biaya),
            #           "base_tax_amount_after_discount_amount": (self.grand_total - total_biaya)
            #       })

            for row in tax.taxes:
                self.append("taxes",{
                        "charge_type":row.charge_type,
                        "account_head": row.account_head,
                        "description": row.description,
                        "currency": row.currency,
                        "included_in_print_rate": row.included_in_print_rate,
                        "rate":row.rate,
                        # "tax_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100,
                        # "base_tax_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100,
                        # # "tax_amount": (self.harga - total_biaya) * ((row.rate)/100),
                        # # "base_tax_amount": (self.harga - total_biaya) * ((row.rate)/100),
                        
                        # "total": (self.harga - total_biaya),
                        # "tax_amount_after_discount_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100,
                        # "base_tax_amount_after_discount_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100
                    })

            

            # frappe.msgprint(str(total_discount)+" total_discount")
            # frappe.msgprint(str(total_discount)+" total_discount_leasing")
            # frappe.msgprint(str(self.outstanding_amount)+" outstanding_amount")
            # frappe.msgprint(str(self.harga)+" harga")
            # frappe.msgprint(str(self.adj_discount)+" adj_discount")
            # frappe.msgprint(str(self.total_advance)+" total_advance")
            
            if self.total_advance:
                tot_adv = self.total_advance
            else:
                tot_adv = 0

            # self.net_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.base_net_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.base_grand_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.outstanding_amount = (self.harga - total_discount - total_discount_leasing) + self.adj_discount - tot_adv


            # self.net_total = flt(self.get("taxes")[-1].total) - flt(self.get("taxes")[-1].total)
            # self.base_net_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.base_grand_total = (self.harga) + self.adj_discount
            # self.outstanding_amount = (self.harga) + self.adj_discount - tot_adv

        calculate_taxes_and_totals_custom(self)

    def add_dpp_sn(self):
        if self.taxes and len(self.taxes) > 0:
            # dpp = self.taxes[0].total 
            dpp = self.net_total
            ppn = self.taxes[0].tax_amount
            if self.docstatus == 1:
                frappe.db.sql(""" UPDATE `tabSerial No` set dpp = {},ppn = {},harga_jual = {} where name = "{}" """.format(dpp,ppn,self.grand_total,self.no_rangka),debug=1)
            elif self.docstatus == 2:
                frappe.db.sql(""" UPDATE `tabSerial No` set dpp = {},ppn = {},harga_jual = {} where name = "{}" """.format(0,0,0,self.no_rangka),debug=1)
            print("sukses")

    def on_submit(self):
        self.add_pemilik()
        self.cek_advance()
        self.validate_pos_paid_amount()
        self.add_dpp_sn()

        if not self.auto_repeat:
            frappe.get_doc("Authorization Control").validate_approving_authority(
                self.doctype, self.company, self.base_grand_total, self
            )

        self.check_prev_docstatus()

        if self.is_return and not self.update_billed_amount_in_sales_order:
            # NOTE status updating bypassed for is_return
            self.status_updater = []

        self.update_status_updater_args()
        self.update_prevdoc_status()
        self.update_billing_status_in_dn()
        self.clear_unallocated_mode_of_payments()

        # Updating stock ledger should always be called after updating prevdoc status,
        # because updating reserved qty in bin depends upon updated delivered qty in SO
        if self.update_stock == 1:
            self.update_stock_ledger()
        if self.is_return and self.update_stock:
            update_serial_nos_after_submit(self, "items")

        # this sequence because outstanding may get -ve
        self.make_gl_entries()

        if self.update_stock == 1:
            self.repost_future_sle_and_gle()

        if not self.is_return:
            self.update_billing_status_for_zero_amount_refdoc("Delivery Note")
            self.update_billing_status_for_zero_amount_refdoc("Sales Order")
            self.check_credit_limit()

        self.update_serial_no()

        if not cint(self.is_pos) == 1 and not self.is_return:
            self.update_against_document_in_jv_custom()

        self.update_time_sheet(self.name)

        if (
            frappe.db.get_single_value("Selling Settings", "sales_update_frequency") == "Each Transaction"
        ):
            update_company_current_month_sales(self.company)
            self.update_project()
        update_linked_doc(self.doctype, self.name, self.inter_company_invoice_reference)

        # create the loyalty point ledger entry if the customer is enrolled in any loyalty program
        if not self.is_return and not self.is_consolidated and self.loyalty_program:
            self.make_loyalty_point_entry()
        elif (
            self.is_return and self.return_against and not self.is_consolidated and self.loyalty_program
        ):
            against_si_doc = frappe.get_doc("Sales Invoice Penjualan Motor", self.return_against)
            against_si_doc.delete_loyalty_point_entry()
            against_si_doc.make_loyalty_point_entry()
        if self.redeem_loyalty_points and not self.is_consolidated and self.loyalty_points:
            self.apply_loyalty_points()

        # Healthcare Service Invoice.
        domain_settings = frappe.get_doc("Domain Settings")
        active_domains = [d.domain for d in domain_settings.active_domains]

        if "Healthcare" in active_domains:
            manage_invoice_submit_cancel(self, "on_submit")

        self.process_common_party_accounting()

    def update_serial_no(self, in_cancel=False):
        """update Sales Invoice refrence in Serial No"""
        invoice = None if (in_cancel or self.is_return) else self.name
        if in_cancel and self.is_return:
            invoice = self.return_against

        for item in self.items:
            if not item.serial_no:
                continue

            for serial_no in get_serial_nos(item.serial_no):
                if serial_no and frappe.db.get_value("Serial No", serial_no, "item_code") == item.item_code:
                    frappe.db.set_value("Serial No", serial_no, "sales_invoice", None)
                    frappe.db.set_value("Serial No", serial_no, "sales_invoice_penjualan_motor", invoice)

    def update_against_document_in_jv_custom(self):
        """
        Links invoice and advance voucher:
                1. cancel advance voucher
                2. split into multiple rows if partially adjusted, assign against voucher
                3. submit advance voucher
        """
        print("kkkkkkhhhhjjjj")
        if self.doctype in ["Sales Invoice", "Sales Invoice Penjualan Motor"]:
            party_type = "Customer"
            party = self.customer
            party_account = self.debit_to
            party_bpkb_stnk = self.coa_bpkb_stnk
            dr_or_cr = "credit_in_account_currency"
        else:
            party_type = "Supplier"
            party = self.supplier
            party_account = self.credit_to
            dr_or_cr = "debit_in_account_currency"

        lst = []
        for d in self.get("advances"):
            if flt(d.allocated_amount) > 0:
                if d.reference_type == 'Journal Entry':
                    cek_akun = frappe.get_doc('Journal Entry Account',d.reference_row).account
                    cek_name = frappe.get_doc('Journal Entry Account',d.reference_row).name
                    print(cek_akun, ' cek_akun')
                    if cek_akun == party_account:
                        print("masuk mo")
                        reference_row = cek_name
                        party_account_tmp = cek_akun
                    if cek_akun == party_bpkb_stnk:
                        print("masuk bs")
                        reference_row = cek_name
                        party_account_tmp = cek_akun
                else:
                    reference_row = d.reference_row
                    party_account_tmp = party_account
                args = frappe._dict(
                    {
                        "voucher_type": d.reference_type,
                        "voucher_no": d.reference_name,
                        "voucher_detail_no": reference_row,
                        "against_voucher_type": self.doctype,
                        "against_voucher": self.name,
                        "account": party_account_tmp,
                        "party_type": party_type,
                        "party": party,
                        "is_advance": "Yes",
                        "dr_or_cr": dr_or_cr,
                        "unadjusted_amount": flt(d.advance_amount),
                        "allocated_amount": flt(d.allocated_amount),
                        "precision": d.precision("advance_amount"),
                        "exchange_rate": (
                            self.conversion_rate if self.party_account_currency != self.company_currency else 1
                        ),
                        "grand_total": (
                            self.base_grand_total
                            if self.party_account_currency == self.company_currency
                            else self.grand_total
                        ),
                        "outstanding_amount": self.outstanding_amount,
                        "difference_account": frappe.db.get_value(
                            "Company", self.company, "exchange_gain_loss_account"
                        ),
                        "exchange_gain_loss": flt(d.get("exchange_gain_loss")),
                    }
                )
                lst.append(args)

        if lst:
            from erpnext.accounts.utils import reconcile_against_document
            print(lst, ' lst')
            reconcile_against_document_custom(lst)

    def make_gl_entries(self, gl_entries=None, from_repost=False):
        from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

        auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)
        if not gl_entries:
            gl_entries = self.get_gl_entries()

        if gl_entries:
            # if POS and amount is written off, updating outstanding amt after posting all gl entries
            update_outstanding = (
                "No"
                if (cint(self.is_pos) or self.write_off_account or cint(self.redeem_loyalty_points))
                else "Yes"
            )

            if self.docstatus == 1:
                make_gl_entries(
                    gl_entries,
                    update_outstanding=update_outstanding,
                    merge_entries=False,
                    from_repost=from_repost,
                )
            elif self.docstatus == 2:
                make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

            if update_outstanding == "No":
                print("lkdlaksdlaskdlmaskdnsadjk")
                from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt

                update_outstanding_amt(
                    self.debit_to,
                    "Customer",
                    self.customer,
                    self.doctype,
                    self.return_against if cint(self.is_return) and self.return_against else self.name,
                )

        elif self.docstatus == 2 and cint(self.update_stock) and cint(auto_accounting_for_stock):
            make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

    def get_gl_entries(self, warehouse_account=None):
        from erpnext.accounts.general_ledger import merge_similar_entries

        gl_entries = []

        self.make_customer_gl_entry(gl_entries)
        # tambahan
        self.make_disc_gl_entry_custom(gl_entries)
        self.make_disc_gl_entry_custom_leasing(gl_entries)
        
        self.make_biaya_gl_entry_custom(gl_entries)
        self.make_adj_disc_gl_entry(gl_entries)
        self.make_disc_gl_entry(gl_entries)
        # self.make_cogs_entry_credit(gl_entries)
        # self.make_disc_gl_entry_lawan_custom(gl_entries)

        self.make_tax_gl_entries(gl_entries)
        # self.make_internal_transfer_gl_entries(gl_entries)

        self.make_item_gl_entries(gl_entries)

        # merge gl entries before adding pos entries
        gl_entries = merge_similar_entries(gl_entries)

        self.make_loyalty_point_redemption_gle(gl_entries)
        self.make_pos_gl_entries(gl_entries)
        self.make_gle_for_change_amount(gl_entries)

        self.make_write_off_gl_entry(gl_entries)
        self.make_gle_for_rounding_adjustment(gl_entries)
        print(gl_entries , " gl_entries")
        return gl_entries

    def make_pos_gl_entries(self, gl_entries):
        if cint(self.is_pos):
            for payment_mode in self.payments:
                if payment_mode.amount:
                    # POS, make payment entries
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": self.debit_to,
                            "party_type": "Customer",
                            "party": self.customer,
                            "against": payment_mode.account,
                            "credit": payment_mode.base_amount,
                            "credit_in_account_currency": payment_mode.base_amount \
                                if self.party_account_currency==self.company_currency \
                                else payment_mode.amount,
                            "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                            "against_voucher_type": self.doctype,
                            "cost_center": self.cost_center
                        }, self.party_account_currency, item=self)
                    )

                    payment_mode_account_currency = get_account_currency(payment_mode.account)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": payment_mode.account,
                            "against": self.customer,
                            "debit": payment_mode.base_amount,
                            "debit_in_account_currency": payment_mode.base_amount \
                                if payment_mode_account_currency==self.company_currency \
                                else payment_mode.amount,
                            "cost_center": self.cost_center
                        }, payment_mode_account_currency, item=self)
                    )

    def make_gle_for_change_amount(self, gl_entries):
        if cint(self.is_pos) and self.change_amount:
            if self.account_for_change_amount:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.debit_to,
                        "party_type": "Customer",
                        "party": self.customer,
                        "against": self.account_for_change_amount,
                        "debit": flt(self.base_change_amount),
                        "debit_in_account_currency": flt(self.base_change_amount) \
                            if self.party_account_currency==self.company_currency else flt(self.change_amount),
                        "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                        "against_voucher_type": self.doctype,
                        "cost_center": self.cost_center,
                        "project": self.project
                    }, self.party_account_currency, item=self)
                )

                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.account_for_change_amount,
                        "against": self.customer,
                        "credit": self.base_change_amount,
                        "cost_center": self.cost_center
                    }, item=self)
                )
            else:
                frappe.throw(_("Select change amount account"), title="Mandatory Field")

    def make_write_off_gl_entry(self, gl_entries):
        # write off entries, applicable if only pos
        if self.write_off_account and flt(self.write_off_amount, self.precision("write_off_amount")):
            write_off_account_currency = get_account_currency(self.write_off_account)
            default_cost_center = frappe.get_cached_value('Company',  self.company,  'cost_center')

            gl_entries.append(
                self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": self.write_off_account,
                    "credit": flt(self.base_write_off_amount, self.precision("base_write_off_amount")),
                    "credit_in_account_currency": (flt(self.base_write_off_amount,
                        self.precision("base_write_off_amount")) if self.party_account_currency==self.company_currency
                        else flt(self.write_off_amount, self.precision("write_off_amount"))),
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project
                }, self.party_account_currency, item=self)
            )
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.write_off_account,
                    "against": self.customer,
                    "debit": flt(self.base_write_off_amount, self.precision("base_write_off_amount")),
                    "debit_in_account_currency": (flt(self.base_write_off_amount,
                        self.precision("base_write_off_amount")) if write_off_account_currency==self.company_currency
                        else flt(self.write_off_amount, self.precision("write_off_amount"))),
                    "cost_center": self.cost_center or self.write_off_cost_center or default_cost_center
                }, write_off_account_currency, item=self)
            )

    def make_gle_for_rounding_adjustment(self, gl_entries):
        if flt(self.rounding_adjustment, self.precision("rounding_adjustment")) and self.base_rounding_adjustment \
            and not self.is_internal_transfer():
            round_off_account, round_off_cost_center = \
                get_round_off_account_and_cost_center(self.company)

            gl_entries.append(
                self.get_gl_dict({
                    "account": round_off_account,
                    "against": self.customer,
                    "credit_in_account_currency": flt(self.rounding_adjustment,
                        self.precision("rounding_adjustment")),
                    "credit": flt(self.base_rounding_adjustment,
                        self.precision("base_rounding_adjustment")),
                    "cost_center": self.cost_center or round_off_cost_center,
                }, item=self))

    def make_loyalty_point_redemption_gle(self, gl_entries):
        if cint(self.redeem_loyalty_points):
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": "Expense account - " + cstr(self.loyalty_redemption_account) + " for the Loyalty Program",
                    "credit": self.loyalty_amount,
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center
                }, item=self)
            )
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.loyalty_redemption_account,
                    "cost_center": self.cost_center or self.loyalty_redemption_cost_center,
                    "against": self.customer,
                    "debit": self.loyalty_amount,
                    "remark": "Loyalty Points redeemed by the customer"
                }, item=self)
            )

    def make_item_gl_entries(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        nominal_diskon = 0
        nominal_diskon_leasing = 0
        total_net_d = 0
        total_net_dl = 0
        for d in self.table_discount:
            # hitung_tax_d = flt((d.nominal) / tax,0)
            hitung_tax_d = flt((d.nominal) / tax)
            net_d = (d.nominal) - hitung_tax_d
            total_net_d = total_net_d + net_d

        for dl in self.table_discount_leasing:
            # hitung_tax_dl = flt((dl.nominal) / tax,0)
            hitung_tax_dl = flt((dl.nominal) / tax)
            net_dl = (dl.nominal) - hitung_tax_dl
            total_net_dl = total_net_dl + net_dl

        # nd = flt(self.nominal_diskon / tax,0)
        nd = flt(self.nominal_diskon / tax)
        net_nd = self.nominal_diskon - nd
        net_total = total_net_d + total_net_dl + net_nd
        # net_total = total_net_d

        
        # income account gl entries
        for item in self.get("items"):
            if flt(item.base_net_amount, item.precision("base_net_amount")):
                if item.is_fixed_asset:
                    asset = frappe.get_doc("Asset", item.asset)

                    if (len(asset.finance_books) > 1 and not item.finance_book
                        and asset.finance_books[0].finance_book):
                        frappe.throw(_("Select finance book for the item {0} at row {1}")
                            .format(item.item_code, item.idx))

                    fixed_asset_gl_entries = get_gl_entries_on_asset_disposal(asset,
                        item.base_net_amount, item.finance_book)

                    for gle in fixed_asset_gl_entries:
                        gle["against"] = self.customer
                        gl_entries.append(self.get_gl_dict(gle, item=item))

                    asset.db_set("disposal_date", self.posting_date)
                    asset.set_status("Sold" if self.docstatus==1 else None)
                else:
                    # Do not book income for transfer within same company
                    # if not self.is_internal_transfer():
                    income_account = (item.income_account
                        if (not item.enable_deferred_revenue or self.is_return) else item.deferred_revenue_account)
                    # frappe.throw("masuk SIni")
                    account_currency = get_account_currency(income_account)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": income_account,
                            "against": self.customer,
                            "credit": flt(item.base_net_amount, item.precision("base_net_amount"))-flt(self.adj_discount),
                            "credit_in_account_currency": (flt(item.base_net_amount, item.precision("base_net_amount")-flt(self.adj_discount))
                                if account_currency==self.company_currency
                                else flt(item.net_amount, item.precision("net_amount"))-flt(self.adj_discount)),
                            "cost_center": item.cost_center,
                            "project": item.project or self.project,
                            # "remarks": "wahyu xxxx"
                        }, account_currency, item=item)
                    )

        # expense account gl entries
        if cint(self.update_stock) and \
            erpnext.is_perpetual_inventory_enabled(self.company):
            # gl_entries += super(SalesInvoice, self).get_gl_entries()
            gl_entries += self.get_gl_entries_stock()

    # jurnal stock
    def get_gl_entries_stock(self, warehouse_account=None, default_expense_account=None,
            default_cost_center=None):

        if not warehouse_account:
            warehouse_account = get_warehouse_account_map(self.company)
            # frappe.throw(str(warehouse_account))

        sle_map = self.get_stock_ledger_details()
        voucher_details = self.get_voucher_details(default_expense_account, default_cost_center, sle_map)

        gl_list = []
        warehouse_with_no_account = []
        precision = self.get_debit_field_precision()
        for item_row in voucher_details:

            sle_list = sle_map.get(item_row.name)
            if sle_list:
                # frappe.throw(str(sle_list))
                for sle in sle_list:
                    if warehouse_account.get(sle.warehouse):
                        # from warehouse account

                        self.check_expense_account(item_row)

                        # If the item does not have the allow zero valuation rate flag set
                        # and ( valuation rate not mentioned in an incoming entry
                        # or incoming entry not found while delivering the item),
                        # try to pick valuation rate from previous sle or Item master and update in SLE
                        # Otherwise, throw an exception

                        if not sle.stock_value_difference and self.doctype != "Stock Reconciliation" \
                            and not item_row.get("allow_zero_valuation_rate"):

                            sle = self.update_stock_ledger_entries(sle)
                            # frappe.throw(str(sle))
                        # expense account/ target_warehouse / source_warehouse
                        if item_row.get('target_warehouse'):
                            warehouse = item_row.get('target_warehouse')
                            expense_account = warehouse_account[warehouse]["account"]
                        else:
                            expense_account = item_row.expense_account

                        gl_list.append(self.get_gl_dict({
                            "account": warehouse_account[sle.warehouse]["account"],
                            "against": expense_account,
                            "cost_center": item_row.cost_center,
                            "project": item_row.project or self.get('project'),
                            "remarks": self.get("remarks") or "Accounting Entry for Stock",
                            "debit": flt(sle.stock_value_difference, precision),
                            "is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
                        }, warehouse_account[sle.warehouse]["account_currency"], item=item_row))

                        gl_list.append(self.get_gl_dict({
                            "account": expense_account,
                            "against": warehouse_account[sle.warehouse]["account"],
                            "cost_center": item_row.cost_center,
                            "project": item_row.project or self.get('project'),
                            "remarks": self.get("remarks") or "Accounting Entry for Stock",
                            "credit": flt(sle.stock_value_difference, precision),
                            "project": item_row.get("project") or self.get("project"),
                            "is_opening": item_row.get("is_opening") or self.get("is_opening") or "No"
                        }, item=item_row))
                        # frappe.msgprint(str(gl_list))
                    elif sle.warehouse not in warehouse_with_no_account:
                        warehouse_with_no_account.append(sle.warehouse)

        if warehouse_with_no_account:
            for wh in warehouse_with_no_account:
                if frappe.db.get_value("Warehouse", wh, "company"):
                    frappe.throw(_("Warehouse {0} is not linked to any account, please mention the account in the warehouse record or set default inventory account in company {1}.").format(wh, self.company))

        return process_gl_map(gl_list, precision=precision)

    def update_stock_ledger_entries(self, sle):
        sle.valuation_rate = get_valuation_rate(sle.item_code, sle.warehouse,
        self.doctype, self.name, currency=self.company_currency, company=self.company)

        sle.stock_value = flt(sle.qty_after_transaction) * flt(sle.valuation_rate)
        sle.stock_value_difference = flt(sle.actual_qty) * flt(sle.valuation_rate)

        if sle.name:
            frappe.db.sql("""
            update
            `tabStock Ledger Entry`
            set
            stock_value = %(stock_value)s,
            valuation_rate = %(valuation_rate)s,
            stock_value_difference = %(stock_value_difference)s
            where
            name = %(name)s""", (sle))

        return sle

    
    
    def make_tax_gl_entries(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        nominal_diskon = 0
        nominal_diskon_leasing = 0
        total_net_d = 0
        total_net_dl = 0
        for d in self.table_discount:
            # hitung_tax_d = flt((d.nominal) / tax,0)
            hitung_tax_d = flt((d.nominal) / tax)
            net_d = (d.nominal) - hitung_tax_d
            total_net_d = total_net_d + net_d

        for dl in self.table_discount_leasing:
            # hitung_tax_dl = flt((dl.nominal) / tax,0)
            hitung_tax_dl = flt((dl.nominal) / tax)
            net_dl = (dl.nominal) - hitung_tax_dl
            total_net_dl = total_net_dl + net_dl

        # nd = flt(self.nominal_diskon / tax,0)
        nd = flt(self.nominal_diskon / tax)
        net_nd = self.nominal_diskon - nd
        print(total_net_d, " total_net_d")
        print(total_net_dl, " total_net_dl")  
        print(net_nd, " net_nd")
        net_total = total_net_d + total_net_dl + net_nd
        # net_total = total_net_d

        print(net_total, " net_total")

        # untuk pajak lebih dari 1 baris
        for tax in self.get("taxes"):
            if flt(tax.base_tax_amount_after_discount_amount):
                account_currency = get_account_currency(tax.account_head)
                if tax.idx == 1:
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": tax.account_head,
                            "against": self.customer,
                            "credit": (flt(tax.base_tax_amount_after_discount_amount-net_nd,
                                tax.precision("tax_amount_after_discount_amount"))),
                            "credit_in_account_currency": ((flt(tax.base_tax_amount_after_discount_amount-net_nd,
                                tax.precision("base_tax_amount_after_discount_amount")))  if account_currency==self.company_currency else
                                (flt(tax.tax_amount_after_discount_amount-net_nd, tax.precision("tax_amount_after_discount_amount")))),
                            "cost_center": tax.cost_center,
                            # "remarks": "coba Lutfi pajak!"
                        }, account_currency, item=tax)
                    )
                else:
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": tax.account_head,
                            "against": self.customer,
                            "credit": (flt(tax.base_tax_amount_after_discount_amount,
                                tax.precision("tax_amount_after_discount_amount"))),
                            "credit_in_account_currency": ((flt(tax.base_tax_amount_after_discount_amount,
                                tax.precision("base_tax_amount_after_discount_amount")))  if account_currency==self.company_currency else
                                (flt(tax.tax_amount_after_discount_amount-net_nd, tax.precision("tax_amount_after_discount_amount")))),
                            "cost_center": tax.cost_center,
                            # "remarks": "coba Lutfi pajak!"
                        }, account_currency, item=tax)
                    )

                # gl_entries.append(
                #   self.get_gl_dict({
                #       "account": tax.account_head,
                #       "against": self.customer,
                #       "debit": net_total,
                #       "debit_in_account_currency": net_total,
                #       "cost_center": tax.cost_center,
                #       # "remarks": "coba Lutfi pajak!"
                #   }, account_currency, item=tax)
                # )

    # adj disc
    def make_adj_disc_gl_entry(self, gl_entries):
        if self.account_adj_discount:
            test = str(self.adj_discount)
            if '-' in test:
                gl_entries.append(
                self.get_gl_dict({
                    "account": self.account_adj_discount,
                    "party_type": "Customer",
                    "party": self.nama_leasing,
                    "due_date": self.due_date,
                    "against": self.against_income_account,
                    "debit": abs(self.adj_discount),
                    "debit_in_account_currency": abs(self.adj_discount),
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi ffff!"
                }, self.party_account_currency, item=self)
            )
            else:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.account_adj_discount,
                        "party_type": "Customer",
                        "party": self.nama_leasing,
                        "due_date": self.due_date,
                        "against": self.against_income_account,
                        "credit": abs(self.adj_discount),
                        "credit_in_account_currency": abs(self.adj_discount),
                        "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                        "against_voucher_type": self.doctype,
                        "cost_center": self.cost_center,
                        "project": self.project,
                        # "remarks": "coba Lutfi ffff!"
                    }, self.party_account_currency, item=self)
                )

     # disc gl
    def make_disc_gl_entry(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        if self.coa_diskon:
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.coa_diskon,
                    # "party_type": "Customer",
                    # "party": self.nama_leasing,
                    # "due_date": self.due_date,
                    "against": self.against_income_account,
                    # "debit": abs(flt(self.nominal_diskon/tax,0)),
                    # "debit_in_account_currency": abs(flt(self.nominal_diskon/tax,0)),
                    "debit": abs(flt(self.nominal_diskon/tax)),
                    "debit_in_account_currency": abs(flt(self.nominal_diskon/tax)),
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi ffff!"
                }, self.party_account_currency, item=self)
            )
            

    # table biaya
    def make_biaya_gl_entry_custom(self, gl_entries):
        for d in self.get('tabel_biaya_motor'):
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa,
                    # "party_type": "Supplier",
                    # "party": d.vendor,
                    "due_date": self.due_date,
                    "against": self.coa_bpkb_stnk,
                    "credit": d.amount ,
                    "credit_in_account_currency": d.amount,
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi cccccc!"
                }, self.party_account_currency, item=self)
            )

    # diskon leasing
    def make_disc_gl_entry_custom_leasing(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        tax_account = self.taxes[0].account_head
        # pendapatan = frappe.get_doc("Company",self.company).pendapatan_lain_leasing
        for d in self.get('table_discount_leasing'):
            hitung_tax = (d.nominal) / tax
            net_dl = (d.nominal) - hitung_tax
            pendapatan = frappe.get_doc("Rule Discount Leasing",d.rule).coa_lawan
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa,
                    # "due_date": self.due_date,
                    "party_type": "Customer",
                    "party": d.nama_leasing,
                    "against": d.coa_lawan,
                    "debit": d.nominal,
                    "debit_in_account_currency": d.nominal,
                    "against_voucher": self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    # "project": self.project,
                    # "remarks": "coba Lutfi yyyyy!"
                }, self.party_account_currency, item=self.table_discount_leasing)
            )
            
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa_lawan,
                    # "due_date": self.due_date,
                    "against": d.coa,
                    "credit": d.nominal,
                    "credit_in_account_currency": d.nominal,
                    # "against_voucher": self.name,
                    # "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    # "project": self.project,
                    # "remarks": "coba Lutfi yyyyy!"
                }, self.party_account_currency, item=self.table_discount_leasing)
            )

        # for d in self.get('table_discount_leasing'):
        #     hitung_tax_c = (d.nominal) / tax
        #     gl_entries.append(
        #         self.get_gl_dict({
        #             "account": d.coa_lawan,
        #             # "party_type": "Customer",
        #             # "party": d.nama_leasing,
        #             "due_date": self.due_date,
        #             # "against": self.against_income_account,
        #             "against": d.coa,
        #             "credit": hitung_tax_c,
        #             "credit_in_account_currency": hitung_tax_c,
        #             "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
        #             "against_voucher_type": self.doctype,
        #             "cost_center": self.cost_center,
        #             "project": self.project,
        #             # "remarks": "coba Lutfi zzzzz!"
        #         }, self.party_account_currency, item=self)
        #     )

    # diskon biasa
    def make_disc_gl_entry_custom(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        tax_account = self.taxes[0].account_head
        total_net_d = 0
        for d in self.get('table_discount'):
            if frappe.db.exists("Rule",d.rule):
                beban = frappe.get_doc("Rule",d.rule).coa_lawan
            else:
                beban = d.coa_lawan
            hitung_tax = flt((d.nominal) / tax,0)
            net_d = (d.nominal) - hitung_tax
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa_receivable,
                    # "due_date": self.due_date,
                    "party_type": "Customer",
                    "party": d.customer,
                    "against": d.coa_lawan,
                    "debit": d.nominal,
                    "debit_in_account_currency": d.nominal,
                    "against_voucher": self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    # "project": self.project,
                    # "remarks": "coba Lutfi yyyyy!"
                }, self.party_account_currency, item=self.table_discount)
            )
            
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa_lawan,
                    # "due_date": self.due_date,
                    "against": d.coa_receivable,
                    "credit": d.nominal,
                    "credit_in_account_currency": d.nominal,
                    # "against_voucher": self.name,
                    # "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    # "project": self.project,
                    # "remarks": "coba Lutfi yyyyy!"
                }, self.party_account_currency, item=self.table_discount)
            )

    def make_customer_gl_entry(self, gl_entries):
        # # Checked both rounding_adjustment and rounded_total
        # # because rounded_total had value even before introcution of posting GLE based on rounded total
        # grand_total = self.rounded_total if (self.rounding_adjustment and self.rounded_total) else self.grand_total
        # # if grand_total and not self.is_internal_transfer():
        # if grand_total:
        #   # Didnot use base_grand_total to book rounding loss gle
        #   grand_total_in_company_currency = flt(grand_total * self.conversion_rate,
        #       self.precision("grand_total"))

        tax = (100+ self.taxes[0].rate) / 100
        tax_account = self.taxes[0].account_head

        tot_disc = 0
        for d in self.get('table_discount'):
            tot_disc = tot_disc + d.nominal

        tot_discl = 0
        for l in self.get('table_discount_leasing'):
            tot_discl = tot_discl + l.nominal

        tmp_akun=[]
        tot_biaya = 0
        for b in self.get('tabel_biaya_motor'):
            if b.type in ['BPKB','STNK']:
                tmp_akun.append(b.coa)
                tot_biaya = tot_biaya + b.amount

        total_diskon_setelah_pajak = 0
        if self.table_discount:
            if len(self.table_discount):
                for i in self.table_discount:
                    diskon_setelah_pajak = flt(i.nominal / tax)
                    total_diskon_setelah_pajak += diskon_setelah_pajak
                    print(diskon_setelah_pajak)
        print(total_diskon_setelah_pajak, ' total_diskon_setelah_pajak')

        total_diskon_leasing_setelah_pajak = 0
        if self.table_discount_leasing:
            if len(self.table_discount_leasing):
                for i in self.table_discount_leasing:
                    diskon_leasing_setelah_pajak = flt(i.nominal / tax)
                    total_diskon_leasing_setelah_pajak += diskon_leasing_setelah_pajak

        print(total_diskon_leasing_setelah_pajak, ' total_diskon_leasing_setelah_pajak')

        nominal_diskon_sp = flt(self.nominal_diskon / tax)
        print(nominal_diskon_sp, ' nominal_diskon_sp')

        # gl_entries.append(
        #   self.get_gl_dict({
        #       "account": self.debit_to,
        #       "party_type": "Customer",
        #       "party": self.customer,
        #       "due_date": self.due_date,
        #       "against": self.against_income_account,
        #       "debit": grand_total_in_company_currency,
        #       "debit_in_account_currency": grand_total_in_company_currency \
        #           if self.party_account_currency==self.company_currency else grand_total,
        #       "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
        #       "against_voucher_type": self.doctype,
        #       "cost_center": self.cost_center,
        #       "project": self.project,
        #       "remarks": "coba Lutfi xxxxx!"
        #   }, self.party_account_currency, item=self)
        # )

        # lebih dari 1 baris
        total_pajak = self.base_rounded_total - (((self.harga + self.adj_discount) - tot_biaya - self.nominal_diskon)+tot_biaya)
        # print(((self.harga + self.adj_discount) - tot_biaya - self.nominal_diskon)+tot_biaya," piutang_motor")
        print(total_pajak, ' total_pajak')

        gl_entries.append(
            self.get_gl_dict({
                "account": self.debit_to,
                "party_type": "Customer",
                "party": self.customer,
                "due_date": self.due_date,
                "against": self.against_income_account,
                # "debit": ((self.grand_total + tot_biaya) - tot_disc - tot_discl) + self.adj_discount,
                # "debit_in_account_currency": ((self.grand_total + tot_biaya) - tot_disc - tot_discl) + self.adj_discount,
                # "debit": (self.harga - tot_disc - tot_discl) + self.adj_discount,
                # "debit_in_account_currency": (self.harga - tot_disc - tot_discl) + self.adj_discount,
                # "debit": (self.harga + self.adj_discount) - tot_biaya - total_diskon_setelah_pajak - total_diskon_leasing_setelah_pajak - nominal_diskon_sp,
                # "debit_in_account_currency": (self.harga + self.adj_discount) - tot_biaya - total_diskon_setelah_pajak - total_diskon_leasing_setelah_pajak - nominal_diskon_sp,
                "debit": ((self.harga + self.adj_discount) - tot_biaya - self.nominal_diskon)+total_pajak,
                "debit_in_account_currency": ((self.harga + self.adj_discount) - tot_biaya - self.nominal_diskon)+total_pajak,
                
                "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                "against_voucher_type": self.doctype,
                "cost_center": self.cost_center,
                "project": self.project,
                # "remarks": "coba Lutfi xxxxx!"
            }, self.party_account_currency, item=self)
        )

        # piutang bpkb sntk
        if self.tabel_biaya_motor:
            if len(self.tabel_biaya_motor) > 0:
                bpkb_stnk = tot_biaya / tax
                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.coa_bpkb_stnk,
                        "party_type": "Customer",
                        "party": self.customer,
                        "due_date": self.due_date,
                        "against": tmp_akun[0]+', '+tmp_akun[1] if len(tmp_akun)>0 else tmp_akun[0],
                        # "debit": ((self.grand_total + tot_biaya) - tot_disc - tot_discl) + self.adj_discount,
                        # "debit_in_account_currency": ((self.grand_total + tot_biaya) - tot_disc - tot_discl) + self.adj_discount,
                        # "debit": (self.harga - tot_disc - tot_discl) + self.adj_discount,
                        # "debit_in_account_currency": (self.harga - tot_disc - tot_discl) + self.adj_discount,
                        "debit": tot_biaya,
                        "debit_in_account_currency": tot_biaya,
                        "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                        "against_voucher_type": self.doctype,
                        "cost_center": self.cost_center,
                        "project": self.project,
                        # "remarks": "coba Lutfi xxxxx!"
                    }, self.party_account_currency, item=self)
                )


    # def calculate(self):
    #     if not len(self.get("items")):
    #         return

    #     self.discount_amount_applied = False
    #     self._calculate()

    #     if self.meta.get_field("discount_amount"):
    #         self.set_discount_amount()
    #         self.apply_discount_amount()

    #     # Update grand total as per cash and non trade discount
    #     if self.apply_discount_on == "Grand Total" and self.get("is_cash_or_non_trade_discount"):
    #         self.grand_total -= self.discount_amount
    #         self.base_grand_total -= self.base_discount_amount
    #         self.set_rounded_total()

    #     self.calculate_shipping_charges()

    #     if self.doctype in ["Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"]:
    #         self.calculate_total_advance()

    #     if self.meta.get_field("other_charges_calculation"):
    #         self.set_item_wise_tax_breakup()

    # def _calculate(self):
    #     self.validate_conversion_rate()
    #     self.calculate_item_values()
    #     self.validate_item_tax_template()
    #     self.initialize_taxes()
    #     self.determine_exclusive_rate()
    #     self.calculate_net_total()
    #     self.calculate_taxes()
    #     self.manipulate_grand_total_for_inclusive_tax()
    #     self.calculate_totals()
    #     self._cleanup()
    #     self.calculate_total_net_weight()

    # def validate_conversion_rate(self):
    #     # validate conversion rate
    #     company_currency = erpnext.get_company_currency(self.company)
    #     if not self.currency or self.currency == company_currency:
    #         self.currency = company_currency
    #         self.conversion_rate = 1.0
    #     else:
    #         validate_conversion_rate(
    #             self.currency,
    #             self.conversion_rate,
    #             self.meta.get_label("conversion_rate"),
    #             self.company,
    #         )

    #     self.conversion_rate = flt(self.conversion_rate)

    def calculate_total_advance(self):
        if self.docstatus < 2:
            total_allocated_amount = sum(
                flt(adv.allocated_amount, adv.precision("allocated_amount"))
                for adv in self.get("advances")
            )

            self.total_advance = flt(total_allocated_amount, self.precision("total_advance"))

            grand_total = self.rounded_total or self.grand_total

            if self.party_account_currency == self.currency:
                invoice_total = flt(
                    grand_total - flt(self.write_off_amount), self.precision("grand_total")
                )
            else:
                base_write_off_amount = flt(
                    flt(self.write_off_amount) * self.conversion_rate,
                    self.precision("base_write_off_amount"),
                )
                invoice_total = (
                    flt(grand_total * self.conversion_rate, self.precision("grand_total"))
                    - base_write_off_amount
                )

            if invoice_total > 0 and self.total_advance > invoice_total:
                frappe.throw(
                    _("Advance amount cannot be greater than {0} {1}").format(
                        self.party_account_currency, invoice_total
                    )
                )

            if self.docstatus == 0:
                if self.get("write_off_outstanding_amount_automatically"):
                    self.write_off_amount = 0

                self.calculate_outstanding_amount()
                # self.calculate_write_off_amount()

            # custom lutfi
            self.calculate_outstanding_amount()

    def calculate_outstanding_amount(self):
        # NOTE:
        # write_off_amount is only for POS Invoice
        # total_advance is only for non POS Invoice
        if self.doctype in ["Sales Invoice", "Sales Invoice Penjualan Motor"] :
        # if self.doctype == "Sales Invoice" :
            self.calculate_paid_amount()

        if (
            self.is_return
            and self.return_against
            and not self.get("is_pos")
            or self.is_internal_invoice()
        ):
            return

        self.round_floats_in(self, ["grand_total", "total_advance", "write_off_amount"])
        _set_in_company_currency(self,self, ["write_off_amount"])

        if self.doctype in ["Sales Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"]:
            grand_total = self.rounded_total or self.grand_total
            base_grand_total = self.base_rounded_total or self.base_grand_total

            if self.party_account_currency == self.currency:
                total_amount_to_pay = flt(
                    grand_total - self.total_advance - flt(self.write_off_amount),
                    self.precision("grand_total"),
                )
            else:
                total_amount_to_pay = flt(
                    flt(base_grand_total, self.precision("base_grand_total"))
                    - self.total_advance
                    - flt(self.base_write_off_amount),
                    self.precision("base_grand_total"),
                )

            self.round_floats_in(self, ["paid_amount"])
            change_amount = 0

            if self.doctype in ["Sales Invoice", "Sales Invoice Penjualan Motor"] and not self.get("is_return"):
                self.calculate_change_amount()
                change_amount = (
                    self.change_amount
                    if self.party_account_currency == self.currency
                    else self.base_change_amount
                )

            paid_amount = (
                self.paid_amount
                if self.party_account_currency == self.currency
                else self.base_paid_amount
            )

            self.outstanding_amount = flt(
                total_amount_to_pay - flt(paid_amount) + flt(change_amount),
                self.precision("outstanding_amount"),
            )

            if (
                self.doctype in ["Sales Invoice", "Sales Invoice Penjualan Motor"]
                and self.get("is_pos")
                and self.get("pos_profile")
                and self.get("is_consolidated")
            ):
                write_off_limit = flt(
                    frappe.db.get_value("POS Profile", self.pos_profile, "write_off_limit")
                )
                if write_off_limit and abs(self.outstanding_amount) <= write_off_limit:
                    self.write_off_outstanding_amount_automatically = 1

            if (
                self.doctype in ["Sales Invoice", "Sales Invoice Penjualan Motor"]
                and self.get("is_pos")
                and self.get("is_return")
                and not self.get("is_consolidated")
            ):
                self.set_total_amount_to_default_mop(total_amount_to_pay)
                self.calculate_paid_amount()

    def is_internal_invoice(self):
        """
        Checks if its an internal transfer invoice
        and decides if to calculate any out standing amount or not
        """

        if self.doctype in ("Sales Invoice", "Purchase Invoice") and self.is_internal_transfer():
            return True

        return False

    def calculate_change_amount(self):
        self.change_amount = 0.0
        self.base_change_amount = 0.0
        grand_total = self.rounded_total or self.grand_total
        base_grand_total = self.base_rounded_total or self.base_grand_total

        if (
            self.doctype == "Sales Invoice"
            and self.paid_amount > grand_total
            and not self.is_return
            and any(d.type == "Cash" for d in self.payments)
        ):

            self.change_amount = flt(
                self.paid_amount - grand_total, self.precision("change_amount")
            )

            self.base_change_amount = flt(
                self.base_paid_amount - base_grand_total, self.precision("base_change_amount")
            )

    def calculate_item(self):
        ppn_rate = self.taxes[0].rate
        print(ppn_rate, ' ppn_rate')
        ppn_div = (100+ppn_rate)/100
        total_biaya_tanpa_dealer = 0 
        
        if self.tabel_biaya_motor:
            if len(self.tabel_biaya_motor) > 0:
                for i in self.tabel_biaya_motor:
                    if i.type in ('STNK','BPKB'):
                        total_biaya_tanpa_dealer += i.amount

        self.total_biaya = total_biaya_tanpa_dealer
        
        print(total_biaya_tanpa_dealer, ' total_biaya_tanpa_dealer')
        total_diskon_setelah_pajak = 0
        if self.table_discount:
            if len(self.table_discount):
                for i in self.table_discount:
                    diskon_setelah_pajak = flt(i.nominal / ppn_div,0)
                    total_diskon_setelah_pajak += diskon_setelah_pajak
                    print(diskon_setelah_pajak)
        print(total_diskon_setelah_pajak, ' total_diskon_setelah_pajak')
        nominal_diskon_sp = flt(self.nominal_diskon / ppn_div,0)
        print(nominal_diskon_sp, ' nominal_diskon_sp')
        harga_asli = self.harga - total_biaya_tanpa_dealer - diskon_setelah_pajak - nominal_diskon_sp
        print(harga_asli, ' harga_asli')
        
        self.items[0].price_list_rate = harga_asli
        self.items[0].rate = harga_asli
        self.items[0].serial_no = self.no_rangka
        

        tdl = 0
        if self.table_discount_leasing:
            if len(self.table_discount_leasing) > 0:
                for i in self.table_discount_leasing:
                    tdl += nominal

        self.total_discoun_leasing = tdl
        
        if self.cek_adjustment_harga:
            if self.adjustment_harga <=0:
                frappe.throw("Adjustment Harga Harus lebih besar dari 0 !")


    def calculate_totals(self):
        doc = self
        print (doc, 'docccc')
        total_biaya_tanpa_dealer = 0
        if self.tabel_biaya_motor:
            if len(self.tabel_biaya_motor) > 0:
                for i in self.tabel_biaya_motor:
                    if i.type in ['STNK','BPKB']:
                        total_biaya_tanpa_dealer += i.amount

        ppn_rate = self.taxes[0].rate
        print(ppn_rate, ' ppn_rate')
        ppn_div = (100+ppn_rate)/100
       
        total_diskon_setelah_pajak = 0
        if self.table_discount:
            if len(self.table_discount):
                for i in self.table_discount:
                    # diskon_setelah_pajak = flt(i.nominal / ppn_div,0)
                    diskon_setelah_pajak = i.nominal / ppn_div
                    total_diskon_setelah_pajak += diskon_setelah_pajak
                    print(diskon_setelah_pajak)
        print(total_diskon_setelah_pajak, ' total_diskon_setelah_pajak')

        total_diskon_leasing_setelah_pajak = 0
        if self.table_discount_leasing:
            if len(self.table_discount_leasing):
                for i in self.table_discount_leasing:
                    # diskon_leasing_setelah_pajak = flt(i.nominal / ppn_div,0)
                    diskon_leasing_setelah_pajak = i.nominal / ppn_div
                    total_diskon_leasing_setelah_pajak += diskon_leasing_setelah_pajak

        print(total_diskon_leasing_setelah_pajak, ' total_diskon_leasing_setelah_pajak')

        # nominal_diskon_sp = flt(self.nominal_diskon / ppn_div,0)
        nominal_diskon_sp = self.nominal_diskon / ppn_div
        print(nominal_diskon_sp, ' nominal_diskon_sp')
        pajak_diskon_sp = self.nominal_diskon - nominal_diskon_sp
        print(pajak_diskon_sp, " pajak_diskon_sp")
       
        if self.get("taxes"):
            print(self.rounding_adjustment, ' self.rounding_adjustment')
            self.grand_total = flt(self.get("taxes")[-1].total)+total_biaya_tanpa_dealer+total_diskon_setelah_pajak+total_diskon_leasing_setelah_pajak-pajak_diskon_sp+ flt(self.rounding_adjustment)
            # self.grand_total = round(self.grand_total,-1)
        else:
            self.grand_total = flt(self.net_total)

        if self.get("taxes"):
            # frappe.msgprint(str(self.grand_total)+" frappe.msgprint")
            # frappe.msgprint(str(self.net_total)+ ' frappe.msgprint2')
            # frappe.msgprint(str(self.rounding_adjustment)+ ' frappe.msgprint3')
            self.total_taxes_and_charges = flt(
                self.grand_total - self.net_total - flt(self.rounding_adjustment),
                self.precision("total_taxes_and_charges"),
            )
        else:
            self.total_taxes_and_charges = 0.0

        _set_in_company_currency(self, doc,["total_taxes_and_charges", "rounding_adjustment"])

        if self.doctype in [
            "Quotation",
            "Sales Order",
            "Delivery Note",
            "Sales Invoice",
            "POS Invoice",
            "Sales Invoice Penjualan Motor"
        ]:
            self.base_grand_total = (
                flt(self.grand_total * self.conversion_rate, self.precision("base_grand_total"))
                if self.total_taxes_and_charges
                else self.base_net_total
            )
        else:
            self.taxes_and_charges_added = self.taxes_and_charges_deducted = 0.0
            for tax in self.get("taxes"):
                if tax.category in ["Valuation and Total", "Total"]:
                    if tax.add_deduct_tax == "Add":
                        self.taxes_and_charges_added += flt(tax.tax_amount_after_discount_amount)
                    else:
                        self.taxes_and_charges_deducted += flt(tax.tax_amount_after_discount_amount)

            self.round_floats_in(self, ["taxes_and_charges_added", "taxes_and_charges_deducted"])

            self.base_grand_total = (
                flt(self.grand_total * self.conversion_rate)
                if (self.taxes_and_charges_added or self.taxes_and_charges_deducted)
                else self.base_net_total
            )

            self._set_in_company_currency(
                self, doc, ["taxes_and_charges_added", "taxes_and_charges_deducted"]
            )

        self.round_floats_in(self, ["grand_total", "base_grand_total"])

        set_rounded_total(self)

def set_rounded_total(self):
    doc = self
    if self.get("is_consolidated") and self.get("rounding_adjustment"):
        return

    if self.meta.get_field("rounded_total"):
        if self.is_rounded_total_disabled():
            self.rounded_total = self.base_rounded_total = 0
            return

        self.rounded_total = round_based_on_smallest_currency_fraction(
            self.grand_total, self.currency, self.precision("rounded_total")
        )

        # if print_in_rate is set, we would have already calculated rounding adjustment
        self.rounding_adjustment = 0
        self.rounding_adjustment += flt(
            self.rounded_total - self.grand_total, self.precision("rounding_adjustment")
        )

        _set_in_company_currency(self,doc, ["rounding_adjustment", "rounded_total"])

def _set_in_company_currency(self, doc, fields):
    """set values in base currency"""
    for f in fields:
        val = flt(
            flt(doc.get(f), doc.precision(f)) * self.conversion_rate, doc.precision("base_" + f)
        )
        doc.set("base_" + f, val)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_rdl(doctype, txt, searchfield, start, page_len, filters):
    # frappe.msgprint(str(doctype)+" doctype")
    # frappe.msgprint(str(txt)+ " txt")
    # frappe.msgprint(str(searchfield)+" searchfield")
    # frappe.msgprint(str(start)+ " start")
    # frappe.msgprint(str(page_len)+ " page_len")
    # frappe.msgprint(str(filters)+" filters")
    # data = frappe.db.sql(""" SELECT cd.name from `tabCategory Discount Leasing`cd 
    #   join `tabRule Discount Leasing` rdl on rdl.nama_promo = cd.name 
    #   where rdl.item_group = '{0}' 
    #   and rdl.valid_from <= '{1}' 
    #   and rdl.valid_to >= '{1}' 
    #   and rdl.disable=0 group by cd.name """.format(filters['item_group'],filters['posting_date']))

    # frappe.msgprint(str(data))
    return frappe.db.sql(""" SELECT cd.name from `tabCategory Discount Leasing`cd 
        join `tabRule Discount Leasing` rdl on rdl.nama_promo = cd.name 
        where rdl.item_group = '{0}' 
        and rdl.valid_from <= '{1}' 
        and rdl.valid_to >= '{1}' 
        and rdl.disable=0 
        and cd.name like "%{2}%" 
        group by cd.name """.format(filters['item_group'],filters['posting_date'],txt),debug=1)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def filter_rule(doctype, txt, searchfield, start, page_len, filters):
    # frappe.msgprint(str(doctype)+" doctype")
    # frappe.msgprint(str(txt)+ " txt")
    # frappe.msgprint(str(searchfield)+" searchfield")
    # frappe.msgprint(str(start)+ " start")
    # frappe.msgprint(str(page_len)+ " page_len")
    # frappe.msgprint(str(filters)+" filters")
    # data = frappe.db.sql(""" SELECT cd.name from `tabCategory Discount Leasing`cd 
    #   join `tabRule Discount Leasing` rdl on rdl.nama_promo = cd.name 
    #   where rdl.item_group = '{0}' 
    #   and rdl.valid_from <= '{1}' 
    #   and rdl.valid_to >= '{1}' 
    #   and rdl.disable=0 group by cd.name """.format(filters['item_group'],filters['posting_date']))

    # frappe.msgprint(str(data))
    # return frappe.db.sql(""" SELECT cd.name from `tabCategory Discount` cd where cd.name like "%{}%" and cd.disabled=0""".format(txt),debug=0) 

    return frappe.db.sql(""" SELECT cd.name from `tabCategory Discount`cd 
        join `tabRule` rdl on rdl.category_discount = cd.name 
        where rdl.item_group = '{0}' 
        and rdl.valid_from <= '{1}' 
        and rdl.valid_to >= '{1}' 
        and rdl.disable=0 
        and cd.name like "%{2}%" 
        group by cd.name """.format(filters['item_group'],filters['posting_date'],txt),debug=1)

def get_advance_payment_entries(pemilik,party_type, party, party_account, order_doctype,
        order_list=None, include_unallocated=True, against_all_orders=False, limit=None):
    party_account_field = "paid_from" if party_type == "Customer" else "paid_to"
    currency_field = "paid_from_account_currency" if party_type == "Customer" else "paid_to_account_currency"
    payment_type = "Receive" if party_type == "Customer" else "Pay"
    payment_entries_against_order, unallocated_payment_entries = [], []
    limit_cond = "limit %s" % limit if limit else ""

    if order_list or against_all_orders:
        if order_list:
            reference_condition = " and t2.reference_name in ({0})" \
                .format(', '.join(['%s'] * len(order_list)))
        else:
            reference_condition = ""
            order_list = []

        payment_entries_against_order = frappe.db.sql("""
            select
                "Payment Entry" as reference_type, t1.name as reference_name,
                t1.remarks, t2.allocated_amount as amount, t2.name as reference_row,
                t2.reference_name as against_order, t1.posting_date,
                t1.{0} as currency
            from `tabPayment Entry` t1, `tabPayment Entry Reference` t2
            where
                t1.name = t2.parent and t1.{1} = %s and t1.payment_type = %s
                and t1.party_type = %s and t1.party = %s and t1.docstatus = 1 and t1.pemilik = %s
                and t2.reference_doctype = %s {2}
            order by t1.posting_date {3}
        """.format(currency_field, party_account_field, reference_condition, limit_cond),
                                                      [party_account, payment_type, party_type, party,pemilik,
                                                       order_doctype] + order_list, as_dict=1)

    if include_unallocated:
        unallocated_payment_entries = frappe.db.sql("""
                select "Payment Entry" as reference_type, name as reference_name,
                remarks, unallocated_amount as amount
                from `tabPayment Entry`
                where
                    {0} = %s and party_type = %s and party = %s and payment_type = %s and pemilik = %s
                    and docstatus = 1 and unallocated_amount > 0
                order by posting_date {1}
            """.format(party_account_field, limit_cond), (party_account, party_type, party, payment_type,pemilik), as_dict=1)

    return list(payment_entries_against_order) + list(unallocated_payment_entries)


def get_advance_journal_entries_custom(
    party_type,
    party,
    party_account,
    party_bpkb_stnk,
    cara_bayar,
    pemilik,
    amount_field,
    order_doctype,
    order_list,
    include_unallocated=True,
):
    dr_or_cr = (
        "credit_in_account_currency" if party_type == "Customer" else "debit_in_account_currency"
    )

    conditions = []
    if include_unallocated:
        conditions.append("ifnull(t2.reference_name, '')=''")

    if order_list:
        order_condition = ", ".join(["%s"] * len(order_list))
        conditions.append(
            " (t2.reference_type = '{0}' and ifnull(t2.reference_name, '') in ({1}))".format(
                order_doctype, order_condition
            )
        )

    reference_condition = " and (" + " or ".join(conditions) + ")" if conditions else ""

    # nosemgrep
    if cara_bayar == 'Cash':
        journal_entries = frappe.db.sql(
            """
            select
                "Journal Entry" as reference_type, t1.name as reference_name,
                t1.remark as remarks, t2.{0} as amount, t2.name as reference_row,
                t2.reference_name as against_order, t2.exchange_rate
            from
                `tabJournal Entry` t1, `tabJournal Entry Account` t2
            where
                t1.name = t2.parent and (t2.account = %s or t2.account = %s)
                and t2.party_type = %s and t2.party = %s
                and t2.is_advance = 'Yes' and t1.docstatus = 1
                and {1} > 0 {2}
            order by t1.posting_date""".format(
                amount_field, dr_or_cr, reference_condition
            ),
            [party_account,party_bpkb_stnk, party_type, party] + order_list,
            as_dict=1,debug=1,
        )
    else:
         journal_entries = frappe.db.sql(
            """
            select
                "Journal Entry" as reference_type, t1.name as reference_name,
                t1.remark as remarks, t2.{0} as amount, t2.name as reference_row,
                t2.reference_name as against_order, t2.exchange_rate
            FROM
                `tabJournal Entry` t1
                LEFT JOIN `tabJournal Entry Account` t2 ON t1.`name` = t2.`parent`
                LEFT JOIN `tabPenerimaan DP` dp ON dp.`name` = t1.`penerimaan_dp`
            where
                t1.name = t2.parent and (t2.account = %s or t2.account = %s)
                and t2.party_type = %s and t2.party = %s AND dp.`pemilik` = %s
                and t2.is_advance = 'Yes' and t1.docstatus = 1
                and {1} > 0 {2}
            order by t1.posting_date""".format(
                amount_field, dr_or_cr, reference_condition
            ),
            [party_account,party_bpkb_stnk, party_type, party,pemilik] + order_list,
            as_dict=1,debug=1,
        )

    return list(journal_entries)

def reconcile_against_document_custom(args):
    print("reconcile_against_document_custom")
    """
    Cancel PE or JV, Update against document, split if required and resubmit
    """
    # To optimize making GL Entry for PE or JV with multiple references
    reconciled_entries = {}
    for row in args:
        if not reconciled_entries.get((row.voucher_type, row.voucher_no)):
            reconciled_entries[(row.voucher_type, row.voucher_no)] = []

        reconciled_entries[(row.voucher_type, row.voucher_no)].append(row)
        print(reconciled_entries, ' reconciled_entries')

    for key, entries in reconciled_entries.items():
        voucher_type = key[0]
        voucher_no = key[1]

        # cancel advance entry
        doc = frappe.get_doc(voucher_type, voucher_no)
        frappe.flags.ignore_party_validation = True
        print(doc.name, doc.doctype, ' je')
        # doc.make_gl_entries(1)
        doc.make_gl_entries(cancel=1, adv_adj=1)
        # delete_gl = frappe.db.sql(""" DELETE FROM `tabGL Entry` WHERE voucher_no = "{}" """.format(doc.name))
        # frappe.db.commit()

        for entry in entries:
            check_if_advance_entry_modified(entry)
            validate_allocated_amount(entry)

            # update ref in advance entry
            if voucher_type == "Journal Entry":
                print(entry, ' entry')
                update_reference_in_journal_entry_custom(entry, doc, do_not_save=True)
            else:
                update_reference_in_payment_entry(entry, doc, do_not_save=True)

        doc.save(ignore_permissions=True)
        # re-submit advance entry
        doc = frappe.get_doc(entry.voucher_type, entry.voucher_no)
        doc.make_gl_entries(cancel=0, adv_adj=1)
        frappe.flags.ignore_party_validation = False

        if entry.voucher_type in ("Payment Entry", "Journal Entry"):
            doc.update_expense_claim()

def update_reference_in_journal_entry_custom(d, journal_entry, do_not_save=False):
    print("update_reference_in_journal_entry_custom")
    """
    Updates against document, if partial amount splits into rows
    """
    jv_detail = journal_entry.get("accounts", {"name": d["voucher_detail_no"]})[0]

    print(d, ' dddddd')

    if flt(d["unadjusted_amount"]) - flt(d["allocated_amount"]) != 0:
        # adjust the unreconciled balance
        amount_in_account_currency = flt(d["unadjusted_amount"]) - flt(d["allocated_amount"])
        amount_in_company_currency = amount_in_account_currency * flt(jv_detail.exchange_rate)
        jv_detail.set(d["dr_or_cr"], amount_in_account_currency)
        jv_detail.set(
            "debit" if d["dr_or_cr"] == "debit_in_account_currency" else "credit",
            amount_in_company_currency,
        )
    else:
        journal_entry.remove(jv_detail)

    # new row with references
    new_row = journal_entry.append("accounts")

    new_row.update((frappe.copy_doc(jv_detail)).as_dict())

    new_row.set(d["dr_or_cr"], d["allocated_amount"])
    new_row.set(
        "debit" if d["dr_or_cr"] == "debit_in_account_currency" else "credit",
        d["allocated_amount"] * flt(jv_detail.exchange_rate),
    )

    new_row.set(
        "credit_in_account_currency"
        if d["dr_or_cr"] == "debit_in_account_currency"
        else "debit_in_account_currency",
        0,
    )
    new_row.set("credit" if d["dr_or_cr"] == "debit_in_account_currency" else "debit", 0)

    new_row.set("reference_type", d["against_voucher_type"])
    new_row.set("reference_name", d["against_voucher"])

    new_row.against_account = cstr(jv_detail.against_account)
    new_row.is_advance = cstr(jv_detail.is_advance)
    new_row.docstatus = 1

    # will work as update after submit
    journal_entry.flags.ignore_validate_update_after_submit = True
    if not do_not_save:
        journal_entry.save(ignore_permissions=True)

def get_party_tax_withholding_details(inv, tax_withholding_category=None):
    pan_no = ""
    parties = []
    party_type, party = get_party_details(inv)
    has_pan_field = frappe.get_meta(party_type).has_field("pan")

    if not tax_withholding_category:
        if has_pan_field:
            fields = ["tax_withholding_category", "pan"]
        else:
            fields = ["tax_withholding_category"]

        tax_withholding_details = frappe.db.get_value(party_type, party, fields, as_dict=1)

        tax_withholding_category = tax_withholding_details.get("tax_withholding_category")
        pan_no = tax_withholding_details.get("pan")

    if not tax_withholding_category:
        return

    # if tax_withholding_category passed as an argument but not pan_no
    if not pan_no and has_pan_field:
        pan_no = frappe.db.get_value(party_type, party, "pan")

    # Get others suppliers with the same PAN No
    if pan_no:
        parties = frappe.get_all(party_type, filters={"pan": pan_no}, pluck="name")

    if not parties:
        parties.append(party)

    posting_date = inv.get("posting_date") or inv.get("transaction_date")
    tax_details = get_tax_withholding_details(tax_withholding_category, posting_date, inv.company)

    if not tax_details:
        frappe.throw(
            _("Please set associated account in Tax Withholding Category {0} against Company {1}").format(
                tax_withholding_category, inv.company
            )
        )

    if party_type == "Customer" and not tax_details.cumulative_threshold:
        # TCS is only chargeable on sum of invoiced value
        frappe.throw(
            _(
                "Tax Withholding Category {} against Company {} for Customer {} should have Cumulative Threshold value."
            ).format(tax_withholding_category, inv.company, party)
        )

    tax_amount, tax_deducted, tax_deducted_on_advances, voucher_wise_amount = get_tax_amount(
        party_type, parties, inv, tax_details, posting_date, pan_no
    )

    if party_type == "Supplier":
        tax_row = get_tax_row_for_tds(tax_details, tax_amount)
    else:
        tax_row = get_tax_row_for_tcs(inv, tax_details, tax_amount, tax_deducted)

    if inv.doctype == "Purchase Invoice":
        return tax_row, tax_deducted_on_advances, voucher_wise_amount
    else:
        return tax_row


def get_party_details(inv):
    party_type, party = "", ""

    if inv.doctype in ["Sales Invoice","Sales Invoice Penjualan Motor"]:
        party_type = "Customer"
        party = inv.customer
    else:
        party_type = "Supplier"
        party = inv.supplier

    if not party:
        frappe.throw(_("Please select {0} first").format(party_type))

    return party_type, party

@frappe.whitelist()
def make_dp(name_dp):
    data = frappe.db.sql(""" SELECT sinv.*,sum(tbm.amount) as nilai from `tabSales Invoice Penjualan Motor` sinv
    left join `tabTabel Biaya Motor` tbm on tbm.parent = sinv.name and tbm.type in ('STNK','BPKB')
    where sinv.name = '{}' """.format(name_dp),as_dict=1,debug=1)
    target_doc = frappe.new_doc("Penerimaan DP")
    frappe.msgprint(str(data)+ " data")
    for i in data:
        target_doc.cara_bayar = i.cara_bayar
        if i.cara_bayar == 'Cash':
            target_doc.customer = i.customer
            target_doc.customer_name = i.customer_name
            target_doc.debit_to = i.debit_to
            target_doc.coa_bpkb_stnk = i.coa_bpkb_stnk
            target_doc.piutang_bpkb_stnk = i.nilai
            target_doc.piutang_motor = i.harga - i.nilai - i.nominal_diskon - i.total_advance
        else:
            target_doc.customer = i.customer
            target_doc.customer_name = i.customer_name
            target_doc.pemilik = i.pemilik
            target_doc.nama_pemilik = i.nama_pemilik
            target_doc.debit_to = i.debit_to
            # target_doc.piutang_motor = i.harga - i.nilai - i.nominal_diskon - i.total_advance
    # target_doc.set_advances()
    return target_doc.as_dict()

