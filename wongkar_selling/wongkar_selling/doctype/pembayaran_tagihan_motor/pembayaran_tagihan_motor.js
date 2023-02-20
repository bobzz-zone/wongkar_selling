// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pembayaran Tagihan Motor', {
	validate: function(frm) {
		let total = 0
		let total_stnk = 0
		let total_bpkb = 0
		if(cur_frm.doc.tagihan_biaya_motor){
			for (let i = 0; i < cur_frm.doc.tagihan_biaya_motor.length; i++) {
				total += cur_frm.doc.tagihan_biaya_motor[i].nilai;
				total_stnk += cur_frm.doc.tagihan_biaya_motor[i].nilai_stnk;
				total_bpkb += cur_frm.doc.tagihan_biaya_motor[i].nilai_bpkb;
			}
		}
		frm.set_value('grand_total',total)
		frm.set_value('base_grand_total',total)
		frm.set_value('outstanding_amount',total)
		frm.set_value('total_stnk',total_stnk)
		frm.set_value('outstanding_amount_stnk',total_stnk)
		frm.set_value('total_bpkb',total_bpkb)
		frm.set_value('outstanding_amount_bpkb',total_bpkb)
	},
	date_from(frm){
		cur_frm.set_value("supplier","")
		cur_frm.set_value("supplier_stnk","")
		cur_frm.set_value("supplier_bpkb","")
		cur_frm.refresh_fields("supplier")
		cur_frm.refresh_fields("supplier_stnk")
		cur_frm.refresh_fields("supplier_bpkb")
	},
	date_to(frm){
		cur_frm.set_value("supplier","")
		cur_frm.set_value("supplier_stnk","")
		cur_frm.set_value("supplier_bpkb","")
		cur_frm.refresh_fields("supplier")
		cur_frm.refresh_fields("supplier_stnk")
		cur_frm.refresh_fields("supplier_bpkb")
	},
	refresh: function(frm){
		cur_frm.set_query("supplier_stnk", function() {
             return {
                 filters: {
                     "name":['Like','STNK%']
                 }
             }
         });
		cur_frm.set_query("supplier_bpkb", function() {
             return {
                 filters: {
                     "name":['Like','BPKB%']
                 }
             }
         });
		show_general_ledger();
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount!=0 && cur_frm.doc.type == "Diskon Dealer") {
			cur_frm.add_custom_button(__('Payment'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
		if (cur_frm.doc.docstatus == 1 && (cur_frm.doc.outstanding_amount_stnk!=0 || cur_frm.doc.outstanding_amount_bpkb!=0 ) && cur_frm.doc.type == "STNK dan BPKB") {
			cur_frm.add_custom_button(__('Payment STNK'),
				make_payment_entry_stnk, __('Create'));
			cur_frm.add_custom_button(__('Payment BPKB'),
				make_payment_entry_bpkb, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		frm.set_query("coa_biaya_motor", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});

		frm.set_query("coa_biaya_motor_stnk", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});

		frm.set_query("coa_biaya_motor_bpkb", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});
	},
	type:function(frm){
		cur_frm.set_value("supplier","")
		cur_frm.set_value("supplier_stnk","")
		cur_frm.set_value("supplier_bpkb","")
	},
	supplier_bpkb(frm){
		// frappe.msgprint("test")
		cur_frm.clear_table("tagihan_biaya_motor");
	    cur_frm.refresh_fields();
		if(cur_frm.doc.supplier_bpkb){
			frappe.call({
	             method: "wongkar_selling.wongkar_selling.get_invoice.get_inv_stnk_bpkb",
	             args: {
	                supplier: cur_frm.doc.supplier,
	                supplier_stnk : cur_frm.doc.supplier_stnk,
	                supplier_bpkb : cur_frm.doc.supplier_bpkb,
	                date_from: cur_frm.doc.date_from,
	                date_to: cur_frm.doc.date_to
	             },
	             callback: function(data) {
					console.log(data,'data')
					if(data.message){
						if(data.message.length > 0){
							for(var i = 0;i<data.message.length;i++){
								var child = cur_frm.add_child("tagihan_biaya_motor");
								frappe.model.set_value(child.doctype, child.name, "no_invoice", data.message[i].name);
								frappe.model.set_value(child.doctype, child.name, "tanggal_inv", data.message[i].posting_date);
								frappe.model.set_value(child.doctype, child.name, "type", "STNK dan BPKB");
								frappe.model.set_value(child.doctype, child.name, "nilai_stnk", data.message[i].amount);
								frappe.model.set_value(child.doctype, child.name, "outstanding_stnk", data.message[i].amount);
								frappe.model.set_value(child.doctype, child.name, "nilai_bpkb", data.message[i].amount_bpkb);
								frappe.model.set_value(child.doctype, child.name, "outstanding_bpkb", data.message[i].amount_bpkb);
								frappe.model.set_value(child.doctype, child.name, "item", data.message[i].item_code);
								frappe.model.set_value(child.doctype, child.name, "no_rangka", data.message[i].no_rangka);
								frappe.model.set_value(child.doctype, child.name, "pemilik", data.message[i].pemilik);
								frappe.model.set_value(child.doctype, child.name, "nama_pemilik", data.message[i].nama_pemilik);
							}
							cur_frm.refresh_field("tagihan_biaya_motor");
						}
					}
	            }
	        });
		}
		
	}
});



