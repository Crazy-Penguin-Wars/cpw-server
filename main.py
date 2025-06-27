import os
import json
from pathlib import Path
from flask import Flask, render_template, send_from_directory, request, redirect, session, Response

p = Path(__file__).parents[0]

TEMPLATES_DIR = os.path.join(p, "templates")
ASSETS_DIR = os.path.join(p, "assets")
STYLES_DIR = os.path.join(p, "templates", "styles")

host = '0.0.0.0'
port = 5055

app = Flask(__name__, template_folder=TEMPLATES_DIR)

# STATIC PART


@app.route("/styles/<path:path>")
def styles(path):
  return send_from_directory(STYLES_DIR, path)


@app.route("/assets/<path:path>")
def assetsLoader(path):
	print(path)
	if path == "json/tuxwars_config_base.json":
		with open(os.path.join(ASSETS_DIR, "json/tuxwars_config_base.json"), "r") as f:
			data = json.load(f)
    
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
  return render_template("play.html")

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
  xml = f"<root call_id='{args['call_id']}' service='GetAccountInformation' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><flags><flag key='Tutorial' value='false'></flag><flag key='settingMusic' value='true'></flag></flags><cash>4999</cash><coins>1000</coins><dcg_id>sgid_04010210b1e184bc</dcg_id><incoming_gift_requests/><incoming_neighbor_requests/><level>99</level><score>2908997</score><name>" + str(session["player_name"]) + "</name><pic_url>http://127.0.0.1:5055/styles/michi.jpg</pic_url><slot_machine_used_spins>0</slot_machine_used_spins><id>515998816</id><platforms_data><platform_data name='" + str(session["player_name"]) + "' user_id='sgid_04010210b1e184bc'></platform_data></platforms_data><items><item item_id='BasicNuke' amount='100'></item><item item_id='Punch' amount='100'></item></items><unlocked_items><unlocked_item item_id='BasicNuke'></unlocked_item></unlocked_items><worn_items><worn_item item_id='BasicNuke'></worn_item><worn_item item_id='Punch'></worn_item></worn_items></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>GetAccountInformation</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><time>{args['time']}</time><uid>515998816</uid></root>"

  return Response(xml, mimetype='text/xml')

@app.route("/SetFlag")
def SetFlag():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='SetFlag' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><dcg_id>sgid_04010210b1e184bc</dcg_id><level>99</level><score>2908997</score><cash>4999</cash><coins>1000</coins></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>SetFlag</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>2908997</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/GetTournamentInformation")
def GetTournamentInformation():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='GetTournamentInformation' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><dcg_id>sgid_04010210b1e184bc</dcg_id><rank>1</rank><points>1000</points><level>99</level><score>2908997</score><cash>4999</cash><coins>1000</coins><played_matches>10</played_matches><status>0</status><name>" + str(session["player_name"]) + "</name><user_id>515998816</user_id><platform>SpilGamesPortals</platform><pic_url></pic_url></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>GetTournamentInformation</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>2908997</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  return Response(xml, mimetype='text/xml')

@app.route("/GetInboxStatus")
def GetInboxStatus():
  return ""

@app.route("/PlayNow")
def PlayNow():
  args = request.args
  xml = f"<root call_id='{args['call_id']}' service='PlayNow' type='DataReceived'><data><gameVersion>0.69.1</gameVersion><key>test</key><game_identifier>test</game_identifier><player_count>3</player_count><dcg_id>sgid_04010210b1e184bc</dcg_id><rank>1</rank><points>1000</points><level>99</level><score>2908997</score><cash>4999</cash><coins>1000</coins><played_matches>10</played_matches><status>0</status><name>" + str(session["player_name"]) + "</name><user_id>515998816</user_id><platform>SpilGamesPortals</platform><pic_url></pic_url></data><gameVersion>0.69.1</gameVersion><maintenance>false</maintenance><maintenanceMode>false</maintenanceMode><platform>SpilGamesPortals</platform><responseCode>0</responseCode><response_code>0</response_code><service>PlayNow</service><sessionId>454</sessionId><sig>e6400557bbd0842536fecf4076a3371e</sig><level>99</level><score>2908997</score><cash>4999</cash><coins>1000</coins><time>{args['time']}</time><uid>515998816</uid></root>"
  #xml = f"<root call_id='{args['call_id']}' service='PlayNow' type='DataReceived'><data><game_identifier>test</game_identifier><player_count>3</player_count></root>"
  return Response(xml, mimetype='text/xml')

if __name__ == '__main__':
  app.secret_key = 'CPW-today-24-3-25'
  app.run(host=host, port=port, debug=True)
