// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rule', {
	// refresh: function(frm) {

	// }
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