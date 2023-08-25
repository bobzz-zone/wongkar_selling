// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'erpnext/accounts/doctype/sales_invoice/sales_invoice.js' %};
// frappe.provide("erpnext.accounts");
{% include 'erpnext/selling/sales_common.js' %};
frappe.provide("erpnext.accounts");

// {% include 'erpnext/selling/sales_common.js' %};
// frappe.provide("erpnext.accounts");

erpnext.accounts.CustomSINV = erpnext.accounts.SalesInvoiceController.extend({
	posting_date(frm){
		cur_frm.set_value("no_rangka","")
		cur_frm.set_value("nama_promo","")
		cur_frm.set_value("nama_diskon")
		cur_frm.refresh_fields("no_rangka")
		cur_frm.refresh_fields("nama_promo")
		cur_frm.refresh_fields("nama_diskon")
	},
	cara_bayar(frm){
		cur_frm.set_value('no_rangka','')
		// cur_frm.set_value('item_code','')
		cur_frm.set_value('no_mesin','')
		cur_frm.set_value('harga',0)
		cur_frm.clear_table("tabel_biaya_motor");
		cur_frm.refresh_field("tabel_biaya_motor");
		if(cur_frm.doc.cara_bayar == 'Cash'){
			cur_frm.set_value('nama_promo','')
			cur_frm.set_value('nama_leasing','')
			cur_frm.set_value('no_po_leasing','')
			cur_frm.set_value('nama_diskon','')
			cur_frm.clear_table("table_discount_leasing");
			cur_frm.refresh_field("table_discount_leasing");
		}
	},
	nama_diskon(frm){
		cur_frm.set_value('no_rangka','')
	    //frappe.msgprint("nama_diskon")
	    if(!cur_frm.doc.nama_diskon){
	    	//frappe.msgprint("kosong")
	    	cur_frm.clear_table("table_discount");
			cur_frm.refresh_field("table_discount");
	    }

	    if(cur_frm.doc.nama_diskon){
	    	// table_discount generate
	    	let today = cur_frm.doc.posting_date;
	    	// frappe.msgprint(str(today)+"today")

	    	frappe.call({
				method: "wongkar_selling.wongkar_selling.get_invoice.get_rule",
				args: {
					// item_group: cur_frm.doc.item_group,
					item_code: cur_frm.doc.item_code,
					territory: cur_frm.doc.territory_real,
					posting_date: cur_frm.doc.posting_date,
					category_discount: cur_frm.doc.nama_diskon,
					from_group: cur_frm.doc.from_group
				},
				callback: function(r) {
					console.log(r.message,"rule")
					cur_frm.clear_table("table_discount");
					cur_frm.refresh_field("table_discount");
					if(r.message.length > 0){
						for (let i = 0; i < r.message.length; i++) {
							if(r.message[i].discount == 'Amount'){
								var child = cur_frm.add_child("table_discount");
								frappe.model.set_value(child.doctype, child.name, "rule", r.message[i].name);
								frappe.model.set_value(child.doctype, child.name, "customer", r.message[i].customer);
								frappe.model.set_value(child.doctype, child.name, "category_discount", r.message[i].category_discount);
								frappe.model.set_value(child.doctype, child.name, "coa_receivable", r.message[i].coa_receivable);
								frappe.model.set_value(child.doctype, child.name, "nominal", r.message[i].amount);
							}else if(data[i].discount == 'Percent'){
								var amount = r.message[i].percent * cur_frm.doc.harga / 100;
								var child2 = cur_frm.add_child("table_discount");
								frappe.model.set_value(child2.doctype, child2.name, "rule", r.message[i].name);
								frappe.model.set_value(child2.doctype, child2.name, "customer", r.message[i].customer);
								frappe.model.set_value(child2.doctype, child2.name, "category_discount", r.message[i].category_discount);
								frappe.model.set_value(child2.doctype, child2.name, "coa_receivable", percent[i].coa_receivable);
								frappe.model.set_value(child2.doctype, child2.name, "nominal", amount);
							}
						}
						// this.calculate_taxes_and_totals();
						cur_frm.refresh_field("table_discount");
					}
					
				}
			});
	    }
	},	
	customer:function(frm) {
		console.log("llooo")
		if (cur_frm.doc.is_pos){
			var pos_profile = cur_frm.doc.pos_profile;
		}
		var me = this;
		if(cur_frm.updating_party_details) return;
		erpnext.utils.get_party_details(cur_frm,
			"wongkar_selling.custom_standard.custom_party.get_party_details", {
			// "erpnext.accounts.party.get_party_details", {
				posting_date: cur_frm.doc.posting_date,
				party: cur_frm.doc.customer,
				party_type: "Customer",
				account: cur_frm.doc.debit_to,
				price_list: cur_frm.doc.selling_price_list,
				pos_profile: pos_profile
			}, function() {
				apply_pricing_rule();
			});

		if(cur_frm.doc.customer) {
			frappe.call({
				"method": "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_loyalty_programs",
				"args": {
					"customer": cur_frm.doc.customer
				},
				callback: function(r) {
					if(r.message && r.message.length > 1) {
						select_loyalty_program(cur_frm, r.message);
					}
				}
			});
		}
	},
	debit_to: function(frm) {
		var me = this;
		frm.set_value("party_account_currency", "IDR");
	},
	nama_promo(frm){
		//cur_frm.trigger("load_discount");
		// table_discount_leasing generate
	    cur_frm.set_value("nama_leasing", "");
	    cur_frm.set_value("no_rangka","")
	    if(!cur_frm.doc.nama_promo){
	    	cur_frm.set_value("nama_leasing", "");
	    	cur_frm.clear_table("table_discount_leasing");
	    	cur_frm.refresh_field("table_discount_leasing");
	    	//cur_frm.refresh_field();
	    }
	    if(cur_frm.doc.nama_promo){
	    	if(cur_frm.doc.cara_bayar == "Credit"){
		    	let today = cur_frm.doc.posting_date;
		    	frappe.call({
					method: "wongkar_selling.wongkar_selling.get_invoice.get_leasing",
					args: {
						// item_group: cur_frm.doc.item_group,
						item_code: cur_frm.doc.item_code,
						nama_promo: cur_frm.doc.nama_promo,
						territory_real: cur_frm.doc.territory_real,
						posting_date: cur_frm.doc.posting_date,
						from_group:cur_frm.doc.from_group
					},
					callback: function(r) {
						console.log(r,"leasing")
						cur_frm.clear_table("table_discount_leasing");
						cur_frm.refresh_field("table_discount_leasing");
						if(r.message.length>0){
							for (let i = 0; i < r.message.length; i++) {
								var child_l = cur_frm.add_child("table_discount_leasing");
						        frappe.model.set_value(child_l.doctype, child_l.name, "coa", r.message[i].coa);
						        frappe.model.set_value(child_l.doctype, child_l.name, "rule", r.message[i].name);
						        frappe.model.set_value(child_l.doctype, child_l.name, "coa_lawan", r.message[i].coa_lawan);
						        frappe.model.set_value(child_l.doctype, child_l.name, "nominal", r.message[i].amount);
						        frappe.model.set_value(child_l.doctype, child_l.name, "nama_leasing", r.message[i].leasing);
						        cur_frm.set_value("nominal_diskon",r.message[i].beban_dealer)
							}
							cur_frm.refresh_fields("nominal_diskon")
							cur_frm.refresh_field("table_discount_leasing");
						}
					}
				});
			}
		}
	},
	diskon(frm){
		if(cur_frm.doc.diskon==0){
			cur_frm.set_value("nominal_diskon",0)
		}
	},
	nominal_diskon(frm){
		cur_frm.set_value("no_rangka","")
	},

	territory_real:function(frm){
		cur_frm.set_value("no_rangka","")
		cur_frm.set_value("nama_diskon","")
		cur_frm.set_value("nama_promo","")
	},
	territory_biaya:function(frm){
		cur_frm.set_value("no_rangka","")
		cur_frm.set_value("nama_diskon","")
		cur_frm.set_value("nama_promo","")
	},
	cost_center:function(frm){
		cur_frm.set_value("no_rangka","")
	},
	selling_price_list:function(frm){
		cur_frm.set_value("no_rangka","")
	},
	set_warehouse:function(frm){
		cur_frm.set_value("no_rangka","")
	},
	refresh(frm){
		// frappe.msgprint('asdsa123')
		// if(cur_frm.doc.items){
		// 	if(cur_frm.doc.items.length > 0){
		// 		// frappe.msgprint('asdsa123zz')
		// 		cur_frm.call("validate",{})
		// 	}
		// }
	},
	validate(frm){
		// frappe.msgprint("test")

		hitung_item_rate()
		this.calculate_taxes_and_totals();
		let td = 0
		let tdl = 0
		if(cur_frm.doc.table_discount){
			for (let i = 0; i < cur_frm.doc.table_discount.length; i++) {
				td += cur_frm.doc.table_discount[i].nominal;
			}
		}
		if(cur_frm.doc.table_discount_leasing){
			for (let i = 0; i < cur_frm.doc.table_discount_leasing.length; i++) {
				tdl += cur_frm.doc.table_discount_leasing[i].nominal;
			}
		}
		let oa =0
		oa = (cur_frm.doc.harga - td - tdl) + cur_frm.doc.adj_discount
		cur_frm.set_value("total_discoun_leasing",tdl)

		if(cur_frm.doc.cek_adjustment_harga){
			if(cur_frm.doc.adjustment_harga <=0){
				frappe.throw("Adjustment Harga Harus lebih besar dari 0 !")
			}
		}
	},
	setup: function(doc) {
		this.setup_posting_date_time_check();
		this._super(doc);

		cur_frm.set_query("nama_promo", function() {
			if (cur_frm.doc.item_group) {
				return {
					query: 'wongkar_selling.wongkar_selling.doctype.sales_invoice_penjualan_motor.sales_invoice_penjualan_motor.get_rdl',
					filters: {
						posting_date: cur_frm.doc.posting_date,
						item_group: cur_frm.doc.item_group
					}
				};
			}
		});

		cur_frm.set_query("nama_diskon", function() {
			if (cur_frm.doc.item_group) {
				return {
					query: 'wongkar_selling.wongkar_selling.doctype.sales_invoice_penjualan_motor.sales_invoice_penjualan_motor.filter_rule',
					filters: {
						posting_date: cur_frm.doc.posting_date,
						item_group: cur_frm.doc.item_group
					}
				};
			}
		});
	},
	company: function() {
		erpnext.accounts.dimensions.update_dimension(this.frm, this.frm.doctype);
		let me = this;
		if (this.frm.doc.company) {
			frappe.call({
				method:
					"erpnext.accounts.party.get_party_account",
				args: {
					party_type: 'Customer',
					party: this.frm.doc.customer,
					company: this.frm.doc.company
				},
				callback: (response) => {
					if (response) me.frm.set_value("debit_to", response.message);
				},
			});
		}
	},

	onload: function() {
		var me = this;
		this._super();

		this.frm.ignore_doctypes_on_cancel_all = ['POS Invoice', 'Timesheet', 'POS Invoice Merge Log',
			'POS Closing Entry', 'Journal Entry', 'Payment Entry'];

		if(!this.frm.doc.__islocal && !this.frm.doc.customer && this.frm.doc.debit_to) {
			// show debit_to in print format
			this.frm.set_df_property("debit_to", "print_hide", 0);
		}

		erpnext.queries.setup_queries(this.frm, "Warehouse", function() {
			return erpnext.queries.warehouse(me.frm.doc);
		});

		if(this.frm.doc.__islocal && this.frm.doc.is_pos) {
			//Load pos profile data on the invoice if the default value of Is POS is 1

			me.frm.script_manager.trigger("is_pos");
			me.frm.refresh_fields();
		}
		erpnext.queries.setup_warehouse_query(this.frm);
	},

	// refresh: function(doc, dt, dn) {
	// 	const me = this;
	// 	this._super();
	// 	if(cur_frm.msgbox && cur_frm.msgbox.$wrapper.is(":visible")) {
	// 		// hide new msgbox
	// 		cur_frm.msgbox.hide();
	// 	}

	// 	this.frm.toggle_reqd("due_date", !this.frm.doc.is_return);

	// 	if (this.frm.doc.is_return) {
	// 		this.frm.return_print_format = "Sales Invoice Return";
	// 	}

	// 	this.show_general_ledger();

	// 	if(doc.update_stock) this.show_stock_ledger();

	// 	if (doc.docstatus == 1 && doc.outstanding_amount!=0
	// 		&& !(cint(doc.is_return) && doc.return_against)) {
	// 		this.frm.add_custom_button(
	// 			__('Payment'),
	// 			() => this.make_payment_entry(),
	// 			__('Create')
	// 		);
	// 		this.frm.page.set_inner_btn_group_as_primary(__('Create'));
	// 	}

	// 	if(doc.docstatus==1 && !doc.is_return) {

	// 		var is_delivered_by_supplier = false;

	// 		is_delivered_by_supplier = cur_frm.doc.items.some(function(item){
	// 			return item.is_delivered_by_supplier ? true : false;
	// 		})

	// 		if(doc.outstanding_amount >= 0 || Math.abs(flt(doc.outstanding_amount)) < flt(doc.grand_total)) {
	// 			cur_frm.add_custom_button(__('Return / Credit Note'),
	// 				this.make_sales_return, __('Create'));
	// 			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
	// 		}

	// 		if(cint(doc.update_stock)!=1) {
	// 			// show Make Delivery Note button only if Sales Invoice is not created from Delivery Note
	// 			var from_delivery_note = false;
	// 			from_delivery_note = cur_frm.doc.items
	// 				.some(function(item) {
	// 					return item.delivery_note ? true : false;
	// 				});

	// 			if(!from_delivery_note && !is_delivered_by_supplier) {
	// 				cur_frm.add_custom_button(__('Delivery'),
	// 					cur_frm.cscript['Make Delivery Note'], __('Create'));
	// 			}
	// 		}

	// 		if (doc.outstanding_amount>0) {
	// 			cur_frm.add_custom_button(__('Payment Request'), function() {
	// 				me.make_payment_request();
	// 			}, __('Create'));

	// 			cur_frm.add_custom_button(__('Invoice Discounting'), function() {
	// 				cur_frm.events.create_invoice_discounting(cur_frm);
	// 			}, __('Create'));

	// 			if (doc.due_date < frappe.datetime.get_today()) {
	// 				cur_frm.add_custom_button(__('Dunning'), function() {
	// 					cur_frm.events.create_dunning(cur_frm);
	// 				}, __('Create'));
	// 			}
	// 		}

	// 		if (doc.docstatus === 1) {
	// 			cur_frm.add_custom_button(__('Maintenance Schedule'), function () {
	// 				cur_frm.cscript.make_maintenance_schedule();
	// 			}, __('Create'));
	// 		}

	// 		if(!doc.auto_repeat) {
	// 			cur_frm.add_custom_button(__('Subscription'), function() {
	// 				erpnext.utils.make_subscription(doc.doctype, doc.name)
	// 			}, __('Create'))
	// 		}
	// 	}

	// 	// Show buttons only when pos view is active
	// 	if (cint(doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !doc.is_return) {
	// 		this.frm.cscript.sales_order_btn();
	// 		this.frm.cscript.delivery_note_btn();
	// 		this.frm.cscript.quotation_btn();
	// 	}

	// 	this.set_default_print_format();
	// 	if (doc.docstatus == 1 && !doc.inter_company_invoice_reference) {
	// 		let internal = me.frm.doc.is_internal_customer;
	// 		if (internal) {
	// 			let button_label = (me.frm.doc.company === me.frm.doc.represents_company) ? "Internal Purchase Invoice" :
	// 				"Inter Company Purchase Invoice";

	// 			me.frm.add_custom_button(button_label, function() {
	// 				me.make_inter_company_invoice();
	// 			}, __('Create'));
	// 		}
	// 	}
	// },

	make_maintenance_schedule: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_maintenance_schedule",
			frm: cur_frm
		})
	},

	on_submit: function(doc, dt, dn) {
		var me = this;

		if (frappe.get_route()[0] != 'Form') {
			return
		}

		$.each(doc["items"], function(i, row) {
			if(row.delivery_note) frappe.model.clear_doc("Delivery Note", row.delivery_note)
		})
	},

	set_default_print_format: function() {
		// set default print format to POS type or Credit Note
		if(cur_frm.doc.is_pos) {
			if(cur_frm.pos_print_format) {
				cur_frm.meta._default_print_format = cur_frm.meta.default_print_format;
				cur_frm.meta.default_print_format = cur_frm.pos_print_format;
			}
		} else if(cur_frm.doc.is_return && !cur_frm.meta.default_print_format) {
			if(cur_frm.return_print_format) {
				cur_frm.meta._default_print_format = cur_frm.meta.default_print_format;
				cur_frm.meta.default_print_format = cur_frm.return_print_format;
			}
		} else {
			if(cur_frm.meta._default_print_format) {
				cur_frm.meta.default_print_format = cur_frm.meta._default_print_format;
				cur_frm.meta._default_print_format = null;
			} else if(in_list([cur_frm.pos_print_format, cur_frm.return_print_format], cur_frm.meta.default_print_format)) {
				cur_frm.meta.default_print_format = null;
				cur_frm.meta._default_print_format = null;
			}
		}
	},

	sales_order_btn: function() {
		var me = this;
		this.$sales_order_btn = this.frm.add_custom_button(__('Sales Order'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
					source_doctype: "Sales Order",
					target: me.frm,
					setters: {
						customer: me.frm.doc.customer || undefined,
					},
					get_query_filters: {
						docstatus: 1,
						status: ["not in", ["Closed", "On Hold"]],
						per_billed: ["<", 99.99],
						company: me.frm.doc.company
					}
				})
			}, __("Get Items From"));
	},

	quotation_btn: function() {
		var me = this;
		this.$quotation_btn = this.frm.add_custom_button(__('Quotation'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.selling.doctype.quotation.quotation.make_sales_invoice",
					source_doctype: "Quotation",
					target: me.frm,
					setters: [{
						fieldtype: 'Link',
						label: __('Customer'),
						options: 'Customer',
						fieldname: 'party_name',
						default: me.frm.doc.customer,
					}],
					get_query_filters: {
						docstatus: 1,
						status: ["!=", "Lost"],
						company: me.frm.doc.company
					}
				})
			}, __("Get Items From"));
	},

	delivery_note_btn: function() {
		var me = this;
		this.$delivery_note_btn = this.frm.add_custom_button(__('Delivery Note'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
					source_doctype: "Delivery Note",
					target: me.frm,
					date_field: "posting_date",
					setters: {
						customer: me.frm.doc.customer || undefined
					},
					get_query: function() {
						var filters = {
							docstatus: 1,
							company: me.frm.doc.company,
							is_return: 0
						};
						if(me.frm.doc.customer) filters["customer"] = me.frm.doc.customer;
						return {
							query: "erpnext.controllers.queries.get_delivery_notes_to_be_billed",
							filters: filters
						};
					}
				});
			}, __("Get Items From"));
	},

	tc_name: function() {
		this.get_terms();
	},
	customer: function() {
		console.log("masuk sini")
		if (this.frm.doc.is_pos){
			var pos_profile = this.frm.doc.pos_profile;
		}
		var me = this;
		if(this.frm.updating_party_details) return;

		if (this.frm.doc.__onload && this.frm.doc.__onload.load_after_mapping) return;

		erpnext.utils.get_party_details(this.frm,
			"erpnext.accounts.party.get_party_details", {
				posting_date: this.frm.doc.posting_date,
				party: this.frm.doc.customer,
				party_type: "Customer",
				account: this.frm.doc.debit_to,
				price_list: this.frm.doc.selling_price_list,
				pos_profile: pos_profile
			}, function() {
				me.apply_pricing_rule();
			});

		if(this.frm.doc.customer) {
			frappe.call({
				"method": "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_loyalty_programs",
				"args": {
					"customer": this.frm.doc.customer
				},
				callback: function(r) {
					if(r.message && r.message.length > 1) {
						select_loyalty_program(me.frm, r.message);
					}
				}
			});
		}
	},

	make_inter_company_invoice: function() {
		let me = this;
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_inter_company_purchase_invoice",
			frm: me.frm
		});
	},

	debit_to: function() {
		var me = this;
		if(this.frm.doc.debit_to) {
			me.frm.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Account",
					fieldname: "account_currency",
					filters: { name: me.frm.doc.debit_to },
				},
				callback: function(r, rt) {
					if(r.message) {
						me.frm.set_value("party_account_currency", r.message.account_currency);
						me.set_dynamic_labels();
					}
				}
			});
		}
	},

	allocated_amount: function() {
		this.calculate_total_advance();
		this.frm.refresh_fields();
	},

	write_off_outstanding_amount_automatically() {
		if (cint(this.frm.doc.write_off_outstanding_amount_automatically)) {
			frappe.model.round_floats_in(this.frm.doc, ["grand_total", "paid_amount"]);
			// this will make outstanding amount 0
			this.frm.set_value("write_off_amount",
				flt(this.frm.doc.grand_total - this.frm.doc.paid_amount - this.frm.doc.total_advance, precision("write_off_amount"))
			);
		}

		this.calculate_outstanding_amount(false);
		this.frm.refresh_fields();
	},

	write_off_amount: function() {
		this.set_in_company_currency(this.frm.doc, ["write_off_amount"]);
		this.write_off_outstanding_amount_automatically();
	},

	items_add: function(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		this.frm.script_manager.copy_from_first_row("items", row, ["income_account", "discount_account", "cost_center"]);
	},

	set_dynamic_labels: function() {
		this._super();
		this.frm.events.hide_fields(this.frm)
	},

	items_on_form_rendered: function() {
		erpnext.setup_serial_or_batch_no();
	},

	packed_items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_or_batch_no();
	},

	make_sales_return: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
			frm: cur_frm
		})
	},

	asset: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if(row.asset) {
			frappe.call({
				method: erpnext.assets.doctype.asset.depreciation.get_disposal_account_and_cost_center,
				args: {
					"company": frm.doc.company
				},
				callback: function(r, rt) {
					frappe.model.set_value(cdt, cdn, "income_account", r.message[0]);
					frappe.model.set_value(cdt, cdn, "cost_center", r.message[1]);
				}
			})
		}
	},

	is_pos: function(frm){
		this.set_pos_data();
	},

	pos_profile: function() {
		this.frm.doc.taxes = []
		this.set_pos_data();
	},

	set_pos_data: function() {
		if(this.frm.doc.is_pos) {
			this.frm.set_value("allocate_advances_automatically", 0);
			if(!this.frm.doc.company) {
				this.frm.set_value("is_pos", 0);
				frappe.msgprint(__("Please specify Company to proceed"));
			} else {
				var me = this;
				return this.frm.call({
					doc: me.frm.doc,
					method: "set_missing_values",
					callback: function(r) {
						if(!r.exc) {
							if(r.message && r.message.print_format) {
								me.frm.pos_print_format = r.message.print_format;
							}
							me.frm.trigger("update_stock");
							if(me.frm.doc.taxes_and_charges) {
								me.frm.script_manager.trigger("taxes_and_charges");
							}

							frappe.model.set_default_values(me.frm.doc);
							me.set_dynamic_labels();
							me.calculate_taxes_and_totals();
						}
					}
				});
			}
		}
		else this.frm.trigger("refresh");
	},

	amount: function(){
		this.write_off_outstanding_amount_automatically()
	},

	change_amount: function(){
		if(this.frm.doc.paid_amount > this.frm.doc.grand_total){
			this.calculate_write_off_amount();
		}else {
			this.frm.set_value("change_amount", 0.0);
			this.frm.set_value("base_change_amount", 0.0);
		}

		this.frm.refresh_fields();
	},

	loyalty_amount: function(){
		console.log("log")
		this.calculate_outstanding_amount();
		this.frm.refresh_field("outstanding_amount");
		this.frm.refresh_field("paid_amount");
		this.frm.refresh_field("base_paid_amount");
	},

	currency() {
		var me = this;
		this._super();
		if (this.frm.doc.timesheets) {
			this.frm.doc.timesheets.forEach((d) => {
				let row = frappe.get_doc(d.doctype, d.name)
				set_timesheet_detail_rate(row.doctype, row.name, me.frm.doc.currency, row.timesheet_detail)
			});
			this.frm.trigger("calculate_timesheet_totals");
		}
	},

	is_cash_or_non_trade_discount() {
		this.frm.set_df_property("additional_discount_account", "hidden", 1 - this.frm.doc.is_cash_or_non_trade_discount);
		this.frm.set_df_property("additional_discount_account", "reqd", this.frm.doc.is_cash_or_non_trade_discount);

		if (!this.frm.doc.is_cash_or_non_trade_discount) {
			this.frm.set_value("additional_discount_account", "");
		}

		this.calculate_taxes_and_totals();
	}
});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.accounts.CustomSINV({frm: cur_frm}));

