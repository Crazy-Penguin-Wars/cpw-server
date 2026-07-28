import xml.etree.ElementTree as ET

def handle_CheckServerStatus(params, id, xml, data_db):
    # Stubbed
    data = ET.SubElement(xml, "data")

    ET.SubElement(data, "productionUpdate").text = "false"

    return xml