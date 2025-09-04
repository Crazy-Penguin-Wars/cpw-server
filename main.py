import json
from flask import Flask, Response, render_template, request, redirect, send_from_directory, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
import random
import re
import smtplib, ssl
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import uuid
from pathlib import Path
import connectionUtils
import xml.etree.ElementTree as ET
from commands import *

p = Path(__file__).parents[0]

TEMPLATES_DIR = os.path.join(p, "templates")
ASSETS_DIR = os.path.join(p, "assets")
STYLES_DIR = os.path.join(p, "templates", "styles")

AVAILABLE_COMMANDS = {
    "GetAccountInformation": handle_GetAccountInformation
}

host = '0.0.0.0'
port = 5055

app = Flask(__name__)
app.secret_key = "CPW-secret"

load_dotenv()

# Connecct to database
uri = os.environ["MONGO_URI"]
client = pymongo.MongoClient(uri, server_api=pymongo.server_api.ServerApi(version="1"))
db = client["cpw-dev"]
auth_db = db["cpw-auth"]
data_db = db["cpw-data"]

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

def send_verification_email(email, code, name):
    msg = EmailMessage()
    msg['Subject'] = "Welcome to Crazy Penguin Wars!"
    msg['From'] = "noreply@crazypenguinwars.me"
    msg['To'] = email

    text = f"Your verification code is {code}"
    html = f"<h2>Dear {name}</h2><h1>Welcome to Crazy Penguin Wars!</h1><br>Your activation code is: <h3>{code}</h3><br>Enjoy playing the game!<br><br><img src=https://crazypenguinwars.me/assets/logo.png width=150><br><a href=https://discord.gg/PxxhzcbemQ target=_blank><img src=https://i.imgur.com/7S5ZLPZ.png width=40 height=40 title='Join our Discord!' /> </a>"

    msg.set_content(text)
    msg.add_alternative(html, subtype='html')

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.zeptomail.eu", 465, context=context) as server:
            server.login(os.environ['MAIL_USERNAME'], os.environ['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(e)
        return False

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
        else:
            query_filter = {"email": email}
            document = auth_db.find_one(query_filter, {"password": 1, "id": 1})
            pwhash = document["password"]
            id = document["id"]
            if check_password_hash(pwhash, password):
                session["id"] = id
                token = str(uuid.uuid4())
                session["token"] = token
                update_operation = { "$set" : { "token" : token}}
                auth_db.update_one(query_filter, update_operation)
                return redirect(url_for("play"))
            else:
                flash("Wrong e-mail or password.", "error")
            return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Input validation
        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "error")
        elif not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif auth_db.find_one({'email' : email}):
            flash("An account with this e-mail already exists.", "error")
        else:
            hashed_pw = generate_password_hash(password)
            code = f"{random.randint(0, 999999):06d}"
            id = str(uuid.uuid4())
            session["verifId"] = id
            session["verifName"] = username
            document = {
                "id": id,
                "username": username,
                "email": email,
                "password": hashed_pw,
                "verified": False,
                "verification_code": code,
                "token": ""
            }
            if not send_verification_email(email, code, username):
                # Could not send e-mail, skip verification
                document["verified"] = True
                del document["verification_code"]
                auth_db.insert_one(document)
                flash("Your account has been created, but skipped e-mail verification because of an error. Please contact the developers about this.", "warning")
                return redirect(url_for("login"))
            auth_db.insert_one(document)
            return redirect(url_for("verify"))

    return render_template("register.html")

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        code = request.form.get("code", "").strip()

        if not code.isdigit() or len(code) != 6:
            flash("Invalid code format. Must be 6 digits.", "error")
        else:
            query_filter = {'id' : session["verifId"]}
            verifcode = auth_db.find_one(query_filter, {"verification_code": 1})["verification_code"]
            if verifcode == code:
                flash("Your account has been created!", "success")
                update_operation = { "$set" : { "verified" : True}, "$unset": {"verification_code": ""}}
                auth_db.update_one(query_filter, update_operation)

                # Create account
                with open(os.path.join(ASSETS_DIR, "json", "default_player.json")) as d:
                    document = json.load(d)
                    d.close()
                document["id"] = session["verifId"]
                document["name"] = session["verifName"]
                data_db.insert_one(document)
                return redirect(url_for("login"))
            else:
                flash("You entered the wrong code.", "error")

    return render_template("verify.html")

@app.route("/play")
def play():
  return render_template("play.html", ID=session["id"], TOKEN=session["token"])

@app.route("/assets/<path:path>")
def assetsLoader(path):
	return send_from_directory(ASSETS_DIR, path)

@app.route("/styles/<path:path>")
def styles(path):
  return send_from_directory(STYLES_DIR, path)

@app.route("/api/<command>", methods=["GET",])
def handle_command(command):
    params = request.args.to_dict()

    id = params.get("uid")

    # Check signature
    given_signature = params.get("sig")
    calculated_signature = connectionUtils.generate_signature(params, session["token"])
    print(given_signature)
    print(calculated_signature)
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

    return Response(ET.tostring(xml, encoding="utf-8", xml_declaration=True), mimetype="application/xml")

if __name__ == "__main__":
    app.run(host=host, port=port, debug=True)
