import uuid
import xml.etree.ElementTree as ET

import connectionUtils

def handle_PlayNow(params, id, xml, data_db):
    data = ET.SubElement(xml, "data")

    ET.SubElement(data, "host").text = "127.0.0.1"
    ET.SubElement(data, "port").text = "5050"

    key = "NoKey" # Can't be empty for some reason

    ET.SubElement(data, "key").text = key
    return xml