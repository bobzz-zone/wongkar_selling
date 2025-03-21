// Copyright (c) 2021, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tagihan Discount Leasing', {
	validate: function(frm) {
		// let total = 0
		// let total_sipm = 0
		// if(cur_frm.doc.daftar_tagihan_leasing){
		// 	for (let i = 0; i < cur_frm.doc.daftar_tagihan_leasing.length; i++) {
		// 		total += cur_frm.doc.daftar_tagihan_leasing[i].nilai;
		// 		total_sipm += cur_frm.doc.daftar_tagihan_leasing[i].tagihan_sipm;
		// 	}
		// }
		// frm.set_value('grand_total',total)
		// frm.set_value('base_grand_total',total)
		// frm.set_value('outstanding_amount',total)
		// frm.set_value('total_tagihan_sipm',total_sipm)
		// frm.set_value('total_outstanding_tagihan_sipm',total_sipm)
		
	},
	date_from(frm){
		cur_frm.set_value("customer","")
		cur_frm.refresh_fields("customer")
	},
	date_to(frm){
		cur_frm.set_value("customer","")
		cur_frm.refresh_fields("customer")
	},
	cek_pph(frm){
		cur_frm.set_value('pph',0)
		cur_frm.set_value('pph_account',null)
	},
	refresh: function(frm){
		show_general_ledger();
		frm.set_df_property("daftar_tagihan_leasing", "cannot_add_rows", true);
		// if(cur_frm.doc.__islocal){
		// 	cur_frm.set_value('customer',null)
		// }
		
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount!=0) {
			cur_frm.add_custom_button(__('Payment Tagihan Discount'),
				// change_value2, __('Create'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
			
		}

		// if (cur_frm.doc.docstatus == 1 && cur_frm.doc.total_outstanding_tagihan_sipm!=0) {
		// 	cur_frm.add_custom_button(__('Payment Tagihan SIPM'),
		// 		// change_value, __('Create'),
		// 		make_payment_entry2, __('Create'));
		// 	cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
			
		// }
		

		frm.set_query("coa_tagihan_discount_leasing", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
					account_type: 'Receivable',
					disabled : 0
				}
			};
		});

		frm.set_query("coa_pendapatan_leasing", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
					disabled : 0
				}
			};
		});

		frm.set_query("coa_tagihan_sipm", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
					account_type: 'Receivable',
					disabled : 0
				}
			};
		});
	}
});

// var change_value = async function(){
// 	frappe.call({
// 			method: "wongkar_selling.custom_standard.custom_payment_entry.change_value",
// 			args: {
// 				"dt": cur_frm.doc.doctype,
// 				"dn": cur_frm.doc.name
// 			},
// 			callback: function(r) {
// 				// var doclist = frappe.model.sync(r.message);
// 				// frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
// 				// cur_frm.refresh_fields()
// 			}
// 		});
// }

// var change_value2 = async function(){
// 	frappe.call({
// 			method: "wongkar_selling.custom_standard.custom_payment_entry.change_value_reverse",
// 			args: {
// 				"dt": cur_frm.doc.doctype,
// 				"dn": cur_frm.doc.name
// 			},
// 			callback: function(r) {
// 				// var doclist = frappe.model.sync(r.message);
// 				// frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
// 				// cur_frm.refresh_fields()
// 			}
// 		});

// }

