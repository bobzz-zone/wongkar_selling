frappe.ui.form.on('Customer', {
	refresh(frm) {
		// your code here
		// cur_frm.add_custom_button(__("Sync"), function(){
  //           sync_document();
  //       });
	}
})

function sync_document(){
    cur_frm.cscript.sync_document_to_site();
}

cur_frm.cscript.sync_document_to_site = function(){
      frappe.call({
              method: "wongkar_selling.wongkar_selling.sync.manual_sync_master",
              args: { 
                  docname: cur_frm.doc.name,
                  doctype : cur_frm.doc.doctype
              },
              callback: function(r) {
                      frappe.msgprint("Sync Selesai");
                      cur_frm.reload_doc();
              }
      })
    console.log(cur_frm.doc.name)
     console.log(cur_frm.doc.doctype)
 }