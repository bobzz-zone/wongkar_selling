frappe.provide("wongkar_selling.custom_financial_statements");

erpnext.financial_statements = {
	"filters": get_filters(),
	"formatter": function(value, row, column, data, default_formatter) {
		if (data && column.fieldname=="account") {
			value = data.account_name || value;

			column.link_onclick =
				"erpnext.financial_statements.open_general_ledger(" + JSON.stringify(data) + ")";
			column.is_tree = true;
		}

		value = default_formatter(value, row, column, data);

		if (data && !data.parent_account) {
			value = $(`<span>${value}</span>`);

			var $value = $(value).css("font-weight", "bold");
			if (data.warn_if_negative && data[column.fieldname] < 0) {
				$value.addClass("text-danger");
			}

			value = $value.wrap("<p></p>").parent().html();
		}

		return value;
	},
	"open_general_ledger": function(data) {
		if (!data.account) return;
		var project = $.grep(frappe.query_report.filters, function(e){ return e.df.fieldname == 'project'; })

		frappe.route_options = {
			"account": data.account,
			"company": frappe.query_report.get_filter_value('company'),
			"from_date": data.from_date || data.year_start_date,
			"to_date": data.to_date || data.year_end_date,
			"project": (project && project.length > 0) ? project[0].$input.val() : ""
		};
		frappe.set_route("query-report", "General Ledger");
	},
	"tree": true,
	"name_field": "account",
	"parent_field": "parent_account",
	"initial_depth": 3,
	onload: function(report) {
		// dropdown for links to other financial statements
		erpnext.financial_statements.filters = get_filters()

		let fiscal_year = frappe.defaults.get_user_default("fiscal_year")

		frappe.model.with_doc("Fiscal Year", fiscal_year, function(r) {
			var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
			frappe.query_report.set_filter_value({
				period_start_date: fy.year_start_date,
				period_end_date: fy.year_end_date
			});
		});

		const views_menu = report.page.add_custom_button_group(__('Financial Statements'));

		report.page.add_custom_menu_item(views_menu, __("Balance Sheet"), function() {
			var filters = report.get_values();
			frappe.set_route('query-report', 'Balance Sheet', {company: filters.company});
		});

		report.page.add_custom_menu_item(views_menu, __("Profit and Loss"), function() {
			var filters = report.get_values();
			frappe.set_route('query-report', 'Profit and Loss Statement', {company: filters.company});
		});

		report.page.add_custom_menu_item(views_menu, __("Cash Flow Statement"), function() {
			var filters = report.get_values();
			frappe.set_route('query-report', 'Cash Flow', {company: filters.company});
		});
	}
};

function bulan(){
	var b = ''
	var tanggal = frappe.datetime.get_today()
	console.log(tanggal, ' bulan')
	var pisah = tanggal.split('-');
	// frappe.msgprint(pisah[1])
	if(pisah[1] == '01'){
		b = 'Januari'
	}
	if(pisah[1] == '02'){
		b = 'Februari'
	}
	if(pisah[1] == '03'){
		b = 'Maret'
	}
	if(pisah[1] == '04'){
		b = 'April'
	}
	if(pisah[1] == '05'){
		b = 'Mei'
	}
	if(pisah[1] == '06'){
		b = 'Juni'
	}
	if(pisah[1] == '07'){
		b = 'Juli'
	}
	if(pisah[1] == '08'){
		b = 'Agustus'
	}
	if(pisah[1] == '09'){
		b = 'September'
	}
	if(pisah[1] == '10'){
		b = 'Oktober'
	}
	if(pisah[1] == '11'){
		b = 'November'
	}
	if(pisah[1] == '12'){
		b = 'Desember'
	}
	return b
}

function getLastDayOfMonth(year, month) {
    // Create a Date object for the first day of the next month
    const nextMonth = new Date(year, month + 1, 1);

    // Subtract one day from the first day of the next month to get the last day of the current month
    const lastDay = new Date(nextMonth - 1);

    // Extract year, month, and day components and format the date string
    const lastDayString = `${lastDay.getFullYear()}-${(lastDay.getMonth() + 1).toString().padStart(2, '0')}-${lastDay.getDate().toString().padStart(2, '0')}`;

    return lastDayString;
}

