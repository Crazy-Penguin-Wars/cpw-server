import uuid
import xml.etree.ElementTree as ET

import connectionUtils

def handle_PlayNow(params, id, xml, data_db):
    data = ET.SubElement(xml, "data")

    ET.SubElement(data, "host").text = "127.0.0.1"
    ET.SubElement(data, "port").text = "5050"

    key = str(uuid.uuid4())

    ET.SubElement(data, "key").text = key

    # Get account from database
    query_filter = {"id": id}
    document = data_db.find_one(query_filter, {"level": 1, "name": 1})

    player = {
        "id": id,
        "name": document["name"],
        "level": int(document["level"])
    }
    connectionUtils.add_key(key, player)
    return xml