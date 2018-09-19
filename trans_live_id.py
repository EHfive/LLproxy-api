import sqlite3

battle = sqlite3.connect("./db/event/battle.db_").execute(
    "SELECT live_difficulty_id,live_setting_id FROM event_battle_live_m").fetchall()
festival = sqlite3.connect("./db/event/festival.db_").execute(
    "SELECT live_difficulty_id,live_setting_id FROM event_festival_live_m").fetchall()
marathon = sqlite3.connect("./db/event/marathon.db_").execute(
    "SELECT live_difficulty_id,live_setting_id FROM event_marathon_live_m").fetchall()
live_db = sqlite3.connect("./db/live/live.db_")
live_setting_normal = live_db.execute("SELECT live_difficulty_id,live_setting_id FROM normal_live_m").fetchall()
live_setting_special = live_db.execute("SELECT live_difficulty_id,live_setting_id FROM special_live_m").fetchall()
res = []
res.extend(live_setting_normal)
res.extend(live_setting_special)
res.extend(marathon)
res.extend(battle)
res.extend(festival)
live_setting_id = dict(res)
i = 1
while i<2000:

    try:
        print(i, live_setting_id[i])
    except KeyError:
        print(i, "no")
    finally:
        i = i + 1
