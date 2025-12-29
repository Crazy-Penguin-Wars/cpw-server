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

def find_player_data(data_db, id):
    # Get account from database
    query_filter = {"id": id}
    document = data_db.find_one(query_filter, {"level": 1, "name": 1})

    player = {
        "id": id,
        "name": document["name"],
        "level": int(document["level"])
    }

    return player