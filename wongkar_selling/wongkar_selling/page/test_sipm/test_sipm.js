frappe.pages['test-sipm'].on_page_load = function(wrapper) {
	new DevExtreme(wrapper)
}

DevExtreme = Class.extend({
	init: function(wrapper){
		var me = this
		var out = []
		var filters = {}
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'SIPM',
			single_column: true
		});
		this.page.add_field({
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype:'Date',
			reqd: 1,
			async change() {
				filters['from_date'] = this.value;
				me.make(filters)
			}
		});
		this.page.add_field({
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype:'Date',
			reqd: 1,
			async change() {
				filters['to_date'] = this.value;
				me.make(filters)
			}
		});
		// out.push(filters)
		// this.make(filters)

	},
	// make page
	async make(filters) {
		console.log(filters, ' filtersxxx')
		console.log(Object.keys(filters).length, ' filtersxxx111')
		let me = $(this);
		DevExpress.localization.locale(navigator.language);
		let body = `<div class="dx-viewport">
			<div id="dataGrid"></div>
		</div>`;
		$(frappe.render_template(body, this)).appendTo(this.page.main)
		if(Object.keys(filters).length > 1){
			var data =  await this.get_data(filters)
			console.log(data)		
			$("#dataGrid").dxDataGrid({
				dataSource: data.message,
				keyExpr: 'name',
				columns: [
				{
					dataField: 'name',
					format: 'string',
					alignment: 'left',
					width: 200,
					caption: 'SIPM',
					// format: {
					// 	type: 'HTML',
					// }
				},
				{
					dataField: 'posting_date',
					format: 'string',
					alignment: 'center',
					width: 100,
					caption: 'Posting Date'
				},
				{
					dataField: 'customer_name',
					format: 'string',
					alignment: 'left',
					width: 200,
					caption: 'Customer Name'
				},
				{
					dataField: 'grand_total',
					format: 'decimal',
					alignment: 'right',
					width: 200,
					caption: 'Grand Total',
					format: {
						type: 'fixedPoint',
						precision: 2,
						thousandsSeparator: ',',
						currencySymbol: '',
						useGrouping: true,
					}
				}
				],
				showBorders: true,
				allowColumnReordering: true,
				allowColumnResizing: true,
				columnAutoWidth: true,
				scrolling: {
					columnRenderingMode: 'virtual',
				},
				groupPanel: {
					visible: true,
				},
				paging: {
					pageSize: 25,
				},
				pager: {
				visible: true,
				allowedPageSizes: [25, 50, 100, 'all'],
				showPageSizeSelector: true,
				showInfo: true,
				showNavigationButtons: true,
				},
				filterRow: { visible: true },
	        	searchPanel: { visible: true }, 
				columnChooser: { enabled: true },
				export: {
					enabled: true
				},
				summary: {
					groupItems: [{
						column: 'grand_total',
						summaryType: 'sum',
						displayFormat: '{0}',
						showInGroupFooter: false,
						alignByColumn: true,
						valueFormat: {
							type: 'fixedPoint',
							precision: 2,
							thousandsSeparator: ',',
							currencySymbol: '',
							useGrouping: true,
						},
					}],
				},
				onExporting(e) {
					const workbook = new ExcelJS.Workbook();
					const worksheet = workbook.addWorksheet('SIPM');
			  
					DevExpress.excelExporter.exportDataGrid({
					  component: e.component,
					  worksheet,
					  autoFilterEnabled: true,
					}).then(() => {
					  workbook.xlsx.writeBuffer().then((buffer) => {
						saveAs(new Blob([buffer], { type: 'application/octet-stream' }), 'SIPM.xlsx');
					  });
					});
					e.cancel = true;
				  }
				});	
		}
		
	},
	async get_data(filters){
		var data = await frappe.call({
			method: 'wongkar_selling.wongkar_selling.page.test_sipm.test_sipm.get_data',
			args: {
				'filters': filters
			}
		});

		return data
	},

})