cur_frm.cscript['Make Delivery Note'] = function() {
	frappe.model.open_mapped_doc({
		method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_delivery_note",
		frm: cur_frm
	})
}

cur_frm.fields_dict.cash_bank_account.get_query = function(doc) {
	return {
		filters: [
			["Account", "account_type", "in", ["Cash", "Bank"]],
			["Account", "root_type", "=", "Asset"],
			["Account", "is_group", "=",0],
			["Account", "company", "=", doc.company]
		]
	}
}

cur_frm.fields_dict.write_off_account.get_query = function(doc) {
	return{
		filters:{
			'report_type': 'Profit and Loss',
			'is_group': 0,
			'company': doc.company
		}
	}
}

// Write off cost center
//-----------------------
cur_frm.fields_dict.write_off_cost_center.get_query = function(doc) {
	return{
		filters:{
			'is_group': 0,
			'company': doc.company
		}
	}
}

// Income Account in Details Table
// --------------------------------
cur_frm.set_query("income_account", "items", function(doc) {
	return{
		query: "erpnext.controllers.queries.get_income_account",
		filters: {'company': doc.company}
	}
});

// Cost Center in Details Table
// -----------------------------
cur_frm.fields_dict["items"].grid.get_field("cost_center").get_query = function(doc) {
	return {
		filters: {
			'company': doc.company,
			"is_group": 0
		}
	}
}

