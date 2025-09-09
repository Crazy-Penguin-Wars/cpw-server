import hashlib
import time

online_players = []

active_keys = []

def generate_signature(params, token):
    params = {k: v for k, v in params.items() if k != "sig"}
    sorted_items = sorted(params.items(), key=lambda x: x[0])

    base_string = "&".join(f"{k}={v}" for k, v in sorted_items)
    print(base_string)
    full_string = base_string + token + "PreCr4c4"

    return hashlib.md5(full_string.encode("utf-8")).hexdigest()

def refresh_online_status(id):
    for player in online_players:
        if player["id"] == id:
            player["timestamp"] = time.time()
            return

    online_players.append({"id": id, "timestamp": time.time()})

def get_online_players():
    current_time = time.time()
    for player in online_players:
        if current_time >= player["timestamp"] + 300: # 5 minutes
            online_players.remove(player)

    return len(online_players)

def add_key(key, player):
    active_keys.append({
        "key": key,
        "player": player,
        "expiration_time": time.time() + 60
    })

def find_key(key):
    current_time = time.time()
    for active_key in active_keys:
        # Also check for inactive keys
        if current_time >= active_key["expiration_time"]:
            active_keys.remove(active_key)

        if active_key["key"] == key:
            player = active_key["player"]
            active_keys.remove(active_key)
            return player

    print("Key not found")    
    return ""