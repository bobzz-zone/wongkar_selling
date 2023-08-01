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
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
    get_party_tax_withholding_details,
)
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from frappe.utils import cint, flt, round_based_on_smallest_currency_fraction
from erpnext.accounts.utils import get_account_currency
from erpnext.stock import get_warehouse_account_map
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries, process_gl_map
from frappe.utils import cint, flt, getdate, add_days, cstr, nowdate, get_link_to_form, formatdate
from erpnext.controllers.accounts_controller import get_advance_journal_entries,get_advance_journal_entries,get_advance_payment_entries

class SalesInvoicePenjualanMotor(SalesInvoice):
    def get_advance_entries(self, include_unallocated=True):
        if self.doctype == "Sales Invoice Penjualan Motor":
            # frappe.msgprint("masuk Sales Invoice Penjualan Motor")
            # tambahan
            # name = self.name
            pemilik = self.pemilik
            party_account = self.debit_to
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
        journal_entries = get_advance_journal_entries(party_type, party, party_account,
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
                if outstanding_amount > 0 and due_date < nowdate and self.is_discounted and discountng_status=='Disbursed':
                    self.status = "Overdue and Discounted"
                if outstanding_amount > 0 and due_date < nowdate:
                    self.status = "Overdue"
                if outstanding_amount > 0 and due_date >= nowdate and self.is_discounted and discountng_status=='Disbursed':
                    self.status = "Unpaid and Discounted"
                if outstanding_amount > 0 and due_date >= nowdate:
                    # frappe.msgprint("masuk sini status 222")
                    self.status = "Unpaid"
                #Check if outstanding amount is 0 due to credit note issued against invoice
                if outstanding_amount <= 0 and self.is_return == 0 and frappe.db.get_value('Sales Invoice Penjualan Motor', {'is_return': 1, 'return_against': self.name, 'docstatus': 1}):
                    self.status = "Credit Note Issued"
                if self.is_return == 1:
                    self.status = "Return"
                if outstanding_amount<=0:
                    if self.customer_group=="Leasing":
                        self.status="Billed"
                    else:
                        self.status = "Paid"
                # else:
                #   self.status = "Submitted coba"
            elif self.docstatus == 0:
                self.status = "Draft"

        if update:
            self.db_set('status', self.status, update_modified = update_modified)

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

    def validate(self):
        self.cek_no_po_leasing()
        self.cek_rdl()
        self.cek_rule()

        if self.no_rangka != self.items[0].serial_no:
            frappe.throw("No rangka tidak sama dengan item !")
        #validate rule biaya harus ada 3
        if not self.bypass_biaya:
            if len(self.tabel_biaya_motor)<2:
                frappe.throw("Error ada biaya yang belum di set")

        # super(SalesInvoice, self).validate()
        self.validate_auto_set_posting_time()
        # self.calculate_taxes_and_totals()
        self.calculate_totals()
        self.calculate_total_advance()
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

       self.remove_pemilik()

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
            self.harga = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"] - self.nominal_diskon
            self.otr = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"]
        else:
            self.harga = get_item_price(self.item_code, self.selling_price_list, self.posting_date)[0]["price_list_rate"] - self.nominal_diskon
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
                # if row.valid_from <= self.posting_date.date() and row.valid_to >= self.posting_date.date():
                if row.valid_from <= self.posting_date and row.valid_to >= self.posting_date:
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
                # if row.valid_from <= self.posting_date.date() and row.valid_to >= self.posting_date.date():
                if row.valid_from <= self.posting_date and row.valid_to >= self.posting_date:
                    if row.discount == "Percent":
                        row.amount = row.percent * self.harga / 100

                    self.append("table_discount",{
                        "rule": row.name,
                        "customer":row.customer,
                        "category_discount": row.category_discount,
                        "coa_receivable": row.coa_receivable,
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
                        "coa":row.coa,
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

        # menambah tabel item
        self.append("items",{
                "item_code":self.item_code,
                "item_name": frappe.get_value("Item", self.item_code,"item_name"),
                "description": frappe.get_value("Item", self.item_code,"description"),
                "stock_uom": frappe.get_value("Item", self.item_code,"stock_uom"),
                "uom": frappe.get_value("Item", self.item_code,"stock_uom"),
                "conversion_factor": 1,
                "rate": total2,
                "base_rate": total2,
                "amount": total2,
                "base_amount": total2,
                "base_net_amount": total2,
                # "net_amount":total2,
                "qty": 1,
                "stock_qty": 1,
                "income_account": income_account,
                "expense_account": expense_account,
                "discount_amount": hasil2 + self.nominal_diskon,
                "warehouse": self.set_warehouse,
                "serial_no": self.no_rangka,
                "cost_center": self.cost_center
            })
        
        self.adj_discount = 0 if not self.adj_discount else self.adj_discount

        tax_template = frappe.db.get_list("Sales Taxes and Charges Template",{"is_default":1},"name")[0]
        # frappe.throw(str(tax_template))

        if not self.taxes:
            # frappe.throw('asdsad')
            self.taxes = []
            self.taxes_and_charges = tax_template["name"]

            tax = frappe.get_doc("Sales Taxes and Charges Template",tax_template)
            # self.grand_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.rounded_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount

            self.grand_total = (self.harga) + self.adj_discount
            self.rounded_total = (self.harga) + self.adj_discount

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
                        "tax_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100,
                        "base_tax_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100,
                        # "tax_amount": (self.harga - total_biaya) * ((row.rate)/100),
                        # "base_tax_amount": (self.harga - total_biaya) * ((row.rate)/100),
                        
                        "total": (self.harga - total_biaya),
                        "tax_amount_after_discount_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100,
                        "base_tax_amount_after_discount_amount": (self.harga - total_biaya) / ((100+row.rate)/100) * row.rate/100
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


            # self.net_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            # self.base_net_total = (self.harga - total_discount - total_discount_leasing) + self.adj_discount
            self.base_grand_total = (self.harga) + self.adj_discount
            self.outstanding_amount = (self.harga) + self.adj_discount - tot_adv



    def on_submit(self):
        self.add_pemilik()

        self.validate_pos_paid_amount()

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
            self.update_against_document_in_jv()

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

    def make_tax_gl_entries(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        nominal_diskon = 0
        nominal_diskon_leasing = 0
        total_net_d = 0
        total_net_dl = 0
        for d in self.table_discount:
            hitung_tax_d = (d.nominal) / tax
            net_d = (d.nominal) - hitung_tax_d
            total_net_d = total_net_d + net_d

        for dl in self.table_discount_leasing:
            hitung_tax_dl = (dl.nominal) / tax
            net_dl = (dl.nominal) - hitung_tax_dl
            total_net_dl = total_net_dl + net_dl

        print(total_net_d, " total_net_d")
        print(total_net_dl, " total_net_dl")  
        net_total = total_net_d + total_net_dl 

        print(net_total, " net_total")

        for tax in self.get("taxes"):
            if flt(tax.base_tax_amount_after_discount_amount):
                account_currency = get_account_currency(tax.account_head)
                gl_entries.append(
                    self.get_gl_dict({
                        "account": tax.account_head,
                        "against": self.customer,
                        "credit": (flt(tax.base_tax_amount_after_discount_amount,
                            tax.precision("tax_amount_after_discount_amount"))+net_total)-net_total,
                        "credit_in_account_currency": ((flt(tax.base_tax_amount_after_discount_amount,
                            tax.precision("base_tax_amount_after_discount_amount"))+net_total)-net_total  if account_currency==self.company_currency else
                            (flt(tax.tax_amount_after_discount_amount, tax.precision("tax_amount_after_discount_amount"))+net_total)-net_total),
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

    # table biaya
    def make_biaya_gl_entry_custom(self, gl_entries):
        for d in self.get('tabel_biaya_motor'):
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa,
                    "party_type": "Supplier",
                    "party": d.vendor,
                    "due_date": self.due_date,
                    "against": self.against_income_account,
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
        pendapatan = frappe.get_doc("Company",self.company).pendapatan_lain_leasing
        for d in self.get('table_discount_leasing'):
            hitung_tax = (d.nominal) / tax
            net_dl = (d.nominal) - hitung_tax
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa,
                    # "party_type": "Customer",
                    # "party": d.nama_leasing,
                    "due_date": self.due_date,
                    # "against": self.against_income_account,
                    "against": pendapatan,
                    "debit": hitung_tax,
                    "debit_in_account_currency": hitung_tax,
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi zzzzz!"
                }, self.party_account_currency, item=self)
            )

            # gl_entries.append(
            #   self.get_gl_dict({
            #       "account": tax_account,
            #       "against": d.nama_leasing,
            #       "debit": net_dl,
            #       "debit_in_account_currency": net_dl,
            #       "cost_center": self.cost_center,
            #   }, self.party_account_currency, item=self)
            # )

        for d in self.get('table_discount_leasing'):
            hitung_tax_c = (d.nominal) / tax
            gl_entries.append(
                self.get_gl_dict({
                    "account": pendapatan,
                    # "party_type": "Customer",
                    # "party": d.nama_leasing,
                    "due_date": self.due_date,
                    # "against": self.against_income_account,
                    "against": d.coa,
                    "credit": hitung_tax_c,
                    "credit_in_account_currency": hitung_tax_c,
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi zzzzz!"
                }, self.party_account_currency, item=self)
            )

    # diskon biasa
    def make_disc_gl_entry_custom(self, gl_entries):
        tax = (100+ self.taxes[0].rate) / 100
        tax_account = self.taxes[0].account_head
        pendapatan = frappe.get_doc("Company",self.company).pendapatan_lain
        total_net_d = 0
        for d in self.get('table_discount'):
            hitung_tax = (d.nominal) / tax
            net_d = (d.nominal) - hitung_tax
            gl_entries.append(
                self.get_gl_dict({
                    "account": d.coa_receivable,
                    # "party_type": "Customer",
                    # "party": d.customer,
                    "due_date": self.due_date,
                    # "against": self.against_income_account,
                    "against": pendapatan,
                    "debit": hitung_tax,
                    "debit_in_account_currency": hitung_tax,
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi yyyyy!"
                }, self.party_account_currency, item=self)
            )
            
            # gl_entries.append(
            #   self.get_gl_dict({
            #       "account": tax_account,
            #       "against": d.customer,
            #       "debit": net_d,
            #       "debit_in_account_currency": net_d,
            #       "cost_center": self.cost_center,
            #   }, self.party_account_currency, item=self)
            # )
        
        for d in self.get('table_discount'):
            hitung_tax_c = (d.nominal) / tax
            gl_entries.append(
                self.get_gl_dict({
                    "account": pendapatan,
                    # "party_type": "Customer",
                    # "party": d.customer,
                    "due_date": self.due_date,
                    # "against": self.against_income_account,
                    "against": d.coa_receivable,
                    "credit": hitung_tax_c,
                    "credit_in_account_currency": hitung_tax_c,
                    "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                    "against_voucher_type": self.doctype,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    # "remarks": "coba Lutfi yyyyy!"
                }, self.party_account_currency, item=self)
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

        tot_disc = 0
        for d in self.get('table_discount'):
            tot_disc = tot_disc + d.nominal

        tot_discl = 0
        for l in self.get('table_discount_leasing'):
            tot_discl = tot_discl + l.nominal

        tot_biaya = 0
        for b in self.get('tabel_biaya_motor'):
            tot_biaya = tot_biaya + b.amount

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
                "debit": (self.harga) + self.adj_discount,
                "debit_in_account_currency": (self.harga) + self.adj_discount,
                "against_voucher": self.return_against if cint(self.is_return) and self.return_against else self.name,
                "against_voucher_type": self.doctype,
                "cost_center": self.cost_center,
                "project": self.project,
                # "remarks": "coba Lutfi xxxxx!"
            }, self.party_account_currency, item=self)
        )


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

    def calculate_totals(self):
        doc = self
        print (doc, 'docccc')
        total_biaya_tanpa_dealer = 0
        if self.tabel_biaya_motor:
            if len(self.tabel_biaya_motor) > 0:
                for i in self.tabel_biaya_motor:
                    if i.type in ['STNK','BPKB']:
                        total_biaya_tanpa_dealer += i.amount
       
        if self.get("taxes"):
            print(self.rounding_adjustment, ' self.rounding_adjustment')
            self.grand_total = flt(self.get("taxes")[-1].total)+total_biaya_tanpa_dealer+ flt(self.rounding_adjustment)
        else:
            self.grand_total = flt(self.net_total)

        if self.get("taxes"):
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




