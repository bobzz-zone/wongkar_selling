// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Leasing', {
	refresh: function(frm) {
		if((cur_frm.doc.docstatus == 1 || cur_frm.doc.docstatus == 2) && cur_frm.doc.sisa > 0 && cur_frm.doc.journal_entry ){
			frm.add_custom_button(__('Make PE'), () => 
				frappe.xcall("wongkar_selling.wongkar_selling.doctype.advance_leasing.advance_leasing.make_pe",{
					'name_fp': cur_frm.doc.name,
					"sisa": cur_frm.doc.sisa,
					"account_debit": cur_frm.doc.account_debit
				}).then(payment_entry =>{
					frappe.model.sync(payment_entry);
					frappe.set_route('Form', payment_entry.doctype, payment_entry.name);
				})
			);
		}

		if(!cur_frm.doc.__islocal && !cur_frm.doc.journal_entry && cur_frm.doc.nilai > 0){
			frm.add_custom_button(__('Make JE'), () => 
				frappe.xcall("wongkar_selling.wongkar_selling.doctype.advance_leasing.advance_leasing.make_je",{
					'name_fp': cur_frm.doc.name,
					"nilai": cur_frm.doc.nilai,
					"tanggal": cur_frm.doc.tanggal,
					"account_debit": cur_frm.doc.account_debit,
					"account_credit": cur_frm.doc.account_credit,
					"leasing": cur_frm.doc.leasing
				}).then(journal_entry =>{
					frappe.model.sync(journal_entry);
					frappe.set_route('Form', journal_entry.doctype, journal_entry.name);
				})
			);
		}

		// if(cur_frm.doc.leasing){
		// 	frm.set_query("journal_entry", function() {
		// 		return {
		// 			query: "wongkar_selling.wongkar_selling.doctype.advance_leasing.advance_leasing.je_query",
		// 			filters: [
		// 				["party","=",frm.doc.leasing],
		//     			["docstatus","=",1],
		//     			["cek_adv_leasing","=",0]
	    // 			]
		// 		}
		// 	});
		// }
		
	},
	// journal_entry(frm){
	// 	if(cur_frm.doc.journal_entry){
	// 		frappe.call({
	// 			method: "wongkar_selling.wongkar_selling.doctype.advance_leasing.advance_leasing.get_je",
	// 			args: {
	// 				name: cur_frm.doc.journal_entry,
	// 			},
	// 			callback: function(r) {
	// 				console.log(r.message)
				
	// 			}
	// 		});
	// 	}
		
	// }
});
