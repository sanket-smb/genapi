#hello
from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.utils import flt, getdate, datetime
from erpnext.stock.utils import get_latest_stock_qty
import json
from frappe import _, throw, msgprint, utils
from frappe.utils import cint, flt, cstr, comma_or, getdate, add_days, getdate, rounded, date_diff, money_in_words
from datetime import datetime

@frappe.whitelist()
def hellosub(loggedInUser):
	return 'pong'

@frappe.whitelist()
def test():
	return "sucess"

@frappe.whitelist()
def get_item_details():
	#reqData = json.loads(frappe.request.data)
	master_items_data = frappe.db.sql("""select  item_code,company,item_name,item_name_ar,item_category,item_group,stock_uom from `tabItem`""",as_dict=1)
	#master_items_data = frappe.db.sql("""select  item_code,item_name,item_group,stock_uom from `tabItem`""",as_dict=1)
	items_json =[]
	for item in master_items_data:
		items_att = {
		"item_code":item.get("item_code"),
                "company":item.get("company"),
		"item_name":item.get("item_name"),
		"item_name_ar":item.get("item_name_ar"),
		"item_category":item.get("item_category"),
		"item_group":item.get("item_group"),
		"default_uom":item.get("stock_uom"),
		"barcode":get_barcode_list(item.get("item_code")),
		"uom_wise_cr_sp":get_uom_wise_conversion_rate(item.get("item_code")),
		"total_qty":get_total_stock_qty_in_all_wh(item.get("item_code"),"store")
		}
		items_json.append(items_att)
	return items_json

@frappe.whitelist()
def get_item_data(page_limit,page_number, item_group=None, item_code=None, last_update_on=None, company="MAQADHE STORE", has_stock=None):

	#Adding item_group
	filter = 'WHERE disabled = 0'
	if (item_group and frappe.db.exists('Item Group', item_group)) or item_code or last_update_on or company:
		filter += ' and '
		if item_group and frappe.db.exists('Item Group', item_group):
			filter += 'item_group=\''+item_group+'\''
		if item_code:
			if item_group and frappe.db.exists('Item Group', item_group) :
				filter += ' AND '
			#else:
			#	filter += '('
			filter += "item_code like '{0}%'".format(item_code)
		#if item_code or item_group:
		#	filter += ' )'
		if company:
			if ( item_group and frappe.db.exists('Item Group', item_group)) or item_code:
				filter += ' AND '
			filter += " company = '{0}'  ".format(company)
			#filter += 'company=\''+company+'\''
			#frappe.errprint("\n\n\n\n"+"company"+"\n")
		if last_update_on:
			print(last_update_on)
			if item_code or item_group or company:
				filter += ' and '
			last_update_on = last_update_on.split('.')[0]
	#		try:
			dt = datetime.strptime(last_update_on, "%Y-%m-%d %H:%M:%S")
			so = frappe.db.sql("""select distinct soi.item_code from `tabSales Order` as so join `tabSales Order Item` as soi on soi.parent = so.name where so.docstatus=1 and so.modified>='{0}' """.format(dt))
			sle = frappe.db.sql(""" select distinct item_code from `tabStock Ledger Entry` where modified>='{0}' """.format(dt))
			ip = frappe.db.sql(""" select distinct item_code from `tabItem Price` where modified >= '{0}' and selling=1 """.format(dt))
			itm = frappe.db.sql(""" select distinct item_code from `tabItem` where modified>='{0}' """.format(dt))
			bn = frappe.db.sql(""" select distinct item_code from `tabBin` where modified >= '{0}' """.format(dt))
			it = list(set(["'"+i[0]+"'" for i in so] + ["'"+i[0]+"'" for i in sle] + ["'"+i[0]+"'" for i in ip] + ["'"+i[0]+"'" for i in bn] + ["'"+i[0]+"'" for i in itm]))
			frappe.errprint("luo.................")
			if "GTRP078" in it:
				frappe.errprint("\n\n\n\n\n\n\n\n\n"+"item code"+"\n\n\n")
			filter += "item_code in ({0})".format(", ".join(it))
		#		except:
	#			pass

	stock_filter= ""
	if str(has_stock) != "None":
		if filter:
			print("INIF")
			stock_filter += " and "
		else:
			print("ELSE")
			stock_filter = " where "
		if str(has_stock)=='1':
			stock_filter += """ name not in (select b.item_code as item_code from `tabBin` as b join `tabItem` as i on i.name=b.item_code
				 where i.disabled=0 and b.actual_qty-b.reserved_qty<=0 and b.warehouse='Stores - MS')"""
		elif str(has_stock)=='0':
			stock_filter += """ name in (select b.item_code as item_code from `tabBin` as b join `tabItem` as i on i.name=b.item_code
				where i.disabled=0 and b.actual_qty-b.reserved_qty<=0 and b.warehouse='Stores - MS')"""
	page_limit=int(page_limit)
	page_number=int(page_number)
	#table_row_count_dic = frappe.db.sql("""select count(*) as count from `tabPacked Box Custom`""",as_dict=1)
	#return """select count(*) as count from `tabItem` {0} {1}""".format(filter, stock_filter)
        #table_row_count_query = """select count(*) as count from `tabItem` {0} {1}""".format(filter, stock_filter)
        #frappe.errprint(table_row_count_query)
        #print(filter)
	table_row_count_dic = frappe.db.sql("""select count(*) as count from `tabItem` {0} {1}""".format(filter, stock_filter),as_dict=1)
	table_row_count = table_row_count_dic[0]["count"]
	#new
	table_row_count_float= float(table_row_count)
	page_limit_float = float(page_limit)
	total_page_number_float = table_row_count_float / page_limit_float


	table_row_count_int= int(table_row_count)
	page_limit_int = int(page_limit)

	total_page_number_int =  int(table_row_count_int / page_limit_int)

	if total_page_number_float > total_page_number_int:
		total_page_number_int = total_page_number_int + 1

	total_page_number =  total_page_number_int
	off_set = (page_number-1 ) * page_limit

	#new
	page_limit_conditions= get_page_limit_conditions("creation","asc",page_limit,off_set)

	#actual_data
	query = """select item_code,item_name,company,item_name_ar,item_category,item_group,stock_uom from `tabItem` %s %s %s"""%(filter, stock_filter, page_limit_conditions)
	print("\n\n\n\n\n\n\n\nquery")
	print(query)
	master_items_data = frappe.db.sql(query,as_dict=1)
	items_json =[]
	for item in master_items_data:
		if item.get("item_code") == "GTRP078":
			print("\n\n\n\n\nn\n\n"+item.get("item_code"))
		sle = frappe.db.sql(""" select max(modified) from `tabStock Ledger Entry` where item_code='{0}' """.format(item.get("item_code")))
		sle = sle[0][0] if sle and sle[0][0] else None
		so = frappe.db.sql(""" select max(so.modified) from `tabSales Order` as so join `tabSales Order Item` as soi on soi.parent=so.name where soi.item_code='{0}' """.format(item.get("item_code")))
		so = so[0][0] if so and so[0][0] else None
		ip = frappe.db.sql(""" select max(modified) from`tabItem Price` where item_code='{0}' and selling=1 """.format(item.get("item_code")))
		ip = ip[0][0] if ip and ip[0][0] else None
		itm = frappe.db.sql(""" select modified from `tabItem` where item_code='{0}' """.format(item.get("item_code")))
		itm = itm[0][0] if itm and itm[0][0] else None
		comp = [k for k in [sle, so, ip, itm] if k]
		last_update_on = str(max(comp)) or datetime.now()
		#print(sle, so, ip, itm)
		#print(last_update_on)
		items_att = {
                "company":item.get("company"),
		"item_code":item.get("item_code"),
		"item_name":item.get("item_name"),
		"item_name_ar":item.get("item_name_ar"),
		"item_category":item.get("item_category"),
		"item_group":item.get("item_group"),
		"default_uom":item.get("stock_uom"),
		"barcode":get_barcode_list(item.get("item_code")),
		"uom_wise_cr_sp":get_uom_wise_conversion_rate(item.get("item_code")),
		"total_qty":get_total_stock_qty_in_all_wh(item.get("item_code"), item.get("company")),
		"last_update_on": str(last_update_on).split(".")[0]
		}
		if frappe.db.exists('Item Warehouse Bin', {'item_code':items_att['item_code']}):
			doc = frappe.get_doc('Item Warehouse Bin', frappe.db.get_value('Item Warehouse Bin', {'item_code':items_att['item_code']}))
			items_att['warehouse_bin'] = [{'warehouse':i.warehouse, 'warehouse_bin':i.warehouse_bin} for i in doc.bin_list]
		items_json.append(items_att)

	item_details = {"cur_page":page_number,"total_count":table_row_count,"total_page":total_page_number,"item_data":items_json}
	return item_details

