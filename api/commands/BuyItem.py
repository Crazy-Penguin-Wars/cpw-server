import xml.etree.ElementTree as ET
from config import CONFIG_BASE
import logging
from api.database import update_coins, update_cash, add_items

def handle_BuyItem(params, id, xml, data_db):
    data = ET.SubElement(xml, "data")

    # amount=1&call_id=call_2&in_battle=false&item_id=ClusterRocket&platform=FB&time=3267233&uid=57a1b524-3d78-4f59-8e82-a52c15d11208

    # <item item_id='{args['item_id']}' total_amount='90' bought_amount='5' reduced_cash='90' reduced_coins='90'></item>

    item_id = params["item_id"]
    bought_amount = int(params["amount"])

    if item_id not in CONFIG_BASE["Item"]:
        logging.error(f"Item {item_id} not found")
        return xml

    # Read database
    document = data_db.find_one(
        {"id": id},
        {
            "level": 1,
            "cash": 1,
            "coins": 1,
            "items": {"$elemMatch": {"item_id": item_id}},
        },
    )
    user_level = document["level"]
    user_items = document.get("items", [])
    user_cash = int(document["cash"])
    user_coins = int(document["coins"])
    if user_items:
        user_amount = int(user_items[0]["amount"])
    else:
        user_amount = 0

    # Checks
    item = CONFIG_BASE["Item"][item_id]
    required_level = item["RequiredLevel"] if "RequiredLevel" in item else 0
    if user_level < required_level:
        logging.error(f"User level {user_level} is lower than required level {required_level} for item {item_id}")
        return xml
    coins_cost = item["PriceInfo"]["InGame"] if "InGame" in item["PriceInfo"] else 0
    cash_cost = item["PriceInfo"]["Premium"] if "Premium" in item["PriceInfo"] else 0
    if user_cash < cash_cost * bought_amount or user_coins < coins_cost * bought_amount:
        logging.error(f"User resources {user_cash} (cash) or {user_coins} (coins) are lower than required for item {item_id}")
        return xml

    # Update database
    pipeline = []
    pipeline.append(update_coins(-coins_cost * bought_amount))
    pipeline.append(update_cash(-cash_cost * bought_amount))
    pipeline.extend(add_items({item_id: bought_amount}))

    result = data_db.update_one(
        {"id": id},
        pipeline,
    )

    # Return XML
    ET.SubElement(
        data,
        "item",
        attrib={
            "item_id": item_id,
            "total_amount": str(user_amount + bought_amount),
            "bought_amount": str(bought_amount),
            "reduced_cash": str(cash_cost * bought_amount),
            "reduced_coins": str(coins_cost * bought_amount),
        }
    )

    return xml