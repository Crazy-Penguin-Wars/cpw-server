import xml.etree.ElementTree as ET

def handle_GetAccountInformation(params, id, xml, data_db):
    # Get account from database
    query_filter = {"id": id}
    document = data_db.find_one(query_filter)

    data = ET.SubElement(xml, "data")

    flags = ET.SubElement(data, "flags")
    for flag in document["flags"]:
        ET.SubElement(flags, "flag", {"key": flag, "value": document["flags"][flag]})

    ET.SubElement(data, "cash").text = str(document["cash"])
    ET.SubElement(data, "coins").text = str(document["coins"])
    ET.SubElement(data, "dcg_id").text = id
    ET.SubElement(data, "incoming_gift_requests")
    ET.SubElement(data, "incoming_neighbor_requests")
    ET.SubElement(data, "level").text = str(document["level"])
    ET.SubElement(data, "score").text = str(document["score"])
    ET.SubElement(data, "name").text = document["name"]
    ET.SubElement(data, "pic_url").text = document["pic_url"]
    ET.SubElement(data, "slot_machine_used_spins").text = str(document["slot_machine_used_spins"])

    items = ET.SubElement(data, "items")
    for item in document["items"]:
        ET.SubElement(items, "item", item)

    unlocked_items = ET.SubElement(data, "unlocked_items")
    for item in document["unlocked_items"]:
        ET.SubElement(unlocked_items, "unlocked_item", item)

    worn_items = ET.SubElement(data, "worn_items")
    for item in document["worn_items"]:
        ET.SubElement(worn_items, "worn_item", item)

    neighbors = ET.SubElement(data, "neighbors")
    for neighbor in document["neighbors"]:
        ET.SubElement(neighbors, "neighbor", neighbor)

    user_data = ET.SubElement(data, "user_data")
    for user_data in document["user_data"]:
        ET.SubElement(user_data, "user_data", user_data)

    known_recipes = ET.SubElement(data, "known_recipes")
    for recipe in document["known_recipes"]:
        ET.SubElement(known_recipes, "known_recipe", recipe)

    ET.SubElement(data, "ongoing_research", document["ongoing_research"])

    ET.SubElement(xml, "maintenance").text = "false"
    ET.SubElement(xml, "responseCode").text = "0"

    return xml