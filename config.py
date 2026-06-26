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

# Login
QUERIES = {
    "serverURL": f"http://127.0.0.1:{PORT}/api/",
    "dataDir": f"http://127.0.0.1:{PORT}/assets/",
    "userId": -1,
    "token": "",
    "platformUserId": None,
    "languageCode": "en",
    "platform": "FB",
    "env": "dev",
    "version": "1.0.0",
    "secure": "false"
}