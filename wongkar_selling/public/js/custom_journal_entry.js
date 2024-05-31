frappe.ui.form.on('Journal Entry', {
	refresh(frm) {
		// your code here
		removeColumns(cur_frm,['no_sinv'],'tagihan_payment_table')
		removeColumns(cur_frm,['no_rangka'],'tagihan_payment_table')
		readonlyColumns(cur_frm,['nilai'],'tagihan_payment_table')
		showColumns(cur_frm,['sales_invoice_sparepart_garansi'],'tagihan_payment_table')
		showColumns(cur_frm,['no_rangka2'],'tagihan_payment_table')
	},
	setup: function(frm) {
		frm.ignore_doctypes_on_cancel_all = ['Sales Invoice', 'Purchase Invoice', 'Asset', 'Asset Movement',"Advance Leasing"];
	},
	get_data(frm){
		cur_frm.clear_table("tagihan_payment_table")
		cur_frm.refresh_fields("tagihan_payment_table")
		frappe.call({
			method: "wongkar_selling.wongkar_selling.get_invoice.get_tagihan",
			args: {
				"doc_type": 'Invoice Penagihan Garansi',
				"tipe_pembayaran": 'Pembayaran Invoice Garansi',
				"data": cur_frm.doc.list_doc_name,
				"name_pe": cur_frm.doc.name,
				"paid_from": '',
				"oli": true
				// "dn": cur_frm.doc.name
			},
			callback: function(r) {
				// console.log(r," dataarr")
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
								frappe.model.set_value(child.doctype, child.name, "cek_realisasi", 1);
								
							}
							
						}
						cur_frm.refresh_fields("tagihan_payment_table")
					}
				}
				
			}
		});
		// }
	},
	calculate(frm){
		var tmp = []
		if(cur_frm.doc.accounts){
			if(cur_frm.doc.accounts[0]){
				tmp.push(cur_frm.doc.accounts[0])
			}
		}
		var tmp_dict = []

		
		// console.log(tmp, ' tmppushxxx')
		frappe.call({
			method:
				"wongkar_selling.wongkar_selling.doctype.invoice_penagihan_garansi.invoice_penagihan_garansi.make_data_claim",
			args: {
				data: cur_frm.doc.tagihan_payment_table,
				data_awal : tmp,
				company: cur_frm.doc.company
			},
			callback: (r) => {
				// console.log(r, ' rrrrr')
				if(r.message && r.message.length > 0){
					cur_frm.clear_table('accounts')
					cur_frm.refresh_fields('accounts')
					for(var i =0;i<r.message.length;i++){
						// console.log(r.message[i],' pppxx')
						var child = cur_frm.add_child("accounts");
     
			            frappe.model.set_value(child.doctype, child.name, "account", r.message[i].account)
			            frappe.model.set_value(child.doctype, child.name, "party_type", r.message[i].party_type)
			            frappe.model.set_value(child.doctype, child.name, "party", r.message[i].party)
			            frappe.model.set_value(child.doctype, child.name, "reference_type", r.message[i].reference_type)
			            frappe.model.set_value(child.doctype, child.name, "reference_name", r.message[i].reference_name)			            
			            frappe.model.set_value(child.doctype, child.name, "cost_center", r.message[i].cost_center)
			            frappe.model.set_value(child.doctype, child.name, "debit", r.message[i].debit)
			            frappe.model.set_value(child.doctype, child.name, "debit_in_account_currency", r.message[i].debit_in_account_currency)
			            frappe.model.set_value(child.doctype, child.name, "credit", r.message[i].credit)
			            frappe.model.set_value(child.doctype, child.name, "credit_in_account_currency", r.message[i].credit_in_account_currency)
					}
					cur_frm.refresh_field("accounts")
				}
			},
		});
		
	}
})


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

var readonlyColumns = function(frm, fields, table) {
    let grid = frm.get_field(table).grid;
    let re_render = false

    // Menampilkan kolom yang tersembunyi
    for (let field of fields) {
        grid.fields_map[field].read_only = 1;
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