// Copyright (c) 2021, w and contributors
// For license information, please see license.txt


// print heading
//cur_frm.pformat.print_heading = 'Invoice';

{% include 'erpnext/selling/sales_common.js' %};
frappe.provide("erpnext.accounts");
frappe.ui.form.on('Sales Invoice Penjualan Motor Item', {
	item_code: function(doc, cdt, cdn) {
		var me = this;
		var item = frappe.get_doc(cdt, cdn);
		var update_stock = 0, show_batch_dialog = 0;
		if(['Sales Invoice Penjualan Motor'].includes(cur_frm.doc.doctype)) {
			update_stock = cint(cur_frm.doc.update_stock);
			// show_batch_dialog = update_stock;

		} else if((cur_frm.doc.doctype === 'Purchase Receipt' && cur_frm.doc.is_return) ||
			cur_frm.doc.doctype === 'Delivery Note') {
			show_batch_dialog = 1;
		}
		// clear barcode if setting item (else barcode will take priority)
		if (cur_frm.from_barcode == 0) {
			item.barcode = null;
		}
		// this.frm.from_barcode = this.frm.from_barcode - 1 >= 0 ? this.frm.from_barcode - 1 : 0;

		if(item.item_code || item.barcode || item.serial_no) {
			if(!validate_company_and_party()) {
				this.frm.fields_dict["items"].grid.grid_rows[item.idx - 1].remove();
			} else {
				return cur_frm.call({
					method: "erpnext.stock.get_item_details.get_item_details",
					child: item,
					args: {
						doc: cur_frm.doc,
						args: {
							item_code: item.item_code,
							barcode: item.barcode,
							serial_no: item.serial_no,
							batch_no: item.batch_no,
							set_warehouse: cur_frm.doc.set_warehouse,
							warehouse: item.warehouse,
							customer: cur_frm.doc.customer || cur_frm.doc.party_name,
							quotation_to: cur_frm.doc.quotation_to,
							supplier: cur_frm.doc.supplier,
							currency: cur_frm.doc.currency,
							update_stock: update_stock,
							conversion_rate: cur_frm.doc.conversion_rate,
							price_list: cur_frm.doc.selling_price_list || cur_frm.doc.buying_price_list,
							price_list_currency: cur_frm.doc.price_list_currency,
							plc_conversion_rate: cur_frm.doc.plc_conversion_rate,
							company: cur_frm.doc.company,
							order_type: cur_frm.doc.order_type,
							is_pos: cint(cur_frm.doc.is_pos),
							is_return: cint(cur_frm.doc.is_return),
							is_subcontracted: cur_frm.doc.is_subcontracted,
							transaction_date: cur_frm.doc.transaction_date || cur_frm.doc.posting_date,
							ignore_pricing_rule: cur_frm.doc.ignore_pricing_rule,
							doctype: cur_frm.doc.doctype,
							name: cur_frm.doc.name,
							project: item.project || cur_frm.doc.project,
							qty: item.qty || 1,
							stock_qty: item.stock_qty,
							conversion_factor: item.conversion_factor,
							weight_per_unit: item.weight_per_unit,
							weight_uom: item.weight_uom,
							manufacturer: item.manufacturer,
							stock_uom: item.stock_uom,
							pos_profile: cur_frm.doc.doctype == 'Sales Invoice Penjualan Motor' ? cur_frm.doc.pos_profile : '',
							cost_center: item.cost_center,
							tax_category: cur_frm.doc.tax_category,
							item_tax_template: item.item_tax_template,
							child_docname: item.name
						}
					},

					callback: function(r) {
						if(!r.exc) {
							frappe.run_serially([
								() => {
									var d = locals[cdt][cdn];
									add_taxes_from_item_tax_template(d.item_tax_rate);
									if (d.free_item_data) {
										apply_product_discount(d);
									}
								},
								() => {
									// for internal customer instead of pricing rule directly apply valuation rate on item
									if (cur_frm.doc.is_internal_customer || cur_frm.doc.is_internal_supplier) {
										get_incoming_rate(item, cur_frm.posting_date, cur_frm.posting_time,
											cur_frm.doc.doctype, cur_frm.doc.company);
									} else {
										cur_frm.script_manager.trigger("price_list_rate", cdt, cdn);
									}
								},
								() => {
									if (cur_frm.doc.is_internal_customer || cur_frm.doc.is_internal_supplier) {
										calculate_taxes_and_totals();
									}
								},
								() => toggle_conversion_factor(item),
								() => {
									if (show_batch_dialog)
										return frappe.db.get_value("Item", item.item_code, ["has_batch_no", "has_serial_no"])
											.then((r) => {
												if (r.message &&
												(r.message.has_batch_no || r.message.has_serial_no)) {
													frappe.flags.hide_serial_batch_dialog = false;
												}
											});
								},
								() => {
									// check if batch serial selector is disabled or not
									if (show_batch_dialog && !frappe.flags.hide_serial_batch_dialog)
										return frappe.db.get_single_value('Stock Settings', 'disable_serial_no_and_batch_selector')
											.then((value) => {
												if (value) {
													frappe.flags.hide_serial_batch_dialog = true;
												}
											});
								},
								() => {
									if(show_batch_dialog && !frappe.flags.hide_serial_batch_dialog) {
										var d = locals[cdt][cdn];
										$.each(r.message, function(k, v) {
											if(!d[k]) d[k] = v;
										});

										if (d.has_batch_no && d.has_serial_no) {
											d.batch_no = undefined;
										}

										erpnext.show_serial_batch_selector(cur_frm, d, (item) => {
											cur_frm.script_manager.trigger('qty', item.doctype, item.name);
											if (!cur_frm.doc.set_warehouse)
												cur_frm.script_manager.trigger('warehouse', item.doctype, item.name);
										}, undefined, !frappe.flags.hide_serial_batch_dialog);
									}
								},
								() => conversion_factor(doc, cdt, cdn, true),
								() => remove_pricing_rule(item),
								() => {
									if (item.apply_rule_on_other_items) {
										let key = item.name;
										apply_rule_on_other_items({key: item});
									}
								},
								() => console.log(locals[cdt][cdn])
							]);
						}
					}
				});
			}
		}
		cur_frm.refresh_field("items")
	},
	uom: function(doc, cdt, cdn) {
		var me = this;
		var item = frappe.get_doc(cdt, cdn);
		if(item.item_code && item.uom) {
			return cur_frm.call({
				method: "erpnext.stock.get_item_details.get_conversion_factor",
				args: {
					item_code: item.item_code,
					uom: item.uom
				},
				callback: function(r) {
					if(!r.exc) {
						frappe.model.set_value(cdt, cdn, 'conversion_factor', r.message.conversion_factor);
					}
				}
			});
		}
		calculate_stock_uom_rate(doc, cdt, cdn);
	},
	price_list_rate: function(doc, cdt, cdn) {
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["price_list_rate", "discount_percentage"]);

		// check if child doctype is Sales Order Item/Qutation Item and calculate the rate
		if (in_list(["Quotation Item", "Sales Order Item", "Delivery Note Item", "Sales Invoice Item","Sales Invoice Penjualan Motor Item", "POS Invoice Item", "Purchase Invoice Item", "Purchase Order Item", "Purchase Receipt Item"]), cdt)
			apply_pricing_rule_on_item(item);
		else
			item.rate = flt(item.price_list_rate * (1 - item.discount_percentage / 100.0),
				precision("rate", item));

		calculate_taxes_and_totals();
	}
})

