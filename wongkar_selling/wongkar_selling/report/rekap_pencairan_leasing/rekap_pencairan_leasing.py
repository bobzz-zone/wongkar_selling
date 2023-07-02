from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date
from collections import OrderedDict

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):
	kondisi = ""
	if filters.get("leasing"):
		kondisi = " and sipm.customer_name = '{}' ".format(filters.get("leasing"))

	tagihan = frappe.db.sql(""" SELECT 
		sipm.customer_name as leasing,
		w.parent_warehouse as cab_area_jual,
		w2.parent_warehouse as cabid_jual,
		sum(dl.nominal)-IFNULL(sum(tl.nilai),0) as bt_tl,
		IFNULL(sum(tl.nilai),0) as st_tl,
		IFNULL(sum(tl.outstanding_discount),0) as o_tl,
		IFNULL(sum(tl.terbayarkan),0) as sb_tl,
		sum(sipm.outstanding_amount)-IFNULL(sum(tl.tagihan_sipm),0) as bt_tp,
		IFNULL(sum(tl.tagihan_sipm),0) as st_tp,
		IFNULL(sum(tl.outstanding_sipm),0) as o_tp,
		IFNULL(sum(tl.terbayarkan_sipm),0) as sb_tp,
		(SELECT IFNULL(SUM(tl.terbayarkan),0) FROM `tabDaftar Tagihan Leasing` tl WHERE tl.mode_of_payment_sipm = "Advance Leasing") AS sb_tpa,
		(SELECT IFNULL(SUM(tl.terbayarkan),0) FROM `tabDaftar Tagihan Leasing` tl WHERE tl.mode_of_payment_sipm != "Advance Leasing") AS sb_tpn,
		count(sipm.name) as tot_booking
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabDaftar Tagihan Leasing` tl ON tl.`docstatus` = 1 AND sipm.name = tl.no_invoice
		left join `tabTagihan Discount Leasing` tdl on tdl.name = tl.parent
		left join `tabTable Disc Leasing` dl on dl.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.cara_bayar = "Credit" and sipm.posting_date between '{}' and '{}'
		group by sipm.customer_name,w.parent_warehouse  order by w2.parent_warehouse asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)

	data = []
	data_with_total = []
	previous_area = None
	total = _dict()
	if tagihan:
		for i in tagihan:
			current_area = i['cabid_jual']
			if (previous_area is not None and previous_area != current_area):
				data_with_total.append({
					'cabid_jual': previous_area,
					'cab_area_jual': "Total",
					'tot_booking': total[key].tot_booking,
					'bt_tl': total[key].bt_tl,
					'st_tl': total[key].st_tl,
					'sb_tl': total[key].sb_tl,
					'o_tl': total[key].o_tl,
					'bt_tp': total[key].bt_tp,
					'st_tp': total[key].st_tp,
					'sb_tpa': total[key].sb_tpa,
					'sb_tpn': total[key].sb_tpn,
					'sb_tp': total[key].sb_tp,
					'o_tp': total[key].o_tp,
				})
			

			key = (i['cabid_jual'])
			if key not in total:				
				total.setdefault(key, _dict({
					'tot_booking': flt(i['tot_booking']),
					'bt_tl': flt(i['bt_tl']),
					'st_tl': flt(i['st_tl']),
					'sb_tl': flt(i['sb_tl']),
					'o_tl': flt(i['o_tl']),
					'bt_tp': flt(i['bt_tp']),
					'st_tp': flt(i['st_tp']),
					'sb_tpa': flt(i['sb_tpa']),
					'sb_tpn': flt(i['sb_tpn']),
					'sb_tp': flt(i['sb_tp']),
					'o_tp': flt(i['o_tp'])
				}))							
			else:
				total[key].tot_booking += flt(i['tot_booking'])
				total[key].bt_tl += flt(i['bt_tl'])
				total[key].st_tl += flt(i['st_tl'])
				total[key].sb_tl += flt(i['sb_tl'])
				total[key].o_tl += flt(i['o_tl'])
				total[key].bt_tp += flt(i['bt_tp'])
				total[key].st_tp += flt(i['st_tp'])
				total[key].sb_tpa += flt(i['sb_tpa'])
				total[key].sb_tpn += flt(i['sb_tpn'])
				total[key].sb_tp += flt(i['sb_tp'])
				total[key].o_tp += flt(i['o_tp'])
			
			
			data_with_total.append(i)
			previous_area = current_area

		data_with_total.append({
				'cabid_jual': total[tagihan[-1]['cabid_jual']].cabid_jual,
				'cab_area_jual': "Total",
				'tot_booking': total[tagihan[-1]['cabid_jual']].tot_booking,
				'bt_tl': total[tagihan[-1]['cabid_jual']].bt_tl,
				'st_tl': total[tagihan[-1]['cabid_jual']].st_tl,
				'sb_tl': total[tagihan[-1]['cabid_jual']].sb_tl,
				'o_tl': total[tagihan[-1]['cabid_jual']].o_tl,
				'bt_tp': total[tagihan[-1]['cabid_jual']].bt_tp,
				'st_tp': total[tagihan[-1]['cabid_jual']].st_tp,
				'sb_tpa': total[tagihan[-1]['cabid_jual']].sb_tpa,
				'sb_tpn': total[tagihan[-1]['cabid_jual']].sb_tpn,
				'sb_tp': total[tagihan[-1]['cabid_jual']].sb_tp,
				'o_tp': total[tagihan[-1]['cabid_jual']].o_tp
			})

		tot_booking = bt_tl = st_tl = sb_tl = o_tl = bt_tp = st_tp = sb_tpa = sb_tpn = sb_tp = o_tp = 0.0
		for d in total.values():
			tot_booking += d['tot_booking']
			bt_tl += d['bt_tl']
			st_tl += d['st_tl']
			sb_tl += d['sb_tl']
			o_tl += d['o_tl']
			bt_tp += d['bt_tp']
			st_tp += d['st_tp']
			sb_tpa += d['sb_tpa']
			sb_tpn += d['sb_tpn']
			sb_tp += d['sb_tp']
			o_tp +=	d['o_tp']
		
		data_with_total.append({
			'cabid_jual': "",
			'cab_area_jual': "Grand Total",
			'tot_booking': tot_booking,
			'bt_tl': bt_tl,
			'st_tl': st_tl,
			'sb_tl': sb_tl,
			'o_tl': o_tl,
			'bt_tp': bt_tp,
			'st_tp': st_tp,
			'sb_tpa':sb_tpa,
			'sb_tpn': sb_tpn,
			'sb_tp': sb_tp,
			'o_tp': o_tp
		})

		for i in data_with_total:
			current_area = i['cabid_jual']
			if (previous_area != current_area):
				i['cabid_jual'] = i['cabid_jual']
			else:
				i['cabid_jual'] = ""
			previous_area = current_area
	

	return data_with_total

def get_columns(filters):
	columns = [
		{
			"label": _("Cab ID Jual"),
			"fieldname": "cabid_jual",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Cab Area Jual"),
			"fieldname": "cab_area_jual",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Tot Booking"),
			"fieldname": "tot_booking",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _(" Tot Subsidi Leasing"),
			"fieldname": "bt_tl",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Tertagih Tambahan Leasing"),
			"fieldname": "st_tl",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Terbayarkan Tambahan Leasing"),
			"fieldname": "sb_tl",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Outstanding Tambahan Leasing"),
			"fieldname": "o_tl",
			"fieldtype": "Currency",
			"width": 200
		},

		{
			"label": _("Tot Tagihan Pokok"),
			"fieldname": "bt_tp",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Sudah Tertagih Tagihan Pokok"),
			"fieldname": "st_tp",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Pencairan Pokok Adv"),
			"fieldname": "sb_tpa",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Pencairan Pokok Normal"),
			"fieldname": "sb_tpn",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tot Pencairan Pokok"),
			"fieldname": "sb_tp",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Outstanding Tagihan Pokok"),
			"fieldname": "o_tp",
			"fieldtype": "Currency",
			"width": 200
		},
	]

	return columns


