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

		if(cur_frm.doc.docstatus == 1 && !cur_frm.doc.dp_ke_2){
			frm.add_custom_button(__("Make SIPM"), function() {
		        // When this button is clicked, do this
		        frappe.xcall("wongkar_selling.wongkar_selling.doctype.penerimaan_dp.penerimaan_dp.make_sipm",{
					'name_dp': cur_frm.doc.name
				}).then(sipm =>{
					frappe.model.sync(sipm);
					frappe.set_route('Form', sipm.doctype, sipm.name);
				})
		        
		    });
		}
		
	},
	customer(frm) {
		console.log("llooo")
		if(cur_frm.doc.cara_bayar == 'Cash'){
			
			if(cur_frm.doc.customer){
				cur_frm.add_fetch('customer','territory','territory')
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
			}
		}
		
	},
	pemilik(frm) {
		console.log("llooo")
		if(cur_frm.doc.cara_bayar == 'Credit'){
			if(cur_frm.doc.pemilik){
				cur_frm.add_fetch('pemilik','territory','territory')
			}
		}
	},
	item_code(frm){
		if(cur_frm.doc.item_code){
			frappe.call({
				method: "wongkar_selling.wongkar_selling.get_invoice.get_item_price",
				args: {
					item_code: cur_frm.doc.item_code,
					price_list: cur_frm.doc.price_list,
					posting_date: cur_frm.doc.tanggal
				},
				callback: function(r) {
					console.log(r,"safasf")
					if(r.message.length > 0){
						if(r.message[0].price_list_rate){
				    		cur_frm.set_value('harga',r.message[0].price_list_rate)
				    	}
					}else{
						cur_frm.set_value('harga',0)
					}
				}
			});

			frappe.call({
				method: "wongkar_selling.wongkar_selling.get_invoice.get_biaya",
				args: {
					// item_group: cur_frm.doc.item_group,
					item_code: cur_frm.doc.item_code,
					territory: cur_frm.doc.territory,
					posting_date: cur_frm.doc.tanggal,
					from_group: 1
				},
				callback: function(r) {
					console.log(r.message,"get_biaya")
					var total = 0
					if(r.message){
						if(r.message.length >0){
							for(var i =0;i<r.message.length;i++){
								if(r.message[i].type == 'STNK' || r.message[i].type == 'BPKB'){
									total = total + r.message[i].amount
								}
							}
						}
					}
					cur_frm.set_value("bpkb_stnk",total)
				   console.log(total,' total')
				}
			});

			if(cur_frm.doc.nama_promo){
				frappe.call({
					method: "wongkar_selling.wongkar_selling.get_invoice.get_leasing",
					args: {
						// item_group: cur_frm.doc.item_group,
						item_code: cur_frm.doc.item_code,
						nama_promo: cur_frm.doc.nama_promo,
						territory_real: cur_frm.doc.territory,
						posting_date: cur_frm.doc.tanggal,
						from_group:1
					},
					callback: function(r) {
						console.log(r,"leasing")
						if(r.message.length>0){
							for (let i = 0; i < r.message.length; i++) {
								cur_frm.set_value("nominal_diskon",r.message[i].beban_dealer)
							}
						}else{
							cur_frm.set_value("nominal_diskon",0)
						}
						cur_frm.refresh_fields("nominal_diskon")
					}
				});
			}
			
		}
		
	},
	dp_ke_2(frm){
		if(cur_frm.doc.dp_ke_2){
			frappe.msgprint("Lakukan Perhitungan Secara Manual !!!")
		}else{
			// cur_frm.set_value("nominal_diskon",0)
			// cur_frm.refresh_fields("nominal_diskon")
		}
	},
	cara_bayar(frm){
		cur_frm.set_value('customer',null)
		cur_frm.set_value('debit_to',null)
		cur_frm.set_value('piutang_motor',0)
		cur_frm.set_value('coa_bpkb_stnk',null)
		cur_frm.set_value('piutang_bpkb_stnk',0)
		cur_frm.set_value('paid_to',null)
		cur_frm.set_value('pemilik',null)
		cur_frm.set_value("item_code",null)
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
	},
	tanggal(frm){
		cur_frm.set_value("item_code",null)
	},
	territory(frm){
		cur_frm.set_value("item_code",null)
	},
	price_list(frm){
		cur_frm.set_value("item_code",null)
	},
	nama_promo(frm){
		cur_frm.set_value("item_code",null)
	},
	nominal_diskon(frm){
		// cur_frm.set_value("item_code",null)
	},
});