frappe.ui.form.on('Sales Invoice Penjualan Motor', {
	
	company: function(frm) {
		erpnext.accounts.dimensions.update_dimension(cur_frm, cur_frm.doctype);
	},
	diskon(frm){
		//cur_frm.set_value("no_rangka","")
		if(cur_frm.doc.diskon==0){
			cur_frm.set_value("nominal_diskon",0)
		}
	},
	nominal_diskon(frm){
		cur_frm.set_value("no_rangka","")
		// var hitung_disc = 0;
		// hitung_disc = cur_frm.doc.harga - cur_frm.doc.nominal_diskon
		// console.log(hitung_disc,"hitung_disc")
		// cur_frm.set_value("harga",hitung_disc)
	},
	territory_real:function(frm){
		cur_frm.set_value("no_rangka","")
		cur_frm.set_value("nama_diskon","")
	},
	territory_biaya:function(frm){
		cur_frm.set_value("no_rangka","")
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
	item_code:function(frm){
		cur_frm.set_value("nama_diskon","")
		//cur_frm.refresh_fields("nama_diskon")
		cur_frm.set_value("no_rangka","")
		//cur_frm.refresh_fields("no_rangka")
	},
	nama_leasing:function(frm){
		/*if(cur_frm.doc.nama_leasing){
			frappe.msgprint("leasing")
		}*/

		// if(cur_frm.doc.cara_bayar == "Credit" && cur_frm.doc.nama_leasing){
	 //    	//frappe.msgprint("test 123wetwet")
	 //    	// let today = frappe.datetime.get_today();
	 //    	let today = cur_frm.doc.posting_date;
		//     frappe.db.get_list('Rule Discount Leasing',{ filters: {'nama_promo':cur_frm.doc.nama_promo,'leasing':cur_frm.doc.nama_leasing,'item_code':cur_frm.doc.item_code,'territory':cur_frm.doc.territory_real,'disable':0}, fields: ['*']})
		// 	.then(data_p => {
		// 		//console.log(data_p,"data_p")
		// 		cur_frm.clear_table("table_discount_leasing");
		// 		cur_frm.refresh_field("table_discount_leasing");
		// 		for (let p = 0; p < data_p.length; p++) {
		// 			if (data_p[p].valid_from <= today && data_p[p].valid_to >= today){
		// 				frappe.db.get_list('Table Discount Leasing',{ filters: { 'parent':  data_p[p].name}, fields: ['*']})
		// 				.then(data => {
		// 					// console.log("wkwkwk");
		// 					cur_frm.clear_table("table_discount_leasing");
		// 					cur_frm.refresh_field("table_discount_leasing");
		// 					for (let i = 0; i < data.length; i++) {
		// 						// if (data[i].valid_from <= today && data[i].valid_to >= today){
		// 							if(data[i].discount == 'Amount'){
		// 								var child_l = cur_frm.add_child("table_discount_leasing");
		// 						        frappe.model.set_value(child_l.doctype, child_l.name, "coa", data[i].coa);
		// 						        frappe.model.set_value(child_l.doctype, child_l.name, "nominal", data[i].amount);
		// 							}
		// 							if(data[i].discount == 'Percent'){
		// 								var amount_b = data[i].percent * cur_frm.doc.harga / 100;
		// 								var child_l2 = cur_frm.add_child("table_discount_leasing");
		// 						        frappe.model.set_value(child_l2.doctype, child_l2.name, "coa", data[i].coa);
		// 						        frappe.model.set_value(child_l2.doctype, child_l2.name, "nominal", amount_b);
		// 							}
									
		// 						/*}else{
		// 							frappe.msgprint("cek vadlidasi tanggal di rule "+data[i].name);
		// 						}*/
		// 					}
		// 					cur_frm.refresh_field("table_discount_leasing");
		// 				});
		// 			}else{
		// 				cur_frm.clear_table("table_discount_leasing");
		// 				cur_frm.refresh_field("table_discount_leasing");
		// 				// frappe.msgprint("cek vadlidasi tanggal di rule "+data_p[p].name);
		// 			}
		// 		}
		// 	});
	    // }
	},
	nama_diskon: function(frm){
		cur_frm.set_value('no_rangka','')
	    //frappe.msgprint("nama_diskon")
	    if(!cur_frm.doc.nama_diskon){
	    	//frappe.msgprint("kosong")
	    	cur_frm.clear_table("table_discount");
			cur_frm.refresh_field("table_discount");
	    }

	    if(cur_frm.doc.nama_diskon){
	    	//frappe.msgprint("isis")
	    	// table_discount
	    	// let today = frappe.datetime.get_today();
	    	let today = cur_frm.doc.posting_date;
	    	// frappe.msgprint(str(today)+"today")
		    frappe.db.get_list('Rule',{ 
		        filters: { 'item_code': cur_frm.doc.item_code, 'territory' : cur_frm.doc.territory_real, 'category_discount': cur_frm.doc.nama_diskon , 'disable': 0 }, fields: ['*']})
	    	    .then(data=>{
	    	    	console.log(data,"data")
	    	        cur_frm.clear_table("table_discount");
					cur_frm.refresh_field("table_discount");
	    	        if(data.length > 0){
						for (let i = 0; i < data.length; i++) {
							if(data[i].disable === 0){
								if (data[i].valid_from <= today && data[i].valid_to >= today){
									if(data[i].discount == 'Amount'){
										var child = cur_frm.add_child("table_discount");
								        frappe.model.set_value(child.doctype, child.name, "rule", data[i].name);
								        frappe.model.set_value(child.doctype, child.name, "customer", data[i].customer);
								        frappe.model.set_value(child.doctype, child.name, "category_discount", data[i].category_discount);
								        frappe.model.set_value(child.doctype, child.name, "coa_receivable", data[i].coa_receivable);
								        frappe.model.set_value(child.doctype, child.name, "nominal", data[i].amount);
									}
									if(data[i].discount == 'Percent'){
										var amount = data[i].percent * cur_frm.doc.harga / 100;
										var child2 = cur_frm.add_child("table_discount");
								        	frappe.model.set_value(child2.doctype, child2.name, "rule", data[i].name);
								        	frappe.model.set_value(child2.doctype, child2.name, "customer", data[i].customer);
								        	frappe.model.set_value(child2.doctype, child2.name, "category_discount", data[i].category_discount);
								        	frappe.model.set_value(child2.doctype, child2.name, "coa_receivable", data[i].coa_receivable);
								        	frappe.model.set_value(child2.doctype, child2.name, "nominal", amount);
									}
								}else{
									// frappe.msgprint("cek vadlidasi tanggal di rule "+data[i].name);
								}
							}
						}
						calculate_taxes_and_totals()
						cur_frm.refresh_field("table_discount");
					}

	    	})
	    }
	    
	},
	/*load_discount: function(frm){
	    
	    frappe.db.get_list('Rule',{ filters: { 'item_code': cur_frm.doc.item_code, 'territory' : cur_frm.doc.territory_real,'disable': 0 }, fields: ['*']})
    	    .then(data=>{
    	        //console.log(data.length)
    	        let v = [];
    	        for(let i = 0; i < data.length; i++){
    	            v.push(data[i].type)
    	            console.log(v)
    	        }
    	        frm.set_df_property('nama_diskon', 'options', v);
    	        cur_frm.refresh_fields("nama_diskon")
    	    })
    	    .catch(error=>{
    	        console.log(error);
    	    })
	},*/
	onload: function(frm) {
		/*if(cur_frm.doc.nama_promo){
    	    if(cur_frm.doc.nama_diskon === ""){
    	        cur_frm.set_value("nama_diskon",cur_frm.doc.nama_diskon);
    	    }else{
    	        cur_frm.trigger("load_discount");
    	    }
    	}*/

		var me = this;
		//this._super();

		cur_frm.ignore_doctypes_on_cancel_all = ['POS Invoice'];
		if(!cur_frm.doc.__islocal && !cur_frm.doc.customer && cur_frm.doc.debit_to) {
			// show debit_to in print format
			cur_frm.set_df_property("debit_to", "print_hide", 0);
		}

		erpnext.queries.setup_queries(cur_frm, "Warehouse", function() {
			return erpnext.queries.warehouse(cur_frm.doc);
		});

		if(cur_frm.doc.__islocal && cur_frm.doc.is_pos) {
			//Load pos profile data on the invoice if the default value of Is POS is 1

			cur_frm.script_manager.trigger("is_pos");
			cur_frm.refresh_fields();
		}
		erpnext.queries.setup_warehouse_query(cur_frm);
		erpnext.accounts.dimensions.setup_dimension_filters(cur_frm, cur_frm.doctype);
		cur_frm.redemption_conversion_factor = null;
		
	},
	refresh: function(doc, dt, dn) {
		const me = this;
		//this._super();
		if(cur_frm.msgbox && cur_frm.msgbox.$wrapper.is(":visible")) {
			// hide new msgbox
			cur_frm.msgbox.hide();
		}

		cur_frm.toggle_reqd("due_date", !cur_frm.doc.is_return);

		if (cur_frm.doc.is_return) {
			cur_frm.return_print_format = "Sales Invoice Return";
		}

		show_general_ledger();

		if(cur_frm.doc.update_stock) show_stock_ledger();

		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount!=0
			&& !(cint(cur_frm.doc.is_return) && cur_frm.doc.return_against)) {
			cur_frm.add_custom_button(__('Payment'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		if(cur_frm.doc.docstatus==1 && !cur_frm.doc.is_return) {

			var is_delivered_by_supplier = false;

			is_delivered_by_supplier = cur_frm.doc.items.some(function(item){
				return item.is_delivered_by_supplier ? true : false;
			})

			if(doc.outstanding_amount >= 0 || Math.abs(flt(doc.outstanding_amount)) < flt(doc.grand_total)) {
				cur_frm.add_custom_button(__('Return / Credit Note'),
					this.make_sales_return, __('Create'));
				cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
			}

			/*if(cint(doc.update_stock)!=1) {
				// show Make Delivery Note button only if Sales Invoice is not created from Delivery Note
				var from_delivery_note = false;
				from_delivery_note = cur_frm.doc.items
					.some(function(item) {
						return item.delivery_note ? true : false;
					});

				if(!from_delivery_note && !is_delivered_by_supplier) {
					cur_frm.add_custom_button(__('Delivery'),
						cur_frm.cscript['Make Delivery Note'], __('Create'));
				}
			}

			if (doc.outstanding_amount>0) {
				cur_frm.add_custom_button(__('Payment Request'), function() {
					me.make_payment_request();
				}, __('Create'));

				cur_frm.add_custom_button(__('Invoice Discounting'), function() {
					cur_frm.events.create_invoice_discounting(cur_frm);
				}, __('Create'));

				if (doc.due_date < frappe.datetime.get_today()) {
					cur_frm.add_custom_button(__('Dunning'), function() {
						cur_frm.events.create_dunning(cur_frm);
					}, __('Create'));
				}
			}

			if (doc.docstatus === 1) {
				cur_frm.add_custom_button(__('Maintenance Schedule'), function () {
					cur_frm.cscript.make_maintenance_schedule();
				}, __('Create'));
			}

			/*if(!doc.auto_repeat) {
				cur_frm.add_custom_button(__('Subscription'), function() {
					erpnext.utils.make_subscription(doc.doctype, doc.name)
				}, __('Create'))
			}*/
		}

		// Show buttons only when pos view is active
		/*if (cint(cur_frm.doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !doc.is_return) {
			sales_order_btn();
			delivery_note_btn();
			quotation_btn();
		}*/

		set_default_print_format();
		if (doc.docstatus == 1 && !doc.inter_company_invoice_reference) {
			let internal = me.frm.doc.is_internal_customer;
			if (internal) {
				let button_label = (me.frm.doc.company === me.frm.doc.represents_company) ? "Internal Purchase Invoice" :
					"Inter Company Purchase Invoice";

				me.frm.add_custom_button(button_label, function() {
					me.make_inter_company_invoice();
				}, __('Create'));
			}
		}
	},
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
	tc_name: function() {
		this.get_terms();
	},
	taxes_and_charges: function() {
		// frappe.msgprint('taxes_and_charges')
		// cur_frm.set_value("taxes_and_charges","PPN 10% - Masukan");
		
		var me = this;
		if(cur_frm.doc.taxes_and_charges) {
			// frappe.msgprint("masuk get_taxes_and_charges")
			cur_frm.clear_table("taxes")
			cur_frm.refresh_field("taxes")
			return cur_frm.call({
				method: "erpnext.controllers.accounts_controller.get_taxes_and_charges",
				args: {
					"master_doctype": frappe.meta.get_docfield(cur_frm.doc.doctype, "taxes_and_charges",
						cur_frm.doc.name).options,
					"master_name": cur_frm.doc.taxes_and_charges
				},
				callback: function(r) {
					if(!r.exc) {
						if(cur_frm.doc.shipping_rule && cur_frm.doc.taxes) {
							for (let tax of r.message) {
								me.frm.add_child("taxes", tax);
							}

							refresh_field("taxes");
						} else {
							// frappe.msgprint("masuk else")
							// console.log(r.message,"message")
							cur_frm.set_value("taxes", r.message);
							calculate_taxes_and_totals();
						}
					}
				}
			});
		}
	},
	customer: function() {
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
	make_inter_company_invoice: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_inter_company_purchase_invoice",
			frm: me.frm
		});
	},
	debit_to: function(frm) {
		var me = this;
		/*if(cur_frm.doc.debit_to) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Account",
					fieldname: "account_currency",
					filters: { name: cur_frm.doc.debit_to },
				},
				callback: function(r, rt) {
					if(r.message) {
						frm.set_value("party_account_currency", r.message.account_currency);
						set_dynamic_labels();
					}
				}
			});
		}*/
		frm.set_value("party_account_currency", "IDR");
	},
	allocated_amount: function() {
		calculate_total_advance();
		cur_frm.refresh_fields();
	},
	write_off_outstanding_amount_automatically: function(frm) {
		if(cint(cur_frm.doc.write_off_outstanding_amount_automatically)) {
			frappe.model.round_floats_in(cur_frm.doc, ["grand_total", "paid_amount"]);
			// this will make outstanding amount 0
			frm.set_value("write_off_amount",
				flt(cur_frm.doc.grand_total - cur_frm.doc.paid_amount - cur_frm.doc.total_advance, precision("write_off_amount"))
			);
			cur_frm.toggle_enable("write_off_amount", false);

		} else {
			cur_frm.toggle_enable("write_off_amount", true);
		}

		calculate_outstanding_amount(false);
		cur_frm.refresh_fields();
	},
	write_off_amount: function() {
		set_in_company_currency(cur_frm.doc, ["write_off_amount"]);
		write_off_outstanding_amount_automatically();
	},
	items_add: function(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		cur_frm.script_manager.copy_from_first_row("items", row, ["income_account", "cost_center"]);
	},
	items_on_form_rendered: function() {
		erpnext.setup_serial_no();
	},
	packed_items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_no();
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
					"company": cur_frm.doc.company
				},
				callback: function(r, rt) {
					frappe.model.set_value(cdt, cdn, "income_account", r.message[0]);
					frappe.model.set_value(cdt, cdn, "cost_center", r.message[1]);
				}
			})
		}
	},
	is_pos: function(frm){
		set_pos_data();
	},
	pos_profile: function() {
		cur_frm.doc.taxes = []
		set_pos_data();
	},
	amount: function(){
		write_off_outstanding_amount_automatically()
	},
	change_amount: function(frm){
		if(cur_frm.doc.paid_amount > cur_frm.doc.grand_total){
			calculate_write_off_amount();
		}else {
			frm.set_value("change_amount", 0.0);
			frm.set_value("base_change_amount", 0.0);
		}

		cur_frm.refresh_fields();
	},
	loyalty_amount: function(){
		calculate_outstanding_amount();
		cur_frm.refresh_field("outstanding_amount");
		cur_frm.refresh_field("paid_amount");
		cur_frm.refresh_field("base_paid_amount");
	}

	,
	validate: function(frm) {
		calculate_total_advance();
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
		calculate_taxes_and_totals()
	},
});

var setup_posting_date_time_check = function(frm) {
	//frappe.msgprint("setup_posting_date_time_check")
	// make posting date default and read only unless explictly checked
	frappe.ui.form.on(cur_frm.doctype, 'set_posting_date_and_time_read_only', function(frm) {
		if(frm.doc.docstatus == 0 && cur_frm.doc.set_posting_time) {
			frm.set_df_property('posting_date', 'read_only', 0);
			frm.set_df_property('posting_time', 'read_only', 0);
		} else {
			frm.set_df_property('posting_date', 'read_only', 1);
			frm.set_df_property('posting_time', 'read_only', 1);
		}
	})

	frappe.ui.form.on(cur_frm.doctype, 'set_posting_time', function(frm) {
		frm.trigger('set_posting_date_and_time_read_only');
	});

	frappe.ui.form.on(cur_frm.doctype, 'refresh', function(frm) {
		// set default posting date / time
		if(cur_frm.doc.docstatus==0) {
			//frappe.msgprint("masuk kosoong")
			if(!cur_frm.doc.posting_date) {
				frm.set_value('posting_date', frappe.datetime.nowdate());
			}
			if(!cur_frm.doc.posting_time) {
				frm.set_value('posting_time', frappe.datetime.now_time());
			}
			frm.trigger('set_posting_date_and_time_read_only');
		}
	});
}