cur_frm.cscript.income_account = function(doc, cdt, cdn) {
	erpnext.utils.copy_value_in_all_rows(doc, cdt, cdn, "items", "income_account");
}

cur_frm.cscript.expense_account = function(doc, cdt, cdn) {
	erpnext.utils.copy_value_in_all_rows(doc, cdt, cdn, "items", "expense_account");
}

cur_frm.cscript.cost_center = function(doc, cdt, cdn) {
	erpnext.utils.copy_value_in_all_rows(doc, cdt, cdn, "items", "cost_center");
}

cur_frm.set_query("debit_to", function(doc) {
	return {
		filters: {
			'account_type': 'Receivable',
			'is_group': 0,
			'company': doc.company
		}
	}
});

cur_frm.set_query("asset", "items", function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	return {
		filters: [
			["Asset", "item_code", "=", d.item_code],
			["Asset", "docstatus", "=", 1],
			["Asset", "status", "in", ["Submitted", "Partially Depreciated", "Fully Depreciated"]],
			["Asset", "company", "=", doc.company]
		]
	}
});

frappe.ui.form.on('Sales Invoice Penjualan Motor', {
	customer(frm) {
		console.log("llooo")
		if (cur_frm.doc.is_pos){
			var pos_profile = cur_frm.doc.pos_profile;
		}
		var me = this;
		if(cur_frm.updating_party_details) return;
		erpnext.utils.get_party_details(cur_frm,
			"wongkar_selling.custom_standard.custom_party.get_party_details", {
			// "erpnext.accounts.party.get_party_details", {
				posting_date: cur_frm.doc.posting_date,
				party: cur_frm.doc.customer,
				party_type: "Customer",
				account: cur_frm.doc.debit_to,
				price_list: cur_frm.doc.selling_price_list,
				pos_profile: pos_profile
			}, function() {
				// apply_pricing_rule();
			});

		if(cur_frm.doc.customer) {
			frappe.call({
				"method": "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_loyalty_programs",
				"args": {
					"customer": cur_frm.doc.customer
				},
				callback: function(r) {
					if(r.message && r.message.length > 1) {
						select_loyalty_program(cur_frm, r.message);
					}
				}
			});
		}
	},
	cek_adjustment_harga(frm){
		if(!cur_frm.cek_adjustment_harga){
			cur_frm.set_value('adjustment_harga',0)
			cur_frm.set_value('no_rangka','')
		}
	},
	adjustment_harga(frm){
		cur_frm.set_value('no_rangka','')
	},
	item_code(frm){
		cur_frm.set_value("nama_diskon","")
		cur_frm.set_value("no_rangka","")
	},
	no_rangka(frm){
		if(cur_frm.doc.no_rangka){
			let today = frappe.datetime.get_today();
			// frappe.msgprint('coba pajak1');
			// cur_frm.clear_table("taxes");
			// cur_frm.refresh_field("taxes");
			frappe.db.get_value("Sales Taxes and Charges Template", {"is_default":1}, ["name"])
			.then((r) => {
				if (r.message) {
					cur_frm.set_value("taxes_and_charges","");
					cur_frm.set_value("taxes_and_charges",r.message.name);
					cur_frm.refresh_fields("taxes");
				}
			});
			

			// harga baru
			frappe.call({
				method: "wongkar_selling.wongkar_selling.get_invoice.get_item_price",
				args: {
					item_code: cur_frm.doc.item_code,
					price_list: cur_frm.doc.selling_price_list,
					posting_date: cur_frm.doc.posting_date
				},
				callback: function(r) {
					console.log(r,"safasf")
					if(r.message[0].price_list_rate){
			    		let values = r.message;
			    		if(cur_frm.doc.diskon==1){
			    			var hitung_disc = 0;
							hitung_disc = r.message[0].price_list_rate - cur_frm.doc.nominal_diskon
							console.log(hitung_disc,"hitung_disc")
							cur_frm.set_value("harga",r.message[0].price_list_rate)
							cur_frm.set_value("otr",r.message[0].price_list_rate)
			    		}

			    		if(cur_frm.doc.diskon==0){
			    			cur_frm.set_value("harga", r.message[0].price_list_rate);
			    			cur_frm.set_value("otr",r.message[0].price_list_rate)
				        	//cur_frm.refresh_fields("harga")
			    		}

			    		if(cur_frm.doc.cek_adjustment_harga == 1){
			    			cur_frm.set_value("otr", r.message[0].price_list_rate);
			    			cur_frm.set_value("harga", cur_frm.doc.adjustment_harga);
			    		}
			    	}else{
			    		//cur_frm.set_value("harga", 0);
				        //cur_frm.refresh_fields("harga")
			    	}
				}
			});


	    	var coba12 = cur_frm.doc.harga
	    	console.log(coba12,"ccccc")

	    	frappe.call({
				method: "wongkar_selling.wongkar_selling.get_invoice.get_biaya",
				args: {
					// item_group: cur_frm.doc.item_group,
					item_code: cur_frm.doc.item_code,
					territory: cur_frm.doc.territory_biaya,
					posting_date: cur_frm.doc.posting_date,
					from_group: cur_frm.doc.from_group
				},
				callback: function(r) {
					console.log(r.message,"get_biaya")
				    cur_frm.clear_table("tabel_biaya_motor");
		        	cur_frm.refresh_field("tabel_biaya_motor");
					var ppn_rate = cur_frm.doc.taxes[0]['rate']
					var ppn_div = (100+ppn_rate)/100
					var total_biaya_tanpa_dealer = 0 
					    
					if(r.message.length > 0){
						for (let i = 0; i < r.message.length; i++) {
							var child_b = cur_frm.add_child("tabel_biaya_motor");
							frappe.model.set_value(child_b.doctype, child_b.name, "rule", r.message[i].name);
					        frappe.model.set_value(child_b.doctype, child_b.name, "vendor", r.message[i].vendor);
					        frappe.model.set_value(child_b.doctype, child_b.name, "type", r.message[i].type);
					        frappe.model.set_value(child_b.doctype, child_b.name, "amount", r.message[i].amount);
				            frappe.model.set_value(child_b.doctype, child_b.name, "coa", r.message[i].coa);
						}
						cur_frm.refresh_field("tabel_biaya_motor");	

						
						// table item
						cur_frm.clear_table("items");
						cur_frm.refresh_field("items");
						var child_i = cur_frm.add_child("items");
						frappe.model.set_value(child_i.doctype, child_i.name, "item_code", cur_frm.doc.item_code);
						// console.log("sebelum get details")
						// frappe.model.set_value(child_i.doctype, child_i.name, "discount_amount", cb_disc);
						frappe.model.set_value(child_i.doctype, child_i.name,"cost_center",cur_frm.doc.cost_center)
						// frappe.model.set_value(child_i.doctype, child_i.name, "price_list_rate", total)
						// frappe.model.set_value(child_i.doctype, child_i.name, "base_price_list_rate", total)
						// frappe.model.set_value(child_i.doctype, child_i.name, "rate", total)
						// frappe.model.set_value(child_i.doctype, child_i.name, "description", "totalwkekek")
						frappe.model.set_value(child_i.doctype, child_i.name, "warehouse", cur_frm.doc.set_warehouse)
						frappe.model.set_value(child_i.doctype, child_i.name, "serial_no", cur_frm.doc.no_rangka)
						cur_frm.refresh_fields("items");

						

					}else{
						cur_frm.set_value("total_biaya",0)
						console.log(cur_frm.doc.harga,"harga")
					    // var total = Math.ceil((cur_frm.doc.harga - total_biaya_tanpa_dealer + cur_frm.doc.adj_discount) / ppn_div);
						var total = (cur_frm.doc.harga - total_biaya_tanpa_dealer + cur_frm.doc.adj_discount) / ppn_div;
						var hasil2 = cur_frm.doc.harga - total;
						var akhir2 = cur_frm.doc.harga - hasil2;
						console.log(total,"total2")
						console.log(hasil2,"hasil2")
						console.log(akhir2,"akhir2")
					    
					    var cb_disc = 0
					    if(cur_frm.doc.diskon==1){
					    	cb_disc = hasil2 + cur_frm.doc.nominal_diskon
					    }else{
					    	cb_disc = hasil2+0
					    }

						// table item
						cur_frm.clear_table("items");
						cur_frm.refresh_field("items");
						var child_i2 = cur_frm.add_child("items");
						frappe.model.set_value(child_i2.doctype, child_i2.name, "item_code", cur_frm.doc.item_code);
						// console.log("sebelum get details 2")
						// frappe.model.set_value(child_i2.doctype, child_i2.name, "discount_amount", cb_disc);
						// frappe.model.set_value(child_i2.doctype, child_i2.name, "price_list_rate", cur_frm.doc.harga);
						// frappe.model.set_value(child_i2.doctype, child_i2.name, "rate", total)
						frappe.model.set_value(child_i2.doctype, child_i2.name, "warehouse", cur_frm.doc.set_warehouse)
						frappe.model.set_value(child_i2.doctype, child_i2.name, "serial_no", cur_frm.doc.no_rangka)
						frappe.model.set_value(child_i2.doctype, child_i2.name,"cost_center",cur_frm.doc.cost_center)
						//cur_frm.refresh_field("items");
					}
					
				}
			});


		    // cur_frm.doc.items[0]['price_list_rate'] = total
		    // cur_frm.refresh_fields("items")
		}

		if(!cur_frm.doc.no_rangka){
			// cur_frm.set_value("harga", 0);
			// cur_frm.refresh_field("harga");
			// cur_frm.set_value("otr", 0);
			// cur_frm.refresh_field("otr");
			cur_frm.clear_table("items");
			cur_frm.refresh_field("items");
		}
	},
	hargaaaa(frm){
		console.log("hargaaaa")
		cur_frm.clear_table("tabel_biaya_motor");
		cur_frm.refresh_field("tabel_biaya_motor");  
		let today = cur_frm.doc.posting_date;
		if(cur_frm.doc.harga > 0){
	    	
	    }
	},
	setup: function(frm){
		frm.add_fetch('customer', 'tax_id', 'tax_id');
		frm.add_fetch('payment_term', 'invoice_portion', 'invoice_portion');
		frm.add_fetch('payment_term', 'description', 'description');

		frm.set_df_property('packed_items', 'cannot_add_rows', true);
		frm.set_df_property('packed_items', 'cannot_delete_rows', true);

		frm.set_query("account_for_change_amount", function() {
			return {
				filters: {
					account_type: ['in', ["Cash", "Bank"]],
					company: frm.doc.company,
					is_group: 0
				}
			};
		});

		frm.set_query("unrealized_profit_loss_account", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
					root_type: "Liability",
				}
			};
		});

		frm.set_query("adjustment_against", function() {
			return {
				filters: {
					company: frm.doc.company,
					customer: frm.doc.customer,
					docstatus: 1
				}
			};
		});

		frm.set_query("additional_discount_account", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
					report_type: "Profit and Loss",
				}
			};
		});

		frm.custom_make_buttons = {
			'Delivery Note': 'Delivery',
			'Sales Invoice': 'Return / Credit Note',
			'Payment Request': 'Payment Request',
			'Payment Entry': 'Payment'
		}

		frm.fields_dict["timesheets"].grid.get_field("time_sheet").get_query = function(doc, cdt, cdn){
			return{
				query: "erpnext.projects.doctype.timesheet.timesheet.get_timesheet",
				filters: {'project': doc.project}
			}
		}

		// discount account
		frm.fields_dict['items'].grid.get_field('discount_account').get_query = function(doc) {
			return {
				filters: {
					'report_type': 'Profit and Loss',
					'company': doc.company,
					"is_group": 0
				}
			}
		}

		frm.fields_dict['items'].grid.get_field('deferred_revenue_account').get_query = function(doc) {
			return {
				filters: {
					'root_type': 'Liability',
					'company': doc.company,
					"is_group": 0
				}
			}
		}

		frm.set_query('company_address', function(doc) {
			if(!doc.company) {
				frappe.throw(__('Please set Company'));
			}

			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Company',
					link_name: doc.company
				}
			};
		});

		frm.set_query('pos_profile', function(doc) {
			if(!doc.company) {
				frappe.throw(_('Please set Company'));
			}

			return {
				query: 'erpnext.accounts.doctype.pos_profile.pos_profile.pos_profile_query',
				filters: {
					company: doc.company
				}
			};
		});

		// set get_query for loyalty redemption account
		frm.fields_dict["loyalty_redemption_account"].get_query = function() {
			return {
				filters:{
					"company": frm.doc.company,
					"is_group": 0
				}
			}
		};

		// set get_query for loyalty redemption cost center
		frm.fields_dict["loyalty_redemption_cost_center"].get_query = function() {
			return {
				filters:{
					"company": frm.doc.company,
					"is_group": 0
				}
			}
		};
	},
	// When multiple companies are set up. in case company name is changed set default company address
	company: function(frm){
		if (frm.doc.company) {
			frappe.call({
				method: "erpnext.setup.doctype.company.company.get_default_company_address",
				args: {name:frm.doc.company, existing_address: frm.doc.company_address || ""},
				debounce: 2000,
				callback: function(r){
					if (r.message){
						frm.set_value("company_address",r.message)
					}
					else {
						frm.set_value("company_address","")
					}
				}
			})
		}
	},

	onload: function(frm) {
		frm.redemption_conversion_factor = null;
	},

	update_stock: function(frm, dt, dn) {
		frm.events.hide_fields(frm);
		frm.fields_dict.items.grid.toggle_reqd("item_code", frm.doc.update_stock);
		frm.trigger('reset_posting_time');
	},

	redeem_loyalty_points: function(frm) {
		frm.events.get_loyalty_details(frm);
	},

	loyalty_points: function(frm) {
		if (frm.redemption_conversion_factor) {
			frm.events.set_loyalty_points(frm);
		} else {
			frappe.call({
				method: "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_redeemption_factor",
				args: {
					"loyalty_program": frm.doc.loyalty_program
				},
				callback: function(r) {
					if (r) {
						frm.redemption_conversion_factor = r.message;
						frm.events.set_loyalty_points(frm);
					}
				}
			});
		}
	},

	hide_fields: function(frm) {
		let doc = frm.doc;
		var parent_fields = ['project', 'due_date', 'is_opening', 'source', 'total_advance', 'get_advances',
		'advances', 'from_date', 'to_date'];

		if(cint(doc.is_pos) == 1) {
			hide_field(parent_fields);
		} else {
			for (var i in parent_fields) {
				var docfield = frappe.meta.docfield_map[doc.doctype][parent_fields[i]];
				if(!docfield.hidden) unhide_field(parent_fields[i]);
			}
		}

		// India related fields
		if (frappe.boot.sysdefaults.country == 'India') unhide_field(['c_form_applicable', 'c_form_no']);
		else hide_field(['c_form_applicable', 'c_form_no']);

		frm.refresh_fields();
	},

	get_loyalty_details: function(frm) {
		if (frm.doc.customer && frm.doc.redeem_loyalty_points) {
			frappe.call({
				method: "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_loyalty_program_details",
				args: {
					"customer": frm.doc.customer,
					"loyalty_program": frm.doc.loyalty_program,
					"expiry_date": frm.doc.posting_date,
					"company": frm.doc.company
				},
				callback: function(r) {
					if (r) {
						frm.set_value("loyalty_redemption_account", r.message.expense_account);
						frm.set_value("loyalty_redemption_cost_center", r.message.cost_center);
						frm.redemption_conversion_factor = r.message.conversion_factor;
					}
				}
			});
		}
	},

	set_loyalty_points: function(frm) {
		if (frm.redemption_conversion_factor) {
			let loyalty_amount = flt(frm.redemption_conversion_factor*flt(frm.doc.loyalty_points), precision("loyalty_amount"));
			var remaining_amount = flt(frm.doc.grand_total) - flt(frm.doc.total_advance) - flt(frm.doc.write_off_amount);
			if (frm.doc.grand_total && (remaining_amount < loyalty_amount)) {
				let redeemable_points = parseInt(remaining_amount/frm.redemption_conversion_factor);
				frappe.throw(__("You can only redeem max {0} points in this order.",[redeemable_points]));
			}
			frm.set_value("loyalty_amount", loyalty_amount);
		}
	},

	// Healthcare
	patient: function(frm) {
		if (frappe.boot.active_domains.includes("Healthcare")){
			if(frm.doc.patient){
				frappe.call({
					method: "frappe.client.get_value",
					args:{
						doctype: "Patient",
						filters: {
							"name": frm.doc.patient
						},
						fieldname: "customer"
					},
					callback:function(r) {
						if(r && r.message.customer){
							frm.set_value("customer", r.message.customer);
						}
					}
				});
			}
		}
	},

	project: function(frm) {
		if (frm.doc.project) {
			frm.events.add_timesheet_data(frm, {
				project: frm.doc.project
			});
		}
	},

	async add_timesheet_data(frm, kwargs) {
		if (kwargs === "Sales Invoice") {
			// called via frm.trigger()
			kwargs = Object();
		}

		if (!kwargs.hasOwnProperty("project") && frm.doc.project) {
			kwargs.project = frm.doc.project;
		}

		const timesheets = await frm.events.get_timesheet_data(frm, kwargs);
		return frm.events.set_timesheet_data(frm, timesheets);
	},

	async get_timesheet_data(frm, kwargs) {
		return frappe.call({
			method: "erpnext.projects.doctype.timesheet.timesheet.get_projectwise_timesheet_data",
			args: kwargs
		}).then(r => {
			if (!r.exc && r.message.length > 0) {
				return r.message
			} else {
				return []
			}
		});
	},

	set_timesheet_data: function(frm, timesheets) {
		frm.clear_table("timesheets")
		timesheets.forEach(async (timesheet) => {
			if (frm.doc.currency != timesheet.currency) {
				const exchange_rate = await frm.events.get_exchange_rate(
					frm, timesheet.currency, frm.doc.currency
				)
				frm.events.append_time_log(frm, timesheet, exchange_rate)
			} else {
				frm.events.append_time_log(frm, timesheet, 1.0);
			}
		});
	},

	async get_exchange_rate(frm, from_currency, to_currency) {
		if (
			frm.exchange_rates
			&& frm.exchange_rates[from_currency]
			&& frm.exchange_rates[from_currency][to_currency]
		) {
			return frm.exchange_rates[from_currency][to_currency];
		}

		return frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency,
				to_currency
			},
			callback: function(r) {
				if (r.message) {
					// cache exchange rates
					frm.exchange_rates = frm.exchange_rates || {};
					frm.exchange_rates[from_currency] = frm.exchange_rates[from_currency] || {};
					frm.exchange_rates[from_currency][to_currency] = r.message;
				}
			}
		});
	},

	append_time_log: function(frm, time_log, exchange_rate) {
		const row = frm.add_child("timesheets");
		row.activity_type = time_log.activity_type;
		row.description = time_log.description;
		row.time_sheet = time_log.time_sheet;
		row.from_time = time_log.from_time;
		row.to_time = time_log.to_time;
		row.billing_hours = time_log.billing_hours;
		row.billing_amount = flt(time_log.billing_amount) * flt(exchange_rate);
		row.timesheet_detail = time_log.name;
		row.project_name = time_log.project_name;

		frm.refresh_field("timesheets");
		frm.trigger("calculate_timesheet_totals");
	},

	calculate_timesheet_totals: function(frm) {
		frm.set_value("total_billing_amount",
			frm.doc.timesheets.reduce((a, b) => a + (b["billing_amount"] || 0.0), 0.0));
		frm.set_value("total_billing_hours",
			frm.doc.timesheets.reduce((a, b) => a + (b["billing_hours"] || 0.0), 0.0));
	},

	refresh: function(frm) {
		// frappe.msgprint("sadasdsa")

		cur_frm.set_value("update_stock",1)
		cur_frm.refresh_fields("update_stock")
		if(frm.doc.__islocal){
			frappe.db.get_value("Sales Taxes and Charges Template", {"is_default":1}, ["name"])
			.then((r) => {
				if (r.message) {
					cur_frm.set_value("taxes_and_charges","");
					cur_frm.set_value("taxes_and_charges",r.message.name);
					
				}
			});
		};
		cur_frm.refresh_fields("taxes");
		cur_frm.add_fetch('pemilik',  'territory',  'territory_real');
		cur_frm.add_fetch('pemilik',  'territory',  'territory_biaya');
		// frappe.msgprint("test 123")
		cur_frm.set_query("no_rangka", function() {
			var wh = ''
			/*if(cur_frm.doc.territory == 'All Territories'){
				wh = "Stores"+ " - "+cur_frm.doc.company
			}else{
				wh = cur_frm.doc.territory+" - "+cur_frm.doc.company
			}*/
			return {
				filters: {
					"item_code": cur_frm.doc.item_code,
					"warehouse": cur_frm.doc.set_warehouse,
					"status": "Active"
				}
			};

		});

		if (frm.doc.docstatus===0 && !frm.doc.is_return) {
			frm.add_custom_button(__("Fetch Timesheet"), function() {
				let d = new frappe.ui.Dialog({
					title: __("Fetch Timesheet"),
					fields: [
						{
							"label" : __("From"),
							"fieldname": "from_time",
							"fieldtype": "Date",
							"reqd": 1,
						},
						{
							fieldtype: "Column Break",
							fieldname: "col_break_1",
						},
						{
							"label" : __("To"),
							"fieldname": "to_time",
							"fieldtype": "Date",
							"reqd": 1,
						},
						{
							"label" : __("Project"),
							"fieldname": "project",
							"fieldtype": "Link",
							"options": "Project",
							"default": frm.doc.project
						},
					],
					primary_action: function() {
						const data = d.get_values();
						frm.events.add_timesheet_data(frm, {
							from_time: data.from_time,
							to_time: data.to_time,
							project: data.project
						});
						d.hide();
					},
					primary_action_label: __("Get Timesheets")
				});
				d.show();
			});
		}

		if (frm.doc.is_debit_note) {
			frm.set_df_property('return_against', 'label', __('Adjustment Against'));
		}

		if (frappe.boot.active_domains.includes("Healthcare")) {
			frm.set_df_property("patient", "hidden", 0);
			frm.set_df_property("patient_name", "hidden", 0);
			frm.set_df_property("ref_practitioner", "hidden", 0);
			if (cint(frm.doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !frm.doc.is_return) {
				frm.add_custom_button(__('Healthcare Services'), function() {
					get_healthcare_services_to_invoice(frm);
				},__("Get Items From"));
				frm.add_custom_button(__('Prescriptions'), function() {
					get_drugs_to_invoice(frm);
				},__("Get Items From"));
			}
		}
		else {
			frm.set_df_property("patient", "hidden", 1);
			frm.set_df_property("patient_name", "hidden", 1);
			frm.set_df_property("ref_practitioner", "hidden", 1);
		}
	},

	create_invoice_discounting: function(frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.create_invoice_discounting",
			frm: frm
		});
	},

	create_dunning: function(frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.create_dunning",
			frm: frm
		});
	}
});


