import os
from pathlib import Path
import json
from types import MappingProxyType
import logging
import re

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

REF_PATTERN = re.compile(r"^#([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)$")

# Concatenate #Item.Punch type of references
def concat_references(obj, root, stack=None):
    if stack is None:
        stack = set()

    if isinstance(obj, str):
        m = REF_PATTERN.match(obj)
        if not m:
            return obj
        category, key = m.group(1), m.group(2)
        ref_id = (category, key)
        if ref_id in stack:
            logging.error(f"Circular reference detected: {obj}")
        try:
            target = root[category][key]
        except KeyError:
            logging.error(f"Broken reference '{obj}': '{category}.{key}' not found in config")
        return concat_references(target, root, stack | {ref_id})

    if isinstance(obj, dict):
        return {k: concat_references(v, root, stack) for k, v in obj.items()}

    if isinstance(obj, list):
        return [concat_references(v, root, stack) for v in obj]

    return obj


def freeze(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return tuple(freeze(v) for v in obj)
    elif isinstance(obj, set):
        return frozenset(freeze(v) for v in obj)
    return obj

with open(os.path.join(p, "assets", "json", "tuxwars_config_base.json"), "r", encoding="utf-8") as f:
    raw = json.loads(f.read())

concatenated = concat_references(raw, raw)
CONFIG_BASE = freeze(concatenated)