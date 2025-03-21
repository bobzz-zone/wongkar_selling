# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version
# wongkar
app_name = "wongkar_selling"
app_title = "Wongkar Selling"
app_publisher = "w"
app_description = "w"
app_icon = "w"
app_color = "w"
app_email = "w"
app_license = "MIT"

jenv = {
    "filters": [
        "number2word:wongkar_selling.wongkar_selling.jinja.toTerbilang",
        "outhari:wongkar_selling.wongkar_selling.jinja.hari",
        "outtgl:wongkar_selling.wongkar_selling.jinja.tgl",
        "outcek_pinv:wongkar_selling.wongkar_selling.jinja.cek_pinv"
    ]
}

fixtures = [
       {
         "dt": "Custom Field", 
         "filters":[["name", "in", ['Serial No-dpp', 'Serial No-ppn', 'Serial No-harga_jual', 'Company-titipan_ahas_account', 'Company-beban_titipan_ahas_account', 
         'Company-sparepart_setting', 'Company-customer', 'Company-column_break_q9dyg', 'Company-customer_name', 'Company-pendapatan_titipan_ahas_account','Company-customer_account',
         'Purchase Invoice-list_sn', 'Serial No-update_rate', 'Stock Entry-purchase_invoice', 'Journal Entry-purchase_invoice', 'Company-diskon_pinv', 'Company-je_credit', 'Company-je_debit',
         'Purchase Order-invoice_penagihan_garansi','Journal Entry-calculate', 'Journal Entry-get_data', 'Journal Entry-tagihan_payment_table', 'Journal Entry-section_break_za3eb', 
         'Journal Entry-list_doc_name', 'Journal Entry-section_break_chyyo', 'Purchase Invoice-list_doc_name', 'Purchase Invoice-section_break_ychs8', 'Purchase Order-list_doc_name', 
         'Purchase Order-section_break_mgaja','Journal Entry-claim','Purchase Invoice-claim','Purchase Order-claim']]]
      },
      {
        "dt": "Property Setter", 
        "filters": [["name", "in", ['Form Pembayaran-tagihan_payment_table-no_copy', 'Form Pembayaran-list_doc_name-no_copy', 'Sales Invoice Sparepart Garansi-posting_time-no_copy', 'Sales Invoice Sparepart Garansi-posting_date-no_copy']]]
      }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/wongkar_selling/css/wongkar_selling.css"
# app_include_js = "/assets/wongkar_selling/js/wongkar_selling.js"
app_include_css = ['/assets/wongkar_selling/css/dx.light.css',
# '/assets/wongkar_selling/css/dx.dark.css'
]
app_include_js = ['/assets/wongkar_selling/js/dx.all.js',
'/assets/wongkar_selling/js/exceljs.min.js',
'/assets/wongkar_selling/js/FileSaver.min.js',
'/assets/wongkar_selling/js/jspdf.umd.min.js',
'/assets/wongkar_selling/js/jszip.min.js',
'/assets/wongkar_selling/js/polyfill.min.js',
'/assets/wongkar_selling/js/clusterize.min.js'
]

# include js, css files in header of web template
# web_include_css = "/assets/wongkar_selling/css/wongkar_selling.css"
# web_include_js = "/assets/wongkar_selling/js/wongkar_selling.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "wongkar_selling/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Payment Entry" : "public/js/custom_payment_entry.js",
"Customer": "public/js/custom_customer.js",
"Serial No": "public/js/custom_serial_no.js",
"Journal Entry": "public/js/custom_journal_entry.js",
'Purchase Invoice': 'public/js/custom_purchase_invoice.js',
"Purchase Order": 'public/js/custom_purchase_order.js'
}

