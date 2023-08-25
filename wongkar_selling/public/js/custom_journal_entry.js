frappe.ui.form.on('Journal Entry', {
	refresh(frm) {
		// your code here
	},
	setup: function(frm) {
		frm.ignore_doctypes_on_cancel_all = ['Sales Invoice', 'Purchase Invoice', 'Asset', 'Asset Movement',"Advance Leasing"];
	},
})