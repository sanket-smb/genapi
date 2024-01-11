import frappe


@frappe.whitelist()
def get_product_bundle():
	raw_data = frappe.db.get_list("Product Bundle",["name", "new_item_code as item_code", "description"])
	for i in range(len(raw_data)):
		available_qty = []
		raw_data[i]["is_out_of_stock"] = 0
		raw_data[i]["item_name"] = frappe.db.get_value("Item", raw_data[i]["item_code"], "item_name")
		raw_data[i]["available_qty"] = 0
		raw_data[i]["items"] = frappe.db.get_list("Product Bundle Item", {"parent": raw_data[i]["name"]}, ["item_code", "qty", "description", "minimum_stock"])
		for j in range(len(raw_data[i]["items"])):
			qty = frappe.db.get_value("Bin", {"warehouse": "Stores - MS", "item_code": raw_data[i]["items"][j]["item_code"]}, "actual_qty")
			if not qty:
				qty = 0
			if raw_data[i]["items"][j]["minimum_stock"] > qty:
				raw_data[i]["is_out_of_stock"] = 1
			available_qty.append(qty // raw_data[i]["items"][j]["qty"])
			del raw_data[i]["items"][j]["minimum_stock"]
		if not raw_data[i]["is_out_of_stock"]:
			raw_data[i]["available_qty"] = min(available_qty)
			if raw_data[i]["available_qty"] == 0:
				raw_data[i]["is_out_of_stock"] = 1
	return raw_data
