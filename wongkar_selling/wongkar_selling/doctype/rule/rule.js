// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rule', {
	refresh: function(frm) {
		frm.set_df_property("category_discount", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("customer", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("valid_from", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("valid_to", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("item_group", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("customer_group", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("territory", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("discount", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("coa_receivable", "read_only", frm.is_new() ? 0 : 1);

	}
});

frappe.ui.form.on("Rule", "customer", function(frm) {
	if(!cur_frm.doc.customer){
		frm.set_value("customer_group","")
		frm.set_value("territory","")
		frm.set_value("discount","")
	}
});

frappe.ui.form.on("Rule", "discount", function(frm) {
	if(cur_frm.doc.discount == "Amount"){
		frm.set_value("percent",0)
	}
	if(cur_frm.doc.discount == "Percent"){
		frm.set_value("amount",0)
	}
});