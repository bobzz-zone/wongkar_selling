# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.naming import set_name_by_naming_series
from frappe import _, msgprint
import frappe.defaults
from frappe.utils import flt, cint, cstr, today, get_formatted_email
from frappe.desk.reportview import build_match_conditions, get_filters_cond
from erpnext.utilities.transaction_base import TransactionBase
from erpnext.accounts.party import validate_party_accounts, get_dashboard_info, get_timeline_data # keep this
from frappe.contacts.address_and_contact import load_address_and_contact, delete_contact_and_address
from frappe.model.rename_doc import update_linked_doctypes
from frappe.model.mapper import get_mapped_doc
from frappe.utils.user import get_users_with_role


@frappe.whitelist()
def search_widget(doctype, txt, query=None, searchfield=None, start=0,
	page_length=20, filters=None, filter_fields=None, as_dict=False, reference_doctype=None, ignore_user_permissions=False):

	start = cint(start)

	if isinstance(filters, string_types):
		filters = json.loads(filters)

	if searchfield:
		sanitize_searchfield(searchfield)

	if not searchfield:
		searchfield = "name"

	standard_queries = frappe.get_hooks().standard_queries or {}

	if query and query.split()[0].lower()!="select":
		# by method
		try:
			is_whitelisted(frappe.get_attr(query))
			frappe.response["values"] = frappe.call(query, doctype, txt,
				searchfield, start, page_length, filters, as_dict=as_dict)
		except frappe.exceptions.PermissionError as e:
			if frappe.local.conf.developer_mode:
				raise e
			else:
				frappe.respond_as_web_page(title='Invalid Method', html='Method not found',
				indicator_color='red', http_status_code=404)
			return
		except Exception as e:
			raise e
	elif not query and doctype in standard_queries:
		# from standard queries
		# if doctype == 'Customer' and frappe.local.site in ['honda.digitalasiasolusindo.com','hondapjk.digitalasiasolusindo.com']:
		if doctype == 'Customer' and frappe.local.site in ["ifmi.digitalasiasolusindo.com","bjm.digitalasiasolusindo.com"]:
			search_widget(doctype, txt, 'wongkar_selling.custom_standard.custom_query.custom_get_customer_list',
				searchfield, start, page_length, filters)
		else:
			search_widget(doctype, txt, standard_queries[doctype][0],
				searchfield, start, page_length, filters)
	else:
		meta = frappe.get_meta(doctype)

		if query:
			frappe.throw(_("This query style is discontinued"))
			# custom query
			# frappe.response["values"] = frappe.db.sql(scrub_custom_query(query, searchfield, txt))
		else:
			if isinstance(filters, dict):
				filters_items = filters.items()
				filters = []
				for f in filters_items:
					if isinstance(f[1], (list, tuple)):
						filters.append([doctype, f[0], f[1][0], f[1][1]])
					else:
						filters.append([doctype, f[0], "=", f[1]])

			if filters==None:
				filters = []
			or_filters = []


			# build from doctype
			if txt:
				search_fields = ["name"]
				if meta.title_field:
					search_fields.append(meta.title_field)

				if meta.search_fields:
					search_fields.extend(meta.get_search_fields())

				for f in search_fields:
					fmeta = meta.get_field(f.strip())
					if (doctype not in UNTRANSLATED_DOCTYPES) and (f == "name" or (fmeta and fmeta.fieldtype in ["Data", "Text", "Small Text", "Long Text",
						"Link", "Select", "Read Only", "Text Editor"])):
							or_filters.append([doctype, f.strip(), "like", "%{0}%".format(txt)])

			if meta.get("fields", {"fieldname":"enabled", "fieldtype":"Check"}):
				filters.append([doctype, "enabled", "=", 1])
			if meta.get("fields", {"fieldname":"disabled", "fieldtype":"Check"}):
				filters.append([doctype, "disabled", "!=", 1])

			# format a list of fields combining search fields and filter fields
			fields = get_std_fields_list(meta, searchfield or "name")
			if filter_fields:
				fields = list(set(fields + json.loads(filter_fields)))
			formatted_fields = ['`tab%s`.`%s`' % (meta.name, f.strip()) for f in fields]

			# find relevance as location of search term from the beginning of string `name`. used for sorting results.
			formatted_fields.append("""locate({_txt}, `tab{doctype}`.`name`) as `_relevance`""".format(
				_txt=frappe.db.escape((txt or "").replace("%", "").replace("@", "")), doctype=doctype))


			# In order_by, `idx` gets second priority, because it stores link count
			from frappe.model.db_query import get_order_by
			order_by_based_on_meta = get_order_by(doctype, meta)
			# 2 is the index of _relevance column
			order_by = "_relevance, {0}, `tab{1}`.idx desc".format(order_by_based_on_meta, doctype)

			ptype = 'select' if frappe.only_has_select_perm(doctype) else 'read'
			ignore_permissions = True if doctype == "DocType" else (cint(ignore_user_permissions) and has_permission(doctype, ptype=ptype))

			if doctype in UNTRANSLATED_DOCTYPES:
				page_length = None

			values = frappe.get_list(doctype,
				filters=filters,
				fields=formatted_fields,
				or_filters=or_filters,
				limit_start=start,
				limit_page_length=page_length,
				order_by=order_by,
				ignore_permissions=ignore_permissions,
				reference_doctype=reference_doctype,
				as_list=not as_dict,
				strict=False)

			if doctype in UNTRANSLATED_DOCTYPES:
				# Filtering the values array so that query is included in very element
				values = (
					v for v in values
					if re.search(
						f"{re.escape(txt)}.*", _(v.name if as_dict else v[0]), re.IGNORECASE
					)
				)

			# Sorting the values array so that relevant results always come first
			# This will first bring elements on top in which query is a prefix of element
			# Then it will bring the rest of the elements and sort them in lexicographical order
			values = sorted(values, key=lambda x: relevance_sorter(x, txt, as_dict))

			# remove _relevance from results
			if as_dict:
				for r in values:
					r.pop("_relevance")
				frappe.response["values"] = values
			else:
				frappe.response["values"] = [r[:-1] for r in values]

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def custom_get_customer_list(doctype, txt, searchfield, start, page_len, filters=None):
	# frappe.msgprint("kjsdjkahdjashd")
	from erpnext.controllers.queries import get_fields
	fields = ["name", "customer_name", "customer_group", "territory"]

	if frappe.db.get_default("cust_master_name") == "Customer Name":
		fields = ["name", "customer_group", "territory"]

	fields = get_fields("Customer", fields)

	match_conditions = build_match_conditions("Customer")
	match_conditions = "and {}".format(match_conditions) if match_conditions else ""

	if filters:
		filter_conditions = get_filters_cond(doctype, filters, [])
		match_conditions += "{}".format(filter_conditions)

	return frappe.db.sql("""
		select %s
		from `tabCustomer`
		where docstatus < 2
			and (%s like %s or customer_name like %s)
			{match_conditions}
		order by
			if(locate(%s, name), locate(%s, name), 99999),
			if(locate(%s, customer_name), locate(%s, customer_name), 99999),
			case when name like %s then 0 else 1 end,
			case when customer_name like %s then 0 else 1 end,
			name, customer_name limit %s, %s
		""".format(match_conditions=match_conditions) % (", ".join(fields), searchfield, "%s", "%s","%s", "%s","%s", "%s", "%s", "%s", "%s", "%s"),
		("%%%s%%" % txt, "%%%s%%" % txt,txt,txt,txt,txt, "%%%s%%" % txt, "%%%s%%" % txt, start, page_len))