def get_total_stock_qty_in_all_wh(item_code, company):
        if "MAQADHE STORE" in company or "maqadhe" in company or "store" in company or "STORE" in company:
	        total_stock_qty_in_all_wh = frappe.db.sql("""select actual_qty, reserved_qty  from `tabBin` where item_code=%s  and warehouse='Stores - MS' """, item_code, as_dict = 1)
        else:
                total_stock_qty_in_all_wh = frappe.db.sql("""select actual_qty, reserved_qty  from `tabBin` where item_code=%s  and warehouse='Stores - Sen' """, item_code, as_dict = 1)
        
        qty = 0
        if total_stock_qty_in_all_wh: 
                qty = total_stock_qty_in_all_wh[0]["actual_qty"]-total_stock_qty_in_all_wh[0]["reserved_qty"]
                if qty < 0:
                    qty = 0
        return qty
	# return total_stock_qty_in_all_wh[0]["actual_qty"] if  total_stock_qty_in_all_wh else 0

def get_uom_wise_conversion_rate(item_code):
	uom_wise_conversion_rate = frappe.get_list("UOM Conversion Detail", filters={"parent":item_code}, fields=["uom","conversion_factor"] )
	uom_detailed_json =[]
	for uom_json in uom_wise_conversion_rate:
		selling_price = frappe.db.get_value("Item Price", {"item_code":item_code,"uom":uom_json["uom"],"selling":1},"price_list_rate")
		if selling_price:
			uom_json["standard_selling_price"] = selling_price
		else:
			uom_json["standard_selling_price"] = ""
		uom_detailed_json.append(uom_json)
	return uom_detailed_json

def get_barcode_list(item_code):
	barcode_list = frappe.get_list("Item Barcode", filters={"parent":item_code}, fields=["barcode", "unit","barcode_type"] )
	return barcode_list

#thi fun is already in sur utils but this file is not reading sur utils so copied here
def get_page_limit_conditions(order_by=None,order_by_type=None,page_limit=None,off_set=None):
	condition = ""
	if order_by:
		condition += " order by "+order_by
	if order_by and order_by_type:
		condition += " "+order_by_type
	if page_limit:
		condition += " limit "+str(page_limit)
	condition += " offset "+ str(off_set)
	return condition
