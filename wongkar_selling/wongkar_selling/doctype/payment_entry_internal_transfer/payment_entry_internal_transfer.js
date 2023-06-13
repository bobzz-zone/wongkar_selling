// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry Internal Transfer', {
	refresh: function(frm) {

	},
	validate(frm){
		
	},
	to_date(frm){
		if(cur_frm.doc.to_date){
			frappe.msgprint("test")
			    frappe.call({
	             method: "wongkar_selling.wongkar_selling.doctype.payment_entry_internal_transfer.payment_entry_internal_transfer.get_pe",
	             args: {
	               name_pe : cur_frm.doc.name,
	               paid_from: cur_frm.doc.account_paid_from,
	               from_date: cur_frm.doc.from_date,
	               to_date: cur_frm.doc.to_date
	             },
	             callback: function(data) {
	             	if(data){
	             		console.log(data,"data")
						cur_frm.clear_table("list_payment_entry");
			        	cur_frm.refresh_fields("list_payment_entry");
						for (let i = 0; i < data.message.length; i++) {
							//console.log(data)
							var child = cur_frm.add_child("list_payment_entry");
							frappe.model.set_value(child.doctype, child.name, "date", data.message[i].posting_date);
							frappe.model.set_value(child.doctype, child.name, "payment_entry", data.message[i].name);
							frappe.model.set_value(child.doctype, child.name, "nama_pemilik", data.message[i].customer_name);
							frappe.model.set_value(child.doctype, child.name, "total_allocated_amount", data.message[i].paid_amount);
						}
						cur_frm.refresh_field("list_payment_entry");
	             	}
	             	
		         }
	        });

			}
	}
});
