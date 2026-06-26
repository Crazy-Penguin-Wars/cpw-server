import xml.etree.ElementTree as ET

def handle_ConfirmBattleEnded(params, id, xml, data_db):
    # Stubbed
    data = ET.SubElement(xml, "data")
    ET.SubElement(data, "internal_code").text = "0"
    return xml