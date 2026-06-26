import xml.etree.ElementTree as ET

def handle_GetTournamentInformation(params, id, xml, data_db):
    # Stubbed
    data = ET.SubElement(xml, "data")
    return xml