frappe.ui.form.on("Sales Invoice Timesheet", {
	timesheets_remove(frm) {
		frm.trigger("calculate_timesheet_totals");
	}
});


var set_timesheet_detail_rate = function(cdt, cdn, currency, timelog) {
	frappe.call({
		method: "erpnext.projects.doctype.timesheet.timesheet.get_timesheet_detail_rate",
		args: {
			timelog: timelog,
			currency: currency
		},
		callback: function(r) {
			if (!r.exc && r.message) {
				frappe.model.set_value(cdt, cdn, 'billing_amount', r.message);
			}
		}
	});
}

var select_loyalty_program = function(frm, loyalty_programs) {
	var dialog = new frappe.ui.Dialog({
		title: __("Select Loyalty Program"),
		fields: [
			{
				"label": __("Loyalty Program"),
				"fieldname": "loyalty_program",
				"fieldtype": "Select",
				"options": loyalty_programs,
				"default": loyalty_programs[0]
			}
		]
	});

	dialog.set_primary_action(__("Set Loyalty Program"), function() {
		dialog.hide();
		return frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "Customer",
				name: frm.doc.customer,
				fieldname: "loyalty_program",
				value: dialog.get_value("loyalty_program"),
			},
			callback: function(r) { }
		});
	});

	dialog.show();
}

