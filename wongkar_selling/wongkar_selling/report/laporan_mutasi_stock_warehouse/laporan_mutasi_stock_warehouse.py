# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from operator import itemgetter

import frappe
from frappe import _
from frappe.query_builder.functions import Coalesce
from frappe.utils import cint, date_diff, flt, getdate
from six import iteritems

import erpnext
from erpnext.stock.report.stock_ageing.stock_ageing import FIFOSlots, get_average_age
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition
from erpnext.stock.utils import add_additional_uom_columns, is_reposting_item_valuation_in_progress


def execute(filters=None):
	is_reposting_item_valuation_in_progress()
	if not filters:
		filters = {}

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	f_wh = filters.get("warehouse")

	if filters.get("company"):
		company_currency = erpnext.get_company_currency(filters.get("company"))
	else:
		company_currency = frappe.db.get_single_value("Global Defaults", "default_currency")

	include_uom = filters.get("include_uom")
	columns = get_columns(filters)
	items = get_items(filters)
	# frappe.msgprint(str(items)+ ' items')
	sle = get_stock_ledger_entries(filters, items)
	# sn = get_sn(filters)
	# frappe.msgprint(str(sn)+ ' sn')

	if filters.get("show_stock_ageing_data"):
		filters["show_warehouse_wise_stock"] = True
		item_wise_fifo_queue = FIFOSlots(filters, sle).generate()

	# if no stock ledger entry found return
	# if not sle:
	# 	return columns, []

	iwb_map = get_item_warehouse_map(filters, sle)
	item_map = get_item_details(items, sle, filters)
	item_reorder_detail_map = get_item_reorder_details(item_map.keys())

	data = []
	# data.extend(sn or [])
	# frappe.msgprint(str(data)+' datasss')
	conversion_factors = {}

	_func = itemgetter(1)
	# frappe.msgprint(f"{iwb_map}")
	for (company, item, warehouse) in sorted(iwb_map):
		if item_map.get(item):
			qty_dict = iwb_map[(company, item, warehouse)]
			item_reorder_level = 0
			item_reorder_qty = 0
			if item + warehouse in item_reorder_detail_map:
				item_reorder_level = item_reorder_detail_map[item + warehouse]["warehouse_reorder_level"]
				item_reorder_qty = item_reorder_detail_map[item + warehouse]["warehouse_reorder_qty"]

			report_data = {
				"currency": company_currency,
				"item_code": item,
				"warehouse": warehouse,
				"company": company,
				"reorder_level": item_reorder_level,
				"reorder_qty": item_reorder_qty,
			}
			report_data.update(item_map[item])
			report_data.update(qty_dict)

			if include_uom:
				conversion_factors.setdefault(item, item_map[item].conversion_factor)

			if filters.get("show_stock_ageing_data"):
				fifo_queue = item_wise_fifo_queue[(item, warehouse)].get("fifo_queue")

				stock_ageing_data = {"average_age": 0, "earliest_age": 0, "latest_age": 0}
				if fifo_queue:
					fifo_queue = sorted(filter(_func, fifo_queue), key=_func)
					if not fifo_queue:
						continue

					stock_ageing_data["average_age"] = get_average_age(fifo_queue, to_date)
					stock_ageing_data["earliest_age"] = date_diff(to_date, fifo_queue[0][1])
					stock_ageing_data["latest_age"] = date_diff(to_date, fifo_queue[-1][1])

				report_data.update(stock_ageing_data)

			data.append(report_data)

	add_additional_uom_columns(columns, data, include_uom, conversion_factors)
	tmp_data = []
	tmp_data_in = []
	tmp_data_open = []
	con = 0
	# frappe.msgprint(f"{data}")
	for i in data:
		cek_ig = frappe.db.get_value('Item',i['item_code'],'has_serial_no')
		if cek_ig == 0:
			tmp_data.append(i)
		elif cek_ig == 1:
			# tmp_data.append(i)
			# frappe.msgprint(f"{con}")
			# frappe.msgprint(f'{i["in_sn"]}xx')
			# frappe.msgprint(f'{i["open_sn"]}xx11')
			
			if i['open_sn']:
				sn = i['open_sn']
				out_sn = i['out_sn']
				tes = get_sn_bale(sn,i['warehouse'],is_opening=True,out_sn=out_sn,to_date=to_date,f_wh=f_wh)
				for t in tes:
					if t['name'] not in str(tmp_data):
						tmp_data.append(t)
			if i['in_sn']:
				sn = i['in_sn']
				out_sn = i['out_sn']
				tes = get_sn_bale(sn,i['warehouse'],is_in=True,out_sn=out_sn,to_date=to_date,f_wh=f_wh)
				for t in tes:
					if t['name'] not in str(tmp_data):
						tmp_data.append(t)
				# print(f'{tes} dddd')
			# 	for t in tes:
			# 		tmp_data.append(t)
		
	# frappe.msgprint(str(tmp_data)+' datasxx11')
	return columns, tmp_data

