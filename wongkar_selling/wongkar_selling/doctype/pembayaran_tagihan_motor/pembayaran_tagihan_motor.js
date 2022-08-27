// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pembayaran Tagihan Motor', {
	validate: function(frm) {
		let total = 0
		if(cur_frm.doc.tagihan_biaya_motor){
			for (let i = 0; i < cur_frm.doc.tagihan_biaya_motor.length; i++) {
				total += cur_frm.doc.tagihan_biaya_motor[i].nilai;
			}
		}
		frm.set_value('grand_total',total)
		frm.set_value('base_grand_total',total)
		frm.set_value('outstanding_amount',total)
	},
	date_from(frm){
		cur_frm.set_value("supplier","")
		cur_frm.refresh_fields("supplier")
	},
	date_to(frm){
		cur_frm.set_value("supplier","")
		cur_frm.refresh_fields("supplier")
	},
	refresh: function(frm){
		show_general_ledger();
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount!=0) {
			cur_frm.add_custom_button(__('Payment'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
	type:function(frm){
		cur_frm.set_value("supplier","")
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
    if(cur_frm.doc.supplier){
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
						frappe.model.set_value(child.doctype, child.name, "item", data.message[i].item_code);
						frappe.model.set_value(child.doctype, child.name, "no_rangka", data.message[i].no_rangka);
						frappe.model.set_value(child.doctype, child.name, "pemilik", data.message[i].pemilik);
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
				company: "DAS",
				group_by: "",
				show_cancelled_entries: cur_frm.doc.docstatus === 2
			};
			frappe.set_route("query-report", "General Ledger");
		}, __("View"));
	}
}