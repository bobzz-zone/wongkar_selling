# Copyright (c) 2013, w and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
import datetime
from datetime import date
from frappe.utils import cint, cstr, flt, getdate, nowdate

def execute(filters=None):

	return get_columns(filters), get_data(filters)

def get_data(filters):
	kondisi = ""
	if filters.get("area"):
		kondisi = " and sipm.cost_center = '{}' ".format(filters.get("area"))

	# frappe.msgprint(str(filters)+ ' filters')
	data = frappe.db.sql(""" SELECT 
			sipm.name AS sipm,
			td.`customer` AS customer,
			sipm.nama_pemilik,
			sipm.posting_date AS tgl_jual,
			sipm.cost_center AS nama_area,
			td.`nominal` AS outstanding_amount,
			dt.`nilai`,
			dt.terbayarkan,
			IF(t_disc.`name` IS NULL,'Belum Tagih',IF(dt.`terbayarkan`=0,'Sudah Realisasi',IF(dt.`terbayarkan`!=0 AND dt.`nilai` > dt.`terbayarkan` ,'Belum Realisasi','Sudah Tagih'))) AS status_sipm,
			t_disc.`name` AS no_tagih,
			td.`rule`,
			t_disc.date AS tgl_tagih,
			IF(dt.terbayarkan,dt.terbayarkan,td.`nominal`) AS piutang,
			COALESCE(IF(t_disc.date ,DATEDIFF(t_disc.date, sipm.posting_date),0),0) AS ht,
			tp.`name`,
			fp.`name` AS fp_name,
			fp.`docstatus`,
			fp.`posting_date`,
			IF(fp.`posting_date` IS NOT NULL,DATEDIFF(fp.`posting_date`,t_disc.date),0) AS hc
			FROM `tabSales Invoice Penjualan Motor` sipm
			LEFT JOIN `tabTable Discount` td ON td.`parent` = sipm.name
			LEFT JOIN `tabDaftar Tagihan` dt ON dt.`no_sinv` = sipm.name
			LEFT JOIN `tabTagihan Discount` t_disc ON t_disc.`name` = dt.`parent` AND t_disc.`docstatus` = 1
			LEFT JOIN `tabTagihan Payment Table` tp ON tp.`doc_name` = t_disc.name AND dt.`no_sinv` = tp.no_sinv AND tp.`docstatus` = 1
			LEFT JOIN `tabForm Pembayaran` fp ON fp.`name` = tp.`parent`  AND fp.`docstatus` = 1
			WHERE sipm.docstatus = 1 
			AND sipm.posting_date <= '{}' AND td.customer = '{}' AND td.`nominal` > 0
			{}
			GROUP BY sipm.name ORDER BY sipm.posting_date ASC
		 """.format(filters.get('to_date'),filters.get('customer'),kondisi),as_dict = 1,debug=1)

	result_dict = {}
		

	tampil = []
	tampil_bt = [
		{
			'nama': 'Belum Tagih',
			'piutang': 0
		}
	]
	tampil_st = [
		{
			'nama': 'Sudah Tagih',
			'piutang': 0
		}
	]
	tampil_sr = [
		{
			'nama': 'Sudah Realisasi',
			'piutang': 0
		}
	]
	tampil_br = [
		{
			'nama': 'Belum Realisasi',
			'piutang': 0
		}
	]
	
	for entry in data:
		status_sipm = entry['status_sipm']
		customer = entry['customer']
		sipm = entry['sipm']

		# Menggunakan setdefault untuk menambahkan item_code dan warehouse jika belum ada
		result_dict.setdefault(status_sipm, {}).setdefault(customer, {}).setdefault(sipm, {}).update(entry)

	# frappe.msgprint(str(result_dict)+ ' result_dict')
	
	for status_sipm, pemilik_dict in result_dict.items():
		if status_sipm == 'Belum Tagih':
			tampil_bt = []
			parent = {
				'nama': status_sipm,
				'piutang': 0
			}
			
			out = []
			for customer,info in pemilik_dict.items():
				# frappe.msgprint(str(status_sipm)+ ' status_sipm')
				parent2 = {
					'nama': customer,
					'indent': 1,
					'parent': status_sipm,
					'piutang': 0,
				}
				isi = []
				for sipm,info_sipm in info.items():
					entry_date = info_sipm['tgl_jual']
					info_sipm['range1'] = info_sipm['range2'] = info_sipm['range3'] = info_sipm['range4'] = info_sipm['range5'] = 0.0
					aging = get_ageing_data(entry_date,info_sipm)
					isi.append({
						'nama': info_sipm['nama_pemilik'],
						'tgl_jual': info_sipm['tgl_jual'],
						'tgl_tagih': info_sipm['tgl_tagih'],
						'ht': info_sipm['ht'],
						'hc': info_sipm['hc'],
						'nama_area': info_sipm['nama_area'],
						'piutang': info_sipm['piutang'],
						'indent': 2,
						"parent": info_sipm['customer'],
						'sipm': info_sipm['sipm'],
						aging[0] : aging[1],
						'no_tagih': info_sipm['no_tagih']
					})
					parent2['piutang'] += info_sipm['piutang']
					parent['piutang'] += info_sipm['piutang']

				out.extend([parent2]+isi)
				
			# frappe.msgprint(str(out)+ ' out')
			tampil_bt.extend([parent]+out)
		elif status_sipm == 'Sudah Tagih':
			tampil_st = []
			parent = {
				'nama': status_sipm,
				'piutang': 0
			}
			
			out = []
			for customer,info in pemilik_dict.items():
				# frappe.msgprint(str(status_sipm)+ ' status_sipm')
				parent2 = {
					'nama': customer,
					'indent': 1,
					'parent': status_sipm,
					'piutang': 0,
				}
				isi = []
				for sipm,info_sipm in info.items():
					entry_date = info_sipm['tgl_tagih']
					info_sipm['range1'] = info_sipm['range2'] = info_sipm['range3'] = info_sipm['range4'] = info_sipm['range5'] = 0.0
					aging = get_ageing_data(entry_date,info_sipm)
					isi.append({
						'nama': info_sipm['nama_pemilik'],
						'tgl_jual': info_sipm['tgl_jual'],
						'tgl_tagih': info_sipm['tgl_tagih'],
						'ht': info_sipm['ht'],
						'hc': info_sipm['hc'],
						'nama_area': info_sipm['nama_area'],
						'piutang': info_sipm['piutang'],
						'indent': 2,
						"parent": info_sipm['customer'],
						'sipm': info_sipm['sipm'],
						aging[0] : aging[1],
						'no_tagih': info_sipm['no_tagih']
					})
					# isi.append(get_ageing_data(entry_date,info_sipm))
					parent2['piutang'] += info_sipm['piutang']
					parent['piutang'] += info_sipm['piutang']

				out.extend([parent2]+isi)
				
			# frappe.msgprint(str(out)+ ' out')
			tampil_st.extend([parent]+out)
			# frappe.msgprint(str(tampil_st)+' tampil_st')
		elif status_sipm == 'Belum Realisasi':
			tampil_br = []
			parent = {
				'nama': 'Belum Realisasi',
				'piutang': 0
			}
			
			out = []
			for customer,info in pemilik_dict.items():
				# frappe.msgprint(str(status_sipm)+ ' status_sipm')
				parent2 = {
					'nama': customer,
					'indent': 1,
					'parent': status_sipm,
					'piutang': 0,
				}
				isi = []
				for sipm,info_sipm in info.items():
					entry_date = info_sipm['tgl_tagih']
					info_sipm['range1'] = info_sipm['range2'] = info_sipm['range3'] = info_sipm['range4'] = info_sipm['range5'] = 0.0
					aging = get_ageing_data(entry_date,info_sipm)
					isi.append({
						'nama': info_sipm['nama_pemilik'],
						'tgl_jual': info_sipm['tgl_jual'],
						'tgl_tagih': info_sipm['tgl_tagih'],
						'ht': info_sipm['ht'],
						'hc': info_sipm['hc'],
						'nama_area': info_sipm['nama_area'],
						'piutang': info_sipm['piutang'],
						'indent': 2,
						"parent": info_sipm['customer'],
						'sipm': info_sipm['sipm'],
						aging[0] : aging[1],
						'no_tagih': info_sipm['no_tagih']
					})
					parent2['piutang'] += info_sipm['piutang']
					parent['piutang'] += info_sipm['piutang']

				out.extend([parent2]+isi)
				
			# frappe.msgprint(str(out)+ ' out')
			tampil_br.extend([parent]+out)	
		elif status_sipm == 'Sudah Realisasi':
			tampil_sr = []
			parent = {
				'nama': status_sipm,
				'piutang': 0
			}
			
			out = []
			for customer,info in pemilik_dict.items():
				# frappe.msgprint(str(status_sipm)+ ' status_sipm')
				parent2 = {
					'nama': customer,
					'indent': 1,
					'parent': status_sipm,
					'piutang': 0,
				}
				isi = []
				for sipm,info_sipm in info.items():
					entry_date = info_sipm['tgl_tagih']
					info_sipm['piutang'] = info_sipm['terbayarkan']
					info_sipm['range1'] = info_sipm['range2'] = info_sipm['range3'] = info_sipm['range4'] = info_sipm['range5'] = 0.0
					aging = get_ageing_data(entry_date,info_sipm)
					# frappe.msgprint(str(aging)+ ' agingaging')
					isi.append({
						'nama': info_sipm['nama_pemilik'],
						'tgl_jual': info_sipm['tgl_jual'],
						'tgl_tagih': info_sipm['tgl_tagih'],
						'ht': info_sipm['ht'],
						'hc': info_sipm['hc'],
						'nama_area': info_sipm['nama_area'],
						'piutang': info_sipm['piutang'],
						'indent': 2,
						"parent": info_sipm['customer'],
						'sipm': info_sipm['sipm'],
						aging[0] : aging[1],
						'no_tagih': info_sipm['no_tagih']
					})
					parent2['piutang'] += info_sipm['terbayarkan']
					parent['piutang'] += info_sipm['terbayarkan']

				out.extend([parent2]+isi)
				
			# frappe.msgprint(str(out)+ ' out')
			tampil_sr.extend([parent]+out)	

	tampil.extend(tampil_bt or [])
	tampil.extend(tampil_st or [])
	tampil.extend(tampil_br or [])
	tampil.extend(tampil_sr or [])

	return tampil

