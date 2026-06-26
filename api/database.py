import base64
import json
import os

from flask import current_app, request

def get_token_from_user_id(user_id):
    auth_db = current_app.auth_db
    query_filter = {"id": user_id}
    document = auth_db.find_one(query_filter, {"token": 1})
    if document:
        return document["token"]
    return None

# To-do: rewrite this because it's sketchy AI code
def update_rewards():
    data_db = current_app.data_db
    params = request.args.to_dict()
    if not params.get("connectionKey") or params.get("connectionKey") != os.environ["CONNECTION_KEY"]:
        # Someone is impersonating the battle server
        print("AMOGUS DETECTED")
        return "bruh"
    rewards_base64 = params.get("rewards")
    rewards_json = base64.urlsafe_b64decode(rewards_base64).decode("utf-8")
    rewards = json.loads(rewards_json)
    print(rewards)
    keys = list(rewards.keys())
    increments = {}
    substractions = {}

    for player in keys:
        query_filter = {"id": player}
        update_operation = { "$set" : {}, "$inc" : {}}
        for item in rewards[player]:
            match item:
                case "coins" | "cash":
                    update_operation["$inc"][item] = rewards[player][item]
                case "experience":
                    update_operation["$inc"]["score"] = rewards[player][item]
                case "usedItems":
                    substractions = rewards[player][item]
                case "earnedItems":
                    increments = rewards[player][item]

        # Items (don't ask me what this code does, chatgpt made it lol)
        changes = {}
        
        for k, v in increments.items():
            changes[k] = changes.get(k, 0) + v
        
        for k, v in substractions.items():
            changes[k] = changes.get(k, 0) - v
        
        branches = []
        for item_id, delta in changes.items():
            branches.append({
                "case": {"$eq": ["$$item.item_id", item_id]},
                "then": {
                    "item_id": "$$item.item_id",
                    "amount": {
                        "$toString": {
                            "$add": [
                                {"$toInt": "$$item.amount"},
                                delta
                            ]
                        }
                    }
                }
            })
        
        branches.append({"case": True, "then": "$$item"})
        
        item_update_operation = [
            {
                "$set": {
                    "items": {
                        "$filter": {
                            "input": {
                                "$map": {
                                    "input": "$items",
                                    "as": "item",
                                    "in": {
                                        "$switch": {
                                            "branches": branches
                                        }
                                    }
                                }
                            },
                            "as": "mappedItem",
                            "cond": {"$ne": ["$$mappedItem.amount", "0"]}
                        }
                    }
                }
            }
        ]

        data_db.update_one(query_filter,item_update_operation)
        # End of chatgpt code

        # Update coins and cash as well
        data_db.update_one(query_filter,update_operation)
        return ""
