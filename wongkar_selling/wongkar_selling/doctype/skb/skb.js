// Copyright (c) 2023, w and contributors
// For license information, please see license.txt

frappe.ui.form.on('SKB', {
	refresh: function(frm) {
		frm.set_df_property("serial_no", "read_only", frm.is_new() ? 0 : 1);
		cur_frm.set_query("serial_no", function(doc) {
			return {
				filters: {
					'Status': 'Delivered'
				}
			}
		});
	}
});
