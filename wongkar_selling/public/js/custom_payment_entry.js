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
	refresh(frm) {
		// your code here
		// cur_frm.set_query("sales_invoice_penjualan_motor", function() {
  //            return {
  //                filters: [
  //                    ['docstatus', '=', 0],
  //                    ['total_advance', '<=', 0]
  //                ]
  //            }
  //       });
	},
	// sales_invoice_penjualan_motor:function(frm){
	// 	if(!cur_frm.doc.sales_invoice_penjualan_motor){
	// 		// frappe.msgprint("123")
	// 		cur_frm.set_value("party","")
	// 		//cur_frm.refresh_field("party")
	// 		cur_frm.set_value("party_type","")
	// 		//cur_frm.refresh_field("party_type")
	// 	}
	// 	cur_frm.set_value("party_type","Customer")
	// 	//cur_frm.refresh_field("party_type")
	// 	if(cur_frm.doc.sales_invoice_penjualan_motor){
	// 		frappe.db.get_value("Sales Invoice Penjualan Motor", {"name": cur_frm.doc.sales_invoice_penjualan_motor}, "customer")
	//         .then(r => { 
	//         	if(r.message.customer){
	//         		// frappe.msgprint("masuk sini")
	//         		cur_frm.set_value("party",r.message.customer)
	//             	//cur_frm.refresh_field("party")
	//         	}
	//         });
	// 	}

	// 	// pemilik
	// 	// if(cur_frm.doc.sales_invoice_penjualan_motor){
	// 	// 	frappe.db.get_value("Sales Invoice Penjualan Motor", {"name": cur_frm.doc.sales_invoice_penjualan_motor}, "pemilik")
	//  //        .then(r => { 
	//  //        	if(r.message.pemilik){
	//  //        		// frappe.msgprint("masuk sini")
	//  //        		cur_frm.set_value("party",r.message.pemilik)
	//  //            	//cur_frm.refresh_field("party")
	//  //        	}
	//  //        });
	// 	// }
		
 //        // frappe.db.get_value("Sales Invoice Penjualan Motor", {"name": cur_frm.doc.sales_invoice_penjualan_motor}, "debit_to")
 //        // .then(r => { 
 //        // 	// frappe.msgprint("456")
 //        // 	console.log(r.message.debit_to,"debit")
 //        //     cur_frm.set_value("paid_from","")
 //        //     cur_frm.refresh_field("paid_from")
 //        // });
	// },
	// paid_from:function(frm){
	// 	// cur_frm.set_value("paid_from","")
 //  		// cur_frm.refresh_field("paid_from")
 //        frappe.db.get_value("Sales Invoice Penjualan Motor", {"name": cur_frm.doc.sales_invoice_penjualan_motor}, "debit_to")
 //        .then(r => { 
 //        	// frappe.msgprint("456")	
 //        	// console.log(r.message.debit_to,"debit")
 //            cur_frm.set_value("paid_from",r.message.debit_to)
 //            // cur_frm.refresh_field("paid_from")
 //        });
	// },
	// down_payment:function(frm){
	// 	cur_frm.set_value("sales_invoice_penjualan_motor","")
	// 	//cur_frm.refresh_field("sales_invoice_penjualan_motor")
	// }
})