var show_general_ledger= function() {
		var me = this;
		if(cur_frm.doc.docstatus > 0) {
			cur_frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: cur_frm.doc.name,
					from_date: cur_frm.doc.posting_date,
					to_date: moment(cur_frm.doc.modified).format('YYYY-MM-DD'),
					company: cur_frm.doc.company,
					group_by: "Group by Voucher (Consolidated)",
					show_cancelled_entries: cur_frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	}

var set_default_print_format= function() {
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
}

var set_dynamic_labels= function() {
	//  this._super();
	set_product_bundle_help(cur_frm.doc);
}

var set_product_bundle_help= function(doc) {
	if(!cur_frm.fields_dict.packing_list) return;
	if ((doc.packed_items || []).length) {
		$(cur_frm.fields_dict.packing_list.row.wrapper).toggle(true);

		if (in_list(['Delivery Note', 'Sales Invoice','Sales Invoice Penjualan Motor'], doc.doctype)) {
			var help_msg = "<div class='alert alert-warning'>" +
				__("For 'Product Bundle' items, Warehouse, Serial No and Batch No will be considered from the 'Packing List' table. If Warehouse and Batch No are same for all packing items for any 'Product Bundle' item, those values can be entered in the main Item table, values will be copied to 'Packing List' table.")+
			"</div>";
			frappe.meta.get_docfield(doc.doctype, 'product_bundle_help', doc.name).options = help_msg;
		}
	} else {
		$(cur_frm.fields_dict.packing_list.row.wrapper).toggle(false);
		if (in_list(['Delivery Note', 'Sales Invoice'], doc.doctype)) {
			frappe.meta.get_docfield(doc.doctype, 'product_bundle_help', doc.name).options = '';
		}
	}
	refresh_field('product_bundle_help');
}

var calculate_total_advance= function(update_paid_amount) {
	// frappe.msgprint("masuk calculate_total_advance")
	var total_allocated_amount = frappe.utils.sum($.map(cur_frm.doc["advances"] || [], function(adv) {
		return flt(adv.allocated_amount, precision("allocated_amount", adv));
	}));
	// cur_frm.doc.total_advance = flt(total_allocated_amount, precision("total_advance"));
	cur_frm.set_value("total_advance",total_allocated_amount)
	// console.log(total_allocated_amount)
	calculate_outstanding_amount(update_paid_amount);
}

var calculate_outstanding_amount= function(update_paid_amount) {
	// NOTE:
	// paid_amount and write_off_amount is only for POS/Loyalty Point Redemption Invoice
	// total_advance is only for non POS Invoice
	if(in_list(["Sales Invoice", "POS Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype) && cur_frm.doc.is_return){
		calculate_paid_amount();
	}

	if (cur_frm.doc.is_return || (cur_frm.doc.docstatus > 0) || is_internal_invoice()) return;

	frappe.model.round_floats_in(cur_frm.doc, ["grand_total", "total_advance", "write_off_amount"]);

	if(in_list(["Sales Invoice", "POS Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype)) {
		var grand_total = cur_frm.doc.rounded_total || cur_frm.doc.grand_total;

		if(cur_frm.doc.party_account_currency == cur_frm.doc.currency) {
			var total_amount_to_pay = flt((grand_total - cur_frm.doc.total_advance
				- cur_frm.doc.write_off_amount), precision("grand_total"));
		} else {
			var total_amount_to_pay = flt(
				(flt(grand_total*cur_frm.doc.conversion_rate, precision("grand_total"))
					- cur_frm.doc.total_advance - cur_frm.doc.base_write_off_amount),
				precision("base_grand_total")
			);
		}

		frappe.model.round_floats_in(cur_frm.doc, ["paid_amount"]);
		set_in_company_currency(cur_frm.doc, ["paid_amount"]);

		if(cur_frm.refresh_field){
			cur_frm.refresh_field("paid_amount");
			cur_frm.refresh_field("base_paid_amount");
		}

		if(in_list(["Sales Invoice", "POS Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype)) {
			let total_amount_for_payment = (cur_frm.doc.redeem_loyalty_points && cur_frm.doc.loyalty_amount)
				? flt(total_amount_to_pay - cur_frm.doc.loyalty_amount, precision("base_grand_total"))
				: total_amount_to_pay;
			set_default_payment(total_amount_for_payment, update_paid_amount);
			calculate_paid_amount();
		}
		calculate_change_amount();

		var paid_amount = (cur_frm.doc.party_account_currency == cur_frm.doc.currency) ?
			cur_frm.doc.paid_amount : cur_frm.doc.base_paid_amount;
		cur_frm.doc.outstanding_amount =  flt(total_amount_to_pay - flt(paid_amount) +
			flt(cur_frm.doc.change_amount * cur_frm.doc.conversion_rate), precision("outstanding_amount"));
	}
}

var is_internal_invoice = function() {
	if (['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor'].includes(cur_frm.doc.doctype)) {
		if (cur_frm.doc.company === cur_frm.doc.represents_company) {
			return true;
		}
	}
	return false;
}

var calculate_paid_amount= function(frm) {
	var me = this;
	var paid_amount = 0.0;
	var base_paid_amount = 0.0;
	if(cur_frm.doc.is_pos) {
		$.each(cur_frm.doc['payments'] || [], function(index, data){
			data.base_amount = flt(data.amount * cur_frm.doc.conversion_rate, precision("base_amount", data));
			paid_amount += data.amount;
			base_paid_amount += data.base_amount;
		});
	} else if(!cur_frm.doc.is_return){
		cur_frm.doc.payments = [];
	}
	if (cur_frm.doc.redeem_loyalty_points && cur_frm.doc.loyalty_amount) {
		base_paid_amount += cur_frm.doc.loyalty_amount;
		paid_amount += flt(cur_frm.doc.loyalty_amount / cur_frm.doc.conversion_rate, precision("paid_amount"));
	}

	cur_frm.set_value('paid_amount', flt(paid_amount, precision("paid_amount")));
	cur_frm.set_value('base_paid_amount', flt(base_paid_amount, precision("base_paid_amount")));
}

var set_in_company_currency= function(doc, fields) {
	//frappe.msgprint("set_in_company_currency")
	var me = this;
	$.each(fields, function(i, f) {
		doc["base_"+f] = flt(flt(doc[f], precision(f, doc)) * cur_frm.doc.conversion_rate, precision("base_" + f, doc));
	});
}

var set_default_payment= function(total_amount_to_pay, update_paid_amount) {
	var me = this;
	var payment_status = true;
	if(cur_frm.doc.is_pos && (update_paid_amount===undefined || update_paid_amount)) {
		$.each(cur_frm.doc['payments'] || [], function(index, data) {
			if(data.default && payment_status && total_amount_to_pay > 0) {
				let base_amount = flt(total_amount_to_pay, precision("base_amount", data));
				frappe.model.set_value(data.doctype, data.name, "base_amount", base_amount);
				let amount = flt(total_amount_to_pay / cur_frm.doc.conversion_rate, precision("amount", data));
				frappe.model.set_value(data.doctype, data.name, "amount", amount);
				payment_status = false;
			} else if(cur_frm.doc.paid_amount) {
				frappe.model.set_value(data.doctype, data.name, "amount", 0.0);
			}
		});
	}
}

var calculate_change_amount= function(){
	cur_frm.doc.change_amount = 0.0;
	cur_frm.doc.base_change_amount = 0.0;
	if(in_list(["Sales Invoice", "POS Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype)
		&& cur_frm.doc.paid_amount > cur_frm.doc.grand_total && !cur_frm.doc.is_return) {

		var payment_types = $.map(cur_frm.doc.payments, function(d) { return d.type; });
		if (in_list(payment_types, 'Cash')) {
			var grand_total = cur_frm.doc.rounded_total || cur_frm.doc.grand_total;
			var base_grand_total = cur_frm.doc.base_rounded_total || cur_frm.doc.base_grand_total;

			cur_frm.doc.change_amount = flt(cur_frm.doc.paid_amount - grand_total +
				cur_frm.doc.write_off_amount, precision("change_amount"));

			cur_frm.doc.base_change_amount = flt(cur_frm.doc.base_paid_amount -
				base_grand_total + cur_frm.doc.base_write_off_amount,
				precision("base_change_amount"));
		}
	}
}

var set_pos_data= function(frm) {
	// frappe.msgprint('set_pos_data')
	if(cur_frm.doc.is_pos) {
		frm.set_value("allocate_advances_automatically", 0);
		if(!cur_frm.doc.company) {
			frm.set_value("is_pos", 0);
			frappe.msgprint(__("Please specify Company to proceed"));
		} else {
			var me = this;
			return cur_frm.call({
				doc: cur_frm.doc,
				method: "set_missing_values",
				callback: function(r) {
					if(!r.exc) {
						if(r.message && r.message.print_format) {
							cur_frm.pos_print_format = r.message.print_format;
						}
						cur_frm.trigger("update_stock");
						if(cur_frm.doc.taxes_and_charges) {
							cur_frm.script_manager.trigger("taxes_and_charges");
						}

						frappe.model.set_default_values(cur_frm.doc);
						set_dynamic_labels();
						calculate_taxes_and_totals();
					}
				}
			});
		}
	}
	else cur_frm.trigger("refresh");
}

var calculate_taxes_and_totals= function(update_paid_amount) {
	// this.discount_amount_applied = false;
	// frappe.msgprint("masuk calculate_taxes_and_totals")
	var discount_amount_applied = false;
	_calculate_taxes_and_totals();
	calculate_discount_amount();

	// Advance calculation applicable to Sales /Purchase Invoice
	if(in_list(["Sales Invoice", "POS Invoice", "Purchase Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype)
		&& cur_frm.doc.docstatus < 2 && !cur_frm.doc.is_return) {
		calculate_total_advance(update_paid_amount);
	}

	if (in_list(["Sales Invoice", "POS Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype) && cur_frm.doc.is_pos &&
		cur_frm.doc.is_return) {
		update_paid_amount_for_return();
	}

	// Sales person's commission
	if(in_list(["Quotation", "Sales Order", "Delivery Note", "Sales Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype)) {
		calculate_commission();
		calculate_contribution();
	}

	// Update paid amount on return/debit note creation
	if(cur_frm.doc.doctype === "Purchase Invoice" && cur_frm.doc.is_return
		&& (cur_frm.doc.grand_total > cur_frm.doc.paid_amount)) {
		cur_frm.doc.paid_amount = flt(cur_frm.doc.grand_total, precision("grand_total"));
	}

	cur_frm.refresh_fields();
}

var _calculate_taxes_and_totals= function() {
	validate_conversion_rate();
	//calculate_totals();
	calculate_item_values();
	initialize_taxes();
	determine_exclusive_rate();
	calculate_net_total();
	calculate_taxes();
	manipulate_grand_total_for_inclusive_tax();
	calculate_totals();
	_cleanup();
}

var validate_conversion_rate= function() {
	cur_frm.doc.conversion_rate = flt(cur_frm.doc.conversion_rate, (cur_frm) ? precision("conversion_rate") : 9);
	var conversion_rate_label = frappe.meta.get_label(cur_frm.doc.doctype, "conversion_rate",
		cur_frm.doc.name);
	var company_currency = get_company_currency();

	if(!cur_frm.doc.conversion_rate) {
		if(cur_frm.doc.currency == company_currency) {
			frm.set_value("conversion_rate", 1);
		} else {
			const subs =  [conversion_rate_label, cur_frm.doc.currency, company_currency];
			const err_message = __('{0} is mandatory. Maybe Currency Exchange record is not created for {1} to {2}', subs);
			frappe.throw(err_message);
		}
	}
}

var get_company_currency= function() {
	return erpnext.get_currency(cur_frm.doc.company);
}

var calculate_item_values= function() {
	// frappe.msgprint("masuk calculate_item_values")
	var me = this;
	//var discount_amount_applied = false;
	//if (!discount_amount_applied) {
		//frappe.msgprint("hhjhjhjhjhjhhj")
	//edited bobby buang if yang selaliu true

	//edit row 1 dari item agar nilai sama dengan total harga - discount dan ppn
/*	var td = 0
	var tdl = 0
	var biaya = 0
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
        if(cur_frm.doc.tabel_biaya_motor){
                for (let i = 0; i < cur_frm.doc.tabel_biaya_motor.length; i++) {
                        biaya += cur_frm.doc.tabel_biaya_motor[i].amount;
                }
        }
	var adj=0;
        if(!cur_frm.doc.adj_discount){
                adj=0;
        }else{
                adj = cur_frm.doc.adj_discount
        }
	cur_frm.doc.items[0].rate=
**/
	$.each(cur_frm.doc["items"] || [], function(i, item) {
		frappe.model.round_floats_in(item);
		item.net_rate = item.rate;
		if ((!item.qty) && cur_frm.doc.is_return) {
			item.amount = flt(item.rate * -1, precision("amount", item));
		} else {
			item.amount = flt(item.rate * item.qty, precision("amount", item));
		}
		item.net_amount = item.amount;
		//frappe.msgprint("here "+item.amount);
		item.item_tax_amount = 0.0;
		item.total_weight = flt(item.weight_per_unit * item.stock_qty);
		set_in_company_currency(item, ["price_list_rate", "rate", "amount", "net_rate", "net_amount"]);
	});
	//}
}

var validate_inclusive_tax = function(tax) {
	var actual_type_error = function() {
		var msg = __("Actual type tax cannot be included in Item rate in row {0}", [tax.idx])
		frappe.throw(msg);
	};

	var on_previous_row_error = function(row_range) {
		var msg = __("For row {0} in {1}. To include {2} in Item rate, rows {3} must also be included",
			[tax.idx, __(tax.doctype), tax.charge_type, row_range])
		frappe.throw(msg);
	};

	if(cint(tax.included_in_print_rate)) {
		if(tax.charge_type == "Actual") {
			// inclusive tax cannot be of type Actual
			actual_type_error();
		} else if(tax.charge_type == "On Previous Row Amount" &&
			!cint(cur_frm.doc["taxes"][tax.row_id - 1].included_in_print_rate)
		) {
			// referred row should also be an inclusive tax
			on_previous_row_error(tax.row_id);
		} else if(tax.charge_type == "On Previous Row Total") {
			var taxes_not_included = $.map(cur_frm.doc["taxes"].slice(0, tax.row_id),
				function(t) { return cint(t.included_in_print_rate) ? null : t; });
			if(taxes_not_included.length > 0) {
				// all rows above this tax should be inclusive
				on_previous_row_error(tax.row_id == 1 ? "1" : "1 - " + tax.row_id);
			}
		} else if(tax.category == "Valuation") {
			frappe.throw(__("Valuation type charges can not marked as Inclusive"));
		}
	}
}

var initialize_taxes= function() {
	var me = this;
	var discount_amount_applied = false;
	$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
		tax.item_wise_tax_detail = {};
		var tax_fields = ["total", "tax_amount_after_discount_amount",
			"tax_amount_for_current_item", "grand_total_for_current_item",
			"tax_fraction_for_current_item", "grand_total_fraction_for_current_item"];

		if (cstr(tax.charge_type) != "Actual" &&
			!(discount_amount_applied && cur_frm.doc.apply_discount_on=="Grand Total")) {
			tax_fields.push("tax_amount");
		}

		$.each(tax_fields, function(i, fieldname) { tax[fieldname] = 0.0; });

		if (!discount_amount_applied && cur_frm) {
			cur_frm.cscript.validate_taxes_and_charges(tax.doctype, tax.name);
			validate_inclusive_tax(tax);
		}
		frappe.model.round_floats_in(tax);
	});
}

var determine_exclusive_rate= function() {
	var me = this;

	var has_inclusive_tax = false;
	$.each(cur_frm.doc["taxes"] || [], function(i, row) {
		if(cint(row.included_in_print_rate)) has_inclusive_tax = true;
	});
	if(has_inclusive_tax==false) return;

//item always cm 1 bobby
	var total_tax=0;
	$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
		if(cint(tax.included_in_print_rate)){
			total_tax+=tax.tax_amount;
		}
	});
	if(cur_frm.doc["items"][0]){
		var item=cur_frm.doc["items"][0];
		var amount = flt(item.amount) - total_tax;
		item.net_amount = amount;
		item.net_rate = amount;
		set_in_company_currency(item, ["net_rate", "net_amount"]);
	}

/**	$.each(cur_frm.doc["items"] || [], function(n, item) {
		var item_tax_map = _load_item_tax_rate(item.item_tax_rate);
		var cumulated_tax_fraction = 0.0;
		var total_inclusive_tax_amount_per_qty = 0;
		$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
			var current_tax_fraction = get_current_tax_fraction(tax, item_tax_map);
			tax.tax_fraction_for_current_item = current_tax_fraction[0];
			var inclusive_tax_amount_per_qty = current_tax_fraction[1];

			if(i==0) {
				tax.grand_total_fraction_for_current_item = 1 + tax.tax_fraction_for_current_item;
			} else {
				tax.grand_total_fraction_for_current_item =
					cur_frm.doc["taxes"][i-1].grand_total_fraction_for_current_item +
					tax.tax_fraction_for_current_item;
			}

			cumulated_tax_fraction += tax.tax_fraction_for_current_item;
			total_inclusive_tax_amount_per_qty += inclusive_tax_amount_per_qty * flt(item.qty);
		});

		if( item.qty && (total_inclusive_tax_amount_per_qty || cumulated_tax_fraction)) {
			var amount = flt(item.amount) - total_inclusive_tax_amount_per_qty;
			item.net_amount = flt(amount / (1 + cumulated_tax_fraction));
			item.net_rate = item.qty ? flt(item.net_amount / item.qty, precision("net_rate", item)) : 0;

			set_in_company_currency(item, ["net_rate", "net_amount"]);
		}
	});
*/
}

var _load_item_tax_rate= function(item_tax_rate) {
	return item_tax_rate ? JSON.parse(item_tax_rate) : {};
}

var get_current_tax_fraction=  function(tax, item_tax_map) {
	// Get tax fraction for calculating tax exclusive amount
	// from tax inclusive amount
	var current_tax_fraction = 0.0;
	var inclusive_tax_amount_per_qty = 0;

	if(cint(tax.included_in_print_rate)) {
		var tax_rate = _get_tax_rate(tax, item_tax_map);

		if(tax.charge_type == "On Net Total") {
			current_tax_fraction = (tax_rate / 100.0);

		} else if(tax.charge_type == "On Previous Row Amount") {
			current_tax_fraction = (tax_rate / 100.0) *
				cur_frm.doc["taxes"][cint(tax.row_id) - 1].tax_fraction_for_current_item;

		} else if(tax.charge_type == "On Previous Row Total") {
			current_tax_fraction = (tax_rate / 100.0) *
				cur_frm.doc["taxes"][cint(tax.row_id) - 1].grand_total_fraction_for_current_item;
		} else if (tax.charge_type == "On Item Quantity") {
			inclusive_tax_amount_per_qty = flt(tax_rate);
		}
	}

	if(tax.add_deduct_tax && tax.add_deduct_tax == "Deduct") {
		current_tax_fraction *= -1;
		inclusive_tax_amount_per_qty *= -1;
	}
	return [current_tax_fraction, inclusive_tax_amount_per_qty];
}

var _get_tax_rate= function(tax, item_tax_map) {
	return (Object.keys(item_tax_map).indexOf(tax.account_head) != -1) ?
		flt(item_tax_map[tax.account_head], precision("rate", tax)) : tax.rate;
}

var calculate_net_total= function() {
	// frappe.msgprint('Masuk calculate_net_total')
	var me = this;
	cur_frm.doc.total_qty = cur_frm.doc.total = cur_frm.doc.base_total = cur_frm.doc.net_total = cur_frm.doc.base_net_total = 0.0;

	$.each(cur_frm.doc["items"] || [], function(i, item) {
		cur_frm.doc.total += item.amount;
		cur_frm.doc.total_qty += item.qty;
		cur_frm.doc.base_total += item.base_amount;
		cur_frm.doc.net_total += item.net_amount;
		cur_frm.doc.base_net_total += item.base_net_amount;
	});

	frappe.model.round_floats_in(cur_frm.doc, ["total", "base_total", "net_total", "base_net_total"]);
}

var calculate_taxes= function() {
	var me = this;
	cur_frm.doc.rounding_adjustment = 0;
	var actual_tax_dict = {};
	var discount_amount_applied = false;
	// maintain actual tax rate based on idx
	$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
		if (tax.charge_type == "Actual") {
			actual_tax_dict[tax.idx] = flt(tax.tax_amount, precision("tax_amount", tax));
		}
	});

	$.each(cur_frm.doc["items"] || [], function(n, item) {
		var item_tax_map = _load_item_tax_rate(item.item_tax_rate);
		$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
			// tax_amount represents the amount of tax for the current step
			var current_tax_amount = get_current_tax_amount(item, tax, item_tax_map);

			// Adjust divisional loss to the last item
			if (tax.charge_type == "Actual") {
				actual_tax_dict[tax.idx] -= current_tax_amount;
				if (n == cur_frm.doc["items"].length - 1) {
					current_tax_amount += actual_tax_dict[tax.idx];
				}
			}

			// accumulate tax amount into tax.tax_amount
			if (tax.charge_type != "Actual" &&
				!(discount_amount_applied && cur_frm.doc.apply_discount_on=="Grand Total")) {
				tax.tax_amount += current_tax_amount;
			}

			// store tax_amount for current item as it will be used for
			// charge type = 'On Previous Row Amount'
			tax.tax_amount_for_current_item = current_tax_amount;

			// tax amount after discount amount
			tax.tax_amount_after_discount_amount += current_tax_amount;

			// for buying
			if(tax.category) {
				// if just for valuation, do not add the tax amount in total
				// hence, setting it as 0 for further steps
				current_tax_amount = (tax.category == "Valuation") ? 0.0 : current_tax_amount;

				current_tax_amount *= (tax.add_deduct_tax == "Deduct") ? -1.0 : 1.0;
			}

			// note: grand_total_for_current_item contains the contribution of
			// item's amount, previously applied tax and the current tax on that item
			if(i==0) {
				tax.grand_total_for_current_item = flt(item.net_amount + current_tax_amount);
			} else {
				tax.grand_total_for_current_item =
					flt(cur_frm.doc["taxes"][i-1].grand_total_for_current_item + current_tax_amount);
			}

			// set precision in the last item iteration
			if (n == cur_frm.doc["items"].length - 1) {
				round_off_totals(tax);

				// in tax.total, accumulate grand total for each item
				set_cumulative_total(i, tax);

				set_in_company_currency(tax,
					["total", "tax_amount", "tax_amount_after_discount_amount"]);

				// adjust Discount Amount loss in last tax iteration
				if ((i == cur_frm.doc["taxes"].length - 1) && discount_amount_applied
					&& cur_frm.doc.apply_discount_on == "Grand Total" && cur_frm.doc.discount_amount) {
					cur_frm.doc.rounding_adjustment = flt(cur_frm.doc.grand_total -
						flt(cur_frm.doc.discount_amount) - tax.total, precision("rounding_adjustment"));
				}
			}
		});
	});
}

var get_current_tax_amount= function(item, tax, item_tax_map) {
	var tax_rate = _get_tax_rate(tax, item_tax_map);
	var current_tax_amount = 0.0;
	// console.log(tax_rate,"tax_rate")
	// To set row_id by default as previous row.
	if(["On Previous Row Amount", "On Previous Row Total"].includes(tax.charge_type)) {
		if (tax.idx === 1) {
			frappe.throw(
				__("Cannot select charge type as 'On Previous Row Amount' or 'On Previous Row Total' for first row"));
		}
		if (!tax.row_id) {
			tax.row_id = tax.idx - 1;
		}
	}
	if(tax.charge_type == "Actual") {
		// distribute the tax amount proportionally to each item row
		var actual = flt(tax.tax_amount, precision("tax_amount", tax));
		current_tax_amount = this.frm.doc.net_total ?
			((item.net_amount / this.frm.doc.net_total) * actual) : 0.0;

	} else if(tax.charge_type == "On Net Total") {
		// frappe.msgprint("masyk pajak")
		current_tax_amount = (tax_rate / 100.0) * item.net_amount;
	} else if(tax.charge_type == "On Previous Row Amount") {
		current_tax_amount = (tax_rate / 100.0) *
			this.frm.doc["taxes"][cint(tax.row_id) - 1].tax_amount_for_current_item;

	} else if(tax.charge_type == "On Previous Row Total") {
		current_tax_amount = (tax_rate / 100.0) *
			this.frm.doc["taxes"][cint(tax.row_id) - 1].grand_total_for_current_item;
	} else if (tax.charge_type == "On Item Quantity") {
		current_tax_amount = tax_rate * item.qty;
	}

	current_tax_amount = get_final_tax_amount(tax, current_tax_amount);
	set_item_wise_tax(item, tax, tax_rate, current_tax_amount);
	// console.log(current_tax_amount,"current_tax_amount")
	return current_tax_amount;
}

var get_final_tax_amount= function(tax, current_tax_amount) {
	//if (frappe.flags.round_off_applicable_accounts.includes(tax.account_head)) {
	if (tax.account_head == frappe.flags.round_off_applicable_accounts) {
		current_tax_amount = Math.round(current_tax_amount);
	}

	return current_tax_amount;
}

var set_item_wise_tax= function(item, tax, tax_rate, current_tax_amount) {
	// store tax breakup for each item
	let tax_detail = tax.item_wise_tax_detail;
	let key = item.item_code || item.item_name;

	let item_wise_tax_amount = current_tax_amount * cur_frm.doc.conversion_rate;
	if (tax_detail && tax_detail[key])
		item_wise_tax_amount += tax_detail[key][1];

	tax_detail[key] = [tax_rate, flt(item_wise_tax_amount, precision("base_tax_amount", tax))];
}

var round_off_totals= function(tax) {
	tax.tax_amount = flt(tax.tax_amount, precision("tax_amount", tax));
	tax.tax_amount_after_discount_amount = flt(tax.tax_amount_after_discount_amount, precision("tax_amount", tax));
}

var set_cumulative_total= function(row_idx, tax) {
	var tax_amount = tax.tax_amount_after_discount_amount;
	if (tax.category == 'Valuation') {
		tax_amount = 0;
	}

	if (tax.add_deduct_tax == "Deduct") { tax_amount = -1*tax_amount; }

	if(row_idx==0) {
		//frappe.msgprint("tax bener")
		tax.total = flt(cur_frm.doc.net_total + tax_amount, precision("total", tax));
	} else {
		// frappe.msgprint("tax salah")
		tax.total = flt(cur_frm.doc["taxes"][row_idx-1].total + tax_amount, precision("total", tax));
	}
	console.log(tax.total,"tax.total")
	console.log(tax_amount,"tax_amount")
}

var manipulate_grand_total_for_inclusive_tax= function() {
	var me = this;
	// if fully inclusive taxes and diff
	if (cur_frm.doc["taxes"] && cur_frm.doc["taxes"].length) {
		var any_inclusive_tax = false;
		$.each(cur_frm.doc.taxes || [], function(i, d) {
			if(cint(d.included_in_print_rate)) any_inclusive_tax = true;
		});
		if (any_inclusive_tax) {
			var last_tax = cur_frm.doc["taxes"].slice(-1)[0];
			var non_inclusive_tax_amount = frappe.utils.sum($.map(cur_frm.doc.taxes || [],
				function(d) {
					if(!d.included_in_print_rate) {
						return flt(d.tax_amount_after_discount_amount);
					}
				}
			));
			var diff = cur_frm.doc.total + non_inclusive_tax_amount
				- flt(last_tax.total, precision("grand_total"));

			if( cur_frm.doc.discount_amount) {
				diff -= flt(cur_frm.doc.discount_amount);
			}

			diff = flt(diff, precision("rounding_adjustment"));

			if ( diff && Math.abs(diff) <= (5.0 / Math.pow(10, precision("tax_amount", last_tax))) ) {
				cur_frm.doc.rounding_adjustment = diff;
			}
		}
	}
}

var calculate_totals= function() {
	// Changing sequence can cause rounding_adjustmentng issue and on-screen discrepency
	// frappe.msgprint("masuk calculate_totals")
	var td = 0
	var tdl = 0
	var biaya = 0
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
	if(cur_frm.doc.tabel_biaya_motor){
		for (let i = 0; i < cur_frm.doc.tabel_biaya_motor.length; i++) {
			biaya += cur_frm.doc.tabel_biaya_motor[i].amount;
		}
	}
	if(!cur_frm.doc.adj_discount){
		var adj=0
	}else{
		adj = cur_frm.doc.adj_discount
	}
	var oa =0
	oa = (cur_frm.doc.harga - td - tdl) + adj
	//console.log(oa)
	//console.log(biaya)
	//cur_frm.doc.items[0].rate=oa;
	var me = this;
	var tax_count = cur_frm.doc["taxes"] ? cur_frm.doc["taxes"].length : 0;
	cur_frm.doc.grand_total = oa
	/*cur_frm.doc.grand_total = flt(tax_count
		? cur_frm.doc["taxes"][tax_count - 1].total + flt(cur_frm.doc.rounding_adjustment)
		: cur_frm.doc.net_total);*/

	if(in_list(["Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "POS Invoice","Sales Invoice Penjualan Motor"], cur_frm.doc.doctype)) {
		// frappe.msgprint("masuk sini untuk total")
		cur_frm.doc.base_grand_total = (cur_frm.doc.total_taxes_and_charges) ?
			flt(cur_frm.doc.grand_total * cur_frm.doc.conversion_rate) : cur_frm.doc.base_net_total;
	} else {
		// frappe.msgprint("masuk sini untuk total salah")
		// other charges added/deducted
		cur_frm.doc.taxes_and_charges_added = cur_frm.doc.taxes_and_charges_deducted = 0.0;
		if(tax_count) {
			// frappe.msgprint("masuk sini untuk total salah1")
			$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
				if (in_list(["Valuation and Total", "Total"], tax.category)) {
					if(tax.add_deduct_tax == "Add") {
						cur_frm.doc.taxes_and_charges_added += flt(tax.tax_amount_after_discount_amount);
					} else {
						cur_frm.doc.taxes_and_charges_deducted += flt(tax.tax_amount_after_discount_amount);
					}
				}
			});

			frappe.model.round_floats_in(cur_frm.doc,
				["taxes_and_charges_added", "taxes_and_charges_deducted"]);
		}

		// frappe.msgprint("masuk sini untuk total salah2")
		cur_frm.doc.base_grand_total = flt((cur_frm.doc.taxes_and_charges_added || cur_frm.doc.taxes_and_charges_deducted) ?
			flt(cur_frm.doc.grand_total * cur_frm.doc.conversion_rate) : cur_frm.doc.base_net_total);

		set_in_company_currency(this.frm.doc,
			["taxes_and_charges_added", "taxes_and_charges_deducted"]);
	}
	// frappe.msgprint("masuk sini untuk total salah3")
	cur_frm.doc.total_taxes_and_charges = cur_frm.doc.harga - biaya;
	/*cur_frm.doc.total_taxes_and_charges = flt(cur_frm.doc.grand_total - cur_frm.doc.net_total
		- flt(cur_frm.doc.rounding_adjustment), precision("total_taxes_and_charges"));*/
	set_in_company_currency(cur_frm.doc, ["total_taxes_and_charges", "rounding_adjustment"]);
	//bobby coba ubah di sini ratenya
	//cur_frm.doc.items[0].rate=oa-cur_frm.doc.total_taxes_and_charges;
	//failed
	// Round grand total as per precision
	frappe.model.round_floats_in(cur_frm.doc, ["grand_total", "base_grand_total"]);

	// rounded totals
	set_rounded_total();
}

var set_rounded_total= function() {
	var disable_rounded_total = 0;
	if(frappe.meta.get_docfield(cur_frm.doc.doctype, "disable_rounded_total", cur_frm.doc.name)) {
		disable_rounded_total = cur_frm.doc.disable_rounded_total;
	} else if (frappe.sys_defaults.disable_rounded_total) {
		disable_rounded_total = frappe.sys_defaults.disable_rounded_total;
	}

	if (cint(disable_rounded_total)) {
		cur_frm.doc.rounded_total = 0;
		cur_frm.doc.base_rounded_total = 0;
		return;
	}

	if(frappe.meta.get_docfield(cur_frm.doc.doctype, "rounded_total", cur_frm.doc.name)) {
		cur_frm.doc.rounded_total = round_based_on_smallest_currency_fraction(cur_frm.doc.grand_total,
			cur_frm.doc.currency, precision("rounded_total"));
		cur_frm.doc.rounding_adjustment += flt(cur_frm.doc.rounded_total - cur_frm.doc.grand_total,
			precision("rounding_adjustment"));

		set_in_company_currency(cur_frm.doc, ["rounding_adjustment", "rounded_total"]);
	}
}

var _cleanup= function() {
	cur_frm.doc.base_in_words = cur_frm.doc.in_words = "";

	if(cur_frm.doc["items"] && cur_frm.doc["items"].length) {
		if(!frappe.meta.get_docfield(cur_frm.doc["items"][0].doctype, "item_tax_amount", cur_frm.doctype)) {
			$.each(cur_frm.doc["items"] || [], function(i, item) {
				delete item["item_tax_amount"];
			});
		}
	}

	if(cur_frm.doc["taxes"] && cur_frm.doc["taxes"].length) {
		var temporary_fields = ["tax_amount_for_current_item", "grand_total_for_current_item",
			"tax_fraction_for_current_item", "grand_total_fraction_for_current_item"];

		if(!frappe.meta.get_docfield(cur_frm.doc["taxes"][0].doctype, "tax_amount_after_discount_amount", cur_frm.doctype)) {
			temporary_fields.push("tax_amount_after_discount_amount");
		}

		$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
			$.each(temporary_fields, function(i, fieldname) {
				delete tax[fieldname];
			});

			tax.item_wise_tax_detail = JSON.stringify(tax.item_wise_tax_detail);
		});
	}
}

var calculate_discount_amount= function(){
	if (frappe.meta.get_docfield(cur_frm.doc.doctype, "discount_amount")) {
		set_discount_amount();
		apply_discount_amount();
	}
}

var set_discount_amount= function() {
	if(cur_frm.doc.additional_discount_percentage) {
		cur_frm.doc.discount_amount = flt(flt(cur_frm.doc[frappe.scrub(cur_frm.doc.apply_discount_on)])
			* cur_frm.doc.additional_discount_percentage / 100, precision("discount_amount"));
	}
}

var apply_discount_amount= function() {
	var me = this;
	var distributed_amount = 0.0;
	cur_frm.doc.base_discount_amount = 0.0;

	if (cur_frm.doc.discount_amount) {
		if(!cur_frm.doc.apply_discount_on)
			frappe.throw(__("Please select Apply Discount On"));

		cur_frm.doc.base_discount_amount = flt(cur_frm.doc.discount_amount * cur_frm.doc.conversion_rate,
			precision("base_discount_amount"));

		var total_for_discount_amount = get_total_for_discount_amount();
		var net_total = 0;
		// calculate item amount after Discount Amount
		if (total_for_discount_amount) {
			$.each(cur_frm.doc["items"] || [], function(i, item) {
				distributed_amount = flt(cur_frm.doc.discount_amount) * item.net_amount / total_for_discount_amount;
				item.net_amount = flt(item.net_amount - distributed_amount,
					precision("base_amount", item));
				net_total += item.net_amount;

				// discount amount rounding loss adjustment if no taxes
				if ((!(cur_frm.doc.taxes || []).length || total_for_discount_amount==cur_frm.doc.net_total || (cur_frm.doc.apply_discount_on == "Net Total"))
						&& i == (me.frm.doc.items || []).length - 1) {
					var discount_amount_loss = flt(cur_frm.doc.net_total - net_total
						- cur_frm.doc.discount_amount, precision("net_total"));
					item.net_amount = flt(item.net_amount + discount_amount_loss,
						precision("net_amount", item));
				}
				item.net_rate = item.qty ? flt(item.net_amount / item.qty, precision("net_rate", item)) : 0;
				set_in_company_currency(item, ["net_rate", "net_amount"]);
			});

			this.discount_amount_applied = true;
			_calculate_taxes_and_totals();
		}
	}
}

var get_total_for_discount_amount= function() {
	if(cur_frm.doc.apply_discount_on == "Net Total") {
		return cur_frm.doc.net_total;
	} else {
		var total_actual_tax = 0.0;
		var actual_taxes_dict = {};

		$.each(cur_frm.doc["taxes"] || [], function(i, tax) {
			if (in_list(["Actual", "On Item Quantity"], tax.charge_type)) {
				var tax_amount = (tax.category == "Valuation") ? 0.0 : tax.tax_amount;
				tax_amount *= (tax.add_deduct_tax == "Deduct") ? -1.0 : 1.0;
				actual_taxes_dict[tax.idx] = tax_amount;
			} else if (actual_taxes_dict[tax.row_id] !== null) {
				var actual_tax_amount = flt(actual_taxes_dict[tax.row_id]) * flt(tax.rate) / 100;
				actual_taxes_dict[tax.idx] = actual_tax_amount;
			}
		});

		$.each(actual_taxes_dict, function(key, value) {
			if (value) total_actual_tax += value;
		});

		return flt(cur_frm.doc.grand_total - total_actual_tax, precision("grand_total"));
	}
}

var update_paid_amount_for_return= function() {
	var grand_total = cur_frm.doc.rounded_total || cur_frm.doc.grand_total;

	if(cur_frm.doc.party_account_currency == cur_frm.doc.currency) {
		var total_amount_to_pay = flt((grand_total - cur_frm.doc.total_advance
			- cur_frm.doc.write_off_amount), precision("grand_total"));
	} else {
		var total_amount_to_pay = flt(
			(flt(grand_total*cur_frm.doc.conversion_rate, precision("grand_total"))
				- cur_frm.doc.total_advance - cur_frm.doc.base_write_off_amount),
			precision("base_grand_total")
		);
	}

	cur_frm.doc.payments.find(pay => {
		if (pay.default) {
			pay.amount = total_amount_to_pay;
		} else {
			pay.amount = 0.0
		}
	});
	cur_frm.refresh_fields();

	calculate_paid_amount();
}

var calculate_commission= function() {
	if(cur_frm.fields_dict.commission_rate) {
		if(cur_frm.doc.commission_rate > 100) {
			var msg = __(frappe.meta.get_label(this.frm.doc.doctype, "commission_rate", this.frm.doc.name)) +
				" " + __("cannot be greater than 100");
			frappe.msgprint(msg);
			throw msg;
		}

		cur_frm.doc.total_commission = flt(cur_frm.doc.base_net_total * cur_frm.doc.commission_rate / 100.0,
			precision("total_commission"));
	}
}

var calculate_contribution= function() {
	var me = this;
	$.each(cur_frm.doc.doctype.sales_team || [], function(i, sales_person) {
		frappe.model.round_floats_in(sales_person);
		if(sales_person.allocated_percentage) {
			sales_person.allocated_amount = flt(
				cur_frm.doc.base_net_total * sales_person.allocated_percentage / 100.0,
				precision("allocated_amount", sales_person));
		}
	});
}

var calculate_write_off_amount= function(){
	if(cur_frm.doc.paid_amount > cur_frm.doc.grand_total){
		cur_frm.doc.write_off_amount = flt(cur_frm.doc.grand_total - cur_frm.doc.paid_amount
			+ cur_frm.doc.change_amount, precision("write_off_amount"));

		cur_frm.doc.base_write_off_amount = flt(cur_frm.doc.write_off_amount * cur_frm.doc.conversion_rate,
			precision("base_write_off_amount"));
	}else{
		cur_frm.doc.paid_amount = 0.0;
	}
	calculate_outstanding_amount(false);
}

var apply_pricing_rule= function(item, calculate_taxes_and_totals) {
	// frappe.msgprint('apply_pricing_rule')
	var me = this;
	var args = _get_args(item);
	//console.log(args)
	if (!(args.items && args.items.length)) {
		if(calculate_taxes_and_totals) calculate_taxes_and_totals();
		return;
	}

	return cur_frm.call({
		method: "erpnext.accounts.doctype.pricing_rule.pricing_rule.apply_pricing_rule",
		args: {	args: args, doc: cur_frm.doc },
		callback: function(r) {
			if (!r.exc && r.message) {
				_set_values_for_item_list(r.message);
				if(item) set_gross_profit(item);
				if(cur_frm.doc.apply_discount_on) cur_frm.trigger("apply_discount_on")
			}
		}
	});
}

var _get_args= function(item) {
	var me = this;
	return {
		"items": _get_item_list(item),
		"customer": cur_frm.doc.customer || cur_frm.doc.party_name,
		"quotation_to": cur_frm.doc.quotation_to,
		"customer_group": cur_frm.doc.customer_group,
		"territory": cur_frm.doc.territory,
		"supplier": cur_frm.doc.supplier,
		"supplier_group": cur_frm.doc.supplier_group,
		"currency": cur_frm.doc.currency,
		"conversion_rate": cur_frm.doc.conversion_rate,
		"price_list": cur_frm.doc.selling_price_list || cur_frm.doc.buying_price_list,
		"price_list_currency": cur_frm.doc.price_list_currency,
		"plc_conversion_rate": cur_frm.doc.plc_conversion_rate,
		"company": cur_frm.doc.company,
		"transaction_date": cur_frm.doc.transaction_date || cur_frm.doc.posting_date,
		"campaign": cur_frm.doc.campaign,
		"sales_partner": cur_frm.doc.sales_partner,
		"ignore_pricing_rule": cur_frm.doc.ignore_pricing_rule,
		"doctype": cur_frm.doc.doctype,
		"name": cur_frm.doc.name,
		"is_return": cint(cur_frm.doc.is_return),
		"update_stock": in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor'], cur_frm.doc.doctype) ? cint(cur_frm.doc.update_stock) : 0,
		"conversion_factor": cur_frm.doc.conversion_factor,
		"pos_profile": cur_frm.doc.doctype == 'Sales Invoice Penjualan Motor' ? cur_frm.doc.pos_profile : '',
		"coupon_code": cur_frm.doc.coupon_code
	};
}

var _set_values_for_item_list= function(children) {
	// frappe.msgprint('_set_values_for_item_list')
	var me = this;
	var price_list_rate_changed = false;
	var items_rule_dict = {};

	for(var i=0, l=children.length; i<l; i++) {
		var d = children[i];
		var existing_pricing_rule = frappe.model.get_value(d.doctype, d.name, "pricing_rules");
		for(var k in d) {
			var v = d[k];
			if (["doctype", "name"].indexOf(k)===-1) {
				if(k=="price_list_rate") {
					if(flt(v) != flt(d.price_list_rate)) price_list_rate_changed = true;
				}

				if (k !== 'free_item_data') {
					frappe.model.set_value(d.doctype, d.name, k, v);
				}
			}
		}

		// if pricing rule set as blank from an existing value, apply price_list
		if(!cur_frm.doc.ignore_pricing_rule && existing_pricing_rule && !d.pricing_rules) {
			apply_price_list(frappe.get_doc(d.doctype, d.name));
		} else if(!d.pricing_rules) {
			remove_pricing_rule(frappe.get_doc(d.doctype, d.name));
		}

		if (d.free_item_data) {
			apply_product_discount(d);
		}

		if (d.apply_rule_on_other_items) {
			items_rule_dict[d.name] = d;
		}
	}

	apply_rule_on_other_items(items_rule_dict);

	if(!price_list_rate_changed) calculate_taxes_and_totals();
}

var set_gross_profit= function(item) {
	if (["Sales Order", "Quotation"].includes(cur_frm.doc.doctype) && item.valuation_rate) {
		var rate = flt(item.rate) * flt(cur_frm.doc.conversion_rate || 1);
		item.gross_profit = flt(((rate - item.valuation_rate) * item.stock_qty), precision("amount", item));
	}
}

var _get_item_list= function(item) {
	// frappe.msgprint('_get_item_list')
	var item_list = [];
	var append_item = function(d) {
		if (d.item_code) {
			item_list.push({
				"doctype": d.doctype,
				"name": d.name,
				"child_docname": d.name,
				"item_code": d.item_code,
				"item_group": d.item_group,
				"brand": d.brand,
				"qty": d.qty,
				"stock_qty": d.stock_qty,
				"uom": d.uom,
				"stock_uom": d.stock_uom,
				"parenttype": d.parenttype,
				"parent": d.parent,
				"pricing_rules": d.pricing_rules,
				"warehouse": d.warehouse,
				"serial_no": d.serial_no,
				"batch_no": d.batch_no,
				"price_list_rate": d.price_list_rate,
				"conversion_factor": d.conversion_factor || 1.0
			});

			// if doctype is Quotation Item / Sales Order Iten then add Margin Type and rate in item_list
			if (in_list(["Quotation Item", "Sales Order Item", "Sales Invoice Penjualan Motor Item", "Delivery Note Item", "Sales Invoice Item",  "Purchase Invoice Item", "Purchase Order Item", "Purchase Receipt Item"]), d.doctype) {
				item_list[0]["margin_type"] = d.margin_type;
				item_list[0]["margin_rate_or_amount"] = d.margin_rate_or_amount;
			}
		}
	};

	if (item) {
		append_item(item);
	} else {
		$.each(cur_frm.doc["items"] || [], function(i, d) {
			append_item(d);
		});
	}
	// console.log(item_list)
	return item_list;
}

var apply_price_list= function(item, reset_plc_conversion) {
	// We need to reset plc_conversion_rate sometimes because the call to
	// `erpnext.stock.get_item_details.apply_price_list` is sensitive to its value
	frappe.msgprint("Masuk apply_price_list")
	if (!reset_plc_conversion) {
		frm.set_value("plc_conversion_rate", "");
	}

	var me = this;
	var args = _get_args(item);
	if (!((args.items && args.items.length) || args.price_list)) {
		return;
	}

	if (me.in_apply_price_list == true) return;

	me.in_apply_price_list = true;
	return this.frm.call({
		method: "erpnext.stock.get_item_details.apply_price_list",
		args: {	args: args },
		callback: function(r) {
			if (!r.exc) {
				frappe.run_serially([
					() => frm.set_value("price_list_currency", r.message.parent.price_list_currency),
					() => frm.set_value("plc_conversion_rate", r.message.parent.plc_conversion_rate),
					() => {
						if(args.items.length) {
							_set_values_for_item_list(r.message.children);
						}
					},
					() => { me.in_apply_price_list = false; }
				]);

			} else {
				me.in_apply_price_list = false;
			}
		}
	}).always(() => {
		me.in_apply_price_list = false;
	});
}

var remove_pricing_rule= function(item) {
	let me = this;
	const fields = ["discount_percentage",
		"discount_amount", "margin_rate_or_amount", "rate_with_margin"];

	if(item.remove_free_item) {
		var items = [];

		cur_frm.doc.items.forEach(d => {
			if(d.item_code != item.remove_free_item || !d.is_free_item) {
				items.push(d);
			}
		});

		cur_frm.doc.items = items;
		refresh_field('items');
	} else if(item.applied_on_items && item.apply_on) {
		const applied_on_items = item.applied_on_items.split(',');
		cur_frm.doc.items.forEach(row => {
			if(applied_on_items.includes(row[item.apply_on])) {
				fields.forEach(f => {
					row[f] = 0;
				});

				["pricing_rules", "margin_type"].forEach(field => {
					if (row[field]) {
						row[field] = '';
					}
				})
			}
		});

		trigger_price_list_rate();
	}
}

var trigger_price_list_rate= function() {
	var me  = this;

	cur_frm.doc.items.forEach(child_row => {
		cur_frm.script_manager.trigger("price_list_rate",
			child_row.doctype, child_row.name);
	})
}

var apply_product_discount= function(args) {
	// frappe.msgprint("masuk apply_product_discount")
	const items = cur_frm.doc.items.filter(d => (d.is_free_item)) || [];

	const exist_items = items.map(row => (row.item_code, row.pricing_rules));

	args.free_item_data.forEach(pr_row => {
		let row_to_modify = {};
		if (!items || !in_list(exist_items, (pr_row.item_code, pr_row.pricing_rules))) {

			row_to_modify = frappe.model.add_child(cur_frm.doc,
				cur_frm.doc.doctype + ' Item', 'items');

		} else if(items) {
			row_to_modify = items.filter(d => (d.item_code === pr_row.item_code
				&& d.pricing_rules === pr_row.pricing_rules))[0];
		}

		for (let key in pr_row) {
			row_to_modify[key] = pr_row[key];
		}
	});

	// free_item_data is a temporary variable
	args.free_item_data = '';
	refresh_field('items');
}

var apply_rule_on_other_items= function(args) {
	const me = this;
	const fields = ["discount_percentage", "pricing_rules", "discount_amount", "rate"];

	for(var k in args) {
		let data = args[k];

		if (data && data.apply_rule_on_other_items) {
			cur_frm.doc.items.forEach(d => {
				if (in_list(data.apply_rule_on_other_items, d[data.apply_rule_on])) {
					for(var k in data) {
						if (in_list(fields, k) && data[k] && (data.price_or_product_discount === 'price' || k === 'pricing_rules')) {
							frappe.model.set_value(d.doctype, d.name, k, data[k]);
						}
					}
				}
			});
		}
	}
}

var validate_company_and_party= function() {
	var me = this;
	var valid = true;

	$.each(["company", "customer"], function(i, fieldname) {
		if(frappe.meta.has_field(cur_frm.doc.doctype, fieldname) && cur_frm.doc.doctype != "Purchase Order") {
			if (!cur_frm.doc[fieldname]) {
				frappe.msgprint(__("Please specify") + ": " +
					frappe.meta.get_label(cur_frm.doc.doctype, fieldname, cur_frm.doc.name) +
					". " + __("It is needed to fetch Item Details."));
				valid = false;
			}
		}
	});
	return valid;
}

var add_taxes_from_item_tax_template= function(item_tax_map) {
	// frappe.msgprint("masuk add_taxes_from_item_tax_template")
	let me = this;

	if(item_tax_map && cint(frappe.defaults.get_default("add_taxes_from_item_tax_template"))) {
		if(typeof (item_tax_map) == "string") {
			item_tax_map = JSON.parse(item_tax_map);
		}

		$.each(item_tax_map, function(tax, rate) {
			let found = (cur_frm.doc.taxes || []).find(d => d.account_head === tax);
			if(!found) {
				let child = frappe.model.add_child(cur_frm.doc, "taxes");
				child.charge_type = "On Net Total";
				child.account_head = tax;
				child.rate = 0;
			}
		});
	}
}

var get_incoming_rate= function(item, posting_date, posting_time, voucher_type, company) {
	// frappe.msgprint("masuk get_incoming_rate")
	let item_args = {
		'item_code': item.item_code,
		'warehouse': in_list('Purchase Receipt', 'Purchase Invoice') ? item.from_warehouse : item.warehouse,
		'posting_date': posting_date,
		'posting_time': posting_time,
		'qty': item.qty * item.conversion_factor,
		'serial_no': item.serial_no,
		'voucher_type': voucher_type,
		'company': company,
		'allow_zero_valuation_rate': item.allow_zero_valuation_rate
	}

	frappe.call({
		method: 'erpnext.stock.utils.get_incoming_rate',
		args: {
			args: item_args
		},
		callback: function(r) {
			frappe.model.set_value(item.doctype, item.name, 'rate', r.message * item.conversion_factor);
		}
	});
}

var toggle_conversion_factor= function(item) {
	// toggle read only property for conversion factor field if the uom and stock uom are same
	if(cur_frm.get_field('items').grid.fields_map.conversion_factor) {
		// frappe.msgprint("masuk toggle_conversion_factor")
		cur_frm.fields_dict.items.grid.toggle_enable("conversion_factor",
			((item.uom != item.stock_uom) && !frappe.meta.get_docfield(cur_frm.fields_dict.items.grid.doctype, "conversion_factor").read_only)? true: false);
	}

}

var conversion_factor= function(doc, cdt, cdn, dont_fetch_price_list_rate) {
	if(frappe.meta.get_docfield(cdt, "stock_qty", cdn)) {
		// frappe.msgprint("conversion_factor")
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["qty", "conversion_factor"]);
		item.stock_qty = flt(item.qty * item.conversion_factor, precision("stock_qty", item));
		refresh_field("stock_qty", item.name, item.parentfield);
		toggle_conversion_factor(item);

		if(doc.doctype != "Material Request") {
			item.total_weight = flt(item.stock_qty * item.weight_per_unit);
			refresh_field("total_weight", item.name, item.parentfield);
			calculate_net_weight();
		}

		// for handling customization not to fetch price list rate
		if (frappe.flags.dont_fetch_price_list_rate) {
			return;
		}

		if (!dont_fetch_price_list_rate &&
			frappe.meta.has_field(doc.doctype, "price_list_currency")) {
			apply_price_list(item, true);
		}
		calculate_stock_uom_rate(doc, cdt, cdn);
	}
}

var calculate_stock_uom_rate= function(doc, cdt, cdn) {
	// frappe.msgprint("masuk calculate_stock_uom_rate")
	let item = frappe.get_doc(cdt, cdn);
	//console.log(item)
	item.stock_uom_rate = flt(item.rate)/flt(item.conversion_factor);
	refresh_field("stock_uom_rate", item.name, item.parentfield);
}

var calculate_net_weight= function(){
	/* Calculate Total Net Weight then further applied shipping rule to calculate shipping charges.*/
	var me = this;
	cur_frm.doc.total_net_weight= 0.0;

	$.each(cur_frm.doc["items"] || [], function(i, item) {
		cur_frm.doc.total_net_weight += flt(item.total_weight);
	});
	refresh_field("total_net_weight");
	shipping_rule();
}

var shipping_rule= function() {
	var me = this;
	if(cur_frm.doc.shipping_rule) {
		return cur_frm.call({
			doc: cur_frm.doc,
			method: "apply_shipping_rule",
			callback: function(r) {
				if(!r.exc) {
					calculate_taxes_and_totals();
				}
			}
		}).fail(() => cur_frm.set_value('shipping_rule', ''));
	}
	else {
		calculate_taxes_and_totals();
	}
}

var sales_order_btn= function() {
	var me = this;
	var sales_order_btn = cur_frm.add_custom_button(__('Sales Order'),
		function() {
			erpnext.utils.map_current_doc({
				method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
				source_doctype: "Sales Order",
				target: me.frm,
				setters: {
					customer: cur_frm.doc.customer || undefined,
				},
				get_query_filters: {
					docstatus: 1,
					status: ["not in", ["Closed", "On Hold"]],
					per_billed: ["<", 99.99],
					company: cur_frm.doc.company
				}
			})
		}, __("Get Items From"));
}

var delivery_note_btn= function() {
	var me = this;
	var delivery_note_btn = cur_frm.add_custom_button(__('Delivery Note'),
		function() {
			erpnext.utils.map_current_doc({
				method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
				source_doctype: "Delivery Note",
				target: me.frm,
				date_field: "posting_date",
				setters: {
					customer: cur_frm.doc.customer || undefined
				},
				get_query: function() {
					var filters = {
						docstatus: 1,
						company: cur_frm.doc.company,
						is_return: 0
					};
					if(cur_frm.doc.customer) filters["customer"] = cur_frm.doc.customer;
					return {
						query: "erpnext.controllers.queries.get_delivery_notes_to_be_billed",
						filters: filters
					};
				}
			});
		}, __("Get Items From"));
}

var quotation_btn= function() {
	var me = this;
	var quotation_btn = cur_frm.add_custom_button(__('Quotation'),
		function() {
			erpnext.utils.map_current_doc({
				method: "erpnext.selling.doctype.quotation.quotation.make_sales_invoice",
				source_doctype: "Quotation",
				target: cur_frm,
				setters: [{
					fieldtype: 'Link',
					label: __('Customer'),
					options: 'Customer',
					fieldname: 'party_name',
					default: cur_frm.doc.customer,
				}],
				get_query_filters: {
					docstatus: 1,
					status: ["!=", "Lost"],
					company: cur_frm.doc.company
				}
			})
		}, __("Get Items From"));
}

var show_stock_ledger= function() {
	var me = this;
	if(cur_frm.doc.docstatus > 0) {
		cur_frm.add_custom_button(__("Stock Ledger"), function() {
			frappe.route_options = {
				voucher_no: cur_frm.doc.name,
				from_date: cur_frm.doc.posting_date,
				to_date: moment(cur_frm.doc.modified).format('YYYY-MM-DD'),
				company: cur_frm.doc.company,
				show_cancelled_entries: cur_frm.doc.docstatus === 2
			};
			frappe.set_route("query-report", "Stock Ledger");
		}, __("View"));
	}

}

var make_payment_entry= function() {
	return cur_frm.call({
		method: get_method_for_payment(),
		args: {
			"dt": cur_frm.doc.doctype,
			"dn": cur_frm.doc.name
		},
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			// cur_frm.refresh_fields()
		}
	});
}

var get_method_for_payment= function(){
	var method = "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
	if(cur_frm.doc.__onload && cur_frm.doc.__onload.make_payment_via_journal_entry){
		if(in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor'],  cur_frm.doc.doctype)){
			method = "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_invoice";
		}else {
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}
	}

	return method
}

var calculate_stock_uom_rate= function(doc, cdt, cdn) {
	let item = frappe.get_doc(cdt, cdn);
	item.stock_uom_rate = flt(item.rate)/flt(item.conversion_factor);
	refresh_field("stock_uom_rate", item.name, item.parentfield);
}

var apply_pricing_rule_on_item= function(item) {
	let effective_item_rate = item.price_list_rate;
	let item_rate = item.rate;
	if (in_list(["Sales Order", "Quotation"], item.parenttype) && item.blanket_order_rate) {
		effective_item_rate = item.blanket_order_rate;
	}
	if(item.margin_type == "Percentage"){
		item.rate_with_margin = flt(effective_item_rate)
			+ flt(effective_item_rate) * ( flt(item.margin_rate_or_amount) / 100);
	} else {
		item.rate_with_margin = flt(effective_item_rate) + flt(item.margin_rate_or_amount);
	}
	item.base_rate_with_margin = flt(item.rate_with_margin) * flt(cur_frm.doc.conversion_rate);

	item_rate = flt(item.rate_with_margin , precision("rate", item));

	if(item.discount_percentage){
		item.discount_amount = flt(item.rate_with_margin) * flt(item.discount_percentage) / 100;
	}

	if (item.discount_amount) {
		item_rate = flt((item.rate_with_margin) - (item.discount_amount), precision('rate', item));
		item.discount_percentage = 100 * flt(item.discount_amount) / flt(item.rate_with_margin);
	}

	frappe.model.set_value(item.doctype, item.name, "rate", item_rate);
}

// asli
frappe.ui.form.on("Sales Invoice Penjualan Motor", "no_rangka", function(frm) {
	if(cur_frm.doc.no_rangka){
		let today = frappe.datetime.get_today();
		// frappe.msgprint('coba pajak1');
		// cur_frm.clear_table("taxes");
		// cur_frm.refresh_field("taxes");
		// cur_frm.set_value("taxes_and_charges","");
		// cur_frm.set_value("taxes_and_charges","PPN 11% - Keluaran - IFMI");

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
						cur_frm.set_value("harga",hitung_disc)
		    		}
		    		if(cur_frm.doc.diskon==0){
		    			cur_frm.set_value("harga", r.message[0].price_list_rate);
			        	//cur_frm.refresh_fields("harga")
		    		}
		    	}else{
		    		cur_frm.set_value("harga", 0);
			        //cur_frm.refresh_fields("harga")
		    	}
			}
		});


    	var coba12 = cur_frm.doc.harga
    	console.log(coba12,"ccccc")
	}

	if(!cur_frm.doc.no_rangka){
		// frappe.msgprint('coba pajak2')
		// cur_frm.set_value("taxes_and_charges","");
		// cur_frm.clear_table("taxes");
		// cur_frm.refresh_field("taxes");
		cur_frm.set_value("harga", 0);
		cur_frm.refresh_field("harga");
		cur_frm.clear_table("items");
		cur_frm.refresh_field("items");
	}
	
});

