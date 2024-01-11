import frappe
from datetime import datetime
from genapi.maq_api import get_total_stock_qty_in_all_wh
@frappe.whitelist()
def get_purchase_receipt(from_date, to_date, is_return=None):
	condition = ''
	if not is_return == None:
		if str(is_return) == '1':
			condition += 'and is_return=1'
		elif str(is_return) == '0':
			condition += 'and is_return=0'
	pe_list = frappe.db.sql(""" select name from `tabPurchase Receipt` where docstatus=1 and posting_date>='{0}' and posting_date<='{1}' {2}""".format(from_date, to_date, condition), as_dict=True)
	pe_data = []
	for i in pe_list:
		doct = frappe.get_doc("Purchase Receipt", i.name)
		doc = frappe._dict(doct.__dict__)
		doc.pop("_meta")
		item = []
		for j in range(len(doct.items)):
			it = frappe._dict(doct.items[j].__dict__)
			it.pop("_meta")
			it.pop("parent_doc")
			item.append(it)
		doc.items = item
		supplied_item = []
		for j in range(len(doct.supplied_items)):
			it = frappe._dict(doct.supplied_items[j].__dict__)
			it.pop("_meta")
			it.pop("parent_doc")
			supplied_item.append(it)
		doc.supplied_items = supplied_item
		tx = []
		for j in range(len(doct.taxes)):
			it = frappe._dict(doct.taxes[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			tx.append(it)
		doc.taxes = tx
		rule = []
		for j in range(len(doct.pricing_rules)):
			it = frappe._dict(doct.taxes[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			rule.append(it)
		doc.pricing_rules = rule
		pe_data.append(doc)
	return pe_data

@frappe.whitelist()
def get_delivery_note(from_date, to_date, is_return=None):
	condition = ''
	if not is_return == None:
		if str(is_return) == '1':
			condition += 'and is_return=1'
		elif str(is_return) == '0':
			condition += 'and is_return=0'
	dn_list = frappe.db.sql(""" select name from `tabDelivery Note` where docstatus=1 and  posting_date>='{0}' and posting_date<='{1}' {2} """.format(from_date, to_date, condition), as_dict=True)
	dn_data = []
	for i in dn_list:
		doct = frappe.get_doc("Delivery Note", i.name)
		doc = frappe._dict(doct.__dict__)
		doc.return_against_reference_no = frappe.db.get_value("Delivery Note", doc.return_against, "wms_reference_no")
		doc.return_against_sales_order = frappe.db.get_value("Delivery Note", doc.return_against, "reference_num")
		doc.pop("_meta")
		item = []
		for j in range(len(doct.items)):
			it = frappe._dict(doct.items[j].__dict__)
			location = frappe.db.sql(""" select iwb.warehouse_bin from `tabItem Warehouse Bin` as iw join `tabItem Warehouse Bin Item` as iwb on iwb.parent=iw.name where 
							iw.item_code='{0}'""".format(it.item_code))
			it.location = location[0][0] if len(location) and location[0][0] else ''
			it.pop("_meta")
			it.pop("parent_doc")
			item.append(it)
		doc.items = item
		rule = []
		for j in range(len(doct.pricing_rules)):
			it = frappe._dict(doct.taxes[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			rule.append(it)
		doc.pricing_rules = rule
		pack = []
		for j in range(len(doct.packed_items)):
			it = frappe._dict(doct.packed_items[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			pack.append(it)
		doc.packed_items = pack
		tx = []
		for j in range(len(doct.taxes)):
			it = frappe._dict(doct.taxes[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			tx.append(it)
		doc.taxes = tx
		st = []
		for j in range(len(doct.sales_team)):
			it = frappe._dict(doct.sales_team[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			st.append(it)
		doc.sales_team = st
		doc.pop("sales_order_payment")
		dn_data.append(doc)
	return dn_data

@frappe.whitelist()
def get_sales_order(from_date=None, to_date=None, last_modified = None, order=None):
	return None
	flt = ""
	if from_date and to_date:
		flt += "and transaction_date>='{0}' and transaction_date<='{1}'".format(from_date, to_date)
	if last_modified:
		flt += " and modified >= '{0}'".format(last_modified)
	if order:
		flt += " and name='{0}' or reference_num='{0}'".format(order)
	#add_log("{4} from_date-{0}, to_date-{1}, last_modified-{2}, order-{3}".format(from_date, to_date,last_modified, order, datetime.now()))
	so_list = frappe.db.sql(""" select name from `tabSales Order` where docstatus=1 {0} order by creation desc""".format(flt), as_dict=True)
	so_data = []
	for i in so_list:
		doct = frappe.get_doc("Sales Order", i.name)
		doc = frappe._dict(doct.__dict__)
		doc.pop('_meta')
		doc.is_bundle = 0
		item = []
		for j in range(len(doct.items)):
			it = frappe._dict(doct.items[j].__dict__)
			it.barcode = frappe.db.get_value("Item Barcode", {"parent": it.item_code, "unit":it.uom}, "barcode")
			if not it.barcode:
				it.barcode = frappe.db.get_value("Item Barcode", {"parent": it.item_code, "unit":it.stock_uom}, "barcode")
			it.is_bundle = 0
			it.location = get_location(it.item_code)
			it.pop("_meta")
			it.pop("parent_doc")
			qty = get_total_stock_qty_in_all_wh(it.item_code)
			it.available_qty = qty
			item.append(it)
			if frappe.db.get_value("Product Bundle", it.item_code):
				doc.is_bundle = 1
				it.is_bundle = 1
				for pb in doc.packed_items:
					if pb.parent_item == it.item_code:
						qty = get_total_stock_qty_in_all_wh(it.item_code)
						item.append({
							"item_code": pb.item_code,
							"barcode": frappe.db.get_value("Item Barcode", {"parent": pb.item_code, "unit":pb.uom}, "barcode"),
							"qty": pb.qty,
							"available_qty": qty,
							"warehouse": pb.warehouse,
							"item_name":pb.item_name,
							"uom":pb.uom,
							"conversion_factor":frappe.db.get_value("UOM Conversion Detail", {"parent": pb.item_code, "uom": pb.uom}, "conversion_factor"),
							"parent": pb.parent_item,
							"location": get_location(pb.item_code),
							"rate": 0,
							"amount": 0,
							"reference_no":it.name,
							"is_bundle": 0
						})
		doc.items = item
		ps = []
		for j in range(len(doct.payment_schedule)):
			it = frappe._dict(doct.payment_schedule[j].__dict__)
			it.pop("_meta")
			it.pop("parent_doc")
			ps.append(it)
		doc.payment_schedule = ps

		tx = []
		for j in range(len(doct.taxes)):
			it = frappe._dict(doct.taxes[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			tx.append(it)
		doc.taxes = tx
		st = []
		for j in range(len(doct.sales_team)):
			it = frappe._dict(doct.sales_team[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			st.append(it)
		doc.sales_team = st
		sop = []
		for j in range(len(doct.sales_order_payment)):
			sp = frappe._dict(doct.sales_order_payment[j].__dict__)
			sp.pop("parent_doc")
			sp.pop("_meta")
			sop.append(sp)
		doc.sales_order_payment = sop
		#doc.pop("sales_order_payment")
		so_data.append(doc)
	frappe.local.response["message"] = [i for i in so_data]
	#return so_data

def get_location(item):
	bin_name = frappe.db.get_value("Item Warehouse Bin", {"item_code":item},"name")
	if not bin_name:
		return ''
	bin_loc = frappe.db.get_value("Item Warehouse Bin Item", {"parent":bin_name},"warehouse_bin")
	return bin_loc or ''

@frappe.whitelist()
def get_purchase_order(from_date, to_date,last_modified=None, name=None):
	flt = ""
	if last_modified:
		flt = "and modified >= '{0}'".format(last_modified)
	if name:
		flt += "and name='{0}'".format(name)
	po_list = frappe.db.sql(""" select name from `tabPurchase Order` where docstatus=1 and transaction_date>='{0}' and transaction_date<='{1}' {2}""".format(from_date, to_date , flt), as_dict=True)
	po_data = []
	for i in po_list:
		doct = frappe.get_doc("Purchase Order", i.name)
		doc = frappe._dict(doct.__dict__)
		doc.pop("_meta")
		item = []
		for j in range(len(doct.items)):
			it = frappe._dict(doct.items[j].__dict__)
			bc = frappe.db.get_value("Item Barcode", {"parent": it.item_code, "unit":it.uom}, "barcode")
			if not bc:
				bc = frappe.db.get_value("Item Barcode", {"parent": it.item_code, "unit":it.stock_uom}, "barcode")
			it.barcode = bc
			it.item_barcode = frappe.db.get_value("Item Barcode", {"parent": it.item_code, "unit":it.stock_uom}, "barcode")
			it.pop("_meta")
			it.pop("parent_doc")
			item.append(it)
		doc.items = item

		ps = []
		for j in range(len(doct.payment_schedule)):
			it = frappe._dict(doct.payment_schedule[j].__dict__)
			it.pop("_meta")
			it.pop("parent_doc")
			ps.append(it)
		doc.payment_schedule = ps

		pr= []
		for j in range(len(doct.pricing_rules)):
			it = frappe._dict(doct.pricing_rules[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			pr.append(it)
		doc.pricing_rules = pr

		si = []
		for j in range(len(doct.supplied_items)):
			it = frappe._dict(doct.supplied_items[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			si.append(it)
		doc.supplied_items = si

		tx = []
		for j in range(len(doct.taxes)):
			it = frappe._dict(doct.taxes[j].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			tx.append(it)
		doc.taxes = tx

		po_data.append(doc)
	return po_data



@frappe.whitelist(allow_guest = True)
def get_stock_transfer(from_date , to_date):
	type = "Material Transfer"
	se_list = frappe.db.sql(""" Select name from `tabStock Entry` where docstatus =1 and stock_entry_type = '{0}' and posting_date >= '{1}' and posting_date <= '{2}'""".format(type,from_date,to_date),as_dict=True)
	se_data = []
	for se in se_list:
		doct = frappe.get_doc("Stock Entry",se.name)
		doc = frappe._dict(doct.__dict__)
		doc.pop("_meta")
		item = []
		for idx in range(len(doct.items)):
			it = frappe._dict(doct.items[idx].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			item.append(it)
		doc.items = item
		se_data.append(doc)
	return se_data

@frappe.whitelist()
def get_stock_reconciliations(from_date , to_date):
	sr_list = frappe.db.sql(""" Select name from `tabStock Reconciliation` where docstatus =1 and purpose = 'Stock Reconciliation' and posting_date >= '{0}' and posting_date <= '{1}'""".format(from_date,to_date),as_dict=True)
	sr_data = []
	for sr in sr_list:
		doct = frappe.get_doc("Stock Reconciliation",sr.name)
		doc = frappe._dict(doct.__dict__)
		doc.pop("_meta")
		item = []
		for idx in range(len(doct.items)):
			it = frappe._dict(doct.items[idx].__dict__)
			it.pop("parent_doc")
			it.pop("_meta")
			item.append(it)
		doc.items = item
		sr_data.append(doc)
	return sr_data

def add_log(message):
	file = open('/home/frappe/frappe-bench/apps/genapi/genapi/call.log','a')
	file.write(message+'\n')
	file.close()
