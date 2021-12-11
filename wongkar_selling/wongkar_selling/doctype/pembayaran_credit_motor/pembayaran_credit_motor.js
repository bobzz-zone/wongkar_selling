// Copyright (c) 2021, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pembayaran Credit Motor', {
	validate: function(frm) {
		let total = 0
		if(cur_frm.doc.daftar_credit_motor){
			for (let i = 0; i < cur_frm.doc.daftar_credit_motor.length; i++) {
				total += cur_frm.doc.daftar_credit_motor[i].nilai;
			}
		}
		//frm.set_value('total',total)
		frm.set_value('grand_total',total)
		frm.set_value('base_grand_total',total)
	},
	refresh: function(frm){
		show_general_ledger();
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.grand_total!=0) {
			cur_frm.add_custom_button(__('Payment'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	}
});


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
	var method = "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
	if(cur_frm.doc.__onload && cur_frm.doc.__onload.make_payment_via_journal_entry){
		if(in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor','Pembayaran Credit Motor'],  cur_frm.doc.doctype)){
			method = "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_invoice";
		}else {
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}
	}

	return method
}

//asli
frappe.ui.form.on("Pembayaran Credit Motor", "leasing", function(frm) {
    // coba = cur_frm.doc.nama_leasing
    if(cur_frm.doc.leasing){
    	frappe.call({
             method: "wongkar_selling.wongkar_selling.get_invoice.get_invc",
             args: {
                leasing: cur_frm.doc.name_leasing,
                nama_promo: cur_frm.doc.nama_promo
             },
             callback: function(data) {
					cur_frm.clear_table("daftar_credit_motor");
		        	cur_frm.refresh_fields();
					for (let i = 0; i < data.message.length; i++) {
						//console.log(data)
						var child = cur_frm.add_child("daftar_credit_motor");
				        frappe.model.set_value(child.doctype, child.name, "no_invoice", data.message[i].name);
				        frappe.model.set_value(child.doctype, child.name, "tanggal_inv", data.message[i].posting_date);
				        frappe.model.set_value(child.doctype, child.name, "no_rangka", data.message[i].no_rangka);
				        frappe.model.set_value(child.doctype, child.name, "nama_promo", data.message[i].nama_promo);
						frappe.model.set_value(child.doctype, child.name, "nilai", data.message[i].outstanding_amount);         
					}
					cur_frm.refresh_field("daftar_credit_motor");
	         }
        });
    }
    if(!cur_frm.doc.leasing){
		cur_frm.clear_table("daftar_credit_motor");
		frm.set_value("name_leasing",""); 
    	frm.set_value("nama_promo","");
    	frm.set_value("territory","");
        cur_frm.refresh_fields("daftar_credit_motor");
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
				company: "DAS",
				group_by: "",
				show_cancelled_entries: cur_frm.doc.docstatus === 2
			};
			frappe.set_route("query-report", "General Ledger");
		}, __("View"));
	}
}
