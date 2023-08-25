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

	tagihan = frappe.db.sql(""" 
		SELECT 
			sipm.customer_name AS leasing,
			w.parent_warehouse AS cab_area_jual,
			w2.parent_warehouse AS cabid_jual,
			SUM(dl.nominal-(dl.nominal*tdl.pph/100))-COALESCE(SUM(tl.nilai_diskon-(tl.nilai_diskon*tdl.pph/100)),0) AS bt_tl,
			COALESCE(SUM(tl.nilai+(tl.nilai_diskon*tdl.pph/100))-IF(tl.terbayarkan>0,sum(tl.terbayarkan+(tl.nilai_diskon*tdl.pph/100)),0),0) AS st_tl,
			if(tl.outstanding_discount<=0,sum(tl.outstanding_discount),SUM(tl.outstanding_discount+(tl.nilai_diskon*tdl.pph/100))) AS o_tl,
			COALESCE(IF(tl.terbayarkan>0,sum(tl.terbayarkan+(tl.nilai_diskon*tdl.pph/100)),0),0) AS sb_tl,
			SUM(sipm.outstanding_amount) AS bt_tp,
			COALESCE(SUM(ltpl.tagihan_sipm),0) - COALESCE(SUM(ltpl.terbayarkan_sipm),0) AS st_tp,
			COALESCE(SUM(ltpl.outstanding_sipm),0) AS o_tp,
			COALESCE(SUM(ltpl.terbayarkan_sipm),0) AS sb_tp,
			COALESCE(SUM(CASE WHEN ltpl.mode_of_payment_sipm = 'Advance Leasing' THEN ltpl.terbayarkan_sipm ELSE 0 END), 0) AS sb_tpa,
			COALESCE(SUM(CASE WHEN ltpl.mode_of_payment_sipm != 'Advance Leasing' THEN ltpl.terbayarkan_sipm ELSE 0 END), 0) AS sb_tpn,
			COUNT(sipm.name) AS tot_booking,
			tl.mode_of_payment_sipm
			FROM `tabSales Invoice Penjualan Motor` sipm
			LEFT JOIN `tabDaftar Tagihan Leasing` tl ON tl.`docstatus` = 1 AND sipm.name = tl.no_invoice
			LEFT JOIN `tabTagihan Discount Leasing` tdl ON tdl.name = tl.parent
			LEFT JOIN `tabTable Disc Leasing` dl ON dl.parent = sipm.name
			lEFT JOIN `tabList Tagihan Piutang Leasing` ltpl on ltpl.docstatus = 1 and sipm.name = ltpl.no_invoice
			LEFT JOIN `tabTagihan Leasing` tpl on tpl.name = ltpl.parent
			LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
			LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
			WHERE sipm.docstatus = 1 {0}   
			AND sipm.cara_bayar = "Credit"
			AND sipm.posting_date BETWEEN '{1}' AND '{2}'
			GROUP BY sipm.customer_name,w.parent_warehouse
			ORDER BY w2.parent_warehouse
		 """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)


	

	data = []
	data_with_total = []
	previous_area = None
	total = _dict()
	if tagihan:
		sorted_data = sorted(tagihan, key=lambda x: x['cabid_jual'])
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
		frappe.msgprint(str(data_with_total))
		for i in data_with_total:
			current_area = i['cabid_jual']

			if (previous_area != current_area):
				i['cabid_jual'] = i['cabid_jual']
			elif len(data_with_total)==3:
				data_with_total[0]['cabid_jual'] = data_with_total[0]['cabid_jual']
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


