// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rule Biaya', {
	refresh: function(frm) {
		frm.set_df_property("type", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("vendor", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("valid_from", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("valid_to", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("item_group", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("territory", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("territory", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("coa", "read_only", frm.is_new() ? 0 : 1);
	}
});

frappe.ui.form.on("Rule Biaya", "vendor", function(frm) {
	if(!cur_frm.doc.vendor){
		frm.set_value("territory","")
		// frm.set_value("amount","")
	}
});
