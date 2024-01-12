// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Form Pembayaran', {
	refresh: function(frm) {
		show_general_ledger();
		
		if(cur_frm.doc.docstatus==1){
			frm.set_df_property("tagihan_payment_table", "cannot_add_rows", true);
			frm.set_df_property("tagihan_payment_table", "cannot_delete_rows", true);
		}

		frm.set_query("paid_from", function() {
			if(cur_frm.doc.customer){
				return {
					filters: {
						"account_type": ["in", ['Receivable']],
						"is_group": 0,
						"company": cur_frm.doc.company,
						"disabled": 0
					}
				}
			}else if(cur_frm.doc.vendor){
				return {
					filters: {
						"account_type": ["in", ['Bank','Cash']],
						"is_group": 0,
						"company": cur_frm.doc.company,
						"disabled": 0
					}
				}
			}
		});

		frm.set_query("paid_to", function() {
			if(cur_frm.doc.customer){
				return {
					filters: {
						"account_type": ["in", ['Bank','Cash']],
						"is_group": 0,
						"company": cur_frm.doc.company,
						"disabled": 0
					}
				}
			}else if(cur_frm.doc.vendor){
				return {
					filters: {
						"account_type": ["in", ['Payable']],
						"is_group": 0,
						"company": cur_frm.doc.company,
						"disabled": 0
					}
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

		frm.set_query("advance_leasing", function() {
			return {
                filters: {
                    'docstatus': 1,
                    'leasing': cur_frm.doc.customer,
                    'account_credit': cur_frm.doc.paid_to,
                    'sisa': [">",0]
                }
            }
		});

		filter_docname()

		if(cur_frm.doc.type == "Pembayaran Invoice Garansi"){
			removeColumns(cur_frm,['no_sinv'],'tagihan_payment_table')
			removeColumns(cur_frm,['no_rangka'],'tagihan_payment_table')
			showColumns(cur_frm,['sales_invoice_sparepart_garansi'],'tagihan_payment_table')
			showColumns(cur_frm,['no_rangka2'],'tagihan_payment_table')
		}else{
			removeColumns(cur_frm,['sales_invoice_sparepart_garansi'],'tagihan_payment_table')
			showColumns(cur_frm,['no_sinv'],'tagihan_payment_table')
		}

			
	},
	vendor(frm){
		filter_docname()
	},
	customer(frm){
		filter_docname()
	},
	type(frm){
		cur_frm.set_value("customer",null)
		cur_frm.set_value("vendor",null)
		cur_frm.clear_table("list_doc_name")
		cur_frm.clear_table("tagihan_payment_table")
		cur_frm.refresh_fields("list_doc_name")
		cur_frm.refresh_fields("tagihan_payment_table")
		cur_frm.set_value("advance_leasing",null)
		cur_frm.set_value("paid_from",null)
		cur_frm.set_value("paid_to",null)
	},
	mode_of_payment(frm){
		cur_frm.set_value("advance_leasing",null)
		filter_docname()
	},
	paid_to(frm){
		cur_frm.set_value("advance_leasing",null)
		filter_docname()
	},
	paid_from(frm){
		filter_docname()
	},
	setup: function(frm) {
		

	},
	get_data(frm){
		var doc_type = ''
		if(cur_frm.doc.type == 'Pembayaran Diskon'){
			doc_type = 'Tagihan Discount'
		}else if(cur_frm.doc.type == 'Pembayaran Diskon Leasing'){
			doc_type = 'Tagihan Discount Leasing'
		}else if(cur_frm.doc.type == 'Pembayaran Tagihan Leasing'){
			doc_type = 'Tagihan Leasing'
		}else if(cur_frm.doc.type == 'Pembayaran STNK' || cur_frm.doc.type == 'Pembayaran BPKB'){
			doc_type = 'Pembayaran Tagihan Motor'
		}else if(cur_frm.doc.type == 'Pembayaran Invoice Garansi'){
			doc_type = 'Invoice Penagihan Garansi'
		}

		cur_frm.clear_table("tagihan_payment_table")
		cur_frm.refresh_fields("tagihan_payment_table")
		frappe.call({
			method: "wongkar_selling.wongkar_selling.get_invoice.get_tagihan",
			args: {
				"doc_type": doc_type,
				"tipe_pembayaran": cur_frm.doc.type,
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
								frappe.model.set_value(child.doctype, child.name, "sales_invoice_sparepart_garansi",r.message[i][j].sales_invoice_sparepart_garansi);
								frappe.model.set_value(child.doctype, child.name, "pemilik",r.message[i][j].pemilik);
								frappe.model.set_value(child.doctype, child.name, "nama_pemilik", r.message[i][j].nama_pemilik);
								frappe.model.set_value(child.doctype, child.name, "item", r.message[i][j].item);
								frappe.model.set_value(child.doctype, child.name, "no_rangka", r.message[i][j].no_rangka);
								frappe.model.set_value(child.doctype, child.name, "no_rangka2", r.message[i][j].no_rangka2);
								frappe.model.set_value(child.doctype, child.name, "nilai", r.message[i][j].outstanding);
								frappe.model.set_value(child.doctype, child.name, "doc_type", r.message[i][j].parenttype);
								frappe.model.set_value(child.doctype, child.name, "doc_name", r.message[i][j].parent);
								frappe.model.set_value(child.doctype, child.name, "id_detail", r.message[i][j].id_detail);
							}
							
						}
						cur_frm.refresh_fields("tagihan_payment_table")
					}
				}
				
			}
		});
		// }
		
	},
});

