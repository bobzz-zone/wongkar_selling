// Copyright (c) 2021, Wongkar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rule Discount Leasing', {
	refresh: function(frm) {
		frm.fields_dict['table_discount_leasing'].grid.get_field('coa').get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        // console.log(child);
            return {    
                filters:[
                    ['is_group', '=', 0]
                ]
            }
        }
	}
});

frappe.ui.form.on("Rule Discount Leasing", "leasing", function(frm) {
	if(!cur_frm.doc.leasing){
		frm.set_value("customer_group","")
		frm.set_value("territory","")
		frm.set_value("discount","")
	}
});

frappe.ui.form.on("Rule Discount Leasing", "discount", function(frm) {
	if(cur_frm.doc.discount == "Amount"){
		frm.set_value("percent",0)
	}
	if(cur_frm.doc.discount == "Percent"){
		frm.set_value("amount",0)
	}
});