def get_sn_bale(sn,wh,is_opening=False,is_in=False,out_sn='',to_date='',f_wh=None):
	sn = sn.split('\n')
	out_sn = out_sn.split('\n')
	str_sn = str(sn)
	str_sn = str_sn.replace('[','(').replace(']',')')
	data_sn = frappe.db.sql(""" 
		SELECT 
			sn.name,
			sn.`purchase_date`,
			sn.delivery_date,
			sn.item_code,
			sn.item_name,
			sn.warehouse AS wh,
			sn.purchase_rate,
			sn.status,
			SUBSTRING_INDEX(sn.name,'--',1) AS no_mesin,
			SUBSTRING_INDEX(sn.name,'--',-1) AS no_rangka,
			IF({2},sn.purchase_rate,0) AS opening_val,
			IF({2},1,0) AS opening_qty,
			IF({3},sn.purchase_rate,0)  AS in_val,
			IF({3},1,0) AS in_qty,
			IF(sn.warehouse != '{1}',1,0) AS out_qtys,
			IF(sn.warehouse != '{1}',sn.purchase_rate,0) AS out_val,
			IF(sn.warehouse IS NOT NULL,sn.purchase_rate,0) AS bal_va,
			IF(sn.warehouse IS NULL,IF(sn.delivery_document_type IS NOT NULL,
			(SELECT set_warehouse FROM `tabSales Invoice Penjualan Motor` WHERE NAME = sn.delivery_document_no),sn.warehouse),sn.warehouse) AS warehouse
		from `tabSerial No` sn where  sn.name in {0} order by sn.purchase_date asc """.format(str_sn,wh,is_opening,is_in),as_dict=1,debug=0)
	# frappe.msgprint(f'{data_sn} snxxx')
	
	for i in data_sn:
		# frappe.msgprint(f'{i["delivery_date"]} {to_date}snxxx')
		if i['name'] in out_sn :
			if i["delivery_date"]:
				# frappe.msgprint(f'{i["delivery_date"]} {to_date}snxxx')
				if i["delivery_date"] <= getdate(to_date):
					i['out_qty'] = 1
					i['out_val'] = i['purchase_rate']
				elif f_wh and wh != i['warehouse']:
					i['out_qty'] = 1
					i['out_val'] = i['purchase_rate']
				else:
					i['out_qty'] = 0
					i['out_val'] = 0
			elif i['status'] == 'Active':
				i['out_qty'] = 0
				i['out_val'] = 0
			else:
				i['out_qty'] = 0
				i['out_val'] = 0
		else:
			i['out_qty'] = 0
			i['out_val'] = 0
		i['bal_qty'] = i['opening_qty'] + i['in_qty'] - i['out_qty']
		i['bal_val'] = i['opening_val'] + i['in_val'] - i['out_val']
	return data_sn

