import os
from pathlib import Path

p = Path(__file__).parents[0]

# Directories
TEMPLATES_DIR = os.path.join(p, "templates")
ASSETS_DIR = os.path.join(p, "assets")
STYLES_DIR = os.path.join(p, "templates", "styles")

# Main
HOST = "0.0.0.0"
PORT = 8000

# Database
DB_NAME = "cpw-dev"
AUTH_COLLECTION = "cpw-auth"
DATA_COLLECTION = "cpw-data"
EXCHANGE_COLLECTION = "exchange-cache"

dev_mode = os.environ.get("DEV_MODE", "1") == "1"

SERVER_URL = f"http://127.0.0.1:{PORT}/api/" if dev_mode else "https://cpw-server.onrender.com/api/"
DATA_URL = f"http://127.0.0.1:{PORT}/assets/" if dev_mode else "https://cpw-server.onrender.com/assets/"

# Login
QUERIES = {
    "serverURL": SERVER_URL,
    "dataDir": DATA_URL,
    "userId": -1,
    "token": "",
    "platformUserId": None,
    "languageCode": "en",
    "platform": "FB",
    "env": "dev",
    "version": "1.0.0",
    "secure": "false",
    "rememberme": "false"
}