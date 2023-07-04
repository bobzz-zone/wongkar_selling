from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):
	kondisi = ""
	if filters.get("area"):
		kondisi = " and w2.parent_warehouse = '{}' ".format(filters.get("area"))

	data = frappe.db.sql(""" SELECT 
		DATE_FORMAT(sipm.posting_date,'%Y%m') as bulan,
		tag_d.`name`,
		td.customer,
		w.parent_warehouse AS cab_area_jual,
		w2.parent_warehouse AS cabid_jual,
		SUM(td.nominal)-IF(tag_d.`name` IS NULL,0,COALESCE(SUM(dt.nilai),0)) AS bt_t,
		IF(tag_d.`name` IS NULL,0,COALESCE(SUM(dt.nilai),0)) AS st_t,
		IF(tag_d.`name` IS NULL,0, COALESCE(SUM(dt.nilai) - SUM(dt.terbayarkan),0)) AS sb_t,
		IF(tag_d.`name` IS NULL,0,COALESCE(SUM(dt.terbayarkan),0)) AS o_t,
		sipm.cara_bayar
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabDaftar Tagihan` dt ON dt.docstatus = 1 AND sipm.name = dt.no_sinv  
		LEFT JOIN `tabTable Discount` td ON td.parent = sipm.name 
		LEFT JOIN `tabTagihan Discount` tag_d ON  tag_d.name = dt.`parent` AND td.`customer` = tag_d.`customer`
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.posting_date between '{}' and '{}' and td.nominal != 0
		group by td.customer,w.parent_warehouse,DATE_FORMAT(sipm.posting_date,'%Y%m') order by w2.parent_warehouse asc,td.customer  """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)
	
	data_with_total = []
	previous_area = None
	total = _dict()

	if data:
		for i in data:
			current_area = i['customer']
			if (previous_area is not None and previous_area != current_area):
				data_with_total.append({
					'bulan': "",
					'customer': previous_area,
					'cabid_jual': "",
					'cab_area_jual': "Total",
					'bt_t': total[key].bt_t,
					'st_t': total[key].st_t,
					'sb_t': total[key].sb_t,
					'o_t': total[key].o_t,
				})

			key = (i['customer'])
			if key not in total:				
				total.setdefault(key, _dict({
					'bt_t': flt(i['bt_t']),
					'st_t': flt(i['st_t']),
					'sb_t': flt(i['sb_t']),
					'o_t': flt(i['o_t']),
				}))							
			else:
				total[key].bt_t += flt(i['bt_t'])
				total[key].st_t += flt(i['st_t'])
				total[key].sb_t += flt(i['sb_t'])
				total[key].o_t += flt(i['o_t'])
			
			data_with_total.append(i)
			previous_area = current_area

		data_with_total.append({
			'bulan': total[data[-1]['customer']].bulan,
			'customer': total[data[-1]['customer']].customer,
			'cabid_jual': "",
			'cab_area_jual': "Total",
			'bt_t': total[data[-1]['customer']].bt_t,
			'st_t': total[data[-1]['customer']].st_t,
			'sb_t': total[data[-1]['customer']].sb_t,
			'o_t': total[data[-1]['customer']].o_t,
		})

		bt_t = st_t = sb_t = o_t = 0.0
		for d in total.values():
			bt_t += d['bt_t']
			st_t += d['st_t']
			sb_t += d['sb_t']
			o_t += d['o_t']

		data_with_total.append({
			'bulan': "",
			'customer': "",
			'cabid_jual': "",
			'cab_area_jual': "Grand Total",
			'bt_t': bt_t,
			'st_t': st_t,
			'sb_t': sb_t,
			'o_t': o_t,
		})

		for i in data_with_total:
			current_area = i['customer']
			if (previous_area != current_area):
				i['customer'] = i['customer']
				i['cabid_jual'] = i['cabid_jual']
				i['bulan'] = i['bulan']
			else:
				i['customer'] = ""
				i['cabid_jual'] = ""
				i['bulan'] = ""
			previous_area = current_area

	frappe.msgprint(str(data_with_total)+ " merged_data") 

	return data_with_total

def get_columns(filters):
	columns = [
		# {
		# 	"label": _("Bulan"),
		# 	"fieldname": "bulan",
		# 	"fieldtype": "Data",
		# 	"width": 100
		# },
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Cab ID Jual"),
			"fieldname": "cabid_jual",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Cab Area Jual"),
			"fieldname": "cab_area_jual",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Belum Tertagih Tagihan"),
			"fieldname": "bt_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Tertagih Tagihan"),
			"fieldname": "st_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Bayar Tagihan"),
			"fieldname": "sb_t",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Outstanding Tagihan"),
			"fieldname": "o_t",
			"fieldtype": "Currency",
			"width": 200
		},
		# {
		# 	"label": _("Cara Bayar"),
		# 	"fieldname": "cara_bayar",
		# 	"fieldtype": "Data",
		# 	"width": 200
		# },
	]

	return columns


