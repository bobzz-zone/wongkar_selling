import frappe

@frappe.whitelist()
def get_adv_leasing(self,method):
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if self.advance_leasing:
			cek = frappe.get_doc("Advance Leasing",self.advance_leasing).journal_entry
			if cek:
				frappe.throw("Sudah ada No Je di "+self.advance_leasing+" !s")
			else:
				frappe.db.sql(""" UPDATE `tabAdvance Leasing` set journal_entry = '{}' where name= '{}' """.format(self.name,self.advance_leasing))
				frappe.db.commit()


@frappe.whitelist()
def get_adv_leasing_cancel(self,method):
	if frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com","honda2.digitalasiasolusindo.com","newbjm.digitalasiasolusindo.com","ifmi2.digitalasiasolusindo.com","bjm2.digitalasiasolusindo.com"]:
		if self.advance_leasing:
			frappe.db.sql(""" UPDATE `tabAdvance Leasing` set journal_entry = '{}' where name= '{}' """.format("",self.advance_leasing))
			frappe.db.commit()