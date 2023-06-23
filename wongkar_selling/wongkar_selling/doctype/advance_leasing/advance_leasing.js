// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Leasing', {
	refresh: function(frm) {
		if(cur_frm.doc.docstatus == 1 && cur_frm.doc.sisa > 0){
			frm.add_custom_button(__('Make PE'), () => 
				frappe.xcall("wongkar_selling.wongkar_selling.doctype.advance_leasing.advance_leasing.make_pe",{
					'name_fp': cur_frm.doc.name,
					"sisa": cur_frm.doc.sisa
				}).then(payment_entry =>{
					frappe.model.sync(payment_entry);
					frappe.set_route('Form', payment_entry.doctype, payment_entry.name);
				})
			);
		}
		
	}
});