def get_sn(filters):
	conditions = ''
	if filters.get("item_code"):
		conditions = ' sn.item_code = "{}" and '.format(filters.get("item_code"))

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	data_sn = frappe.db.sql(""" 
		SELECT 
			sn.`purchase_date`,
			sn.delivery_date,
			sn.item_code,
			sn.item_name,
			sn.warehouse AS wh,
			sn.purchase_rate,
			sn.status,
			SUBSTRING_INDEX(sn.name,'--',1) AS no_mesin,
			SUBSTRING_INDEX(sn.name,'--',-1) AS no_rangka,
			IF(sn.warehouse IS NULL,0,IF(sn.`purchase_date` < CURRENT_DATE(),sn.purchase_rate,0))  AS opening_val,
			IF(sn.warehouse IS NULL,0,IF(sn.`purchase_date` < CURRENT_DATE(),1,0)) AS opening_qty,
			IF(sn.warehouse IS NOT NULL,IF(sn.`purchase_date` < CURRENT_DATE(),0,sn.purchase_rate),0) AS in_val,
			IF(sn.warehouse IS NOT NULL,IF(sn.`purchase_date` < CURRENT_DATE(),0,1),0) AS in_qty,
			IF(sn.warehouse IS NOT NULL,0,1) AS out_qty,
			IF(sn.warehouse IS NOT NULL,0,sn.purchase_rate) AS out_val,
			IF(sn.warehouse IS NOT NULL,sn.purchase_rate,0) AS bal_val,
			IF(sn.warehouse IS NULL,IF(sn.delivery_document_type IS NOT NULL,
			(SELECT set_warehouse FROM `tabSales Invoice Penjualan Motor` WHERE NAME = sn.delivery_document_no),sn.warehouse),sn.warehouse) AS warehouse
		from `tabSerial No` sn where  {0}  sn.purchase_date <= '{2}' order by sn.purchase_date asc """.format(conditions,from_date,to_date),as_dict=1,debug=0)

	tmp = []
	for i in data_sn:
		if  (i['purchase_date'] > getdate(from_date) and i['purchase_date'] < getdate(to_date)):
			tmp.append({
					'item_code': i['item_code'],
					'item_name': i['item_name'],
					'no_rangka': i['no_rangka'],
					'no_mesin': i['no_mesin'],
					'warehouse': i['warehouse'],
					'status': i['status'],
					'purchase_date': i['purchase_date'],
					'opening_qty': 0,
					'opening_val': 0,
					'in_qty':1,
					'in_val': i['purchase_rate'],
					'out_qty': 0,
					'out_val': 0,
					'saldo_qty': 1,
					'bal_val': i['purchase_rate']

				})
		# if i['purchase_date'] >= getdate(from_date):
		# 	if i['status'] == 'Delivered':
		# 			tmp.append({
		# 			'item_code': i['item_code'],
		# 			'item_name': i['item_name'],
		# 			'no_rangka': i['no_rangka'],
		# 			'no_mesin': i['no_mesin'],
		# 			'warehouse': i['warehouse'],
		# 			'status': i['status'],
		# 			'purchase_date': i['purchase_date'],
		# 			'opening_qty': 0,
		# 			'opening_val': 0,
		# 			'in_qty':0,
		# 			'in_val': 0,
		# 			'out_qty': 1,
		# 			'out_val': i['purchase_rate'],
		# 			'bal_val': 0
		# 		})
		# 	else:
		# 		tmp.append({
		# 			'item_code': i['item_code'],
		# 			'item_name': i['item_name'],
		# 			'no_rangka': i['no_rangka'],
		# 			'no_mesin': i['no_mesin'],
		# 			'warehouse': i['warehouse'],
		# 			'status': i['status'],
		# 			'purchase_date': i['purchase_date'],
		# 			'opening_qty': 1,
		# 			'opening_val': i['purchase_rate'],
		# 			'in_qty':0,
		# 			'in_val': 0,
		# 			'out_qty': 0
		# 		})

	return tmp


