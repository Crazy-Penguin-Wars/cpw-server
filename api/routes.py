import xml.etree.ElementTree as ET

from flask import Response, current_app, request, session, Blueprint
import hmac
import logging

import connectionUtils
from .commands import AVAILABLE_COMMANDS
from .database import *

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/<command>", methods=["GET"])
def handle_command(command):
    data_db = current_app.data_db
    params = request.args.to_dict()

    id = params.get("uid")

    if session.get("last_call_id", "") == params.get("call_id"):
        logging.warning(f"Duplicate request detected for user {id}: {params['call_id']}")
        return "Duplicate request", 400
    
    session["last_call_id"] = params["call_id"]

    # Check signature
    given_signature = params.get("sig")
    if "token" not in session:
        session["token"] = get_token_from_user_id(id)
    calculated_signature = connectionUtils.generate_signature(params, session["token"])
    if given_signature != calculated_signature:
        logging.warning(f"Signature mismatch for user {id}. Given: {given_signature}, Calculated: {calculated_signature}")
        return "Wrong token", 403
    
    xml = ET.Element("root", {
        "call_id": params["call_id"],
        "service": command
    })

    if command in AVAILABLE_COMMANDS:
        handler = AVAILABLE_COMMANDS[command]
        xml = handler(params, id, xml, data_db)
    else:
        logging.warning(f"Command not handled: {command} for user {id}")
        return f"Command not handled: {command}"
    
    ET.SubElement(xml, "maintenance").text = "false"
    ET.SubElement(xml, "responseCode").text = "0"

    connectionUtils.refresh_online_status(id)

    logging.debug(f"Response for user {id}: {ET.tostring(xml, encoding='utf-8', xml_declaration=True)}")

    return Response(ET.tostring(xml, encoding="utf-8", xml_declaration=True), mimetype="application/xml")


@api_bp.route("/status", methods=["GET"])
def get_status():
    return {"estimated_online_player_count": connectionUtils.get_online_players()}


@api_bp.route("/get-player-data", methods=["GET"])
def get_player_data():
    params = request.args.to_dict()
    return connectionUtils.find_player_data(current_app.data_db, params.get("id"))


@api_bp.route("/update-rewards", methods=["POST", "GET"])
def update_rewards():
    data_db = current_app.data_db
    params = request.args.to_dict()

    # Check if this is really sent by the battle server
    # using hmac to prevent timing attacks
    if not params.get("connectionKey") or not hmac.compare_digest(params.get("connectionKey"), os.environ["CONNECTION_KEY"]):
        logging.warning("AMOGUS DETECTED")
        return "bruh"
    
    rewards_base64 = params.get("rewards")
    rewards_json = base64.urlsafe_b64decode(rewards_base64).decode("utf-8")
    rewards = json.loads(rewards_json)
    logging.debug(f"Updating rewards for user {id}: {rewards}")

    for player, player_rewards in rewards.items():
        query_filter = {"id": player}
        pipeline = []

        for item, value in player_rewards.items():
            match item:
                case "coins":
                    pipeline.append(update_coins(value))
                case "cash":
                    pipeline.append(update_cash(value))
                case "experience":
                    pipeline.append(update_experience(value))
                case "earnedItems":
                    pipeline.append(add_items(value))
                case "usedItems":
                    pipeline.append(add_items(-value))
                case _:
                    logging.warning(f"Unknown reward type: {item}")

        if pipeline:
            data_db.update_one(query_filter, pipeline)

    return ""