var make_payment_entry_stnk= function() {
	return frappe.call({
		method: "wongkar_selling.custom_standard.custom_payment_entry.get_payment_entry_custom_stnk",
		args: {
			"dt": cur_frm.doc.doctype,
			"dn": cur_frm.doc.name
		},
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			// cur_frm.refresh_fields()
		}
	});
}

var make_payment_entry_bpkb= function() {
	return frappe.call({
		method: "wongkar_selling.custom_standard.custom_payment_entry.get_payment_entry_custom_bpkb",
		args: {
			"dt": cur_frm.doc.doctype,
			"dn": cur_frm.doc.name
		},
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			// cur_frm.refresh_fields()
		}
	});
}

var make_payment_entry= function() {
	return frappe.call({
		method: get_method_for_payment(),
		args: {
			"dt": cur_frm.doc.doctype,
			"dn": cur_frm.doc.name
		},
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			// cur_frm.refresh_fields()
		}
	});
}

var get_method_for_payment= function(){
	var method = "wongkar_selling.custom_standard.custom_payment_entry.get_payment_entry_custom";
	//"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
	if(cur_frm.doc.__onload && cur_frm.doc.__onload.make_payment_via_journal_entry){
		if(in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor','Pembayaran Tagihan Motor'],  cur_frm.doc.doctype)){
			method = "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_invoice";
		}else {
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}
	}

	return method
}

//asli
frappe.ui.form.on("Pembayaran Tagihan Motor", "supplier", function(frm) {
    if(cur_frm.doc.supplier && cur_frm.doc.type == "Diskon Dealer"){
    	frappe.call({
             method: "wongkar_selling.wongkar_selling.get_invoice.get_inv",
             args: {
                supplier: cur_frm.doc.supplier,
                types: cur_frm.doc.type,
                date_from: cur_frm.doc.date_from,
                date_to: cur_frm.doc.date_to
             },
             callback: function(data) {
				console.log(data,'data')
				cur_frm.clear_table("tagihan_biaya_motor");
	        	cur_frm.refresh_fields();
				for (let i = 0; i < data.message.length; i++) {
					if (data.message[i].name){
						var child = cur_frm.add_child("tagihan_biaya_motor");
						frappe.model.set_value(child.doctype, child.name, "no_invoice", data.message[i].name);
						frappe.model.set_value(child.doctype, child.name, "tanggal_inv", data.message[i].posting_date);
						frappe.model.set_value(child.doctype, child.name, "type", data.message[i].type);
						frappe.model.set_value(child.doctype, child.name, "nilai", data.message[i].amount);
						frappe.model.set_value(child.doctype, child.name, "terbayarkan", data.message[i].amount);
						frappe.model.set_value(child.doctype, child.name, "item", data.message[i].item_code);
						frappe.model.set_value(child.doctype, child.name, "no_rangka", data.message[i].no_rangka);
						frappe.model.set_value(child.doctype, child.name, "pemilik", data.message[i].pemilik);
						frappe.model.set_value(child.doctype, child.name, "nama_pemilik", data.message[i].nama_pemilik);
					}
				}
				cur_frm.refresh_field("tagihan_biaya_motor");
            }
        });
    } 

    if(!cur_frm.doc.supplier){
    	cur_frm.clear_table("tagihan_biaya_motor");
    	//cur_frm.clear_fields("nama_customer");
    	frm.set_value("nama_vendor",""); 
    	//frm.set_value("type","");
    	frm.set_value("territory","");
        cur_frm.refresh_fields("tagihan_biaya_motor");
    } 
});

var show_general_ledger= function() {
	var me = this;
	if(cur_frm.doc.docstatus > 0) {
		cur_frm.add_custom_button(__('Accounting Ledger'), function() {
			frappe.route_options = {
				voucher_no: cur_frm.doc.name,
				from_date: cur_frm.doc.date,
				to_date: moment(cur_frm.doc.modified).format('YYYY-MM-DD'),
				company: "IFMI Group",
				group_by: "",
				show_cancelled_entries: cur_frm.doc.docstatus === 2
			};
			frappe.set_route("query-report", "General Ledger");
		}, __("View"));
	}
}