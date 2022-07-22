from __future__ import unicode_literals
import frappe
import json
import time
import requests
from six import iteritems
from frappe import _
from frappe.model.document import Document
from frappe.frappeclient import FrappeClient
from frappe.utils.background_jobs import get_jobs
from frappe.utils.data import get_url, get_link_to_form
from frappe.utils.password import get_decrypted_password
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


@frappe.whitelist()
def debug_create():
	log = frappe.get_doc("Doc Sync Log","D-LOG-07-22-00002")
	ste = frappe.get_doc(json.loads(log.data))
	ste.save()

@frappe.whitelist()
def coba():
	doc = frappe.new_doc('Event Producer')
	doc.producer_url = 'https://honda.digitalasiasolusindo.com'
	row = doc.append('producer_doctypes', {})
	row.ref_doctype = "Item"
	row.status = "Pending"
	row.use_same_name = 1
	doc.api_key = '907b672c4b813c7'
	doc.api_secret = '4c3da0ecc9971f2'
	doc.user = 'sync@das.com'
	doc.flags.ignore_permission = True
	doc.save()

@frappe.whitelist()
def debug_create_event_consumer():
	self = frappe.get_doc("Event Producer","https://honda.digitalasiasolusindo.com")
	"""register event consumer on the producer site"""
	if self.is_producer_online():
		producer_site = FrappeClient(
			url=self.producer_url,
			api_key=self.api_key,
			api_secret=self.get_password('api_secret')
		)

		response = producer_site.post_api(
			'frappe.event_streaming.doctype.event_consumer.event_consumer.register_consumer',
			params={'data': json.dumps(self.get_request_data())}
		)
		if response:
			response = json.loads(response)
			self.set_last_update(response['last_update'])
		else:
			frappe.throw(_('Failed to create an Event Consumer or an Event Consumer for the current site is already registered.'))