def get_columns(filters):
	"""return columns"""
	columns = [
		{
			"label": _("Kode Barang"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200,
		},
		{"label": _("Nama Barang"), "fieldname": "item_name", "width": 150,"hidden":0},
		{"label": _("Nomor Rangka"), "fieldname": "no_rangka", "width": 150},
		{"label": _("Nomor Mesin"), "fieldname": "no_mesin", "width": 150},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 100,
			"hidden":1
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 200,
			"hidden":0
		},
		# {
		# 	"label": _("Serial No"),
		# 	"fieldname": "serial_no",
		# 	"fieldtype": "Data",
		# 	"width": 200,
		# 	"hidden":0
		# },
		# {
		# 	"label": _("Status"),
		# 	"fieldname": "status",
		# 	"fieldtype": "Data",
		# 	"width": 200,
		# 	"hidden":0
		# },
		# {
		# 	"label": _("purchase_date"),
		# 	"fieldname": "purchase_date",
		# 	"fieldtype": "Date",
		# 	"width": 200,
		# 	"hidden":0
		# },
		{
			"label": _("Stock UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 90,
			"hidden":1
		},
		# {
		# 	"label": _("Balance Qty"),
		# 	"fieldname": "bal_qty",
		# 	"fieldtype": "Float",
		# 	"width": 100,
		# 	"convertible": "qty",
		# 	"hidden":1
		# },
		{
			"label": _("Opening Qty"),
			"fieldname": "opening_qty",
			"fieldtype": "Float",
			"width": 100,
			"convertible": "qty",
			"hidden":0
		},
		# {"label": _("No Mesin--No Rangka Open"), "fieldname": "open_sn", "fieldtype": "Small Text", "width": 200},
		{
			"label": _("Saldo Awal"),
			"fieldname": "opening_val",
			"fieldtype": "Currency",
			"width": 150,
			"options": "currency",
		},
		{
			"label": _("In Qty"),
			"fieldname": "in_qty",
			"fieldtype": "Float",
			"width": 80,
			"convertible": "qty",
			"hidden":0
		},
		# {"label": _("No Mesin--No Rangka In"), "fieldname": "in_sn", "fieldtype": "Small Text", "width": 200},
		{"label": _("Pembelian"), "fieldname": "in_val", "fieldtype": "Currency", "width": 150},
		{"label": _("Barang Siap Yang Dijual"), "fieldname": "barang_jual", "fieldtype": "Currency", "width": 180,"hidden":1},
		{
			"label": _("Out Qty"),
			"fieldname": "out_qty",
			"fieldtype": "Float",
			"width": 80,
			"convertible": "qty",
			"hidden":0
		},
		# {"label": _("No Mesin--No Rangka Out"), "fieldname": "out_sn", "fieldtype": "Small Text", "width": 200},
		{"label": _("Harga Pokok Penjualan"), "fieldname": "out_val", "fieldtype": "Currency", "width": 180,},
		{
			"label": _("Saldo Qty"),
			"fieldname": "bal_qty",
			"fieldtype": "Float",
			"width": 80,
			"convertible": "qty",
			"hidden":0
		},
		# {"label": _("No Mesin--No Rangka Saldo"), "fieldname": "bal_sn", "fieldtype": "Small Text", "width": 200},
		{
			"label": _("Saldo Akhir"),
			"fieldname": "bal_val",
			"fieldtype": "Currency",
			"width": 150,
			"options": "currency",
		},
		{
			"label": _("Valuation Rate"),
			"fieldname": "val_rate",
			"fieldtype": "Currency",
			"width": 90,
			"convertible": "rate",
			"options": "currency",
			"hidden":1
		},
		{
			"label": _("Reorder Level"),
			"fieldname": "reorder_level",
			"fieldtype": "Float",
			"width": 80,
			"convertible": "qty",
			"hidden":1
		},
		{
			"label": _("Reorder Qty"),
			"fieldname": "reorder_qty",
			"fieldtype": "Float",
			"width": 80,
			"convertible": "qty",
			"hidden":1
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 100,
			"hidden":1
		},
	]

	if filters.get("show_stock_ageing_data"):
		columns += [
			{"label": _("Average Age"), "fieldname": "average_age", "width": 100},
			{"label": _("Earliest Age"), "fieldname": "earliest_age", "width": 100},
			{"label": _("Latest Age"), "fieldname": "latest_age", "width": 100},
		]

	if filters.get("show_variant_attributes"):
		columns += [
			{"label": att_name, "fieldname": att_name, "width": 100}
			for att_name in get_variants_attributes()
		]

	return columns


def get_conditions(filters):
	conditions = ""
	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))

	if filters.get("to_date"):
		conditions += " and sle.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))
	else:
		frappe.throw(_("'To Date' is required"))

	if filters.get("company"):
		conditions += " and sle.company = %s" % frappe.db.escape(filters.get("company"))

	if filters.get("warehouse"):
		warehouse_details = frappe.db.get_value(
			"Warehouse", filters.get("warehouse"), ["lft", "rgt"], as_dict=1
		)
		if warehouse_details:
			conditions += (
				" and exists (select name from `tabWarehouse` wh \
				where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)"
				% (warehouse_details.lft, warehouse_details.rgt)
			)

	if filters.get("warehouse_type") and not filters.get("warehouse"):
		conditions += (
			" and exists (select name from `tabWarehouse` wh \
			where wh.warehouse_type = '%s' and sle.warehouse = wh.name)"
			% (filters.get("warehouse_type"))
		)

	return conditions


