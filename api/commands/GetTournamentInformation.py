import xml.etree.ElementTree as ET

stub_db = {
    "tournaments": {
        "57a1b524-3d78-4f59-8e82-a52c15d11208": {
            "config_id": "tournament_weekly_01",
            "seconds_left": 13542,
            "status": 10,  # STATUS_PLAYING
        }
    },
    "leagues": {
        "57a1b524-3d78-4f59-8e82-a52c15d11208": {
            "league_id": "league_bronze_03",
            "played_matches": 7,
            "points": 42,
            "score": 1380,
            "previous_rank": 5,
            "rank": 3,
            "status": 30,  # ACCOUNT_STATUS_READY
            "division_id": "division_12",
            "determined_reward": {
                "first_rank_reward": "coin_pack_large",
                "first_rank_reward_amount": 500,
                "second_rank_reward": "coin_pack_medium",
                "second_rank_reward_amount": 250,
                "third_rank_reward": "coin_pack_small",
                "third_rank_reward_amount": 100,
                "fourth_rank_reward": "",
                "fourth_rank_reward_amount": 0,
            },
            "user_data_in_division": [
                {
                    "user_id": "11111111-1111-1111-1111-111111111111",
                    "dcg_id": "11111111-1111-1111-1111-111111111111",
                    "name": "PenguinSlayer",
                    "pic_url": "https://example.com/pics/11111111.jpg",
                    "platform": "FB",
                    "rank": 1,
                    "previous_rank": 1,
                    "played_matches": 8,
                    "points": 55,
                    "score": 1900,
                    "status": 30,
                },
                {
                    "user_id": "22222222-2222-2222-2222-222222222222",
                    "dcg_id": "22222222-2222-2222-2222-222222222222",
                    "name": "IceColdKiller",
                    "pic_url": "https://example.com/pics/22222222.jpg",
                    "platform": "FB",
                    "rank": 2,
                    "previous_rank": 3,
                    "played_matches": 6,
                    "points": 48,
                    "score": 1620,
                    "status": 30,
                },
            ],
        }
    },
    "rewards": {
        "57a1b524-3d78-4f59-8e82-a52c15d11208": {
            "id": "reward_98765",
            "league_id": "league_bronze_02",
            "previous_rank": 4,
            "rank": 2,
            "rank_reward": "coin_pack_medium",
            "rank_reward_amount": 250,
            "played_matches": 10,
            "points": 60,
            "score": 2100,
            "status": 40,  # ACCOUNT_STATUS_FINISHED
            "division_id": "division_07",
            "user_data_in_division": [
                {
                    "user_id": "33333333-3333-3333-3333-333333333333",
                    "dcg_id": "33333333-3333-3333-3333-333333333333",
                    "name": "WaddleWarrior",
                    "pic_url": "https://example.com/pics/33333333.jpg",
                    "platform": "FB",
                    "rank": 1,
                    "previous_rank": 2,
                    "played_matches": 10,
                    "points": 65,
                    "score": 2300,
                    "status": 40,
                }
            ],
        }
    },
}


def add_player(parent, tag, player):
    user_elem = ET.SubElement(parent, tag)
    ET.SubElement(user_elem, "user_id").text = str(player["user_id"])
    ET.SubElement(user_elem, "dcg_id").text = str(player["dcg_id"])
    ET.SubElement(user_elem, "name").text = str(player["name"])
    ET.SubElement(user_elem, "pic_url").text = str(player["pic_url"])
    ET.SubElement(user_elem, "platform").text = str(player["platform"])
    ET.SubElement(user_elem, "rank").text = str(player["rank"])
    ET.SubElement(user_elem, "previous_rank").text = str(player["previous_rank"])
    ET.SubElement(user_elem, "played_matches").text = str(player["played_matches"])
    ET.SubElement(user_elem, "points").text = str(player["points"])
    ET.SubElement(user_elem, "score").text = str(player["score"])
    ET.SubElement(user_elem, "status").text = str(player["status"])
    return user_elem