// Healthcare
var get_healthcare_services_to_invoice = function(frm) {
	var me = this;
	let selected_patient = '';
	var dialog = new frappe.ui.Dialog({
		title: __("Get Items from Healthcare Services"),
		fields:[
			{
				fieldtype: 'Link',
				options: 'Patient',
				label: 'Patient',
				fieldname: "patient",
				reqd: true
			},
			{ fieldtype: 'Section Break'	},
			{ fieldtype: 'HTML', fieldname: 'results_area' }
		]
	});
	var $wrapper;
	var $results;
	var $placeholder;
	dialog.set_values({
		'patient': frm.doc.patient
	});
	dialog.fields_dict["patient"].df.onchange = () => {
		var patient = dialog.fields_dict.patient.input.value;
		if(patient && patient!=selected_patient){
			selected_patient = patient;
			var method = "erpnext.healthcare.utils.get_healthcare_services_to_invoice";
			var args = {patient: patient, company: frm.doc.company};
			var columns = (["service", "reference_name", "reference_type"]);
			get_healthcare_items(frm, true, $results, $placeholder, method, args, columns);
		}
		else if(!patient){
			selected_patient = '';
			$results.empty();
			$results.append($placeholder);
		}
	}
	$wrapper = dialog.fields_dict.results_area.$wrapper.append(`<div class="results"
		style="border: 1px solid #d1d8dd; border-radius: 3px; height: 300px; overflow: auto;"></div>`);
	$results = $wrapper.find('.results');
	$placeholder = $(`<div class="multiselect-empty-state">
				<span class="text-center" style="margin-top: -40px;">
					<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
					<p class="text-extra-muted">No billable Healthcare Services found</p>
				</span>
			</div>`);
	$results.on('click', '.list-item--head :checkbox', (e) => {
		$results.find('.list-item-container .list-row-check')
			.prop("checked", ($(e.target).is(':checked')));
	});
	set_primary_action(frm, dialog, $results, true);
	dialog.show();
};