def get_stock_ledger_entries_sp(filters, items):
	item_conditions_sql = ""
	if items:
		item_conditions_sql = " and sle.item_code in ({})".format(
			", ".join(frappe.db.escape(i, percent=False) for i in items)
		)

	conditions = get_conditions(filters)

	return frappe.db.sql(
		"""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
			sle.item_code as name, sle.voucher_no, sle.stock_value, sle.batch_no,sle.serial_no
		from
			`tabStock Ledger Entry` sle
		join `tabItem` i on i.name = sle.item_code
		where sle.docstatus < 2 %s %s
		and is_cancelled = 0 and i.item_group in ('All Item Groups', 'Aset Tetap', 'Kendaraan Operasional', 'KO-001', 'H1 - Motor', 'H2 - Ahass', 
		'Ganti Ban Depan/Blakang', 'Ganti belt drive', 'Ganti Kabel Speedo/Kopling', 'Ganti Kampas Cakram Depan/Blakang', 'Ganti Kampas Tromol', 
		'Ganti rantai mesin', 'Ganti rantai/ Gear Set', 'Jasa Service', 'Overhaul turun mesin', 'Paket Kuras Tangki', 'Paket Pembersihan CVT', 
		'Paket Pemeriksaan PGM-FI', 'Service lengkap', 'H3 - Sparepart', 'HGA', 'Oli', 'Sparepart', 'Tools', 'Jasa')
		order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty"""
		% (item_conditions_sql, conditions),  # nosec
		as_dict=1,debug=0
	)

def get_stock_ledger_entries_motor(filters, items):
	item_conditions_sql = ""
	if items:
		item_conditions_sql = " and sle.item_code in ({})".format(
			", ".join(frappe.db.escape(i, percent=False) for i in items)
		)

	conditions = get_conditions(filters)

	return frappe.db.sql(
		"""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
			sle.item_code as name, sle.voucher_no, sle.stock_value, sle.batch_no,sle.serial_no
		from
			`tabStock Ledger Entry` sle
		join `tabItem` i on i.name = sle.item_code
		where sle.docstatus < 2 %s %s
		and is_cancelled = 0 and i.item_group not in ('All Item Groups', 'Aset Tetap', 'Kendaraan Operasional', 'KO-001', 'H1 - Motor', 'H2 - Ahass', 
		'Ganti Ban Depan/Blakang', 'Ganti belt drive', 'Ganti Kabel Speedo/Kopling', 'Ganti Kampas Cakram Depan/Blakang', 'Ganti Kampas Tromol', 
		'Ganti rantai mesin', 'Ganti rantai/ Gear Set', 'Jasa Service', 'Overhaul turun mesin', 'Paket Kuras Tangki', 'Paket Pembersihan CVT', 
		'Paket Pemeriksaan PGM-FI', 'Service lengkap', 'H3 - Sparepart', 'HGA', 'Oli', 'Sparepart', 'Tools', 'Jasa')
		order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty"""
		% (item_conditions_sql, conditions),  # nosec
		as_dict=1,debug=0
	)


def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ""
	if items:
		item_conditions_sql = " and sle.item_code in ({})".format(
			", ".join(frappe.db.escape(i, percent=False) for i in items)
		)

	conditions = get_conditions(filters)

	return frappe.db.sql(
		"""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
			sle.item_code as name, sle.voucher_no,sle.voucher_detail_no, sle.stock_value, sle.batch_no,sle.serial_no
		from
			`tabStock Ledger Entry` sle
		join `tabItem` i on i.name = sle.item_code
		where sle.docstatus < 2 %s %s
		and is_cancelled = 0 """
		% (item_conditions_sql, conditions),  # nosec
		as_dict=1,debug=0
	)


def get_opening_vouchers(to_date):
	opening_vouchers = {"Stock Entry": [], "Stock Reconciliation": []}

	se = frappe.qb.DocType("Stock Entry")
	sr = frappe.qb.DocType("Stock Reconciliation")

	vouchers_data = (
		frappe.qb.from_(
			(
				frappe.qb.from_(se)
				.select(se.name, Coalesce("Stock Entry").as_("voucher_type"))
				.where((se.docstatus == 1) & (se.posting_date <= to_date) & (se.is_opening == "Yes"))
			)
			+ (
				frappe.qb.from_(sr)
				.select(sr.name, Coalesce("Stock Reconciliation").as_("voucher_type"))
				.where((sr.docstatus == 1) & (sr.posting_date <= to_date) & (sr.purpose == "Opening Stock"))
			)
		).select("voucher_type", "name")
	).run(as_dict=True)

	if vouchers_data:
		for d in vouchers_data:
			opening_vouchers[d.voucher_type].append(d.name)

	return opening_vouchers


