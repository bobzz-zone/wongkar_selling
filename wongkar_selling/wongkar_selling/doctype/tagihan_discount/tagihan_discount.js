// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tagihan Discount', {
	validate: function(frm) {
		let total = 0
		if(cur_frm.doc.daftar_tagihan){
			for (let i = 0; i < cur_frm.doc.daftar_tagihan.length; i++) {
				total += cur_frm.doc.daftar_tagihan[i].nilai;
			}
		}
		frm.set_value('grand_total',total)
		frm.set_value('base_grand_total',total)
		frm.set_value('outstanding_amount',total)
		//frm.set_value('status',total)
	},
	date_from(frm){
		cur_frm.set_value("customer","")
		cur_frm.refresh_fields("customer")
	},
	date_to(frm){
		cur_frm.set_value("customer","")
		cur_frm.refresh_fields("customer")
	},
	refresh: function(frm){
		show_general_ledger();
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount!=0) {
			cur_frm.add_custom_button(__('Payment'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	}/*,
	before_submit: function(frm){
		cur_frm.set_value('status','Submitted')
	}*/
});

var make_payment_entry= function() {
	return frappe.call({
		method: get_method_for_payment(),
		args: {
			"dt": cur_frm.doc.doctype,
			"dn": cur_frm.doc.name
		},
		callback: function(r) {
			console.log(r,r)
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
		if(in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor','Tagihan Discount'],  cur_frm.doc.doctype)){
			method = "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_invoice";
		}else {
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}
	}

	return method
}

// asli
frappe.ui.form.on("Tagihan Discount", "customer", function(frm) {
    if(cur_frm.doc.customer){
    	console.log("tgatsdg")
    	frappe.call({
             method: "wongkar_selling.wongkar_selling.get_invoice.get_invd",
             args: {
                customer: cur_frm.doc.customer,
                date_from: cur_frm.doc.date_from,
                date_to: cur_frm.doc.date_to
             },
             callback: function(data) {
             	console.log(data,"data")
				cur_frm.clear_table("daftar_tagihan");
	        	cur_frm.refresh_fields();
				for (let i = 0; i < data.message.length; i++) {
					if (data.message[i].name){
						var child = cur_frm.add_child("daftar_tagihan");
						frappe.model.set_value(child.doctype, child.name, "no_sinv", data.message[i].name);
						frappe.model.set_value(child.doctype, child.name, "tanggal_inv", data.message[i].posting_date);
						frappe.model.set_value(child.doctype, child.name, "type", data.message[i].category_discount);
						frappe.model.set_value(child.doctype, child.name, "nilai", data.message[i].nominal);
						frappe.model.set_value(child.doctype, child.name, "item", data.message[i].item_code);
						frappe.model.set_value(child.doctype, child.name, "no_rangka", data.message[i].no_rangka);
						frappe.model.set_value(child.doctype, child.name, "pemilik", data.message[i].pemilik);
						
					}
				}
				cur_frm.refresh_field("daftar_tagihan");
            }
        });
    } 
    if(!cur_frm.doc.customer){
    	cur_frm.clear_table("daftar_tagihan");
    	//cur_frm.clear_fields("nama_customer");
    	//frm.set_value("customer",""); 
    	frm.set_value("type","");
    	frm.set_value("territory","");
        cur_frm.refresh_fields("daftar_tagihan");
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