var get_healthcare_items = function(frm, invoice_healthcare_services, $results, $placeholder, method, args, columns) {
	var me = this;
	$results.empty();
	frappe.call({
		method: method,
		args: args,
		callback: function(data) {
			if(data.message){
				$results.append(make_list_row(columns, invoice_healthcare_services));
				for(let i=0; i<data.message.length; i++){
					$results.append(make_list_row(columns, invoice_healthcare_services, data.message[i]));
				}
			}else {
				$results.append($placeholder);
			}
		}
	});
}

var make_list_row= function(columns, invoice_healthcare_services, result={}) {
	var me = this;
	// Make a head row by default (if result not passed)
	let head = Object.keys(result).length === 0;
	let contents = ``;
	columns.forEach(function(column) {
		contents += `<div class="list-item__content ellipsis">
			${
				head ? `<span class="ellipsis">${__(frappe.model.unscrub(column))}</span>`

				:(column !== "name" ? `<span class="ellipsis">${__(result[column])}</span>`
					: `<a class="list-id ellipsis">
						${__(result[column])}</a>`)
			}
		</div>`;
	})

	let $row = $(`<div class="list-item">
		<div class="list-item__content" style="flex: 0 0 10px;">
			<input type="checkbox" class="list-row-check" ${result.checked ? 'checked' : ''}>
		</div>
		${contents}
	</div>`);

	$row = list_row_data_items(head, $row, result, invoice_healthcare_services);
	return $row;
};

