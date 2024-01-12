// Copyright (c) 2024, w and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %};
frappe.provide("erpnext.accounts");

erpnext.accounts.SalesInvoiceSPController = erpnext.selling.SellingController.extend({
	setup: function() {
		// this._super();
	},

	company: function() {
		// frappe.msgprint("test !!")
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
					// if (response) me.frm.set_value("debit_to", response.message);
				},
			});
		}
	},

	set_dynamic_labels: function() {
		// this._super();
		this.set_product_bundle_help(this.frm.doc);
	},

	onload_post_render: function() {
		if(this.frm.doc.__islocal && !(this.frm.doc.taxes || []).length
			&& !(this.frm.doc.__onload ? this.frm.doc.__onload.load_after_mapping : false)) {
			frappe.after_ajax(() => this.apply_default_taxes());
		} else if(this.frm.doc.__islocal && this.frm.doc.company && this.frm.doc["items"]
			&& !this.frm.doc.is_pos) {
			frappe.after_ajax(() => this.calculate_taxes_and_totals());
		}
		if(frappe.meta.get_docfield(this.frm.doc.doctype + " Item", "item_code")) {
			this.setup_item_selector();
			// this.frm.get_field("items").grid.set_multiple_add("item_code", "qty");
		}
	},

	apply_product_discount: function(args) {
		// const items = this.frm.doc.items.filter(d => (d.is_free_item)) || [];

		// const exist_items = items.map(row => (row.item_code, row.pricing_rules));

		// args.free_item_data.forEach(pr_row => {
		// 	let row_to_modify = {};
		// 	if (!items || !in_list(exist_items, (pr_row.item_code, pr_row.pricing_rules))) {

		// 		row_to_modify = frappe.model.add_child(this.frm.doc,
		// 			this.frm.doc.doctype + ' Item', 'items');

		// 	} else if(items) {
		// 		row_to_modify = items.filter(d => (d.item_code === pr_row.item_code
		// 			&& d.pricing_rules === pr_row.pricing_rules))[0];
		// 	}

		// 	for (let key in pr_row) {
		// 		row_to_modify[key] = pr_row[key];
		// 	}
		// });

		// // free_item_data is a temporary variable
		// args.free_item_data = '';
		// refresh_field('items');
	},

	toggle_conversion_factor: function(item) {
		// toggle read only property for conversion factor field if the uom and stock uom are same
		// if(this.frm.get_field('items').grid.fields_map.conversion_factor) {
		// 	this.frm.fields_dict.items.grid.toggle_enable("conversion_factor",
		// 		((item.uom != item.stock_uom) && !frappe.meta.get_docfield(cur_frm.fields_dict.items.grid.doctype, "conversion_factor").read_only)? true: false);
		// }

	},

	set_currency_labels(fields_list, currency, parentfield) {
		// To set the currency in the label
		// For example Total Cost(INR), Total Cost(USD)
		// if (!currency) return;
		// var me = this;
		// var doctype = parentfield ? this.fields_dict[parentfield].grid.doctype : this.doc.doctype;
		// var field_label_map = {};
		// var grid_field_label_map = {};

		// $.each(fields_list, function(i, fname) {
		// 	var docfield = frappe.meta.docfield_map[doctype][fname];
		// 	if(docfield) {
		// 		var label = __(docfield.label || "").replace(/\([^\)]*\)/g, ""); // eslint-disable-line
		// 		if(parentfield) {
		// 			grid_field_label_map[doctype + "-" + fname] =
		// 				label.trim() + " (" + __(currency) + ")";
		// 		} else {
		// 			field_label_map[fname] = label.trim() + " (" + currency + ")";
		// 		}
		// 	}
		// });

		// $.each(field_label_map, function(fname, label) {
		// 	me.fields_dict[fname].set_label(label);
		// });

		// $.each(grid_field_label_map, function(fname, label) {
		// 	fname = fname.split("-");
		// 	me.fields_dict[parentfield].grid.update_docfield_property(fname[1], 'label', label);
		// });
	},

	update_item_grid_labels: function(company_currency) {
		// this.frm.set_currency_labels([
		// 	"base_rate", "base_net_rate", "base_price_list_rate",
		// 	"base_amount", "base_net_amount", "base_rate_with_margin"
		// ], company_currency, "items");

		// this.frm.set_currency_labels([
		// 	"rate", "net_rate", "price_list_rate", "amount",
		// 	"net_amount", "stock_uom_rate", "rate_with_margin"
		// ], this.frm.doc.currency, "items");
	},

	refresh: function(doc, dt, dn) {
		
		this.show_general_ledger();
		this.show_stock_ledger();
	},

});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceSPController({frm: cur_frm}));


frappe.ui.form.on('Sales Invoice Sparepart Garansi', {
	refresh: function(frm) {
		if(cur_frm.doc.__islocal){
			cur_frm.set_value('posting_time', frappe.datetime.now_time())
		}
	},
});
