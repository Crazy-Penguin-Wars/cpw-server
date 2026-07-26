import xml.etree.ElementTree as ET

def handle_GetInboxStatus(params, id, xml, data_db):
    # Stubbed
    data = ET.SubElement(xml, "data")
    return xml