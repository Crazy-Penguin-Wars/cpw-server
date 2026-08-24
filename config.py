import os
from pathlib import Path
import json
from types import MappingProxyType

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

dev_mode = os.environ.get("DEV_MODE", "0") == "1"

SERVER_URL = f"http://127.0.0.1:{PORT}/api/" if dev_mode else f"{os.environ.get('ONLINE_URL')}/api/"
DATA_URL = f"http://127.0.0.1:{PORT}/assets/" if dev_mode else f"{os.environ.get('ONLINE_URL')}/assets/"

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

# Recursively freezes a nested dictionary (so that the config can't be accidentally modified)
def freeze(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return tuple(freeze(v) for v in obj)
    elif isinstance(obj, set):
        return frozenset(freeze(v) for v in obj)
    return obj

with open(os.path.join(p, "assets", "json", "tuxwars_config_base.json"), "r", encoding="utf-8") as f:
    CONFIG_BASE = json.loads(f.read())
    CONFIG_BASE = freeze(CONFIG_BASE)