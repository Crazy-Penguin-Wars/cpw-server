import xml.etree.ElementTree as ET
from config import CONFIG_BASE

def handle_BuyItem(params, id, xml, data_db):
    data = ET.SubElement(xml, "data")

    # amount=1&call_id=call_2&in_battle=false&item_id=ClusterRocket&platform=FB&time=3267233&uid=57a1b524-3d78-4f59-8e82-a52c15d11208

    # <item item_id='{args['item_id']}' total_amount='90' bought_amount='5' reduced_cash='90' reduced_coins='90'></item>

    ET.SubElement(
        data,
        "item",
        attrib={
            "item_id": str(params["item_id"]),
            "total_amount": "90",
            "bought_amount": "5",
            "reduced_cash": "90",
            "reduced_coins": "90",
        }
    )

    return xml