def get_item_warehouse_map(filters, sle):
	iwb_map = {}
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	opening_vouchers = get_opening_vouchers(to_date)
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	serial_no = ''
	for d in sle:
		key = (d.company, d.item_code, d.warehouse)
		if key not in iwb_map:
			iwb_map[key] = frappe._dict(
				{
					"opening_qty": 0.0,
					"opening_val": 0.0,
					"in_qty": 0.0,
					"in_val": 0.0,
					"out_qty": 0.0,
					"out_val": 0.0,
					"bal_qty": 0.0,
					"bal_val": 0.0,
					"val_rate": 0.0,
					"open_sn": "",
					"in_sn": "",
					"out_sn": "",
					"bal_sn": ""
				}
			)

		qty_dict = iwb_map[(d.company, d.item_code, d.warehouse)]

		if d.voucher_type == "Stock Reconciliation" and not d.batch_no:
			qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
		else:
			qty_diff = flt(d.actual_qty)
			if d.serial_no:
				serial_no = d.serial_no
			
		value_diff = flt(d.stock_value_difference)

		if d.posting_date < from_date or d.voucher_no in opening_vouchers.get(d.voucher_type, []):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff
			# frappe.msgprint(f"{d} dddddd")
			if d.serial_no:
				qty_dict.open_sn += format(serial_no+"\t")
			# frappe.msgprint(serial_no)

		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(qty_diff, float_precision) >= 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
				# frappe.msgprint(f"{serial_no}")
				if d.serial_no:
					qty_dict.in_sn += format(serial_no+"\t")
				# frappe.msgprint(f"{qty_dict.in_sn} xxx" )
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)
				if d.serial_no:
				
					qty_dict.out_sn += format(serial_no+"\t")
				# qty_dict.serial_no += serial_no

		qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff
		qty_dict.bal_val += value_diff

		# qty_dict.bal_sn += qty_dict.in_sn.replace(qty_dict.out_sn, "")
	# frappe.msgprint(f"{qty_dict.in_sn} in {qty_dict.out_sn} out")
		# if qty_dict.bal_qty  > 0:
		# 	qty_dict.bal_sn += serial_no
		# frappe.msgprint(f"{ d.serial_no} bal_sn")

	# frappe.msgprint(f'{iwb_map} iwb_map before')

	iwb_map = filter_items_with_no_transactions(iwb_map, float_precision)
	# frappe.msgprint(f'{iwb_map} iwb_mapxxx')

	return iwb_map

def hilang_data_sama(data_str,opening_qty,out_sn):
	from collections import Counter
	
	data_list = data_str.split("\t")
	hasil = list(filter(None, set(data_list)))
	# frappe.msgprint(f"{hasil}zzzzxxx {opening_qty}xxx{out_sn}yyy")
	
	
	if len(hasil) == opening_qty:
		new_str = "\t".join(hasil)
		return new_str
	else:
		count_dict = Counter(data_list)
		
		new_list = ["" if count_dict[item]%2 <1  else item for item in data_list]
		filtered_list = list(filter(None, new_list))
		new_str = "\t".join(filtered_list)
		
		return new_str

def hilang_data_dup(data_str):
	data_list = data_str.split("\t")
	new_str = "\t".join(data_list)

	# frappe.msgprint(f'{data_list} data_listxx')

	return new_str