def setup_ageing_columns():
	columns = []
	range1 = 30
	range2 = 60
	range3 = 90
	range4 = 120
	for i, label in enumerate(
		[
			"0-{range1}".format(range1=range1),
			"{range1}-{range2}".format(
				range1=cint(range1) + 1, range2=range2
			),
			"{range2}-{range3}".format(
				range2=cint(range2) + 1, range3=range3
			),
			"{range3}-{range4}".format(
				range3=cint(range3) + 1, range4=range4
			),
			"{range4}-{above}".format(range4=cint(range4) + 1, above=_("Above")),
		]
	):
			columns.append({
			"label": _(label),
			"fieldname": "range" + str(i + 1),
			"fieldtype": 'Currency',
			"width": 100
		})
	
	return columns

def get_ageing_data(entry_date, row):
	# [0-30, 30-60, 60-90, 90-120, 120-above]
	# row.range1 = row.range2 = row.range3 = row.range4 = row.range5 = 0.0
	row['range1'] = row['range2'] = row['range3'] = row['range4'] = row['range5'] = 0.0

	age_as_on = getdate(nowdate())

	row['age'] = (getdate(age_as_on) - getdate(entry_date)).days or 0
	index = None

	range1 = 30
	range2 = 60
	range3 = 90
	range4 = 120
	
	for i, days in enumerate(
		[range1, range2,range3, range4]
	):
		if cint(row['age']) <= cint(days):
			index = i
			break

	if index is None:
		index = 4

	o_range = "range" + str(index + 1)
	o_piutang = row['piutang']
	row["range" + str(index + 1)] = row['piutang']
	# frappe.msgprint(str(index + 1)+' jkjkj')
	# frappe.msgprint(str(row["range" + str(index + 1)]))
	return o_range,o_piutang
	

