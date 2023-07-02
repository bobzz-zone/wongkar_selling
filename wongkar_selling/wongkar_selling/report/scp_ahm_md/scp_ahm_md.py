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

	data = frappe.db.sql(""" SELECT 
		td.name,
		sipm.cara_bayar,
		COUNT(sipm.name) AS tot_booking_cash,
		w.parent_warehouse AS cab_area_jual,
		w2.parent_warehouse AS cabid_jual,
		sum(td.`nominal`) AS beban_ahm_cash
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabTable Discount` td ON td.`customer` = 'AHM' AND  td.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.posting_date between '{}' and '{}' AND sipm.`cara_bayar` = 'Cash'
		group by w.parent_warehouse  order by w2.parent_warehouse asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)

	data_cr = frappe.db.sql(""" SELECT 
		COUNT(sipm.name) AS tot_booking_credit,
		w.parent_warehouse AS cab_area_jual,
		w2.parent_warehouse AS cabid_jual,
		sum(td.`nominal`) AS beban_ahm_credit
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabTable Discount` td ON td.`customer` = 'AHM' AND  td.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.posting_date between '{}' and '{}' AND sipm.`cara_bayar` != 'Cash' 
		group by w.parent_warehouse  order by w2.parent_warehouse asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)

	data_md = frappe.db.sql(""" SELECT 
		w.parent_warehouse AS cab_area_jual,
		w2.parent_warehouse AS cabid_jual,
		sum(td.`nominal`) AS beban_md_cash
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabTable Discount` td ON td.`customer` != 'AHM' AND  td.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.posting_date between '{}' and '{}' AND sipm.`cara_bayar` = 'Cash'
		group by w.parent_warehouse  order by w2.parent_warehouse asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)

	data_cr_md = frappe.db.sql(""" SELECT 
		w.parent_warehouse AS cab_area_jual,
		w2.parent_warehouse AS cabid_jual,
		sum(td.`nominal`) AS beban_md_credit
		FROM `tabSales Invoice Penjualan Motor` sipm
		LEFT JOIN `tabTable Discount` td ON td.`customer` != 'AHM' AND  td.parent = sipm.name
		LEFT JOIN `tabWarehouse` w ON w.name = sipm.`set_warehouse`
		LEFT JOIN `tabWarehouse` w2 ON w2.name = w.parent_warehouse
		where sipm.docstatus = 1 {} and sipm.posting_date between '{}' and '{}' AND sipm.`cara_bayar` != 'Cash' 
		group by w.parent_warehouse  order by w2.parent_warehouse asc """.format(kondisi,filters.get('from_date'),filters.get('to_date')),as_dict = 1,debug=1)


	merged_data = []

	# Menggabungkan data berdasarkan "cab_area_jual"
	for d1 in data_cr:
		conter=0
		for d2 in data:
			if d1["cab_area_jual"] == d2["cab_area_jual"]:
				conter = 0
				merged_data.append({
					"cabid_jual": d1["cabid_jual"],
					"cab_area_jual": d1["cab_area_jual"],
					"tot_booking_cash": d2.get("tot_booking_cash", 0),
					"beban_ahm_cash": d2.get("beban_ahm_cash", 0),
					"tot_booking_credit": d1.get("tot_booking_credit", 0),
					"beban_ahm_credit": d1.get("beban_ahm_credit", 0),
				})
			else:
				conter=conter+1
		if conter == len(data):
			merged_data.append({
				"cabid_jual": d1["cabid_jual"],
				"cab_area_jual": d1["cab_area_jual"],
				"tot_booking_cash": 0,
				"beban_ahm_cash": 0,
				"tot_booking_credit": d1.get("tot_booking_credit", 0),
				"beban_ahm_credit": d1.get("beban_ahm_credit", 0),
			})

		for d1 in merged_data:
			conter=0
			for d2 in data_md:
				if d1["cab_area_jual"] == d2["cab_area_jual"]:
					conter = 0
					d1.update({
						"beban_md_cash": d2.get("beban_md_cash", 0),
					})
				else:
					conter=conter+1
			
			if conter == len(data_md):
				d1.update({
					"beban_md_cash": 0,
				})

			for d2 in data_cr_md:
				if d1["cab_area_jual"] == d2["cab_area_jual"]:
					conter = 0
					d1.update({
						"beban_md_credit": d2.get("beban_md_credit", 0),
					})
				else:
					conter=conter+1
			
			if conter == len(data_cr_md):
				d1.update({
					"beban_md_credit": 0,
				})

		for m in merged_data:
			m.update({
					"total_beban_cash" : m['beban_ahm_cash'] + m['beban_md_cash'],
					"total_beban_credit" : m['beban_ahm_credit'] + m['beban_md_credit'],
					"tot_booking_all": m['tot_booking_cash'] + m['tot_booking_credit'],
					"beban_ahm_all": m['beban_ahm_cash'] + m['beban_ahm_credit'],
					"beban_md_all": m['beban_md_cash'] + m['beban_md_credit'],
					"total_beban_all": (m['beban_ahm_cash'] + m['beban_ahm_credit']) + (m['beban_md_cash'] + m['beban_md_credit'])

				})


	data_with_total = []
	previous_area = None
	total = _dict()
	if merged_data:
		for i in merged_data:
			current_area = i['cabid_jual']
			if (previous_area is not None and previous_area != current_area):
				data_with_total.append({
					'cabid_jual': previous_area,
					'cab_area_jual': "Total",
					'tot_booking_cash': total[key].tot_booking_cash,
					'beban_ahm_cash': total[key].beban_ahm_cash,
					'beban_md_cash': total[key].beban_md_cash,
					'total_beban_cash': total[key].total_beban_cash,
					'tot_booking_credit': total[key].tot_booking_credit,
					'beban_ahm_credit': total[key].beban_ahm_credit,
					'beban_md_credit': total[key].beban_md_credit,
					'total_beban_credit': total[key].total_beban_credit,
					'tot_booking_all': total[key].tot_booking_all,
					'beban_ahm_all': total[key].beban_ahm_all,
					'beban_md_all': total[key].beban_md_all,
					'total_beban_all': total[key].total_beban_all,
					
				})

			key = (i['cabid_jual'])
			if key not in total:				
				total.setdefault(key, _dict({
					'tot_booking_cash': flt(i['tot_booking_cash']),
					'beban_ahm_cash': flt(i['beban_ahm_cash']),
					'beban_md_cash': flt(i['beban_md_cash']),
					'total_beban_cash': flt(i['total_beban_cash']),
					'tot_booking_credit': flt(i['tot_booking_credit']),
					'beban_ahm_credit': flt(i['beban_ahm_credit']),
					'beban_md_credit': flt(i['beban_md_credit']),
					'total_beban_credit': flt(i['total_beban_credit']),
					'tot_booking_all': flt(i['tot_booking_all']),
					'beban_ahm_all': flt(i['beban_ahm_all']),
					'beban_md_all': flt(i['beban_md_all']),
					'total_beban_all': flt(i['total_beban_all'])
				}))							
			else:
				total[key].tot_booking_cash += flt(i['tot_booking_cash'])
				total[key].beban_ahm_cash += flt(i['beban_ahm_cash'])
				total[key].beban_md_cash += flt(i['beban_md_cash'])
				total[key].total_beban_cash += flt(i['total_beban_cash'])
				total[key].tot_booking_credit += flt(i['tot_booking_credit'])
				total[key].beban_ahm_credit += flt(i['beban_ahm_credit'])
				total[key].beban_md_credit += flt(i['beban_md_credit'])
				total[key].total_beban_credit += flt(i['total_beban_credit'])
				total[key].tot_booking_all += flt(i['tot_booking_all'])
				total[key].beban_ahm_all += flt(i['beban_ahm_all'])
				total[key].beban_md_all += flt(i['beban_md_all'])
				total[key].total_beban_all += flt(i['total_beban_all'])
			
			
			data_with_total.append(i)
			previous_area = current_area


		data_with_total.append({
			'cabid_jual': total[merged_data[-1]['cabid_jual']].cabid_jual,
			'cab_area_jual': "Total",
			'tot_booking_cash': total[merged_data[-1]['cabid_jual']].tot_booking_cash,
			'beban_ahm_cash': total[merged_data[-1]['cabid_jual']].beban_ahm_cash,
			'beban_md_cash': total[merged_data[-1]['cabid_jual']].beban_md_cash,
			'total_beban_cash': total[merged_data[-1]['cabid_jual']].total_beban_cash,
			'tot_booking_credit': total[merged_data[-1]['cabid_jual']].tot_booking_credit,
			'beban_ahm_credit': total[merged_data[-1]['cabid_jual']].beban_ahm_credit,
			'beban_md_credit': total[merged_data[-1]['cabid_jual']].beban_md_credit,
			'total_beban_credit': total[merged_data[-1]['cabid_jual']].total_beban_credit,
			'tot_booking_all': total[merged_data[-1]['cabid_jual']].tot_booking_all,
			'beban_ahm_all': total[merged_data[-1]['cabid_jual']].beban_ahm_all,
			'beban_md_all': total[merged_data[-1]['cabid_jual']].beban_md_all,
			'total_beban_all': total[merged_data[-1]['cabid_jual']].total_beban_all,
		})

		tot_booking_cash = beban_ahm_cash = beban_md_cash = total_beban_cash = tot_booking_credit = beban_ahm_credit = beban_md_credit = total_beban_credit = tot_booking_all = beban_ahm_all = beban_md_all = total_beban_all = 0.0
		for d in total.values():
			tot_booking_cash += d['tot_booking_cash']
			beban_ahm_cash += d['beban_ahm_cash']
			beban_md_cash += d['beban_md_cash']
			total_beban_cash += d['total_beban_cash']
			tot_booking_credit += d['tot_booking_credit']
			beban_ahm_credit += d['beban_ahm_credit']
			beban_md_credit += d['beban_md_credit']
			total_beban_credit += d['total_beban_credit']
			tot_booking_all += d['tot_booking_all']
			beban_ahm_all += d['beban_ahm_all']
			beban_md_all +=	d['beban_md_all']
			total_beban_all +=	d['total_beban_all']

		data_with_total.append({
			'cabid_jual': "",
			'cab_area_jual': "Grand Total",
			'tot_booking_cash': tot_booking_cash,
			'beban_ahm_cash': beban_ahm_cash,
			'beban_md_cash': beban_md_cash,
			'total_beban_cash': total_beban_cash,
			'tot_booking_credit': tot_booking_credit,
			'beban_ahm_credit': beban_ahm_credit,
			'beban_md_credit': beban_md_credit,
			'total_beban_credit':total_beban_credit,
			'tot_booking_all': tot_booking_all,
			'beban_ahm_all': beban_ahm_all,
			'beban_md_all': beban_md_all,
			'total_beban_all': total_beban_all,
		})

		for i in data_with_total:
			current_area = i['cabid_jual']
			if (previous_area != current_area):
				i['cabid_jual'] = i['cabid_jual']
			else:
				i['cabid_jual'] = ""
			previous_area = current_area

	frappe.msgprint(str(data_with_total)+ " merged_data") 
	 


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
			"label": _("Tot Booking Cash"),
			"fieldname": "tot_booking_cash",
			"fieldtype": "Int",
			"width": 180
		},
		{
			"label": _("Beban AHM Cash"),
			"fieldname": "beban_ahm_cash",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Beban MD Cash"),
			"fieldname": "beban_md_cash",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Total Beban Cash"),
			"fieldname": "total_beban_cash",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tot Booking Credit"),
			"fieldname": "tot_booking_credit",
			"fieldtype": "Int",
			"width": 180
		},
		{
			"label": _("Beban AHM Credit"),
			"fieldname": "beban_ahm_credit",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Beban MD Credit"),
			"fieldname": "beban_md_credit",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Total Beban Credit"),
			"fieldname": "total_beban_credit",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Tot Booking All"),
			"fieldname": "tot_booking_all",
			"fieldtype": "Int",
			"width": 180
		},
		{
			"label": _("Beban AHM All"),
			"fieldname": "beban_ahm_all",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Beban MD All"),
			"fieldname": "beban_md_all",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Total Beban All"),
			"fieldname": "total_beban_all",
			"fieldtype": "Currency",
			"width": 200
		},

	]

	return columns