def filter_items_with_no_transactions(iwb_map, float_precision):
	# frappe.msgprint(f'{iwb_map} fdfdfdf')
	tmp_in = []
	tmp_out = []
	for (company, item, warehouse) in sorted(iwb_map):
		qty_dict = iwb_map[(company, item, warehouse)]

		no_transactions = True
		for key, val in iteritems(qty_dict):
			# frappe.msgprint(f"{key} {val} valxx")
			if key not in ['in_sn','out_sn','bal_sn','open_sn']:
				val = flt(val, float_precision)
			# qty_dict['bal_sn'] = qty_dict['out_sn'].replace(qty_dict['in_sn'], "")
			
			# if qty_dict['bal_sn']
			qty_dict[key] = val
			if qty_dict['opening_qty'] == 0:
				qty_dict['open_sn'] = ''
			if key == 'open_sn':
				# frappe.msgprint(f"{key} {val}")
				qty_dict['open_sn'] = qty_dict['open_sn'].replace('\n','\t')
				qty_dict['open_sn'] = hilang_data_sama(qty_dict['open_sn'],qty_dict['opening_qty'],qty_dict['out_sn'])
			if key in ['in_sn']:
				qty_dict['in_sn'] = qty_dict['in_sn'].replace('\n','\t')
				qty_dict['out_sn'] = qty_dict['out_sn'].replace('\n','\t')
				tmp_in_open = qty_dict['in_sn'] + qty_dict['open_sn']
				qty_dict['bal_sn'] = tmp_in_open.replace(qty_dict['out_sn'], "")
			
			qty_dict['open_sn'] = qty_dict['open_sn'].replace('\t','\n')
			qty_dict['in_sn'] = qty_dict['in_sn'].replace('\t','\n')
			qty_dict['out_sn'] = qty_dict['out_sn'].replace('\t','\n')
			qty_dict['bal_sn'] = qty_dict['bal_sn'].replace('\t','\n')

			if qty_dict['bal_qty'] == 0:
				qty_dict['bal_sn'] = ''
			if key != "val_rate" and val:
				no_transactions = False

		if no_transactions:
			iwb_map.pop((company, item, warehouse))

	
	# frappe.msgprint(f'{iwb_map} afterxx')
	
	return iwb_map


def get_items(filters):
	"Get items based on item code, item group or brand."
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))
		if filters.get("brand"):  # used in stock analytics report
			conditions.append("item.brand=%(brand)s")

	items = []
	# frappe.msgprint(str(filters)+ ' filtersxx')
	# frappe.msgprint(str(conditions)+ ' conditionsxx')
	if conditions:
		# frappe.msgprint('Masuk sini !!')
		items = frappe.db.sql_list(
			"""select name from `tabItem` item where {}""".format(" and ".join(conditions)), filters,debug=0
		)
	return items


def get_item_details(items, sle, filters):
	item_details = {}
	if not items:
		items = list(set(d.item_code for d in sle))

	if not items:
		return item_details

	cf_field = cf_join = ""
	if filters.get("include_uom"):
		cf_field = ", ucd.conversion_factor"
		cf_join = (
			"left join `tabUOM Conversion Detail` ucd on ucd.parent=item.name and ucd.uom=%s"
			% frappe.db.escape(filters.get("include_uom"))
		)

	res = frappe.db.sql(
		"""
		select
			item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom %s
		from
			`tabItem` item
			%s
		where
			item.name in (%s)
	"""
		% (cf_field, cf_join, ",".join(["%s"] * len(items))),
		items,
		as_dict=1,
	)

	for item in res:
		item_details.setdefault(item.name, item)

	if filters.get("show_variant_attributes", 0) == 1:
		variant_values = get_variant_values_for(list(item_details))
		item_details = {k: v.update(variant_values.get(k, {})) for k, v in iteritems(item_details)}

	return item_details


def get_item_reorder_details(items):
	item_reorder_details = frappe._dict()

	if items:
		item_reorder_details = frappe.db.sql(
			"""
			select parent, warehouse, warehouse_reorder_qty, warehouse_reorder_level
			from `tabItem Reorder`
			where parent in ({0})
		""".format(
				", ".join(frappe.db.escape(i, percent=False) for i in items)
			),
			as_dict=1,
		)

	return dict((d.parent + d.warehouse, d) for d in item_reorder_details)


def get_variants_attributes():
	"""Return all item variant attributes."""
	return [i.name for i in frappe.get_all("Item Attribute")]


def get_variant_values_for(items):
	"""Returns variant values for items."""
	attribute_map = {}
	for attr in frappe.db.sql(
		"""select parent, attribute, attribute_value
		from `tabItem Variant Attribute` where parent in (%s)
		"""
		% ", ".join(["%s"] * len(items)),
		tuple(items),
		as_dict=1,
	):
		attribute_map.setdefault(attr["parent"], {})
		attribute_map[attr["parent"]].update({attr["attribute"]: attr["attribute_value"]})

	return attribute_map

