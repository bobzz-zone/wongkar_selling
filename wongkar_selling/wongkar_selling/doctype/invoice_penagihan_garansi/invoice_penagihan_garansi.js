// Copyright (c) 2024, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Penagihan Garansi', {
	refresh: function(frm) {
		show_general_ledger()
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.outstanding_amount!=0) {
			cur_frm.add_custom_button(__('Payment'),
				// change_value2, __('Create'),
				make_payment_entry, __('Create'));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
	to_date(frm){
		if(cur_frm.doc.to_date){
			cur_frm.clear_table("list_invoice_penagihan_garansi");
			cur_frm.refresh_field("list_invoice_penagihan_garansi");
			frappe.call({
				method:
					"wongkar_selling.wongkar_selling.doctype.invoice_penagihan_garansi.invoice_penagihan_garansi.get_data",
				args: {
					from_date: cur_frm.doc.from_date,
					to_date: cur_frm.doc.to_date
				},
				callback: (r) => {
					console.log(r, ' rrrrr')
					if(r){
						for(var i=0;i<r.message.length;i++){
							var child = cur_frm.add_child("list_invoice_penagihan_garansi");
							frappe.model.set_value(child.doctype, child.name, "sales_invoice_sparepart_garansi", r.message[i].name);
							frappe.model.set_value(child.doctype, child.name, "customer", r.message[i].customer);
							frappe.model.set_value(child.doctype, child.name, "customer_name", r.message[i].customer_name);
							frappe.model.set_value(child.doctype, child.name, "no_rangka", r.message[i].no_rangka_manual_atau_lama);
							frappe.model.set_value(child.doctype, child.name, "no_mesin", r.message[i].no_mesin);
							frappe.model.set_value(child.doctype, child.name, "grand_total", r.message[i].grand_total);
							frappe.model.set_value(child.doctype, child.name, "outstanding_amount", r.message[i].outstanding_amount);
						}
						cur_frm.refresh_field("list_invoice_penagihan_garansi");
					}
				},
			});
		}
	}
});

var show_general_ledger= function() {
	let me = this;
	if(cur_frm.doc.docstatus > 0) {
		cur_frm.add_custom_button(__('Accounting Ledger'), function() {
			frappe.route_options = {
				voucher_no: cur_frm.doc.name,
				from_date: cur_frm.doc.posting_date,
				to_date: moment(cur_frm.doc.modified).format('YYYY-MM-DD'),
				company: cur_frm.doc.company,
				group_by: "Group by Voucher (Consolidated)",
				show_cancelled_entries: cur_frm.doc.docstatus === 2,
				ignore_prepared_report: true
			};
			frappe.set_route("query-report", "General Ledger");
		}, __("View"));
	}
}

var make_payment_entry= async function() {
	// change_value2()

	return frappe.call({
		method: 'wongkar_selling.wongkar_selling.doctype.form_pembayaran.form_pembayaran.get_form_pemabayaran',
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