var set_primary_action= function(frm, dialog, $results, invoice_healthcare_services) {
	var me = this;
	dialog.set_primary_action(__('Add'), function() {
		let checked_values = get_checked_values($results);
		if(checked_values.length > 0){
			if(invoice_healthcare_services) {
				frm.set_value("patient", dialog.fields_dict.patient.input.value);
			}
			frm.set_value("items", []);
			add_to_item_line(frm, checked_values, invoice_healthcare_services);
			dialog.hide();
		}
		else{
			if(invoice_healthcare_services){
				frappe.msgprint(__("Please select Healthcare Service"));
			}
			else{
				frappe.msgprint(__("Please select Drug"));
			}
		}
	});
};

var get_checked_values= function($results) {
	return $results.find('.list-item-container').map(function() {
		let checked_values = {};
		if ($(this).find('.list-row-check:checkbox:checked').length > 0 ) {
			checked_values['dn'] = $(this).attr('data-dn');
			checked_values['dt'] = $(this).attr('data-dt');
			checked_values['item'] = $(this).attr('data-item');
			if($(this).attr('data-rate') != 'undefined'){
				checked_values['rate'] = $(this).attr('data-rate');
			}
			else{
				checked_values['rate'] = false;
			}
			if($(this).attr('data-income-account') != 'undefined'){
				checked_values['income_account'] = $(this).attr('data-income-account');
			}
			else{
				checked_values['income_account'] = false;
			}
			if($(this).attr('data-qty') != 'undefined'){
				checked_values['qty'] = $(this).attr('data-qty');
			}
			else{
				checked_values['qty'] = false;
			}
			if($(this).attr('data-description') != 'undefined'){
				checked_values['description'] = $(this).attr('data-description');
			}
			else{
				checked_values['description'] = false;
			}
			return checked_values;
		}
	}).get();
};

