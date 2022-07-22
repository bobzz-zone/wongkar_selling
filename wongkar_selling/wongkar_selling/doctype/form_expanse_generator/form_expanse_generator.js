// Copyright (c) 2022, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Form Expanse Generator', {
	// refresh: function(frm) {

	// }
	validate: function(frm){
		if(cur_frm.doc.expanse_table){
			cek_biaya(cur_frm)
		}
	},
	generate(frm){
		frappe.msgprint("00000")
		frappe.call({
              method: "wongkar_selling.wongkar_selling.doctype.form_expanse_generator.form_expanse_generator.coba",
              args: { 
                  name: cur_frm.doc.name,
                  from_date: cur_frm.doc.from_date,
                  to_date: cur_frm.doc.to_date,
                  coa_inc: cur_frm.doc.coa_income
              },
              callback: function(r) {
                   console.log(r,"asdasdds")
                   cur_frm.clear_table("list_invoice")
                   cur_frm.refresh_fields("list_invoice")
                   cur_frm.clear_table("expanse_table")
                   cur_frm.refresh_fields("expanse_table")
                   var total = 0
                   for(var i=0;i<r.message.length;i++){
                   		var child = cur_frm.add_child("list_invoice");
                        	frappe.model.set_value(child.doctype, child.name, "sales_invoice", r.message[i].name);
                        	frappe.model.set_value(child.doctype, child.name, "nilai", r.message[i].amount);
                   		total = total + r.message[i].amount
                   }
                   cur_frm.refresh_fields("list_invoice")
                   console.log(total,"amount")
                   cur_frm.set_value("total_income",total)

              }
      	})
	}
});

frappe.ui.form.on('Expanse Table', { // The child table is defined in a DoctType called "Dynamic Link"
   expanse_table_add(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event
        // frm: current ToDo form
        // cdt: child DocType 'Dynamic Link'
        // cdn: child docname (something like 'a6dfk76')
        // cdt and cdn are useful for identifying which row triggered this event
        var data = locals[cdt][cdn]
        data.tanggal_posting = cur_frm.doc.default_posting_date
        cur_frm.refresh_fields("expanse_table")

        // frm.set_value("tanggal_posting",cur_frm.doc.default_posting_date)
    },
    biaya(frm, cdt, cdn){
    	frappe.msgprint("biaya")
    	var data = locals[cdt][cdn]
    	data.nilai = cur_frm.doc.total_income * data.biaya / 100
    	 cur_frm.refresh_fields("expanse_table")
    }
});


function cek_biaya(fmr){
	// frappe.msgprint("masuk sini")
	var total = 0
	for(var i=0;i<cur_frm.doc.expanse_table.length;i++){
		total = total + cur_frm.doc.expanse_table[i].biaya
	}
	if(total>100){
		frappe.throw("Biaya yang dimasukkan lebih dari 100 %")
	}
}

// frappe.ui.form.on("Expanse Table", {
// 	tanggal_posting: function(frm, cdt, cdn) {
// 		var row = locals[cdt][cdn];
// 		if (row.tanggal_posting) {
// 			if(!cur_frm.doc.default_posting_date) {
// 				frappe.msgprint("123")
// 				erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "expanse_table", "tanggal_posting");
// 			} else {
// 				frappe.msgprint("else")
// 				set_schedule_date(frm);
// 			}
// 		}
// 	}
// });

// function set_schedule_date(frm) {
// 	frappe.msgprint("456")
// 	if(cur_frm.doc.default_posting_date){
// 		erpnext.utils.copy_value_in_all_rows(cur_frm.doc, cur_frm.doc.doctype, cur_frm.doc.name, "expanse_table", "tanggal_posting");
// 	}
// }