frappe.ui.form.on("Sales Invoice Penjualan Motor", "harga", function(frm) {
	console.log("hargaaaa")
	cur_frm.clear_table("tabel_biaya_motor");
	cur_frm.refresh_field("tabel_biaya_motor");  
	// let today = frappe.datetime.get_today();
	let today = cur_frm.doc.posting_date;
	if(cur_frm.doc.harga){
    	// harga
    	
		// table biaya
	    frappe.db.get_list('Rule Biaya',{ filters: { 'item_code':  cur_frm.doc.item_code,'territory': cur_frm.doc.territory_biaya,'disable': 0}, fields: ['*']})
		.then(data => {
	        // console.log(data,"data")
	        cur_frm.clear_table("tabel_biaya_motor");
	        cur_frm.refresh_field("tabel_biaya_motor");    

	        if(data.length > 0){
	        	
		        for (let i = 0; i < data.length; i++) {
					if (data[i].valid_from <= today && data[i].valid_to >= today){
						var child_b = cur_frm.add_child("tabel_biaya_motor");
						frappe.model.set_value(child_b.doctype, child_b.name, "rule", data[i].name);
				        frappe.model.set_value(child_b.doctype, child_b.name, "vendor", data[i].vendor);
				        frappe.model.set_value(child_b.doctype, child_b.name, "type", data[i].type);
				        frappe.model.set_value(child_b.doctype, child_b.name, "amount", data[i].amount);
			            frappe.model.set_value(child_b.doctype, child_b.name, "coa", data[i].coa);
			            // cur_frm.refresh_field("tabel_biaya_motor");	     
					}else{
						// frappe.msgprint("cek vadlidasi tanggal di rule "+data[i].name);
					}
				}
				cur_frm.refresh_field("tabel_biaya_motor");	 
				//frappe.msgprint("tabel_biaya_motor2 !!")
				let sum = 0;
				let sum2=0
			
				for (let z = 0; z < cur_frm.doc.tabel_biaya_motor.length; z++) {
					sum += cur_frm.doc.tabel_biaya_motor[z].amount;
				}
				cur_frm.set_value("total_biaya",sum)
				
				console.log(sum,"sum")
				
				var ppn_rate = cur_frm.doc.taxes[0]['rate']
				var ppn_div = (100+ppn_rate)/100
			    var total = (cur_frm.doc.harga - cur_frm.doc.total_biaya) / ppn_div;
				var hasil = cur_frm.doc.harga - total;
				var akhir = cur_frm.doc.harga - hasil;
				console.log(total,"total")
				console.log(hasil,"hasil")
				console.log(akhir,"akhir")

			    var cb_disc = 0
			    if(cur_frm.doc.diskon==1){
			    	cb_disc = hasil + cur_frm.doc.nominal_diskon
			    }else{
			    	cb_disc = hasil + 0
			    }
				// table item

				
				cur_frm.clear_table("items");
				cur_frm.refresh_field("items");
				var child_i = cur_frm.add_child("items");
				frappe.model.set_value(child_i.doctype, child_i.name, "item_code", cur_frm.doc.item_code);
				// console.log("sebelum get details")
				frappe.model.set_value(child_i.doctype, child_i.name, "discount_amount", cb_disc);
				frappe.model.set_value(child_i.doctype, child_i.name,"cost_center",cur_frm.doc.cost_center)
				frappe.model.set_value(child_i.doctype, child_i.name, "rate", total)
				frappe.model.set_value(child_i.doctype, child_i.name, "warehouse", cur_frm.doc.set_warehouse)
				frappe.model.set_value(child_i.doctype, child_i.name, "serial_no", cur_frm.doc.no_rangka)
				//cur_frm.refresh_field("items");
		    }

		    if(data.length == 0){
		    	cur_frm.set_value("total_biaya",0)
				console.log(cur_frm.doc.harga,"harga")
			    var ppn_rate = cur_frm.doc.taxes[0]['rate']
				var ppn_div = (100+ppn_rate)/100
			    var total = (cur_frm.doc.harga - cur_frm.doc.total_biaya) / ppn_div;
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
				frappe.model.set_value(child_i2.doctype, child_i2.name, "discount_amount", cb_disc);
				// frappe.model.set_value(child_i2.doctype, child_i2.name, "price_list_rate", cur_frm.doc.harga);
				frappe.model.set_value(child_i2.doctype, child_i2.name, "rate", total)
				frappe.model.set_value(child_i2.doctype, child_i2.name, "warehouse", cur_frm.doc.set_warehouse)
				frappe.model.set_value(child_i2.doctype, child_i2.name, "serial_no", cur_frm.doc.no_rangka)
				frappe.model.set_value(child_i2.doctype, child_i2.name,"cost_center",cur_frm.doc.cost_center)
				//cur_frm.refresh_field("items");
		    }
		});

    }
});



