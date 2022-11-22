// Copyright (c) 2022, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tagihan Leasing', {
	refresh: function(frm) {

	},
	leasing(frm){
		if(cur_frm.doc.leasing){
			// frappe.msgprint("test")
			frappe.call({
                 method: "wongkar_selling.wongkar_selling.doctype.tagihan_leasing.tagihan_leasing.get_sipm",
                 args: {
                   leasing: cur_frm.doc.leasing,
                   from_date: cur_frm.doc.from_date,
                   to_date: cur_frm.doc.to_date
                 },
                 callback: function(data) {
                   cur_frm.clear_table("list__outstanding__tagihan_leasing");
		        	cur_frm.refresh_fields();
					for (let i = 0; i < data.message.length; i++) {
						if (data.message[i].name){
							var child = cur_frm.add_child("list__outstanding__tagihan_leasing");
							frappe.model.set_value(child.doctype, child.name, "sipm", data.message[i].name);
							frappe.model.set_value(child.doctype, child.name, "outstanding_amount", data.message[i].outstanding_amount);
							
						}
					}
					cur_frm.refresh_field("list__outstanding__tagihan_leasing");
                   
            	}
       		});
		}
	}
});
