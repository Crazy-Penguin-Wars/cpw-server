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
    return {"$set": {"coins": {"$add": [{"$ifNull": ["$coins", 0]}, amount]}}}


def update_cash(amount):
    return {"$set": {"cash": {"$add": [{"$ifNull": ["$cash", 0]}, amount]}}}

def update_experience(amount):
    return {"$set": {"score": {"$add": [{"$ifNull": ["$score", 0]}, amount]}}}

# For items that already exist in the "items" list in Mongo
# Also removes items that reach amount 0
# Usually you should just use add_items()
def add_existing_items(item_amounts):
    branches = [
        {
            "case": {"$eq": ["$$item.item_id", item_id]},
            "then": {
                "item_id": "$$item.item_id",
                "amount": {
                    "$max": [
                        0,
                        {
                            "$add": [
                                {"$toInt": {"$ifNull": ["$$item.amount", 0]}},
                                amount,
                            ]
                        },
                    ]
                },
            },
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
                            "input": {"$ifNull": ["$items", []]},
                            "as": "item",
                            "in": {"$switch": {"branches": branches}},
                        }
                    },
                    "as": "mappedItem",
                    "cond": {"$ne": ["$$mappedItem.amount", 0]},
                }
            }
        }
    }

# For items that the user did not have yet
# Usually you should just use add_items()
def add_missing_items(item_amounts):
    new_item_docs = [
        {"item_id": item_id, "amount": amount}
        for item_id, amount in item_amounts.items()
        if amount > 0
    ]

    return {
        "$set": {
            "items": {
                "$concatArrays": [
                    "$items",
                    {
                        "$filter": {
                            "input": new_item_docs,
                            "as": "newItem",
                            "cond": {
                                "$not": {
                                    "$in": [
                                        "$$newItem.item_id",
                                        {"$ifNull": ["$items.item_id", []]},
                                    ]
                                }
                            },
                        }
                    },
                ]
            }
        }
    }


def add_items(item_amounts):
    item_amounts = {k: v for k, v in item_amounts.items() if v != 0}
    if not item_amounts:
        return []

    return [
        add_existing_items(item_amounts),
        add_missing_items(item_amounts),
    ]