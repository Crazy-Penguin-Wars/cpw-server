import json
import os
import random
import re
import uuid

from flask import render_template, redirect, send_from_directory, session, url_for, current_app, flash, request, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash

from config import ASSETS_DIR, STYLES_DIR, QUERIES

from web.email import send_verification_email

site_bp = Blueprint("site", __name__)

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@site_bp.route("/play")
def play():
  if "id" not in session or "token" not in session:
      return redirect(url_for("site.login"))
  return render_template("play.html", ID=session["id"], TOKEN=session["token"])

@site_bp.route("/success")
def success():
    return("you shouldn't see this")


@site_bp.route("/assets/<path:path>")
def assetsLoader(path):
	return send_from_directory(ASSETS_DIR, path)


@site_bp.route("/styles/<path:path>")
def styles(path):
  return send_from_directory(STYLES_DIR, path)

@site_bp.route("/")
def home():
    return redirect(url_for("site.login"))


@site_bp.route("/login", methods=["GET", "POST"])
def login():
    auth_db = current_app.auth_db

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

                uses_client = request.headers.get('User-Agent').startswith("TuxWarsDesktop")
                print(request.headers.get('User-Agent'))
                if uses_client:
                    session_data = QUERIES.copy()
                    session_data["userId"] = id
                    session_data["token"] = token
                    return redirect(url_for("site.success", **session_data))
                return redirect(url_for("site.play"))
            else:
                flash("Wrong e-mail or password.", "error")
            return redirect(url_for("site.home"))

    return render_template("login.html")


@site_bp.route("/register", methods=["GET", "POST"])
def register():
    auth_db = current_app.auth_db
    data_db = current_app.data_db

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

                # Also insert player data
                with open(os.path.join(ASSETS_DIR, "json", "default_player.json")) as d:
                    player_document = json.load(d)
                    d.close()
                player_document["id"] = id
                player_document["name"] = username
                data_db.insert_one(player_document)
                flash("Your account has been created, but skipped e-mail verification because of an error. Please contact the developers about this.", "warning")
                return redirect(url_for("site.login"))
            auth_db.insert_one(document)
            return redirect(url_for("site.verify"))

    return render_template("register.html")


@site_bp.route("/verify", methods=["GET", "POST"])
def verify():
    auth_db = current_app.auth_db
    data_db = current_app.data_db

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
                return redirect(url_for("site.login"))
            else:
                flash("You entered the wrong code.", "error")

    return render_template("verify.html")