var get_drugs_to_invoice = function(frm) {
	var me = this;
	let selected_encounter = '';
	var dialog = new frappe.ui.Dialog({
		title: __("Get Items from Prescriptions"),
		fields:[
			{ fieldtype: 'Link', options: 'Patient', label: 'Patient', fieldname: "patient", reqd: true },
			{ fieldtype: 'Link', options: 'Patient Encounter', label: 'Patient Encounter', fieldname: "encounter", reqd: true,
				description:'Quantity will be calculated only for items which has "Nos" as UoM. You may change as required for each invoice item.',
				get_query: function(doc) {
					return {
						filters: {
							patient: dialog.get_value("patient"),
							company: frm.doc.company,
							docstatus: 1
						}
					};
				}
			},
			{ fieldtype: 'Section Break' },
			{ fieldtype: 'HTML', fieldname: 'results_area' }
		]
	});
	var $wrapper;
	var $results;
	var $placeholder;
	dialog.set_values({
		'patient': frm.doc.patient,
		'encounter': ""
	});
	dialog.fields_dict["encounter"].df.onchange = () => {
		var encounter = dialog.fields_dict.encounter.input.value;
		if(encounter && encounter!=selected_encounter){
			selected_encounter = encounter;
			var method = "erpnext.healthcare.utils.get_drugs_to_invoice";
			var args = {encounter: encounter};
			var columns = (["drug_code", "quantity", "description"]);
			get_healthcare_items(frm, false, $results, $placeholder, method, args, columns);
		}
		else if(!encounter){
			selected_encounter = '';
			$results.empty();
			$results.append($placeholder);
		}
	}
	$wrapper = dialog.fields_dict.results_area.$wrapper.append(`<div class="results"
		style="border: 1px solid #d1d8dd; border-radius: 3px; height: 300px; overflow: auto;"></div>`);
	$results = $wrapper.find('.results');
	$placeholder = $(`<div class="multiselect-empty-state">
				<span class="text-center" style="margin-top: -40px;">
					<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
					<p class="text-extra-muted">No Drug Prescription found</p>
				</span>
			</div>`);
	$results.on('click', '.list-item--head :checkbox', (e) => {
		$results.find('.list-item-container .list-row-check')
			.prop("checked", ($(e.target).is(':checked')));
	});
	set_primary_action(frm, dialog, $results, false);
	dialog.show();
};

var list_row_data_items = function(head, $row, result, invoice_healthcare_services) {
	if(invoice_healthcare_services){
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
				data-dn= "${result.reference_name}" data-dt= "${result.reference_type}" data-item= "${result.service}"
				data-rate = ${result.rate}
				data-income-account = "${result.income_account}"
				data-qty = ${result.qty}
				data-description = "${result.description}">
				</div>`).append($row);
	}
	else{
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
				data-item= "${result.drug_code}"
				data-qty = ${result.quantity}
				data-description = "${result.description}">
				</div>`).append($row);
	}
	return $row
};

var add_to_item_line = function(frm, checked_values, invoice_healthcare_services){
	if(invoice_healthcare_services){
		frappe.call({
			doc: frm.doc,
			method: "set_healthcare_services",
			args:{
				checked_values: checked_values
			},
			callback: function() {
				frm.trigger("validate");
				frm.refresh_fields();
			}
		});
	}
	else{
		for(let i=0; i<checked_values.length; i++){
			var si_item = frappe.model.add_child(frm.doc, 'Sales Invoice Penjualan Motor Item', 'items');
			frappe.model.set_value(si_item.doctype, si_item.name, 'item_code', checked_values[i]['item']);
			frappe.model.set_value(si_item.doctype, si_item.name, 'qty', 1);
			if(checked_values[i]['qty'] > 1){
				frappe.model.set_value(si_item.doctype, si_item.name, 'qty', parseFloat(checked_values[i]['qty']));
			}
		}
		frm.refresh_fields();
	}
};

var hitung_item_rate = function(frm){
	var ppn_rate = cur_frm.doc.taxes[0]['rate']
	var ppn_div = (100+ppn_rate)/100
	var total_biaya_tanpa_dealer = 0 
	let sum = 0;
	let sum2 = 0;
	
	for (let z = 0; z < cur_frm.doc.tabel_biaya_motor.length; z++) {
		sum += cur_frm.doc.tabel_biaya_motor[z].amount;
		if(cur_frm.doc.tabel_biaya_motor[z].type == "STNK" || cur_frm.doc.tabel_biaya_motor[z].type == "BPKB"){
			total_biaya_tanpa_dealer += cur_frm.doc.tabel_biaya_motor[z].amount;
		}
	}
	cur_frm.set_value("total_biaya",sum)

    var total_diskon_setelah_pajak = 0
	if(cur_frm.doc.table_discount){
		if(cur_frm.doc.table_discount.length > 0){
			for(var i = 0;i<cur_frm.doc.table_discount.length;i++){
				// var diskon_setelah_pajak = Math.ceil(cur_frm.doc.table_discount[i].nominal /ppn_div)
				var diskon_setelah_pajak = cur_frm.doc.table_discount[i].nominal /ppn_div
				total_diskon_setelah_pajak += diskon_setelah_pajak
			}
		}
	}
	
	console.log(total_diskon_setelah_pajak, ' total_diskon_setelah_pajak')

	var total_diskon_leasing_setelah_pajak = 0

	if(cur_frm.doc.table_discount_leasing){
		if(cur_frm.doc.table_discount_leasing.length > 0){
			for(var i =0;i<cur_frm.doc.table_discount_leasing.length;i++){
				// var diskon_leasing_setelah_pajak = Math.ceil(cur_frm.doc.table_discount_leasing[i].nominal /ppn_div)
				var diskon_leasing_setelah_pajak = cur_frm.doc.table_discount_leasing[i].nominal /ppn_div
				total_diskon_leasing_setelah_pajak += diskon_leasing_setelah_pajak
			}
		}
	}
	
	console.log(total_diskon_leasing_setelah_pajak, ' total_diskon_leasing_setelah_pajak')
	// var nominal_diskon_sp = Math.ceil(cur_frm.doc.nominal_diskon / ppn_div)
	var nominal_diskon_sp = cur_frm.doc.nominal_diskon / ppn_div
	console.log(nominal_diskon_sp, ' nominal_diskon_sp')
	var harga_asli = cur_frm.doc.harga - total_biaya_tanpa_dealer - total_diskon_setelah_pajak - total_diskon_leasing_setelah_pajak - nominal_diskon_sp
	
   
    cur_frm.doc.items[0].price_list_rate = harga_asli
    cur_frm.doc.items[0].rate = harga_asli
    cur_frm.doc.items[0].stock_uom_rate = harga_asli
    cur_frm.doc.items[0].serial_no = cur_frm.doc.no_rangka
    cur_frm.doc.items[0].stock_uom_rate
    cur_frm.refresh_fields("items");
    console.log(cur_frm.doc.items, " cur_frm.doc.items[0]xxx")
	
}
