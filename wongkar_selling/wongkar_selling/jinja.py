from num2words import num2words
import frappe
import datetime

@frappe.whitelist()
def toTerbilang(num):
  indo = num2words(num, lang='id').title()
  return indo

@frappe.whitelist()
def hari(tanggal):
  days = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu", "Minguu"]
  test = datetime.datetime.today().weekday()
  output = days[test]

  return output
