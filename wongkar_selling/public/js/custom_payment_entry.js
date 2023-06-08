frappe.ui.form.on('Tagihan Payment Table', {
	refresh(frm) {
		// your code here

	},
	nilai:function(frm,cdt,cdn){
		//frappe.msgprint("tes")



		var total = 0
		for(var i = 0;i<cur_frm.doc.tagihan_payment_table.length;i++){
			total = total + cur_frm.doc.tagihan_payment_table[i].nilai
		}
		cur_frm.set_value("paid_amount",total)
		cur_frm.refresh_field("paid_amount")
	}
})

frappe.ui.form.on('Payment Entry', {
	// payment_type(frm){
	// 	cur_frm.set_value("doc_type","")
	// 	cur_frm.refresh_fields("doc_type")
	// 	if(cur_frm.doc.payment_type== "Receive"){
	// 		cur_frm.set_df_property("doc_type", "options", ["Tagihan Discount Leasing","Tagihan Discount"]);
	// 	}else if(cur_frm.doc.payment_type== "Pay"){
	// 		cur_frm.set_df_property("doc_type", "options", ["Pembayaran Tagihan Motor"]);
	// 	}
	// },
	// doc_type(frm){
	// 	console.log("xxxx")
	// 	cur_frm.set_value("tipe_pembayaran","")
	// 	cur_frm.refresh_fields("tipe_pembayaran")
	// 	if(cur_frm.doc.doc_type == "Tagihan Discount Leasing"){
	// 		cur_frm.set_df_property("tipe_pembayaran", "options", ["Pembayaran Diskon Leasing","Pembayaran SIPM"]);
	// 	}else if(cur_frm.doc.doc_type == "Pembayaran Tagihan Motor"){
	// 		cur_frm.set_df_property("tipe_pembayaran", "options", ["Pembayaran STNK","Pembayaran BPKB","Pembayaran Diskon Dealer"]);
	// 	}else{
	// 		cur_frm.set_value("tipe_pembayaran","Pembayaran Diskon")
	// 	}
		
	// },
	after_save(frm){
		
		
	},
	validate(frm){
		var total = 0
		if(cur_frm.doc.tagihan_payment_table){
			if(cur_frm.doc.tagihan_payment_table.length > 1){
				for(var i = 0;i<cur_frm.doc.tagihan_payment_table.length;i++){
					total = total + cur_frm.doc.tagihan_payment_table[i].nilai
				}
				cur_frm.set_value("paid_amount",total)
				cur_frm.refresh_field("paid_amount")
			}
		}
		
		
	},
	before_save(frm){
//		if (!cur_frm.doc.references){return;}
		try{
			for(var i = 0;i<cur_frm.doc.references.length;i++){
				var tmp = [0]
				var hit = 0
				for(var j = 0;j<cur_frm.doc.tagihan_payment_table.length;j++){
					if(cur_frm.doc.references[i].reference_name == cur_frm.doc.tagihan_payment_table[j].doc_name){
						hit = hit + cur_frm.doc.tagihan_payment_table[j].nilai
						// cur_frm.doc.references[i].allocated_amount = hit
						tmp.push(cur_frm.doc.tagihan_payment_table[j].nilai)
					}
					if(cur_frm.doc.references[i].reference_name == cur_frm.doc.tagihan_payment_table[j].doc_name){
						cur_frm.doc.references[i].allocated_amount = hit
					}
				}
				console.log(tmp,'tmp')
			}

			if(cur_frm.doc.doc_type){
				if(cur_frm.doc.doc_type == "Pembayaran Tagihan Motor"){
					if(cur_frm.doc.payment_type != "Pay"){
						frappe.throw("Salah Memilih Payment Tyepe")
					}
				}else{
					if(cur_frm.doc.payment_type != "Receive"){
						frappe.throw("Salah Memilih Payment Tyepe")
					}
				}
			}
		}catch(err){}
	},
	refresh(frm) {
		// your code here
		frappe.msgprint("asasas")
		if(cur_frm.doc.docstatus == 1 && cur_frm.doc.pemilik){
			frm.add_custom_button(__("Make SIPM"), function() {
		        // When this button is clicked, do this
		        frappe.xcall("wongkar_selling.custom_standard.custom_payment_entry.make_sipm",{
					'name_pe': cur_frm.doc.name
				}).then(sipm =>{
					frappe.model.sync(sipm);
					frappe.set_route('Form', sipm.doctype, sipm.name);
				})
		        
		    });
		}
		

		cur_frm.set_query("doc_type", function() {
                return {
                    filters: {
                        'name': ["in",["Pembayaran Tagihan Motor","Tagihan Discount Leasing","Tagihan Discount"]]
                    }
                }
        });

        
        frm.set_query("pemilik", function() {
			return {
				query: "erpnext.controllers.queries.customer_query"
			}
		});
		
		if(cur_frm.doc.doc_type == "Pembayaran Tagihan Motor" && cur_frm.doc.tipe_pembayaran == "Pembayaran STNK"){
			// frappe.msgprint("test 123")
			cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
		   		var child = locals[cdt][cdn];
		        // console.log(child);
		    	
		    	var child_names = [];
				if (cur_frm.doc.list_doc_name){
					for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
						if (cur_frm.doc.list_doc_name[i].docname){
							child_names.push(cur_frm.doc.list_doc_name[i].docname);
						}
					}
				}
		        return {    
		            filters:[
		                ["name","NOT IN",child_names],
		                ['docstatus', '=', 1],
		                ['outstanding_amount_stnk', '>',0],
		                ['supplier_stnk','=',cur_frm.doc.party],
		                ['coa_biaya_motor_stnk','=',cur_frm.doc.paid_to]
		            ]
		        }
	        }
		}else if(cur_frm.doc.doc_type == "Pembayaran Tagihan Motor" && cur_frm.doc.tipe_pembayaran == "Pembayaran BPKB"){
			// frappe.msgprint("test")
			cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
		   		var child = locals[cdt][cdn];
		        // console.log(child);
		    	
		    	var child_names = [];
				if (cur_frm.doc.list_doc_name){
					for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
						if (cur_frm.doc.list_doc_name[i].docname){
							child_names.push(cur_frm.doc.list_doc_name[i].docname);
						}
					}
				}
		        return {    
		            filters:[
		                ["name","NOT IN",child_names],
		                ['docstatus', '=', 1],
		                ['outstanding_amount_bpkb', '>',0],
		                ['supplier_bpkb','=',cur_frm.doc.party],
		                ['coa_biaya_motor_bpkb','=',cur_frm.doc.paid_to]
		            ]
		        }
	        }
		}else if(cur_frm.doc.doc_type == "Pembayaran Tagihan Motor" && cur_frm.doc.tipe_pembayaran == "Pembayaran Diskon Dealer"){
			// frappe.msgprint("test")
			cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
		   		var child = locals[cdt][cdn];
		        // console.log(child);
		    	
		    	var child_names = [];
				if (cur_frm.doc.list_doc_name){
					for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
						if (cur_frm.doc.list_doc_name[i].docname){
							child_names.push(cur_frm.doc.list_doc_name[i].docname);
						}
					}
				}
		        return {    
		            filters:[
		                ["name","NOT IN",child_names],
		                ['docstatus', '=', 1],
		                ['outstanding_amount', '>',0],
		                ['supplier','=',cur_frm.doc.party],
		                ['coa_biaya_motor','=',cur_frm.doc.paid_to]
		            ]
		        }
	        }
		}else if(cur_frm.doc.doc_type == "Tagihan Discount Leasing" && cur_frm.doc.tipe_pembayaran == "Pembayaran Diskon Leasing"){
			// frappe.msgprint("test")
			cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
		   		var child = locals[cdt][cdn];
		        // console.log(child);
		    	
		    	var child_names = [];
				if (cur_frm.doc.list_doc_name){
					for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
						if (cur_frm.doc.list_doc_name[i].docname){
							child_names.push(cur_frm.doc.list_doc_name[i].docname);
						}
					}
				}
		        return {    
		            filters:[
		                ["name","NOT IN",child_names],
		                ['docstatus', '=', 1],
		                ['outstanding_amount', '>',0],
		                ['customer','=',cur_frm.doc.party],
		                ['coa_tagihan_discount_leasing','=',cur_frm.doc.paid_from]
		            ]
		        }
	        }
		}else if(cur_frm.doc.doc_type == "Tagihan Discount Leasing" && cur_frm.doc.tipe_pembayaran == "Pembayaran SIPM"){
			// frappe.msgprint("test")
			cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
		   		var child = locals[cdt][cdn];
		        // console.log(child);
		    	
		    	var child_names = [];
				if (cur_frm.doc.list_doc_name){
					for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
						if (cur_frm.doc.list_doc_name[i].docname){
							child_names.push(cur_frm.doc.list_doc_name[i].docname);
						}
					}
				}
		        return {    
		            filters:[
		                ["name","NOT IN",child_names],
		                ['docstatus', '=', 1],
		                ['total_outstanding_tagihan_sipm', '>',0],
		                ['customer','=',cur_frm.doc.party],
		                ['coa_tagihan_sipm','=',cur_frm.doc.paid_from]
		            ]
		        }
	        }
		}else if(cur_frm.doc.doc_type == "Tagihan Discount" && cur_frm.doc.tipe_pembayaran == "Pembayaran Diskon"){
			// frappe.msgprint("test")
			cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
		   		var child = locals[cdt][cdn];
		        // console.log(child);
		    	
		    	var child_names = [];
				if (cur_frm.doc.list_doc_name){
					for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
						if (cur_frm.doc.list_doc_name[i].docname){
							child_names.push(cur_frm.doc.list_doc_name[i].docname);
						}
					}
				}
		        return {    
		            filters:[
		                ["name","NOT IN",child_names],
		                ['docstatus', '=', 1],
		                ['outstanding_amount', '>',0],
		                ['customer','=',cur_frm.doc.party],
		                ['coa_tagihan_discount','=',cur_frm.doc.paid_from]
		            ]
		        }
	        }
		}

       
	},
	get_data(frm){
		cur_frm.clear_table("references")
		cur_frm.refresh_fields("references")
		
		if(cur_frm.doc.list_doc_name){
			if(cur_frm.doc.list_doc_name.length > 0){
				for(var i =0;i<cur_frm.doc.list_doc_name.length;i++){
					var child = cur_frm.add_child("references");
					frappe.model.set_value(child.doctype, child.name, "reference_doctype", cur_frm.doc.list_doc_name[i].reference_doctype);
					frappe.model.set_value(child.doctype, child.name, "reference_name", cur_frm.doc.list_doc_name[i].docname);
					frappe.model.set_value(child.doctype, child.name, "total_amount", cur_frm.doc.list_doc_name[i].grand_total);
					frappe.model.set_value(child.doctype, child.name, "outstanding_amount", cur_frm.doc.list_doc_name[i].outstanding);
					frappe.model.set_value(child.doctype, child.name, "allocated_amount", cur_frm.doc.list_doc_name[i].outstanding);
				}
				cur_frm.refresh_fields("references")
			}
		}
		// cur_frm.save()

		cur_frm.clear_table("tagihan_payment_table")
		cur_frm.refresh_fields("tagihan_payment_table")
		// if (!cur_frm.doc.__islocal){
		frappe.call({
			method: "wongkar_selling.wongkar_selling.get_invoice.get_tagihan",
			args: {
				"doc_type": cur_frm.doc.doc_type,
				"tipe_pembayaran": cur_frm.doc.tipe_pembayaran,
				"data": cur_frm.doc.list_doc_name,
				"name_pe": cur_frm.doc.name,
				"paid_from": cur_frm.doc.paid_from
				// "dn": cur_frm.doc.name
			},
			callback: function(r) {
				console.log(r," dataarr")
				if(r.message){
					if(r.message.length>0){
						for(var i=0;i<r.message.length;i++){
							for( var j=0;j<r.message[i].length;j++){
								var child = cur_frm.add_child("tagihan_payment_table");
								frappe.model.set_value(child.doctype, child.name, "no_sinv",r.message[i][j].no_invoice);
								frappe.model.set_value(child.doctype, child.name, "pemilik",r.message[i][j].pemilik);
								frappe.model.set_value(child.doctype, child.name, "nama_pemilik", r.message[i][j].nama_pemilik);
								frappe.model.set_value(child.doctype, child.name, "item", r.message[i][j].item);
								frappe.model.set_value(child.doctype, child.name, "no_rangka", r.message[i][j].no_rangka);
								frappe.model.set_value(child.doctype, child.name, "nilai", r.message[i][j].outstanding);
								frappe.model.set_value(child.doctype, child.name, "doc_type", r.message[i][j].parenttype);
								frappe.model.set_value(child.doctype, child.name, "doc_name", r.message[i][j].parent);
							}
							
						}
						cur_frm.refresh_fields("tagihan_payment_table")
					}
				}
				
			}
		});
		// }
		
	},
	tagihan(frm){
		cur_frm.set_value("doc_type","")
		cur_frm.refresh_fields("doc_type")
	},
	doc_type(frm){
		console.log("kjanjksabdijsabdfui")
		cur_frm.set_value("tipe_pembayaran","")
		cur_frm.refresh_fields("tipe_pembayaran")
		if(!cur_frm.doc.doc_type){
			cur_frm.set_value("tipe_pembayaran","")
			cur_frm.clear_table("list_doc_name")
			cur_frm.refresh_fields("tipe_pembayaran")
			cur_frm.refresh_fields("list_doc_name")
		}else{
			
			if(cur_frm.doc.doc_type == "Tagihan Discount Leasing"){
				cur_frm.set_df_property("tipe_pembayaran", "options", ["Pembayaran Diskon Leasing","Pembayaran SIPM"]);
			}else if(cur_frm.doc.doc_type == "Pembayaran Tagihan Motor"){
				cur_frm.set_df_property("tipe_pembayaran", "options", ["Pembayaran STNK","Pembayaran BPKB","Pembayaran Diskon Dealer"]);
			}else if(cur_frm.doc.doc_type == 'Tagihan Discount'){
				cur_frm.set_df_property("tipe_pembayaran", "options", ["Pembayaran Diskon"]);
				cur_frm.set_value("tipe_pembayaran","Pembayaran Diskon")
			}
			
		}
		
	}
})