frappe.ui.form.on("Sales Invoice Penjualan Motor", "nama_promo", function(frm) {
	//cur_frm.trigger("load_discount");
	// table discount leasing
    frm.set_value("nama_leasing", "");
    cur_frm.set_value("no_rangka","")
    if(!cur_frm.doc.nama_promo){
    	frm.set_value("nama_leasing", "");
    	cur_frm.clear_table("table_discount_leasing");
    	cur_frm.refresh_field("table_discount_leasing");
    	//cur_frm.refresh_field();
    }
    if(cur_frm.doc.nama_promo){
    	if(cur_frm.doc.cara_bayar == "Credit"){
	    	//frappe.msgprint("test 123wetwet")
	    	// let today = frappe.datetime.get_today();
	    	let today = cur_frm.doc.posting_date;
	    	frappe.call({
				method: "wongkar_selling.wongkar_selling.get_invoice.get_leasing",
				args: {
					item_code: cur_frm.doc.item_code,
					nama_promo: cur_frm.doc.nama_promo,
					territory_real: cur_frm.doc.territory_real,
					posting_date: cur_frm.doc.posting_date
				},
				callback: function(r) {
					console.log(r,"leasing")
					cur_frm.clear_table("table_discount_leasing");
					cur_frm.refresh_field("table_discount_leasing");
					if(r.message.length>0){
						for (let i = 0; i < r.message.length; i++) {
							var child_l = cur_frm.add_child("table_discount_leasing");
					        frappe.model.set_value(child_l.doctype, child_l.name, "coa", r.message[i].coa);
					        frappe.model.set_value(child_l.doctype, child_l.name, "nominal", r.message[i].amount);
					        frappe.model.set_value(child_l.doctype, child_l.name, "nama_leasing", r.message[i].leasing);
						}
						cur_frm.refresh_field("table_discount_leasing");
					}
				}
			});
		}
	}
});

