import xml.etree.ElementTree as ET
import random

def handle_PlaySlotMachine(params, id, xml, data_db):
    # Get account from database
    query_filter = {"id": id}
    document = data_db.find_one(query_filter)

    data = ET.SubElement(xml, "data")

    ET.SubElement(data, "number_of_neighbors").text = str(0)

    servedReel1 = round(random.random() * 23)
    servedReel2 = round(random.random() * 23)
    servedReel3 = round(random.random() * 23)

    central_row_positions = ET.SubElement(data, "central_row_positions")
    ET.SubElement(central_row_positions, "reel_0").text = str(servedReel1)
    ET.SubElement(central_row_positions, "reel_1").text = str(servedReel2)
    ET.SubElement(central_row_positions, "reel_2").text = str(servedReel3)

    return xml