doctype_list_js = {"Sales Invoice Penjualan Motor" : "public/js/sales_invoice_motor.js",
"Tagihan Discount": "public/js/ls_tagihan_discount.js",
"Tagihan Discount Leasing": "public/js/ls_tagihan_discount_leasing.js",
"Pembayaran Tagihan Motor": "public/js/ls_pembayaran_tagihan_motor.js",
"Pembayaran Credit Motor": "public/js/ls_pembayaran_credit_motor.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "wongkar_selling.install.before_install"
# after_install = "wongkar_selling.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "wongkar_selling.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"GL Entry": "wongkar_selling.custom_standard.custom_gl_entry.custom_advance",
	"Expense Claim": "wongkar_selling.custom_standard.custom_expense_claim.custom_advance",
    "Purchase Invoice": "wongkar_selling.custom_standard.custom_purchase_invoice.PurchaseInvoiceCustom",
    "Purchase Receipt": "wongkar_selling.custom_standard.custom_purchase_receipt.PurchaseReceiptCustom"
}

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# "Sales Invoice": {
	# 	"before_submit" : ["wongkar_selling.wongkar_selling.selling.overide_make_gl"]
	# },
	# pe lama
	# "Payment Entry": {
	# 	# "before_save" : ["wongkar_selling.wongkar_selling.selling.overide_make_pe"],
	# 	# "after_insert" : ["wongkar_selling.wongkar_selling.pe.overide_make_pe2"]
	# 	# "before_save" : ["wongkar_selling.wongkar_selling.selling.overide_make_pe"],
	# 	# "validate" : ["wongkar_selling.custom_payment_entry.override_on_submit_on_cancel","wongkar_selling.wongkar_selling.get_invoice.cek_tagihan"],
	# 	"validate" : ["wongkar_selling.custom_payment_entry.override_on_submit_on_cancel","wongkar_selling.custom_standard.custom_payment_entry.validasi_advance_leasing"],
	# 	"on_submit" : ["wongkar_selling.custom_payment_entry.override_on_submit_on_cancel","wongkar_selling.custom_payment_entry.kalkulasi_oa","wongkar_selling.custom_standard.custom_payment_entry.get_terbayarkan","wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync","wongkar_selling.custom_standard.custom_payment_entry.get_terbayarkan_multi","wongkar_selling.custom_standard.custom_payment_entry.add_tanggalcair","wongkar_selling.custom_standard.custom_payment_entry.calculate_advance_leasing"],
	# 	"on_cancel" : ["wongkar_selling.custom_payment_entry.override_on_submit_on_cancel","wongkar_selling.custom_payment_entry.kalkulasi_oa_cancel",
	# 	"wongkar_selling.custom_payment_entry.kalkulasi_tagihan_cancel","wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli",
	# 	"wongkar_selling.custom_standard.custom_payment_entry.get_terbayarkan_cancel","wongkar_selling.custom_standard.custom_payment_entry.get_terbayarkan_multi_cancel",
	# 	"wongkar_selling.custom_standard.custom_payment_entry.calculate_advance_leasing_cancel","wongkar_selling.custom_standard.custom_payment_entry.validasi_pe_internal_tranfer"],
	# 	"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"]
	# },

	"Payment Entry": {
		"on_cancel" : ["wongkar_selling.custom_standard.custom_payment_entry.validasi_pe_internal_tranfer"],
	},
	"Journal Entry":{
		# "before_cancel": ["wongkar_selling.wongkar_selling.doctype.form_expanse_generator.form_expanse_generator.cencel_form"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.after_submit_sync"],
		# "on_update_after_submit": ["wongkar_selling.wongkar_selling.sync_custom.test_update_je"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli","wongkar_selling.custom_standard.custom_journal_entry.cek_cancel_adv_leasing","wongkar_selling.custom_standard.custom_stock_entry.cek_diskon_pinv",'wongkar_selling.custom_standard.custom_journal_entry.hitung_outstanding_claim'],
		"before_cancel":["wongkar_selling.custom_standard.custom_journal_entry.get_adv_leasing_cancel","wongkar_selling.custom_standard.custom_journal_entry.get_penerimaan_dp"],
		"on_submit": ["wongkar_selling.custom_standard.custom_journal_entry.get_adv_leasing",'wongkar_selling.custom_standard.custom_journal_entry.hitung_outstanding_claim'],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"]
	},
	"Purchase Invoice": {
		# "before_submit" : ["wongkar_selling.wongkar_selling.selling.overide_make_gl"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.after_submit_sync"],
		"on_update_after_submit": ["wongkar_selling.wongkar_selling.sync_custom.test_update"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli","wongkar_selling.custom_standard.custom_purchase_invoice.can_diskon_sn_ste"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"],
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync","wongkar_selling.custom_standard.custom_purchase_invoice.diskon_sn_ste"],
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sales_order_log.sales_order_log.after_submit_so"]
	},
	"Purchase Receipt": {
		# "before_submit" : ["wongkar_selling.wongkar_selling.selling.overide_make_gl"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.after_submit_sync"],
		"on_update_after_submit": ["wongkar_selling.wongkar_selling.sync_custom.test_update"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"],
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"],
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sales_order_log.sales_order_log.after_submit_so"]
	},
	"Sales Invoice": {
		# "before_submit" : ["wongkar_selling.wongkar_selling.selling.overide_make_gl"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.after_submit_sync"],
		"on_update_after_submit": ["wongkar_selling.wongkar_selling.sync_custom.test_update"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		# "on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"],
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"],
		"validate": "wongkar_selling.custom_standard.custom_sales_invoice.cek_akun_return"
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sales_order_log.sales_order_log.after_submit_so"]
	},
	"Delivery Note": {
		# "before_submit" : ["wongkar_selling.wongkar_selling.selling.overide_make_gl"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.after_submit_sync"],
		"on_update_after_submit": ["wongkar_selling.wongkar_selling.sync_custom.test_update"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		# "on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"],
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sales_order_log.sales_order_log.after_submit_so"]
	},
	"Expense Claim": {
		# "before_submit" : ["wongkar_selling.wongkar_selling.selling.overide_make_gl"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.after_submit_sync"],
		"on_update_after_submit": ["wongkar_selling.wongkar_selling.sync_custom.test_update_ec"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"],
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"]
		# "on_submit": ["wongkar_selling.wongkar_selling.doctype.sales_order_log.sales_order_log.after_submit_so"]
	},
	# "Sync Log":{
	# 	"before_insert": ["wongkar_selling.wongkar_selling.doctype.sync_log.sync_log.validate_method_sync_log"],
	# },
	"Doc Sync Log":{
		"after_insert": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_insert_doc"],
	},
	# "Territory": {
	# 	"after_insert": ["wongkar_selling.wongkar_selling.gen_wh.gen_warehouse"]
	# }
	"Sales Invoice Penjualan Motor": {
		#"on_cancel" : "frappe.event_streaming.doctype.event_update_log.event_update_log.notify_consumers"
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"],
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"]
	},
	"Stock Entry": {
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli","wongkar_selling.custom_standard.custom_stock_entry.cek_diskon_pinv"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"]
	},
	"Stock Reconciliation": {
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"]
	},
	"Sales Invoice Penjualan Motor": {
		"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"],
		"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
		"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"]
	},
	"Serial No":{
		"validate": "wongkar_selling.custom_standard.custom_serial_no.isi_nosin",
		# "after_insert": "wongkar_selling.custom_standard.custom_serial_no.isi_nosin",
		# "on_update": "wongkar_selling.custom_standard.custom_serial_no.isi_nosin",
		"onload": ["wongkar_selling.custom_standard.custom_serial_no.rem_sinv","wongkar_selling.custom_standard.custom_serial_no.isi_nosin"]
	},

	# "Payment Entry": {
	# 	"on_submit": ["wongkar_selling.wongkar_selling.doctype.doc_sync_log.doc_sync_log.after_submit_sync"],
	# 	"on_cancel": ["wongkar_selling.wongkar_selling.sync_custom.cencel_sumber_asli"],
	# 	"on_trash": ["wongkar_selling.wongkar_selling.sync_custom.delete_sumber_asli"]
	# }
	# "*": {
	# 	"on_update": "method",
	# 	"on_cancel": "method",
	# 	"on_trash": "method"
	# }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"wongkar_selling.tasks.all"
# 	],
# 	"daily": [
# 		"wongkar_selling.tasks.daily"
# 	],
# 	"hourly": [
# 		"wongkar_selling.tasks.hourly"
# 	],
# 	"weekly": [
# 		"wongkar_selling.tasks.weekly"
# 	]
# 	"monthly": [
# 		"wongkar_selling.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "wongkar_selling.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	#"frappe.desk.doctype.event.event.get_events": "wongkar_selling.event.get_events"
	# "erpnext.accounts.doctype.payment_entry.payment_entry.make_payment_order": "wongkar_selling.wongkar_selling.selling.make_payment_order",
	"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry": "wongkar_selling.wongkar_selling.selling.get_payment_entry_custom",
	# "erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents": "wongkar_selling.wongkar_selling.selling.get_outstanding_reference_documents_custom",
	"erpnext.controllers.taxes_and_totals.calculate_totals": "wongkar_selling.wongkar_selling.override_controler.calculate_totals_custom",
	"erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice": "wongkar_selling.custom_standard.custom_purchase_order.make_purchase_invoice_custom"
	# "erpnext.accounts.doctype.journal_entry.journal_entry.get_outstanding": "wongkar_selling.custom_standard.custom_journal_entry.get_outstanding_custom",
	# "erpnext.accounts.doctype.payment_entry.payment_entry.get_reference_details": "wongkar_selling.custom_payment_entry.get_reference_details_chandra",
	# "erpnext.accounts.doctype.payment_entry.payment_entry.set_missing_values": "wongkar_selling.wongkar_selling.selling.set_missing_values_custom",
}
	

#
# override_doctype_class = {
#     'PaymentEntry': 'wongkar_selling.wongkar_selling.pe.CustomPaymentEntry'
# }
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "wongkar_selling.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

