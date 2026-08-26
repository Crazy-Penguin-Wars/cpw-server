# A leftover from the demo
# but now being recycled for the map editor cuz easier to update the browser version than to make new client for every change

import os
import json
import secrets
import time
from pathlib import Path
from flask import Flask, abort, jsonify, render_template, send_from_directory, request, redirect, session, Response, url_for

p = Path(__file__).parents[0]

TEMPLATES_DIR = os.path.join(p, "templates")
ASSETS_DIR = os.path.join(p, "assets")
STYLES_DIR = os.path.join(p, "templates", "styles")

host = '0.0.0.0'
port = 8000

TEST_MAPS = {}
TEST_MAP_TTL_SECONDS = 60 * 60
MAX_TEST_MAP_BYTES = 5 * 1024 * 1024

TEST_MATCH_SETTINGS = {
  "OpponentAmount": 3,
  "TurnDuration": 20,
  "MatchDuration": 300,
  "player_name": "You",
  "OpponentNames": ["Bot 1", "Bot 2", "Bot 3", ""],
}

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = 'CPW-today-24-3-25'


def cleanup_test_maps():
  expires_before = time.time() - TEST_MAP_TTL_SECONDS
  for map_id, record in list(TEST_MAPS.items()):
    if record["created_at"] < expires_before:
      del TEST_MAPS[map_id]


def get_uploaded_level():
  uploaded_file = request.files.get("level")
  if uploaded_file:
    raw_level = uploaded_file.read(MAX_TEST_MAP_BYTES + 1)
  elif "level" in request.form:
    raw_level = request.form["level"]
  else:
    raw_level = request.get_data(cache=False, as_text=True)

  if isinstance(raw_level, bytes):
    if len(raw_level) > MAX_TEST_MAP_BYTES:
      abort(413, "Level file is larger than 5 MiB.")
    try:
      raw_level = raw_level.decode("utf-8")
    except UnicodeDecodeError:
      abort(400, "Level file must be UTF-8 JSON.")
  elif len(raw_level.encode("utf-8")) > MAX_TEST_MAP_BYTES:
    abort(413, "Level file is larger than 5 MiB.")

  try:
    level = json.loads(raw_level)
  except (TypeError, json.JSONDecodeError):
    abort(400, "Level file must contain valid JSON.")

  if isinstance(level, dict) and set(level) == {"level"}:
    level = level["level"]
  if not isinstance(level, dict):
    abort(400, "Level JSON must be an object.")

  return json.dumps(level, ensure_ascii=False, separators=(",", ":"))


def active_test_map():
  map_id = session.get("test_map_id")
  record = TEST_MAPS.get(map_id)
  if record and record["created_at"] >= time.time() - TEST_MAP_TTL_SECONDS:
    return map_id, record
  session.pop("test_map_id", None)
  return None, None


def apply_test_match_settings():
  """Set only this browser's practice session; the normal demo settings remain untouched."""
  session.update(TEST_MATCH_SETTINGS)

# STATIC PART


@app.route("/styles/<path:path>")
def styles(path):
  return send_from_directory(STYLES_DIR, path)


