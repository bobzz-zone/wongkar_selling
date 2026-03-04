# Copyright (c) 2024, [Your Company] and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
    if not filters:
        filters = {}
    
    # Validasi filter wajib
    validate_filters(filters)
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def validate_filters(filters):
    """Validasi bahwa from_date dan to_date harus diisi"""
    if not filters.get("from_date"):
        frappe.throw(_("From Date is mandatory"))
    if not filters.get("to_date"):
        frappe.throw(_("To Date is mandatory"))

def get_columns():
    """Define kolom untuk report"""
    return [
        {
            "fieldname": "posting_date",
            "label": _("Tanggal Transaksi"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "posting_time",
            "label": _("Waktu Transaksi"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "serial_no",
            "label": _("Serial No"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
        },
        {
            "fieldname": "item_name",
            "label": _("Item Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "item_group",
            "label": _("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 120
        },
        {
            "fieldname": "warehouse",
            "label": _("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 120
        },
        {
            "fieldname": "qty_in",
            "label": _("Qty In"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "qty_out",
            "label": _("Qty Out"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "voucher_type",
            "label": _("Voucher Type"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "voucher_no",
            "label": _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 150
        },
        {
            "fieldname": "hpp",
            "label": _("HPP"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "nilai_setelah_transaksi",
            "label": _("Nilai Setelah Transaksi"),
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    """Ambil dan proses data untuk report"""
    data = []
    
    # Get opening balance
    opening_value = get_opening_balance(filters)
    
    # Tambahkan baris Saldo Awal
    data.append({
        "posting_date": filters.get("from_date"),
        "posting_time": "",
        "serial_no": "",
        "item_code": "",
        "item_name": "<b>SALDO AWAL</b>",
        "item_group": "",
        "warehouse": filters.get("warehouse", ""),
        "qty_in": 0,
        "qty_out": 0,
        "voucher_type": "",
        "voucher_no": "",
        "hpp": opening_value,
        "nilai_setelah_transaksi": opening_value
    })
    
    # Get stock ledger entries
    stock_entries = get_stock_ledger_entries(filters)
    
    # Proses setiap transaksi
    running_value = opening_value
    
    for entry in stock_entries:
        # Get item details
        item_details = get_item_details(entry.item_code)
        
        # Hitung HPP
        hpp = calculate_hpp(entry)
        
        # Update running value
        running_value += hpp
        
        # Pisahkan qty in dan out
        qty_in = flt(entry.actual_qty) if flt(entry.actual_qty) > 0 else 0
        qty_out = abs(flt(entry.actual_qty)) if flt(entry.actual_qty) < 0 else 0
        
        # Format posting_time ke string
        posting_time_str = str(entry.posting_time) if entry.posting_time else ""
        
        # Format serial_no - ganti newline dengan spasi
        serial_no_str = entry.serial_no.replace("\n", " ").strip() if entry.serial_no else ""
        
        data.append({
            "posting_date": entry.posting_date,
            "posting_time": posting_time_str,
            "serial_no": serial_no_str,
            "item_code": entry.item_code,
            "item_name": item_details.get("item_name", ""),
            "item_group": item_details.get("item_group", ""),
            "warehouse": entry.warehouse,
            "qty_in": qty_in,
            "qty_out": qty_out,
            "voucher_type": entry.voucher_type or "",
            "voucher_no": entry.voucher_no or "",
            "hpp": hpp,
            "nilai_setelah_transaksi": running_value
        })
    
    # Tambahkan baris Saldo Akhir
    data.append({
        "posting_date": filters.get("to_date"),
        "posting_time": "",
        "serial_no": "",
        "item_code": "",
        "item_name": "<b>SALDO AKHIR</b>",
        "item_group": "",
        "warehouse": filters.get("warehouse", ""),
        "qty_in": 0,
        "qty_out": 0,
        "voucher_type": "",
        "voucher_no": "",
        "hpp": running_value,
        "nilai_setelah_transaksi": running_value
    })
    
    return data

def get_opening_balance(filters):
    """Hitung saldo awal sebelum from_date"""
    conditions = ["posting_date < %(from_date)s"]
    
    if filters.get("company"):
        conditions.append("company = %(company)s")
    
    if filters.get("item_code"):
        conditions.append("item_code = %(item_code)s")
    
    if filters.get("warehouse"):
        conditions.append("warehouse = %(warehouse)s")
    
    # Tambahkan kondisi untuk item dengan serial no
    conditions.append("serial_no IS NOT NULL AND serial_no != ''")
    
    query = f"""
        SELECT 
            COALESCE(SUM(stock_value_difference), 0) as opening_value
        FROM 
            `tabStock Ledger Entry`
        WHERE 
            {' AND '.join(conditions)}
            AND docstatus = 1 and is_cancelled=0
    """
    
    result = frappe.db.sql(query, filters, as_dict=True)
    return flt(result[0].opening_value) if result else 0

def get_stock_ledger_entries(filters):
    """Ambil stock ledger entries sesuai filter"""
    conditions = [
        "posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "serial_no IS NOT NULL",
        "serial_no != ''",
        "docstatus = 1"
    ]
    
    if filters.get("company"):
        conditions.append("company = %(company)s")
    
    if filters.get("item_code"):
        conditions.append("item_code = %(item_code)s")
    
    if filters.get("warehouse"):
        conditions.append("warehouse = %(warehouse)s")
    
    query = f"""
        SELECT 
            posting_date,
            posting_time,
            item_code,
            warehouse,
            actual_qty,
            abs(stock_value_difference) as valuation_rate,
            serial_no,
            stock_value_difference,
            voucher_type,
            voucher_no
        FROM 
            `tabStock Ledger Entry`
        WHERE 
            {' AND '.join(conditions)} and is_cancelled=0
        ORDER BY 
            posting_date, posting_time, creation
    """
    
    return frappe.db.sql(query, filters, as_dict=True)

def get_item_details(item_code):
    """Ambil detail item dari tabItem"""
    return frappe.db.get_value(
        "Item",
        item_code,
        ["item_name", "item_group"],
        as_dict=True
    ) or {}

def calculate_hpp(entry):
    """
    Hitung HPP berdasarkan actual_qty
    - Jika actual_qty = 1: gunakan valuation_rate
    - Jika actual_qty > 1: ambil purchase_rate dari masing-masing serial no
    - Fallback ke stock_value_difference jika purchase_rate tidak ada
    """
    actual_qty = abs(flt(entry.actual_qty))
    
    # Jika actual_qty = 1, gunakan valuation_rate
    if actual_qty == 1:
        hpp = flt(entry.valuation_rate) * flt(entry.actual_qty)
        
        # Jika valuation_rate = 0, gunakan stock_value_difference
        if hpp == 0 and entry.stock_value_difference:
            hpp = flt(entry.stock_value_difference)
        
        # Jika masih 0, coba ambil dari serial no purchase_rate
        if hpp == 0 and entry.serial_no:
            serial_nos = entry.serial_no.strip().split()
            if serial_nos:
                purchase_rate = frappe.db.get_value(
                    "Serial No",
                    serial_nos[0],
                    "purchase_rate"
                )
                multiplier = 1 if flt(entry.actual_qty) > 0 else -1
                hpp = flt(purchase_rate) * multiplier
        
        return hpp
    
    # Jika actual_qty > 1, ambil purchase_rate dari Serial No
    serial_nos = entry.serial_no.strip().split() if entry.serial_no else []
    total_hpp = 0
    found_rates = 0
    
    for serial_no in serial_nos:
        if not serial_no:
            continue
            
        purchase_rate = frappe.db.get_value(
            "Serial No",
            serial_no,
            "purchase_rate"
        )
        
        if purchase_rate and flt(purchase_rate) > 0:
            # Tentukan apakah ini transaksi masuk atau keluar
            multiplier = 1 if flt(entry.actual_qty) > 0 else -1
            total_hpp += flt(purchase_rate) * multiplier
            found_rates += 1
    
    # Jika tidak ada purchase_rate yang ditemukan, gunakan stock_value_difference
    if found_rates == 0 and entry.stock_value_difference:
        total_hpp = flt(entry.stock_value_difference)
    
    # Jika masih 0 dan ada valuation_rate, gunakan sebagai fallback
    if total_hpp == 0 and entry.valuation_rate:
        total_hpp = flt(entry.valuation_rate) * flt(entry.actual_qty)
    
    return total_hpp
