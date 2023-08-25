// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry Internal Transfer', {
	refresh: function(frm) {
		if(cur_frm.doc.__islocal){
			cur_frm.set_value("to_date",null)
		}
		frm.set_df_property("list_penerimaan_dp", "cannot_add_rows", true);

		frm.set_query("account_paid_from", function() {
			return {
				filters: {
					"account_type": ["in", ['Bank','Cash']],
					"is_group": 0,
					"company": cur_frm.doc.company,
					"disabled": 0
				}
			}
		});

		frm.set_query("account_paid_to", function() {
			return {
				filters: {
					"account_type": ["in", ['Bank','Cash']],
					"is_group": 0,
					"company": cur_frm.doc.company,
					"disabled": 0
				}
			}
		});

		frm.set_query("cost_center", function() {
			return {
				filters: {
					"is_group": 0,
					"company": cur_frm.doc.company,
					"disabled": 0
				}
			}
		});
	},
	account_paid_from(frm){
		cur_frm.set_value("to_date",null)
	},
	validate(frm){
		
	},
	to_date(frm){
		cur_frm.clear_table("list_penerimaan_dp");
		cur_frm.refresh_fields("list_penerimaan_dp");
		if(cur_frm.doc.to_date){
			
			// frappe.msgprint("test")
			    frappe.call({
	             method: "wongkar_selling.wongkar_selling.doctype.payment_entry_internal_transfer.payment_entry_internal_transfer.get_dp",
	             args: {
	               name_pe : cur_frm.doc.name,
	               paid_from: cur_frm.doc.account_paid_from,
	               from_date: cur_frm.doc.from_date,
	               to_date: cur_frm.doc.to_date
	             },
	             callback: function(data) {
	             	if(data){
	             		console.log(data,"data")
						for (let i = 0; i < data.message.length; i++) {
							//console.log(data)
							var child = cur_frm.add_child("list_penerimaan_dp");
							frappe.model.set_value(child.doctype, child.name, "date", data.message[i].tanggal);
							frappe.model.set_value(child.doctype, child.name, "pemilik", data.message[i].pemilik);
							frappe.model.set_value(child.doctype, child.name, "nama_pemilik", data.message[i].nama_pemilik);
							frappe.model.set_value(child.doctype, child.name, "penerimaan_dp", data.message[i].name);
							frappe.model.set_value(child.doctype, child.name, "total", data.message[i].total);
						}
						cur_frm.refresh_field("list_penerimaan_dp");
	             	}
	             	
		         }
	        });

		}
	}
});
