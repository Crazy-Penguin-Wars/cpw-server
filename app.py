from flask import Flask
from dotenv import load_dotenv
import pymongo
import os
from config import AUTH_COLLECTION, DATA_COLLECTION, EXCHANGE_COLLECTION, DB_NAME, HOST, PORT
from web.routes import site_bp
from api.routes import api_bp
import logging

format = '%(asctime)s %(message)s'
logging.basicConfig(level=logging.INFO, format=format)
logging.info("[+] Starting...")
logging.info("[+] Loading environment variables...")
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CPW-secret")

logging.info("[+] Connecting to MongoDB...")
uri = os.environ["MONGO_URI"]
client = pymongo.MongoClient(uri, server_api=pymongo.server_api.ServerApi(version="1"))
app.db = client[DB_NAME]
app.auth_db = app.db[AUTH_COLLECTION]
app.exchange_cache = app.db[EXCHANGE_COLLECTION]
app.data_db = app.db[DATA_COLLECTION]

app.register_blueprint(site_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    logging.info(f"[+] Server started on {HOST}:{PORT}...")
    app.run(host=HOST, port=PORT, debug=True)
