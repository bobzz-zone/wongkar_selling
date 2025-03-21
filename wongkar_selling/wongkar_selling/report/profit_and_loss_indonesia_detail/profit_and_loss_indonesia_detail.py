import frappe
from frappe import _
from frappe.utils import flt

from wongkar_selling.wongkar_selling.report.financial_statements import (
	get_columns,
	get_data,
	get_filtered_list_for_consolidated_report,
	get_period_list,
)


def execute(filters=None):
	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)
	filters40=filters
	filters40["account_like"]="4%"
	acc40 = get_data(
		filters.company,
		"Income",
		"Credit",
		period_list,
		filters=filters40,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
		enable_total=False
	)
	filters50=filters
	filters50["account_like"]="5%"
	acc50 = get_data(
		filters.company,
		"Expense",
		"Debit",
		period_list,
		filters=filters50,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
		enable_total=False
	)

	filters60=filters
	filters60["account_like"]="6%"
	acc60 = get_data(
		filters.company,
		"Income",
		"Credit",
		period_list,
		filters=filters60,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
		enable_total=False
	)

	filters70=filters
	filters70["account_like"]="7%"
	acc70 = get_data(
		filters.company,
		"Expense",
		"Debit",
		period_list,
		filters=filters70,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
		enable_total=False
	)

	laba_kotor = get_net_profit_loss(
		[acc40], [acc50], period_list, filters.company, filters.presentation_currency,title="Laba Kotor"
	)
	laba_bersih = get_net_profit_loss(
		[acc40,acc60], [acc50,acc70], period_list, filters.company, filters.presentation_currency,title="Laba Bersih"
	)
	# net_profit_loss = get_net_profit_loss(
	# 	[acc40,acc70], [acc50,acc60,acc80,acc90,acc99], period_list, filters.company, filters.presentation_currency
	# )

	data = []
	data.extend(acc40 or [])
	data.extend(acc50 or [])
	data.append(laba_kotor)
	data.append({})
	data.extend(acc60 or [])
	data.extend(acc70 or [])
	data.append({})
	data.append(laba_bersih)
	# if net_profit_loss:
	# 	data.append(net_profit_loss)

	columns = get_columns(
		filters.periodicity, period_list, filters.accumulated_values, filters.company
	)

	#chart = get_chart_data(filters, columns, income, expense, net_profit_loss)

	# currency = filters.presentation_currency or frappe.get_cached_value(
	# 	"Company", filters.company, "default_currency"
	# )
	# report_summary = get_report_summary(
	# 	period_list, filters.periodicity, income, expense, net_profit_loss, currency, filters
	# )

	return columns, data
	#, None, chart, report_summary


# def get_report_summary(
# 	period_list, periodicity, income, expense, net_profit_loss, currency, filters, consolidated=False
# ):
# 	net_income, net_expense, net_profit = 0.0, 0.0, 0.0

# 	# from consolidated financial statement
# 	if filters.get("accumulated_in_group_company"):
# 		period_list = get_filtered_list_for_consolidated_report(filters, period_list)

# 	for period in period_list:
# 		key = period if consolidated else period.key
# 		if income:
# 			net_income += income[-2].get(key)
# 		if expense:
# 			net_expense += expense[-2].get(key)
# 		if net_profit_loss:
# 			net_profit += net_profit_loss.get(key)

# 	if len(period_list) == 1 and periodicity == "Yearly":
# 		profit_label = _("Profit This Year")
# 		income_label = _("Total Income This Year")
# 		expense_label = _("Total Expense This Year")
# 	else:
# 		profit_label = _("Net Profit")
# 		income_label = _("Total Income")
# 		expense_label = _("Total Expense")

# 	return [
# 		{"value": net_income, "label": income_label, "datatype": "Currency", "currency": currency},
# 		{"type": "separator", "value": "-"},
# 		{"value": net_expense, "label": expense_label, "datatype": "Currency", "currency": currency},
# 		{"type": "separator", "value": "=", "color": "blue"},
# 		{
# 			"value": net_profit,
# 			"indicator": "Green" if net_profit > 0 else "Red",
# 			"label": profit_label,
# 			"datatype": "Currency",
# 			"currency": currency,
# 		},
# 	]

def get_net_profit_loss(income_list, expense_list, period_list, company, currency=None, consolidated=False,title="Profit for the year"):
	total = 0
	net_profit_loss = {
		"account_name": title,
		"account": title,
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
	}

	has_value = False

	for period in period_list:
		key = period if consolidated else period.key
		total_income=0
		for income in income_list:
			total_income = total_income + (flt(income[0][key], 8) if income else 0)
		total_expense=0
		for expense in expense_list:
			total_expense =total_expense+ (flt(expense[0][key], 8) if expense else 0)

		net_profit_loss[key] = total_income - total_expense

		if net_profit_loss[key]:
			has_value = True

		total += flt(net_profit_loss[key])
		net_profit_loss["total"] = total

	if has_value:
		return net_profit_loss


# def get_chart_data(filters, columns, income, expense, net_profit_loss):
# 	labels = [d.get("label") for d in columns[2:]]

# 	income_data, expense_data, net_profit = [], [], []

# 	for p in columns[2:]:
# 		if income:
# 			income_data.append(income[-2].get(p.get("fieldname")))
# 		if expense:
# 			expense_data.append(expense[-2].get(p.get("fieldname")))
# 		if net_profit_loss:
# 			net_profit.append(net_profit_loss.get(p.get("fieldname")))

# 	datasets = []
# 	if income_data:
# 		datasets.append({"name": _("Income"), "values": income_data})
# 	if expense_data:
# 		datasets.append({"name": _("Expense"), "values": expense_data})
# 	if net_profit:
# 		datasets.append({"name": _("Net Profit/Loss"), "values": net_profit})

# 	chart = {"data": {"labels": labels, "datasets": datasets}}

# 	if not filters.accumulated_values:
# 		chart["type"] = "bar"
# 	else:
# 		chart["type"] = "line"

# 	chart["fieldtype"] = "Currency"

# 	return chart
