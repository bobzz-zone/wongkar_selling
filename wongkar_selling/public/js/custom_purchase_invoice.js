frappe.ui.form.on('Purchase Invoice', {
	refresh(frm) {
		// your code here
		if(cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount != 0
			&& !(cur_frm.doc.is_return && cur_frm.doc.return_against) && !cur_frm.doc.on_hold) {
			cur_frm.add_custom_button(
				__('Crate JE Claim'),
				() => make_je(),
				__('Create')
			);
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
	// setup: function(frm) {
	// 	frappe.msgprint('Test 123 !')
	// 	frm.ignore_doctypes_on_cancel_all = ['Stock Entry','Repost Item Valuation'];
	// },
	// onload(frm){
	// 	frappe.msgprint('Test 123xxx !')
	// 	frm.ignore_doctypes_on_cancel_all = [
	// 		"Journal Entry",
	// 		"Payment Entry",
	// 		"Purchase Invoice",
	// 		"Repost Payment Ledger",
	// 		"Repost Accounting Ledger",
	// 		"Unreconcile Payment",
	// 		"Unreconcile Payment Entries",
	// 		"Serial and Batch Bundle",
	// 		"Bank Transaction",
	// 		"Stock Entry"
	// 	];
	// }
})


var make_je= async function() {
	// change_value2()
	console.log('make_je')
	return frappe.call({
		method: 'wongkar_selling.wongkar_selling.doctype.invoice_penagihan_garansi.invoice_penagihan_garansi.make_je_claim',
		args: {
			"dt": cur_frm.doc.doctype,
			"dn": cur_frm.doc.name
		},
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			// cur_frm.refresh_fields()
		}
	});
}