@app.route("/assets/<path:path>")
def assetsLoader(path):
  print(path)
  if "OpponentAmount" not in session:
    session.update(TEST_MATCH_SETTINGS)
  map_id, test_map = active_test_map()
  if path == "flash/levels/test-maps/" + str(map_id) + ".lvl" and test_map:
    return Response(test_map["level"], mimetype="application/json")

  if path == "json/tuxwars_config_base.json":
    with open(os.path.join(ASSETS_DIR, "json/tuxwars_config_base.json"), "r") as f:
      data = json.load(f)

    if test_map:
      # PracticeLevels chooses a random row.  Leave exactly one test row so the
      # uploaded map is always selected while keeping the client in practice mode.
      data["Practice"]["Default"].update({
        "OpponentAmount": TEST_MATCH_SETTINGS["OpponentAmount"],
        "TurnDuration": TEST_MATCH_SETTINGS["TurnDuration"],
        "MatchDuration": TEST_MATCH_SETTINGS["MatchDuration"],
      })
      data["PracticeLevel"] = {
        "$DATA_TYPE": data["PracticeLevel"]["$DATA_TYPE"],
        "editor_test_map": {
          "ID": "editor_test_map",
          "MinLevel": 0,
          "LevelFile": "flash/levels/test-maps/" + map_id + ".lvl",
        },
      }
    
    # Replace placeholders
    replacements = {
          "{{OpponentAmount}}": int(session["OpponentAmount"]),
          "{{MatchDuration}}": int(session["MatchDuration"]),
          "{{TurnDuration}}": int(session["TurnDuration"]),
          "{{bot1_enable}}": 99,
          "{{bot2_enable}}": 99 if int(session["OpponentAmount"]) >=2 else 10,
          "{{bot3_enable}}": 99 if int(session["OpponentAmount"]) >=3 else 10
      }
        
    def replace_placeholders(obj):
      if isinstance(obj, dict):
        return {key: replace_placeholders(value) for key, value in obj.items()}
               
      elif isinstance(obj, list):
        return [replace_placeholders(item) for item in obj]
               
      elif isinstance(obj, str) and obj in replacements:
        return replacements[obj]
               
      return obj
          
    data = replace_placeholders(data)
  
    return Response(json.dumps(data), 
                mimetype="application/json", 
                headers={"Content-Disposition": 'inline; filename="tuxwars_config_base.json"'})

  elif path == "json/tuxwars_config_en.json":
    with open(os.path.join(ASSETS_DIR, "json/tuxwars_config_en.json"), "r") as f:
      content = f.read()
    
    # Replace placeholders
    replacements = {
        "{{bot1_name}}": session["OpponentNames"][0],
        "{{bot2_name}}": session["OpponentNames"][1] if int(session["OpponentAmount"]) >=2 else "",
        "{{bot3_name}}": session["OpponentNames"][2] if int(session["OpponentAmount"]) >=3 else ""
      }
  
    for placeholder, value in replacements.items():
      content = content.replace(placeholder, value)
  
    return Response(content, 
                mimetype="application/json", 
                headers={"Content-Disposition": 'inline; filename="tuxwars_config_en.json"'})
  
  return send_from_directory(ASSETS_DIR, path)


@app.route("/crossdomain.xml")
def crossdomain():
  return send_from_directory(ASSETS_DIR, "crossdomain.xml")


@app.route("/play")
def play():
  return render_template("play.html", ID="sgid_04010210b1e184bc", TOKEN="test", SERVER_URL="http://127.0.0.1:8000/", DATA_URL="http://127.0.0.1:8000/assets/")


@app.route("/test-map", methods=["GET", "POST"])
def test_map():
  cleanup_test_maps()
  if request.method == "POST":
    level = get_uploaded_level()
    map_id = secrets.token_urlsafe(18)
    TEST_MAPS[map_id] = {"level": level, "created_at": time.time()}
    return jsonify({
      "map_id": map_id,
      "launch_url": url_for("test_map", map=map_id, _external=True),
      "expires_in_seconds": TEST_MAP_TTL_SECONDS,
    }), 201

  map_id = request.args.get("map")
  if not map_id:
    return jsonify({"error": "Upload a level with POST, then open the returned launch_url."}), 400
  if map_id not in TEST_MAPS:
    abort(404, "This test map does not exist or has expired.")

  session["test_map_id"] = map_id
  apply_test_match_settings()
  return redirect("/play")

@app.route("/demo")
def demo():
  if "OpponentAmount" in session:
    match_minutes = int(int(session["MatchDuration"]) / 60)
    match_seconds = int(session["MatchDuration"]) % 60
    return render_template("demo.html", match_minutes=match_minutes, match_seconds=match_seconds, turn_time=int(session["TurnDuration"]), map="", botCount=session["OpponentAmount"], bot1_name = session["OpponentNames"][0], bot2_name = session["OpponentNames"][1], bot3_name = session["OpponentNames"][2], bot4_name = session["OpponentNames"][3], player_name=session["player_name"])
  else:
    return render_template("demo.html", match_minutes=5, match_seconds=0, turn_time=20, map="", botCount=1, bot1_name="", bot2_name="", bot3_name="", bot4_name="", player_name="")

