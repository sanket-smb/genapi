from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.utils import flt, getdate, datetime
from erpnext.stock.utils import get_latest_stock_qty
import json
from frappe import _, throw, msgprint, utils
from frappe.utils import cint, flt, cstr, comma_or, getdate, add_days, getdate, rounded, date_diff, money_in_words

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

@frappe.whitelist()
def test():
    return "sucess"
