frappe.ui.form.on('Purchase Order', {
	refresh(frm) {
		// your code here
		// frm.set_query("invoice_penagihan_garansi", function(doc) {
		// 	console.log('eeee')
		// 	console.log(doc.items, ' docxx')
		// 	var tmp = []
				
		// 	if(doc.items && doc.items.length >0){
		// 		for(var i=0;i<doc.items.length;i++){
		// 			tmp.push(doc.items[i].item_code)
		// 		}
		// 		console.log(tmp,' tmpxxx')
		// 	}
		// 	return {
		// 			query: "wongkar_selling.wongkar_selling.doctype.invoice_penagihan_garansi.invoice_penagihan_garansi.get_inv",
		// 			filters: {
		// 				'data': tmp
		// 			}
		// 	}
		// 	// if(frm.doc.party_type == 'Employee'){
		// 	// 	return {
		// 	// 		query: "erpnext.controllers.queries.employee_query"
		// 	// 	}
		// 	// }
		// 	// else if(frm.doc.party_type == 'Customer'){
		// 	// 	return {
		// 	// 		query: "erpnext.controllers.queries.customer_query"
		// 	// 	}
		// 	// }
		// });
	}
})

frappe.ui.form.on('List Doc Name', {
	refresh(frm) {
		// your code here
	},
	list_doc_name_add(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event
        // frm: current ToDo form
        // cdt: child DocType 'Dynamic Link'
        // cdn: child docname (something like 'a6dfk76')
        // cdt and cdn are useful for identifying which row triggered this event
    	var d = locals[cdt][cdn]
    	d.reference_doctype = 'Invoice Penagihan Garansi'
    	filter_docname()
        // frappe.msgprint('A row has been added to the links table 🎉 ');
    },
    docname(frm,cdt,cdn){
    	filter_docname()
    }
})

var filter_docname = function(frm){
	cur_frm.fields_dict['list_doc_name'].grid.get_field('docname').get_query = function(doc, cdt, cdn) {
   		var child = locals[cdt][cdn];
        // console.log(child);
    	var tmp = []
    	var child_names = [];
		if (cur_frm.doc.list_doc_name){
			for (var i = 0; i < cur_frm.doc.list_doc_name.length; i++) {
				if (cur_frm.doc.list_doc_name[i].docname){
					child_names.push(cur_frm.doc.list_doc_name[i].docname);
				}
			}
		}

		if(cur_frm.doc.items && cur_frm.doc.items.length >0){
			for(var i=0;i<cur_frm.doc.items.length;i++){
				tmp.push(cur_frm.doc.items[i].item_code)
			}
			console.log(tmp,' tmpxxx')
		}
		return {
				query: "wongkar_selling.wongkar_selling.doctype.invoice_penagihan_garansi.invoice_penagihan_garansi.get_inv",
				filters: {
					'data': tmp,
					'data_name': child_names
				}
		}
    }
}
