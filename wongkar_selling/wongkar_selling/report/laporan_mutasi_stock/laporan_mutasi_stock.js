// Copyright (c) 2024, w and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Laporan Mutasi Stock"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "get_query": function() {
                return {
                    "filters": {
                        "has_serial_no": 1
                    }
                }
            }
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    "filters": {
                        "company": company
                    }
                }
            }
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Bold untuk Saldo Awal dan Saldo Akhir
        if (data && (data.item_name === "<b>SALDO AWAL</b>" || data.item_name === "<b>SALDO AKHIR</b>")) {
            if (column.fieldname === "hpp" || column.fieldname === "nilai_setelah_transaksi") {
                value = "<span style='font-weight: bold;'>" + value + "</span>";
            }
        }
	if (column.fieldname == "out_qty" && data && data.out_qty > 0) {
                        value = "<span style='color:red'>" + value + "</span>";
                }
                else if (column.fieldname == "in_qty" && data && data.in_qty > 0) {
                        value = "<span style='color:green'>" + value + "</span>";
                }       
        return value;
    }
};