def get_columns(filters):
	columns = [
	
		{
			"label": _("Nama"),
			"fieldname": "nama",
			"fieldtype": "HTML",
			"width": 200
		},
		{
			"label": _("Tgl Jual"),
			"fieldname": "tgl_jual",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Tgl Tagih"),
			"fieldname": "tgl_tagih",
			"fieldtype": "Date",
			"width": 100
		},
		# {
		# 	"label": _("No Tagih"),
		# 	"fieldname": "no_tagih",
		# 	"fieldtype": "Link",
		# 	"options": "Tagihan Leasing",
		# 	"width": 200
		# },
		{
			"label": _("Ht"),
			"fieldname": "ht",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Hc"),
			"fieldname": "hc",
			"fieldtype": "Int",
			"width": 100
		},
		{
			"label": _("Nama Area"),
			"fieldname": "nama_area",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Piutang"),
			"fieldname": "piutang",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("SIPM"),
			"fieldname": "sipm",
			"fieldtype": "Link",
			"options": "Sales Invoice Penjualan Motor",
			"width": 200
		},
		# {
		# 	"label": _("KetBerkas"),
		# 	"fieldname": "ket",
		# 	"fieldtype": "Data",
		# 	"width": 150
		# },
		
	]

	# columns.extend(setup_ageing_columns())

	return columns

