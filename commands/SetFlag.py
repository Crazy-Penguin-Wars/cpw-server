import xml.etree.ElementTree as ET

def handle_SetFlag(params, id, xml, data_db):
    # No return data needed
    data = ET.SubElement(xml, "data")

    query_filter = {"id": id}

    update_operation = { "$set" : { f"flags.{params.get("key")}" : params.get("value")}}
    data_db.update_one(query_filter, update_operation)

    return xml