frappe.ui.form.on('List Doc Name', { // The child table is defined in a DoctType called "Dynamic Link"
    list_doc_name_add(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event
        // frm: current ToDo form
        // cdt: child DocType 'Dynamic Link'
        // cdn: child docname (something like 'a6dfk76')
        // cdt and cdn are useful for identifying which row triggered this event
    	var d = locals[cdt][cdn]
    	if(cur_frm.doc.type == 'Pembayaran Diskon'){
    		d.reference_doctype = 'Tagihan Discount'
    	}else if(cur_frm.doc.type == 'Pembayaran Diskon Leasing'){
    		d.reference_doctype = 'Tagihan Discount Leasing'
    	}else if(cur_frm.doc.type == 'Pembayaran Tagihan Leasing'){
    		d.reference_doctype = 'Tagihan Leasing'
    	}else if(cur_frm.doc.type == 'Pembayaran STNK' || cur_frm.doc.type == 'Pembayaran BPKB'){
    		d.reference_doctype = 'Pembayaran Tagihan Motor'
    	}else if(cur_frm.doc.type == 'Pembayaran Invoice Garansi'){
			d.reference_doctype = 'Invoice Penagihan Garansi'
		}
    	filter_docname()
	 
        // frappe.msgprint('A row has been added to the links table 🎉 ');
    },
    docname(frm,cdt,cdn){
    	var d = locals[cdt][cdn]
    	console.log('111')
    	if(cur_frm.doc.type == "Pembayaran Diskon"){
    		frappe.db.get_value("Tagihan Discount", {"name": d.docname }, "grand_total")
	        .then(r => { 
	            d.grand_total = r.message.grand_total
	        });

	        frappe.db.get_value("Tagihan Discount", {"name": d.docname }, "outstanding_amount")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount
	        });
    	}else if(cur_frm.doc.type == "Pembayaran Diskon Leasing"){
    		frappe.db.get_value("Tagihan Discount Leasing", {"name": d.docname }, "grand_total")
	        .then(r => { 
	            d.grand_total = r.message.grand_total
	        });

	        frappe.db.get_value("Tagihan Discount Leasing", {"name": d.docname }, "outstanding_amount")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount
	        });
    	}else if(cur_frm.doc.type == 'Pembayaran Tagihan Leasing'){
    		frappe.db.get_value("Tagihan Leasing", {"name": d.docname }, "grand_total")
	        .then(r => { 
	            d.grand_total = r.message.grand_total
	        });

	        frappe.db.get_value("Tagihan Leasing", {"name": d.docname }, "outstanding_amount")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount
	        });
    	}else if(cur_frm.doc.type == 'Pembayaran STNK'){
    		console.log('stnk')
    		frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.docname }, "total_stnk")
	        .then(r => { 
	            d.grand_total = r.message.total_stnk
	        });

	        frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.docname }, "outstanding_amount_stnk")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount_stnk
	        });
    	}else if(cur_frm.doc.type == 'Pembayaran BPKB'){
    		console.log('stnk')
    		frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.docname }, "total_bpkb")
	        .then(r => { 
	            d.grand_total = r.message.total_bpkb
	        });

	        frappe.db.get_value("Pembayaran Tagihan Motor", {"name": d.docname }, "outstanding_amount_bpkb")
	        .then(r => { 
	            d.outstanding = r.message.outstanding_amount_bpkb
	        });
    	}

	    	
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