@app.route("/start_game", methods=['POST'])
def startGame():
  print(request.form)
  session["OpponentAmount"] = request.form["botCount"]
  session["TurnDuration"] = request.form["turn_time"]
  session["MatchDuration"] = request.form["match_time"]
  session["map"] = request.form["map"]
  session["player_name"] = request.form["player_name"]
  session["OpponentNames"] = ["", "", "", ""]
  for i in range(int(request.form["botCount"])):
      session["OpponentNames"][i] = request.form["bot" + str(i + 1) + "_name"]
  return redirect("/play")

@app.route("/")
def home():
  return redirect("/demo")


# DYNAMIC PART


@app.route("/GetAccountInformation")
def GetAccountInformation():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='GetAccountInformation' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><flags><flag key='Tutorial' value='false'></flag><flag key='settingMusic' value='true'></flag></flags><cash>4999</cash><coins>1000</coins><dcg_id>{args['uid']}</dcg_id><incoming_gift_requests/><incoming_neighbor_requests/><level>99</level><score>12059</score><name>" + str(session["player_name"]) + "</name><pic_url>http://127.0.0.1:8000/styles/michi.jpg</pic_url><slot_machine_used_spins>0</slot_machine_used_spins><id>515998816</id><platforms_data><platform_data name='" + str(session["player_name"]) + f"' user_id='{args['uid']}'></platform_data></platforms_data><items><item item_id='BasicNuke' amount='100'></item><item item_id='Punch' amount='100'></item></items><unlocked_items><unlocked_item item_id='BasicNuke'></unlocked_item></unlocked_items><worn_items><worn_item item_id='BasicNuke'></worn_item><worn_item item_id='Punch'></worn_item></worn_items></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>GetAccountInformation</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><time>{args['time']}</time><uid>515998816</uid></root>"

  return Response(xml, mimetype='text/xml')

@app.route("/SetFlag")
def SetFlag():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='SetFlag' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><dcg_id>{args['uid']}</dcg_id><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>SetFlag</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/GetTournamentInformation")
def GetTournamentInformation():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='GetTournamentInformation' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><dcg_id>{args['uid']}</dcg_id><rank>1</rank><points>1000</points><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><played_matches>10</played_matches><status>0</status><name>{str(session['player_name'])}</name><user_id>515998816</user_id><platform>SpilGamesPortals</platform><pic_url></pic_url></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>GetTournamentInformation</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/GetInboxStatus")
def GetInboxStatus():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='ClientTracking' type='DataReceived'><data></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/PlayNow")
def PlayNow():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='PlayNow' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><host>127.0.0.1</host><port>5050</port><key>test</key><game_identifier>test</game_identifier><player_count>3</player_count><dcg_id>{args['uid']}</dcg_id><rank>1</rank><points>1000</points><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><played_matches>10</played_matches><status>0</status><name>{str(session['player_name'])}</name><user_id>515998816</user_id><platform>SpilGamesPortals</platform><pic_url></pic_url></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  #xml = f"<root call_id='{args['call_id']}' service='PlayNow' type='DataReceived'><data><game_identifier>test</game_identifier><player_count>3</player_count></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/CheckServerStatus")
def CheckServerStatus():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='CheckServerStatus' type='DataReceived'><data><productionUpdate>false</productionUpdate></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/ClientTracking")
def ClientTracking():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='ClientTracking' type='DataReceived'><data></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/BuyItem")
def BuyItem():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='BuyItem' type='DataReceived'><data><item item_id='{args['item_id']}' total_amount='90' bought_amount='5' reduced_cash='90' reduced_coins='90'></item></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/ConfirmBattleEnded")
def ConfirmBattleEnded():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='ConfirmBattleEnded' type='DataReceived'><data><internal_code>1</internal_code></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>12059</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

if __name__ == '__main__':
  app.run(host=host, port=port, debug=True)
