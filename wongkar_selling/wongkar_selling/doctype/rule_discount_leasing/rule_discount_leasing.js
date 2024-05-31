// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rule Discount Leasing', {
	refresh: function(frm) {
		// frm.fields_dict['table_discount_leasing'].grid.get_field('coa').get_query = function(doc, cdt, cdn) {
        // var child = locals[cdt][cdn];
        // // console.log(child);
        //     return {    
        //         filters:[
        //             ['is_group', '=', 0]
        //         ]
        //     }
        // }
        frm.set_df_property("nama_promo", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("leasing", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("valid_from", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("valid_to", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("item_group", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("customer_group", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("territory", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("table_discount_leasing", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("coa", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("coa_lawan", "read_only", frm.is_new() ? 0 : 1);
		// frm.set_df_property("amount", "read_only", frm.is_new() ? 0 : 1);
		// frm.set_df_property("beban_dealer", "read_only", frm.is_new() ? 0 : 1);
	}
});

frappe.ui.form.on("Rule Discount Leasing", "leasing", function(frm) {
	if(!cur_frm.doc.leasing){
		frm.set_value("customer_group","")
		frm.set_value("territory","")
		frm.set_value("discount","")
	}
});

frappe.ui.form.on("Rule Discount Leasing", "discount", function(frm) {
	if(cur_frm.doc.discount == "Amount"){
		frm.set_value("percent",0)
	}
	if(cur_frm.doc.discount == "Percent"){
		frm.set_value("amount",0)
	}
});