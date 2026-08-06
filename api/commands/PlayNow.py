import os
import uuid
import xml.etree.ElementTree as ET

import connectionUtils

def handle_PlayNow(params, id, xml, data_db):
    data = ET.SubElement(xml, "data")

    battle_server_list = os.environ.get("BATTLE_SERVER_LIST").split(",")
    battle_server = battle_server_list[0].rsplit(':', 1) # Splits 1 from the right so that http:// isn't split
    print(battle_server)
    ET.SubElement(data, "host").text = battle_server[0]
    ET.SubElement(data, "port").text = battle_server[1]
    ET.SubElement(data, "dcg_id").text = id

    key = "NoKey" # Can't be empty for some reason

    ET.SubElement(data, "key").text = key
    return xml