frappe.ui.form.on("Sales Invoice Penjualan Motor", "cara_bayar", function(frm) {
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
	/*if(cur_frm.doc.nama_promo){
		frm.set_value('item_code','')
	}*/
})


/*frappe.ui.form.on("Sales Invoice Penjualan Motor", "setup", function(frm) {
	frappe.msgprint("Wahyu Lutfi Yansyah")*/

//tampilan
// for backward compatibility: combine new and previous states
// $.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceController({frm: cur_frm}));

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

// project name
//--------------------------
cur_frm.fields_dict['project'].get_query = function(doc, cdt, cdn) {
	return{
		query: "erpnext.controllers.queries.get_project_name",
		filters: {'customer': cur_frm.doc.customer}
	}
}

// Income Account in Details Table
// --------------------------------
cur_frm.set_query("income_account", "items", function(frm) {
	return{
		query: "erpnext.controllers.queries.get_income_account",
		filters: {'company': cur_frm.doc.company}
	}
});


// Cost Center in Details Table
// -----------------------------
cur_frm.fields_dict["items"].grid.get_field("cost_center").get_query = function(doc) {
	return {
		filters: {
			'company': cur_frm.doc.company,
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
	setup: function(frm){
		setup_posting_date_time_check();
		frm.add_fetch('customer', 'tax_id', 'tax_id');
		frm.add_fetch('payment_term', 'invoice_portion', 'invoice_portion');
		frm.add_fetch('payment_term', 'description', 'description');

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

		// expense account
		frm.fields_dict['items'].grid.get_field('expense_account').get_query = function(doc) {
			if (erpnext.is_perpetual_inventory_enabled(doc.company)) {
				return {
					filters: {
						'report_type': 'Profit and Loss',
						'company': doc.company,
						"is_group": 0
					}
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
	/*territory_baru: function(frm){
		if(cur_frm.doc.territory_baru==1){
			frappe.call({
				method: "wongkar_selling.wongkar_selling.gen_wh.get_ter",
				callback: function(r){
					var data =[]
					for(let i=0;i<r.message.length;i++){
						console.log(r.message[i].name)
						data.push(r.message[i].name)
					}
					console.log(data)
					frm.set_df_property('new_territory', 'options', data);
				}
			});
		}else{
			cur_frm.set_value('new_territory','')

			cur_frm.set_query("no_rangka", function() {
				var wh = ''
				if(cur_frm.doc.territory == 'All Territories'){
					wh = "Stores"+ " - "+cur_frm.doc.company
				}else{
					wh = cur_frm.doc.territory+" - "+cur_frm.doc.company
				}
				return {
					filters: {
						"item_code": cur_frm.doc.item_code,
						"warehouse": wh,
						"status": "Active"
					}
				};

			});
			if(cur_frm.doc.territory == 'All Territories'){
				cur_frm.set_value("set_warehouse","Stores"+ " - "+cur_frm.doc.company)
			}else{
				cur_frm.set_value("set_warehouse",cur_frm.doc.territory+" - "+cur_frm.doc.company)
			}
		}
	},
	new_territory: function(frm){
		if(cur_frm.doc.new_territory){
			cur_frm.set_query("no_rangka", function() {
				var wh = ''
				if(cur_frm.doc.new_territory == 'All Territories'){
					wh = "Stores"+ " - "+cur_frm.doc.company
				}else{
					wh = cur_frm.doc.new_territory+" - "+cur_frm.doc.company
				}
				return {
					filters: {
						"item_code": cur_frm.doc.item_code,
						"warehouse": wh,
						"status": "Active"
					}
				};

			});
			if(cur_frm.doc.new_territory == 'All Territories'){
				cur_frm.set_value("set_warehouse","Stores"+ " - "+cur_frm.doc.company)
			}else{
				cur_frm.set_value("set_warehouse",cur_frm.doc.new_territory+" - "+cur_frm.doc.company)
			}
		}else{
			if(cur_frm.doc.territory == 'All Territories'){
				cur_frm.set_value("set_warehouse","Stores"+ " - "+cur_frm.doc.company)
			}else{
				cur_frm.set_value("set_warehouse",cur_frm.doc.territory+" - "+cur_frm.doc.company)
			}
		}
	},*/
	/*set_warehouse: function(frm){
		//frappe.msgprint('test')
		cur_frm.set_query("no_rangka", function() {
			return {
				filters: {
					"item_code": cur_frm.doc.item_code,
					"warehouse": cur_frm.doc.set_warehouse,
					"status": "Active"
				}
			};

		});
	},*/
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

	project: function(frm){
		frm.call({
			method: "add_timesheet_data",
			doc: frm.doc,
			callback: function(r, rt) {
				refresh_field(['timesheets'])
			}
		})
		frm.refresh();
	},

	/*onload: function(frm) {
		frm.redemption_conversion_factor = null;
	},*/

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

		frm.toggle_enable("write_off_amount", !!!cint(doc.write_off_outstanding_amount_automatically));

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

	refresh: function(frm) {
		// frappe.msgprint("refresh nvbvbv")
		// tambhan coba
		/*if(cur_frm.doc.advances){
			calculate_total_advance();
		}*/
		//calculate_total_advance();
		cur_frm.add_fetch('pemilik',  'territory',  'territory_real');
		cur_frm.add_fetch('pemilik',  'territory',  'territory_biaya');
		/*cur_frm.set_query("nama_diskon", function() {
			return {
				filters: {
					"item_code": cur_frm.doc.item_code,
					'territory': cur_frm.doc.territory_real,
					//'customer_group': cur_frm.doc.customer_group,
					"disable": 0
				}
			};
		});*/
		/*cur_frm.set_query("nama_promo", function() {
			return {
				filters: {
					"item_code": cur_frm.doc.item_code,
					'territory': cur_frm.doc.territory_real,
					//'customer_group': cur_frm.doc.customer_group,
					"disable": 0
				}
			};
		});*/
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
		/*if(cur_frm.doc.territory == 'All Territories'){
			cur_frm.set_value("set_warehouse","Stores"+ " - "+cur_frm.doc.company)
		}else{
			cur_frm.set_value("set_warehouse",cur_frm.doc.territory+" - "+cur_frm.doc.company)
		}*/
		//bobby
		// if (!frm.doc.cost_center){
		// 	frappe.db.get_value("Company", {"name": cur_frm.doc.company}, "round_off_cost_center")
		// 	.then(data => { 
		// 		frm.set_value("cost_center", data.message.round_off_cost_center);
		// 	});
		// }
		if (cur_frm.doc.project) {
			cur_frm.add_custom_button(__('Fetch Timesheet'), function() {
				let d = new frappe.ui.Dialog({
					title: __('Fetch Timesheet'),
					fields: [
						{
							"label" : "From",
							"fieldname": "from_time",
							"fieldtype": "Date",
							"reqd": 1,
						},
						{
							fieldtype: 'Column Break',
							fieldname: 'col_break_1',
						},
						{
							"label" : "To",
							"fieldname": "to_time",
							"fieldtype": "Date",
							"reqd": 1,
						}
					],
					primary_action: function() {
						let data = d.get_values();
						frappe.call({
							method: "erpnext.projects.doctype.timesheet.timesheet.get_projectwise_timesheet_data",
							args: {
								from_time: data.from_time,
								to_time: data.to_time,
								project: cur_frm.doc.project
							},
							callback: function(r) {
								if(!r.exc) {
									if(r.message.length > 0) {
										frm.clear_table('timesheets')
										r.message.forEach((d) => {
											frm.add_child('timesheets',{
												'time_sheet': d.parent,
												'billing_hours': d.billing_hours,
												'billing_amount': d.billing_amt,
												'timesheet_detail': d.name
											});
										});
										frm.refresh_field('timesheets')
									}
									else {
										frappe.msgprint(__('No Timesheet Found.'))
									}
									d.hide();
								}
							}
						});
					},
					primary_action_label: __('Get Timesheets')
				});
				d.show();
			})
		}

		if (frappe.boot.active_domains.includes("Healthcare")) {
			frm.set_df_property("patient", "hidden", 0);
			frm.set_df_property("patient_name", "hidden", 0);
			frm.set_df_property("ref_practitioner", "hidden", 0);
			if (cint(cur_frm.doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !cur_frm.doc.is_return) {
				cur_frm.add_custom_button(__('Healthcare Services'), function() {
					get_healthcare_services_to_invoice(cur_frm);
				},"Get Items From");
				cur_frm.add_custom_button(__('Prescriptions'), function() {
					get_drugs_to_invoice(cur_frm);
				},"Get Items From");
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
})

frappe.ui.form.on('Sales Invoice Timesheet', {
	time_sheet: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if(d.time_sheet) {
			frappe.call({
				method: "erpnext.projects.doctype.timesheet.timesheet.get_timesheet_data",
				args: {
					'name': d.time_sheet,
					'project': frm.doc.project || null
				},
				callback: function(r, rt) {
					if(r.message){
						data = r.message;
						frappe.model.set_value(cdt, cdn, "billing_hours", data.billing_hours);
						frappe.model.set_value(cdt, cdn, "billing_amount", data.billing_amount);
						frappe.model.set_value(cdt, cdn, "timesheet_detail", data.timesheet_detail);
						calculate_total_billing_amount(frm)
					}
				}
			})
		}
	}
})

var calculate_total_billing_amount =  function(frm) {
	var doc = frm.doc;

	doc.total_billing_amount = 0.0
	if(doc.timesheets) {
		$.each(doc.timesheets, function(index, data){
			doc.total_billing_amount += data.billing_amount
		})
	}

	refresh_field('total_billing_amount')
}

var select_loyalty_program = function(frm, loyalty_programs) {
	// frappe.msgprint("select_loyalty_program")
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

	dialog.set_primary_action(__("Set"), function() {
		dialog.hide();
		return cur_frm.call({
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
	// frappe.msgprint("get_healthcare_services_to_invoice")
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
	// frappe.msgprint("get_checked_values")
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
	// frappe.msgprint("sinikkk")
	if(invoice_healthcare_services){
		frappe.call({
			doc: cur_frm.doc,
			method: "set_healthcare_services",
			args:{
				checked_values: checked_values
			},
			callback: function() {
				cur_frm.trigger("validate");
				//cur_frm.refresh_fields();
			}
		});
	}
	else{
		for(let i=0; i<checked_values.length; i++){
			var si_item = frappe.model.add_child(cur_frm.doc, 'Sales Invoice Penjualan Motor Item', 'items');
			frappe.model.set_value(si_item.doctype, si_item.name, 'item_code', checked_values[i]['item']);
			frappe.model.set_value(si_item.doctype, si_item.name, 'qty', 1);
			if(checked_values[i]['qty'] > 1){
				frappe.model.set_value(si_item.doctype, si_item.name, 'qty', parseFloat(checked_values[i]['qty']));
			}
		}
		//frm.refresh_fields();
	}
};
//});


