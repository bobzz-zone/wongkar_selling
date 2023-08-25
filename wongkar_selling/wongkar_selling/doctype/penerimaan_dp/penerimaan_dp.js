// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Penerimaan DP', {
	setup: function(frm) {
		// frm.add_fetch("bank_account", "account", "account");
		frm.ignore_doctypes_on_cancel_all = ['Journal Entry'];
	},
	refresh: function(frm) {
		frm.set_query("debit_to", function() {
			return {
				filters: {
					"account_type": ["in", ['Receivable']],
					"is_group": 0,
					"company": cur_frm.doc.company,
					"disabled": 0
				}
			}
		});

		frm.set_query("coa_bpkb_stnk", function() {
			return {
				filters: {
					"account_type": ["in", ['Receivable']],
					"is_group": 0,
					"company": cur_frm.doc.company,
					"disabled": 0
				}
			}
		});

		frm.set_query("paid_to", function() {
			return {
				filters: {
					"account_type": ["in", ['Bank','Cash']],
					"is_group": 0,
					"company": cur_frm.doc.company,
					"disabled": 0
				}
			}
		});

		// if(cur_frm.doc.docstatus == 1){
		// 	frm.add_custom_button(__("Make SIPM"), function() {
		//         // When this button is clicked, do this
		//         frappe.xcall("wongkar_selling.wongkar_selling.doctype.penerimaan_dp.penerimaan_dp.make_sipm",{
		// 			'name_dp': cur_frm.doc.name
		// 		}).then(sipm =>{
		// 			frappe.model.sync(sipm);
		// 			frappe.set_route('Form', sipm.doctype, sipm.name);
		// 		})
		        
		//     });
		// }
		
	},
	customer(frm) {
		console.log("llooo")
		if(cur_frm.doc.customer)
		erpnext.utils.get_party_details(cur_frm,
		"wongkar_selling.custom_standard.custom_party.get_party_details", {
		// "erpnext.accounts.party.get_party_details", {
			posting_date: cur_frm.doc.tanggal,
			party: cur_frm.doc.customer,
			party_type: "Customer",
			account: cur_frm.doc.debit_to,
			company: 'BJM Group',
			// price_list: cur_frm.doc.selling_price_list,
			// pos_profile: pos_profile
		}, function() {
			// apply_pricing_rule();
		});
	},
	cara_bayar(frm){
		cur_frm.set_value('customer',null)
		cur_frm.set_value('debit_to',null)
		cur_frm.set_value('piutang_motor',0)
		cur_frm.set_value('coa_bpkb_stnk',null)
		cur_frm.set_value('piutang_bpkb_stnk',0)
		cur_frm.set_value('paid_to',null)
		cur_frm.set_value('pemilik',null)
	},
	company(frm) {
		erpnext.accounts.dimensions.update_dimension(cur_frm, cur_frm.doctype);
		let me = this;
		if (cur_frm.doc.company) {
			frappe.call({
				method:
					"erpnext.accounts.party.get_party_account",
				args: {
					party_type: 'Customer',
					party: cur_frm.doc.customer,
					company: cur_frm.doc.company
				},
				callback: (response) => {
					if (response) cur_frm.set_value("debit_to", response.message);
				},
			});
		}
	}
});