function get_tanggal(bulan, tahun) {
    let awal = "";
    let akhir = "";

    bulan = bulan.toLowerCase();

    switch (bulan) {
        case "januari":
            awal = `${tahun}-01-01`;
            break;
        case "februari":
            awal = `${tahun}-02-01`;
            break;
        case "maret":
            awal = `${tahun}-03-01`;
            break;
        case "april":
            awal = `${tahun}-04-01`;
            break;
        case "mei":
            awal = `${tahun}-05-01`;
            break;
        case "juni":
            awal = `${tahun}-06-01`;
            break;
        case "juli":
            awal = `${tahun}-07-01`;
            break;
        case "agustus":
            awal = `${tahun}-08-01`;
            break;
        case "september":
            awal = `${tahun}-09-01`;
            break;
        case "oktober":
            awal = `${tahun}-10-01`;
            break;
        case "november":
            awal = `${tahun}-11-01`;
            break;
        case "desember":
            awal = `${tahun}-12-01`;
            break;
        default:
            console.log("Invalid month");
            return;
    }

    akhir = getLastDayOfMonth(tahun, new Date(awal).getMonth());

    console.log(awal, ' awalawalaaa');
    console.log(akhir, ' akhirakhiraaa');

    // Assuming frappe.query_report.set_filter_value is defined elsewhere
    frappe.query_report.set_filter_value('period_start_date', awal);
    frappe.query_report.set_filter_value('period_end_date', akhir);
}

// function get_tanggal(bulan,tahun){
// 	if(bulan == "Desember"){
// 		awal = tahun+'-'+'12-01'
// 	}
// 	console.log(awal, ' awalawalaaa')
// 	frappe.query_report.set_filter_value('period_start_date', awal);
// }


function get_filters() {

	let filters = [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"tahun",
			"label": __("Tahun"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1,
			on_change: function() {
				let tahun = frappe.query_report.get_filter_value('tahun');
				let bulan = frappe.query_report.get_filter_value('bulan');
				get_tanggal(bulan,tahun)
			},
		},
		{
			"fieldname":"bulan",
			"label": __("bulan"),
			"fieldtype": "Select",
			"options": "\nJanuari\nFebruari\nMaret\nApril\nMei\nJuni\nJuli\nAgustus\nSeptember\nOktober\nNovember\nDesember",
			// "default": bulan(),
			"reqd": 1,
			on_change: function() {
				let tahun = frappe.query_report.get_filter_value('tahun');
				let bulan = frappe.query_report.get_filter_value('bulan');
				get_tanggal(bulan,tahun)
			},
		},
		{
			"fieldname":"finance_book",
			"label": __("Finance Book"),
			"fieldtype": "Link",
			"options": "Finance Book",
			"hidden": 1
		},
		{
			"fieldname":"filter_based_on",
			"label": __("Filter Based On123"),
			"fieldtype": "Select",
			"options": ["Date Range"],
			"default": ["Date Range"],
			"reqd": 1,
			on_change: function() {
				let filter_based_on = frappe.query_report.get_filter_value('filter_based_on');
				frappe.query_report.toggle_filter_display('from_fiscal_year', filter_based_on === 'Date Range');
				frappe.query_report.toggle_filter_display('to_fiscal_year', filter_based_on === 'Date Range');
				frappe.query_report.toggle_filter_display('period_start_date', filter_based_on === 'Fiscal Year');
				frappe.query_report.toggle_filter_display('period_end_date', filter_based_on === 'Fiscal Year');

				frappe.query_report.refresh();
			},
			"hidden": 1
		},
		{
			"fieldname":"period_start_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"depends_on": "eval:doc.filter_based_on == 'Date Range'",
			"hidden": 1
		},
		{
			"fieldname":"period_end_date",
			"label": __("End Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"depends_on": "eval:doc.filter_based_on == 'Date Range'",
			"hidden": 1
		},
		{
			"fieldname":"from_fiscal_year",
			"label": __("Start Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1,
			"depends_on": "eval:doc.filter_based_on == 'Fiscal Year'"
		},
		{
			"fieldname":"to_fiscal_year",
			"label": __("End Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1,
			"depends_on": "eval:doc.filter_based_on == 'Fiscal Year'",
			"hidden": 1
		},
		{
			"fieldname": "periodicity",
			"label": __("Periodicity"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Monthly", "label": __("Monthly") },
				// { "value": "Yearly", "label": __("Yearly") }
			],
			"default": "Monthly",
			"reqd": 1,
			"hidden": 1
		},
		// Note:
		// If you are modifying this array such that the presentation_currency object
		// is no longer the last object, please make adjustments in cash_flow.js
		// accordingly.
		{
			"fieldname": "presentation_currency",
			"label": __("Currency"),
			"fieldtype": "Select",
			"options": erpnext.get_presentation_currency_list(),
			"hidden": 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Cost Center', txt, {
					company: frappe.query_report.get_filter_value("company")
				});
			},
			"hidden": 1
		}
	]
	
	return filters;
}
