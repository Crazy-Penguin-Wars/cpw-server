import xml.etree.ElementTree as ET

from flask import Response, current_app, request, session, Blueprint

import connectionUtils
from .commands import AVAILABLE_COMMANDS
from .database import *

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/<command>", methods=["GET"])
def handle_command(command):
    data_db = current_app.data_db
    params = request.args.to_dict()

    id = params.get("uid")

    # Check signature
    given_signature = params.get("sig")
    if "token" not in session:
        session["token"] = get_token_from_user_id(id)
    calculated_signature = connectionUtils.generate_signature(params, session["token"])
    if given_signature != calculated_signature:
        print(session["token"])
        return "Wrong token"
    
    xml = ET.Element("root", {
        "call_id": params.get("call_id", ""),
        "service": command
    })

    if command in AVAILABLE_COMMANDS:
        handler = AVAILABLE_COMMANDS[command]
        xml = handler(params, id, xml, data_db)
    else:
        print(f"Command not handled: {command}")
        return f"Command not handled: {command}"
    
    ET.SubElement(xml, "maintenance").text = "false"
    ET.SubElement(xml, "responseCode").text = "0"

    connectionUtils.refresh_online_status(id)

    print(xml)

    return Response(ET.tostring(xml, encoding="utf-8", xml_declaration=True), mimetype="application/xml")


@api_bp.route("/status", methods=["GET"])
def get_status():
    return {"estimated_online_player_count": connectionUtils.get_online_players()}


@api_bp.route("/get-player-data", methods=["GET"])
def get_player_data():
    params = request.args.to_dict()
    return connectionUtils.find_player_data(current_app.data_db, params.get("id"))


@api_bp.route("/update-rewards", methods=["POST", "GET"])
def update_player_rewards():
    return update_rewards()
