# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from datetime import date
from erpnext.stock.doctype.batch.batch import get_batch_qty
__version__ = '0.0.1'


def update_batches():
	item = frappe.db.get_list("Item", {"has_batch_no":1})
	today = date.today()
	l = []
	for i in item:
		target_batch = frappe.db.get_value("Batch", {"expiry_date":"2099-12-31", "item": i.name})
		batch = frappe.db.get_list("Batch", {"expiry_date": [">=", today], "item": i.name, "name":["!=", target_batch]})
		for j in batch:
#			warehouse = frappe.db.sql(""" select distinct warehouse as name from `tabStock Ledger Entry` where item_code=%s and batch_no=%s """, (i.name, j.name), as_dict=True)
			for k in [frappe._dict({"name":"Stores - MS"})]: #warehouse:
				batch_qty = get_batch_qty(j.name)
				available_qty = [q.qty for q in batch_qty if q.warehouse == k.name]
				available_qty = available_qty[0] if len(available_qty) else  0
				if available_qty:
					try:
						doc = frappe.new_doc("Stock Entry")
						doc.stock_entry_type = "Repack"
						doc.append("items", {
								"s_warehouse":k.name,
								"item_code": i.name,
								"qty": available_qty,
								"batch_no": j.name
								})
						doc.append("items", {
								"t_warehouse":k.name,
								"item_code": i.name,
								"qty": available_qty,
								"batch_no": target_batch
								})
						doc.save()
						doc.submit()
					except:
						l.append([i.name, j.name, k.name, available_qty])
	print(l)