def handle_GetTournamentInformation(params, id, xml, data_db):
    data = ET.SubElement(xml, "data")
    """

    uid = params["uid"]
    sectors = params["sectors"]
    requested = set(s.strip() for s in sectors.split(",") if s.strip())

    active_tournament = stub_db["tournaments"][uid]
    active_league = stub_db["leagues"][uid]
    pending_reward = stub_db["rewards"][uid]

    # tournament_ongoing
    if "tournament_ongoing" in requested:
        tournament_ongoing = ET.SubElement(data, "tournament_ongoing")
        ET.SubElement(tournament_ongoing, "config_id").text = str(active_tournament["config_id"])
        ET.SubElement(tournament_ongoing, "seconds_left").text = str(active_tournament["seconds_left"])
        ET.SubElement(tournament_ongoing, "status").text = str(active_tournament["status"])

    # tournament_account_ongoing
    if "tournament_account_ongoing" in requested:
        acc_ongoing = ET.SubElement(data, "tournament_account_ongoing")
        ET.SubElement(acc_ongoing, "league_id").text = str(active_league["league_id"])
        ET.SubElement(acc_ongoing, "played_matches").text = str(active_league["played_matches"])
        ET.SubElement(acc_ongoing, "points").text = str(active_league["points"])
        ET.SubElement(acc_ongoing, "score").text = str(active_league["score"])
        ET.SubElement(acc_ongoing, "previous_rank").text = str(active_league["previous_rank"])
        ET.SubElement(acc_ongoing, "rank").text = str(active_league["rank"])
        ET.SubElement(acc_ongoing, "status").text = str(active_league["status"])
        ET.SubElement(acc_ongoing, "division_id").text = str(active_league["division_id"])

        determined_reward = active_league["determined_reward"]
        if determined_reward:
            dr = ET.SubElement(acc_ongoing, "determined_reward")
            ET.SubElement(dr, "first_rank_reward").text = str(determined_reward["first_rank_reward"])
            ET.SubElement(dr, "first_rank_reward_amount").text = str(determined_reward["first_rank_reward_amount"])
            ET.SubElement(dr, "second_rank_reward").text = str(determined_reward["second_rank_reward"])
            ET.SubElement(dr, "second_rank_reward_amount").text = str(determined_reward["second_rank_reward_amount"])
            ET.SubElement(dr, "third_rank_reward").text = str(determined_reward["third_rank_reward"])
            ET.SubElement(dr, "third_rank_reward_amount").text = str(determined_reward["third_rank_reward_amount"])
            ET.SubElement(dr, "fourth_rank_reward").text = str(determined_reward["fourth_rank_reward"])
            ET.SubElement(dr, "fourth_rank_reward_amount").text = str(determined_reward["fourth_rank_reward_amount"])

        opponents = active_league["user_data_in_division"]
        if opponents:
            division = ET.SubElement(acc_ongoing, "user_data_in_division")
            for opponent in opponents:
                add_player(division, "user", opponent)

    # tournament_account_reward
    if "tournament_account_reward" in requested:
        acc_reward = ET.SubElement(data, "tournament_account_reward")
        ET.SubElement(acc_reward, "id").text = str(pending_reward["id"])
        ET.SubElement(acc_reward, "league_id").text = str(pending_reward["league_id"])
        ET.SubElement(acc_reward, "previous_rank").text = str(pending_reward["previous_rank"])
        ET.SubElement(acc_reward, "rank").text = str(pending_reward["rank"])
        ET.SubElement(acc_reward, "rank_reward").text = str(pending_reward["rank_reward"])
        ET.SubElement(acc_reward, "rank_reward_amount").text = str(pending_reward["rank_reward_amount"])
        ET.SubElement(acc_reward, "played_matches").text = str(pending_reward["played_matches"])
        ET.SubElement(acc_reward, "points").text = str(pending_reward["points"])
        ET.SubElement(acc_reward, "score").text = str(pending_reward["score"])
        ET.SubElement(acc_reward, "status").text = str(pending_reward["status"])
        ET.SubElement(acc_reward, "division_id").text = str(pending_reward["division_id"])

        opponents = pending_reward["user_data_in_division"]
        if opponents:
            division = ET.SubElement(acc_reward, "user_data_in_division")
            for opponent in opponents:
                add_player(division, "user", opponent)

        """

    return xml