var make_payment_entry2= async function() {
	// change_value()
	
	return frappe.call({
		method: get_method_for_payment2(),
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

var get_method_for_payment2= function(){
	var method = "wongkar_selling.custom_standard.custom_payment_entry.get_payment_entry_custom_sipm";
	//"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
	if(cur_frm.doc.__onload && cur_frm.doc.__onload.make_payment_via_journal_entry){
		if(in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor','Tagihan Discount Leasing'],  cur_frm.doc.doctype)){
			method = "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_invoice";
		}else {
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}
	}

	return method
}

var make_payment_entry= async function() {
	// change_value2()

	return frappe.call({
		method: 'wongkar_selling.wongkar_selling.doctype.form_pembayaran.form_pembayaran.get_form_pemabayaran',
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
	var method = "wongkar_selling.custom_standard.custom_payment_entry.get_payment_entry_custom_tl";
	//"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry";
	if(cur_frm.doc.__onload && cur_frm.doc.__onload.make_payment_via_journal_entry){
		if(in_list(['Sales Invoice', 'Purchase Invoice','Sales Invoice Penjualan Motor','Tagihan Discount Leasing'],  cur_frm.doc.doctype)){
			method = "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_invoice";
		}else {
			method= "erpnext.accounts.doctype.journal_entry.journal_entry.get_payment_entry_against_order";
		}
	}

	return method
}

// asli
frappe.ui.form.on("Tagihan Discount Leasing", "customer", function(frm) {
    // coba = cur_frm.doc.nama_leasing
    if(cur_frm.doc.customer){
    	frappe.call({
             method: "wongkar_selling.wongkar_selling.get_invoice.get_invd_l",
             args: {
                //leasing: cur_frm.doc.leasing,
                customer: cur_frm.doc.customer,
                date_from: cur_frm.doc.date_from,
                date_to: cur_frm.doc.date_to
             },
             callback: function(data) {
             	console.log(data,"data")
					cur_frm.clear_table("daftar_tagihan_leasing");
		        	cur_frm.refresh_fields("daftar_tagihan_leasing");
					for (let i = 0; i < data.message.length; i++) {
						//console.log(data)
						var child = cur_frm.add_child("daftar_tagihan_leasing");
						frappe.model.set_value(child.doctype, child.name, "no_invoice", data.message[i].name);
						frappe.model.set_value(child.doctype, child.name, "tanggal_inv", data.message[i].posting_date);
						frappe.model.set_value(child.doctype, child.name, "no_rangka", data.message[i].no_rangka);
						frappe.model.set_value(child.doctype, child.name, "nama_promo", data.message[i].nama_promo);
						// frappe.model.set_value(child.doctype, child.name, "nilai", data.message[i].total_discoun_leasing);
						// frappe.model.set_value(child.doctype, child.name, "terbayarkan", data.message[i].total_discoun_leasing);
						frappe.model.set_value(child.doctype, child.name, "nilai_diskon", data.message[i].nominal);
						frappe.model.set_value(child.doctype, child.name, "nilai", data.message[i].nominal);
						frappe.model.set_value(child.doctype, child.name, "outstanding_discount", data.message[i].nominal);
						// frappe.model.set_value(child.doctype, child.name, "tagihan_sipm", data.message[i].outstanding_amount);
						// frappe.model.set_value(child.doctype, child.name, "outstanding_sipm", data.message[i].outstanding_amount);
						frappe.model.set_value(child.doctype, child.name, "item", data.message[i].item_code);
						frappe.model.set_value(child.doctype, child.name, "pemilik", data.message[i].pemilik); 
						frappe.model.set_value(child.doctype, child.name, "nama_pemilik", data.message[i].nama_pemilik);       
					}
					cur_frm.refresh_field("daftar_tagihan_leasing");
	         }
        });
    }
    if(!cur_frm.doc.customer){
		cur_frm.clear_table("daftar_tagihan_leasing");
		//frm.set_value("name_leasing",""); 
		//frm.set_value("customer",""); 
    	//frm.set_value("nama_promo","");
    	//frm.set_value("territory","");
        cur_frm.refresh_fields("daftar_tagihan_leasing");
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
				company: cur_frm.doc.company,
				group_by: "",
				show_cancelled_entries: cur_frm.doc.docstatus === 2
			};
			frappe.set_route("query-report", "General Ledger");
		}, __("View"));
	}
}

/*let total =0
let tmp =[]
frappe.db.get_list('Table Disc Leasing',{ filters: {'parent': data[i].name}, fields: ['*']})
.then(data2 => {
	//console.log(data2)
	for (let j = 0; j < data2.length; j++) {
		total = total + data2[j].nominal
		tmp.push(total)
	}
	console.log(tmp)
	//frappe.model.set_value(child.doctype, child.name, "nilai", total);	
});*/