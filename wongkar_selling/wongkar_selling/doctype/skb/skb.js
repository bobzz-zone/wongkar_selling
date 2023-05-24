// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('SKB', {
	refresh: function(frm) {
		cur_frm.set_query("serial_no", function(doc) {
			return {
				filters: {
					'Status': 'Delivered'
				}
			}
		});
	}
});
