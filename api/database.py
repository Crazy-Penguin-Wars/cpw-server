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

def update_coins(amount):
    """Pipeline stage: add amount to the player's coins."""
    return {"$set": {"coins": {"$add": [{"$ifNull": ["$coins", 0]}, amount]}}}


def update_cash(amount):
    """Pipeline stage: add amount to the player's cash."""
    return {"$set": {"cash": {"$add": [{"$ifNull": ["$cash", 0]}, amount]}}}

def update_experience(amount):
    """Pipeline stage: add amount to the player's score."""
    return {"$set": {"score": {"$add": [{"$ifNull": ["$score", 0]}, amount]}}}

def add_items(item_amounts):
    branches = [
        {
            "case": {"$eq": ["$$item.item_id", item_id]},
            "then": {
                "item_id": "$$item.item_id",
                "amount": {"$add": ["$$item.amount", amount]}
            }
        }
        for item_id, amount in item_amounts.items()
    ]
    branches.append({"case": True, "then": "$$item"})

    return {
        "$set": {
            "items": {
                "$filter": {
                    "input": {
                        "$map": {
                            "input": "$items",
                            "as": "item",
                            "in": {"$switch": {"branches": branches}}
                        }
                    },
                    "as": "mappedItem",
                    "cond": {"$ne": ["$$mappedItem.amount", 0]}
                }
            }
        }
    }