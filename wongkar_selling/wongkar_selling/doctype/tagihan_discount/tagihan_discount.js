// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tagihan Discount', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Tagihan Discount", "customer", function(frm) {
    frappe.db.get_list('Table Discount',{ filters: { 'rule': cur_frm.doc.customer}, fields: ['*']})
	.then(data => {
		//console.log(data);
		//var no_rangka =""
		// var posting_date =""
		for (let i = 0; i < data.length; i++) {
			
			let coba1 = []
			let coba2 = []
			/*var no_rangka = frappe.db.get_value("Sales Invoice", {"name": data[i].parent}, "no_rangka")
			var posting_date = frappe.db.get_value("Sales Invoice", {"name": data[i].parent}, "posting_date")
			var tgl = moment(posting_date).format("DD-MM-YYYY")
			// var posting_date = frappe.utils.formatdate(temp_from_date, "dd-mm-yyyy");

            console.log(no_rangka)
           //console.log(posting_date)
            console.log(tgl)*/
            
            frappe.db.get_value("Sales Invoice", {"name": data[i].parent}, "no_rangka").then(data2 => { 
            	coba1.push(data2.message.no_rangka)
            	// console.log(no_rangka)
            });
            
            frappe.db.get_value("Sales Invoice", {"name": data[i].parent}, "posting_date")
            .then(data3 => { 
            	//console.log(data3)
            	coba2.push(data3.message.posting_date)
            	//var posting_date = data3.message.posting_date 
            });
            console.log(coba1)
            console.log(coba2)

			var child = cur_frm.add_child("daftar_tagihan");
	        frappe.model.set_value(child.doctype, child.name, "no_sinv", data[i].parent);
	        frappe.model.set_value(child.doctype, child.name, "tanggal_inv", coba2[0]);
	        frappe.model.set_value(child.doctype, child.name, "no_rangka", coba1[0]);
	        frappe.model.set_value(child.doctype, child.name, "type", data[i].type);
            frappe.model.set_value(child.doctype, child.name, "nilai", data[i].nominal);	     
	        cur_frm.refresh_field("daftar_tagihan");
		}
	});
});