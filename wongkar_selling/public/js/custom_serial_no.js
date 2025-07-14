frappe.ui.form.on('Serial No', {
	refresh(frm) {
		// your code here
		// frappe.msgprint('askjdokajd')
		show_general_ledger()
	},
	validate(frm){
	    // frappe.msgprint("test")
	    // if(cur_frm.doc.delivery_document_type == 'Sales Invoice Penjualan Motor'){
	    //     cur_frm.set_value("sales_invoice","")
	    //     cur_frm.set_value("sales_invoice_penjualan_motor",cur_frm.doc.delivery_document_no)
	    //     cur_frm.refresh_fields("sales_invoice")
	    //     cur_frm.refresh_fields("sales_invoice_penjualan_motor")
	    // }
	    
	}
})

var show_general_ledger= function() {
	var me = this;
	if(cur_frm.doc.docstatus == 0) {
		cur_frm.add_custom_button(__('Document Refernce'), function() {
			frappe.route_options = {
				serial_no: cur_frm.doc.name,
			};
			frappe.set_route("query-report", "Serial No Reference");
		}, __("View"));
	}
}