frappe.ui.form.on('List Doc Name', { // The child table is defined in a DoctType called "Dynamic Link"
    list_doc_name_add(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event
        // frm: current ToDo form
        // cdt: child DocType 'Dynamic Link'
        // cdn: child docname (something like 'a6dfk76')
        // cdt and cdn are useful for identifying which row triggered this event
    	var d = locals[cdt][cdn]
    	d.reference_doctype = cur_frm.doc.doc_type
	 
        // frappe.msgprint('A row has been added to the links table 🎉 ');
    },
    reference_name(frm,cdt,cdn){
    	var d = locals[cdt][cdn]
    	if(cur_frm.doc.tipe_pembayaran == "Pembayaran STNK"){
    		frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.reference_name }, "total_stnk")
	        .then(r => { 
	            d.grand_total = r.message.total_stnk
	        });

	        frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.reference_name }, "outstanding_amount_stnk")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount_stnk
	        });
    	}else if(cur_frm.doc.tipe_pembayaran == "Pembayaran BPKB"){
    		frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.reference_name }, "total_bpkb")
	        .then(r => { 
	            d.grand_total = r.message.total_bpkb
	        });

	        frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.reference_name }, "outstanding_amount_bpkb")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount_bpkb
	        });
    	}else if(cur_frm.doc.tipe_pembayaran == "Pembayaran Diskon Dealer"){
    		frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.reference_name }, "grand_total")
	        .then(r => { 
	            d.grand_total = r.message.grand_total
	        });

	        frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.reference_name }, "outstanding_amount")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount
	        });
    	}else if(cur_frm.doc.tipe_pembayaran == "Pembayaran Diskon Leasing"){
    		frappe.db.get_value("Tagihan Discount Leasing", {"name": d.reference_name }, "grand_total")
	        .then(r => { 
	            d.grand_total = r.message.grand_total
	        });

	        frappe.db.get_value("Tagihan Discount Leasing", {"name": d.reference_name }, "outstanding_amount")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount
	        });
    	}else if(cur_frm.doc.tipe_pembayaran == "Pembayaran SIPM"){
    		frappe.db.get_value("Tagihan Discount Leasing", {"name": d.reference_name }, "total_tagihan_sipm")
	        .then(r => { 
	            d.grand_total = r.message.total_tagihan_sipm
	        });

	        frappe.db.get_value("Tagihan Discount Leasing", {"name": d.reference_name }, "total_outstanding_tagihan_sipm")
	        .then(r => { 
	            d.outstanding = r.message.total_outstanding_tagihan_sipm
	        });
    	}else if(cur_frm.doc.tipe_pembayaran == "Pembayaran Diskon"){
    		frappe.db.get_value("Tagihan Discount", {"name": d.reference_name }, "grand_total")
	        .then(r => { 
	            d.grand_total = r.message.grand_total
	        });

	        frappe.db.get_value("Tagihan Discount", {"name": d.reference_name }, "outstanding_amount")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount
	        });
    	}

	    	
    }
});

