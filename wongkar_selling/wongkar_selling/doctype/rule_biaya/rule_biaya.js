// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rule Biaya', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Rule Biaya", "vendor", function(frm) {
	if(!cur_frm.doc.vendor){
		frm.set_value("territory","")
		// frm.set_value("amount","")
	}
});