var filter_docname = function(frm){
	if(cur_frm.doc.type == "Pembayaran Diskon"){
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
	                ['customer','=',cur_frm.doc.customer],
	                ['coa_tagihan_discount','=',cur_frm.doc.paid_from]
	            ]
	        }
        }
	}else if(cur_frm.doc.type == "Pembayaran Diskon Leasing"){
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
	                ['customer','=',cur_frm.doc.customer],
	                ['coa_tagihan_discount_leasing','=',cur_frm.doc.paid_from]
	            ]
	        }
        }
	}else if(cur_frm.doc.type == 'Pembayaran Tagihan Leasing'){
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
	                ['customer','=',cur_frm.doc.customer],
	                ['coa_lawan','=',cur_frm.doc.paid_from]
	            ]
	        }
        }
	} else if(cur_frm.doc.type == 'Pembayaran STNK'){
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
	                ['supplier_stnk','=',cur_frm.doc.vendor],
	                ['coa_biaya_motor_stnk','=',cur_frm.doc.paid_to]
	            ]
	        }
        }
	}else if(cur_frm.doc.type == 'Pembayaran BPKB'){
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
	                ['supplier_bpkb','=',cur_frm.doc.vendor],
	                ['coa_biaya_motor_bpkb','=',cur_frm.doc.paid_to]
	            ]
	        }
        }
	}else if(cur_frm.doc.type == "Pembayaran Invoice Garansi"){
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
	                ['customer','=',cur_frm.doc.customer],
	                ['debit_to','=',cur_frm.doc.paid_from]
	            ]
	        }
        }
	}
}

var showColumns = function(frm, fields, table) {
    let grid = frm.get_field(table).grid;
    let re_render = false

    // Menampilkan kolom yang tersembunyi
    for (let field of fields) {
        grid.fields_map[field].in_list_view = 1;
        re_render = true
    }

    // Mengatur ulang kolom yang terlihat
    grid.visible_columns = undefined;
    grid.setup_visible_columns();
    
    // Menghapus header row dan membuat ulang
    grid.header_row.wrapper.remove();
    delete grid.header_row;
    grid.make_head();
    
    
    // Mengembalikan kolom-kolom yang dihapus pada setiap baris
    for (let row of grid.grid_rows) {
        // Menghapus tombol open form
        row.wrapper.children().children('.grid-static-col').remove()
        row.columns = []
        if (row.open_form_button) {
            row.open_form_button.parent().remove();
            delete row.open_form_button;
        }

        // Menampilkan Column Baru
        row.render_row();
    }
}

var removeColumns = function(frm, fields, table) {
        let grid = frm.get_field(table).grid;
        let re_render = false

        for (let field of fields) {
            // console.log(grid.fields_map[field])
            grid.fields_map[field].in_list_view = 0;
            re_render = true
        }
        
        grid.visible_columns = undefined;
        grid.setup_visible_columns();
        
        grid.header_row.wrapper.remove();
        delete grid.header_row;
        grid.make_head();
        
        for (let row of grid.grid_rows) {
            if (row.open_form_button) {
                row.open_form_button.parent().remove();
                delete row.open_form_button;
            }
            
            for (let field in row.columns) {
                if (row.columns[field] !== undefined) {
                    row.columns[field].remove();
                }
            }
            delete row.columns;
            row.columns = [];
            row.render_row();
        }
}