function get_nilai(frm){
	// frappe.msgprint("est")
}


frappe.ui.form.on('Payment Entry Reference', {
	reference_doctype: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frm.events.validate_reference_document(frm, row);
	},

	reference_name: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if(!cur_frm.doc.doc_type){
			console.log(1)
			if (row.reference_name && row.reference_doctype) {
				if(!cur_frm.doc.doc_type){
					return frappe.call({
						method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_reference_details",
						args: {
							reference_doctype: row.reference_doctype,
							reference_name: row.reference_name,
							party_account_currency: frm.doc.payment_type=="Receive" ?
								frm.doc.paid_from_account_currency : frm.doc.paid_to_account_currency
						},
						callback: function(r, rt) {
							if(r.message) {
								$.each(r.message, function(field, value) {
									frappe.model.set_value(cdt, cdn, field, value);
								})

								let allocated_amount = frm.doc.unallocated_amount > row.outstanding_amount ?
									row.outstanding_amount : frm.doc.unallocated_amount;

								frappe.model.set_value(cdt, cdn, 'allocated_amount', allocated_amount);
								frm.refresh_fields();
							}
						}
					})
				}
			
			}
		}
		
	},

	allocated_amount: function(frm) {
		frm.events.set_total_allocated_amount(frm);
	},

	references_remove: function(frm) {
		frm.events.set_total_allocated_amount(frm);
	}
})
