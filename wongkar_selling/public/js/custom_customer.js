frappe.ui.form.on('Customer', {
	refresh(frm) {
		// your code here
		// cur_frm.add_custom_button(__("Sync"), function(){
  //           sync_document();
  //       });

      cur_frm.set_query("kelurahan_2", function() {
             return {
                 filters: {
                    "parent": cur_frm.doc.kecamatan2
                 }
             }
        });
	},
    nama_kecamatan(frm){
        // cur_frm.set_value("kecamatan2","")
        cur_frm.set_value("kelurahan_2","")
        cur_frm.set_value("nama_kelurahan","")
         // cur_frm.refresh_fields("kecamatan2")
        cur_frm.refresh_fields("nama_kelurahan")
        cur_frm.refresh_fields("kelurahan_2")
    },
    kelurahan_2(frm){
        if(cur_frm.doc.kelurahan_2){
            frappe.call({
                  method: "wongkar_selling.custom_standard.custom_customer.get_kelurahan",
                  args: { 
                      kel: cur_frm.doc.kelurahan_2
                  },
                  callback: function(r) {
                        console.log(r.message)
                        cur_frm.set_value("nama_kelurahan",r.message)
                  }
            })
        }
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