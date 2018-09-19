#!/usr/bin/env python3

import requests as rq
import json
import pymysql
import time
import sys
import datetime
import sqlite3

sys.path.append("..")
import config as cfg

IEB_EVENT_API = "http://sifcn.loveliv.es/api/event_list"
PLL_LOG_STARTTIME = datetime.datetime(2017, 6, 1).timestamp()

db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME, charset=cfg.DB_CHARSET)
cur = db.cursor()
def fetch_logged_eventid():

    cur.execute("SELECT event_id FROM event_list")
    return [x[0] for x in cur.fetchall()]


def tranevent_from_ieb():
    curr_time = time.time()
    eventdb = sqlite3.connect('../db/event/event_common.db_')
    eventcur = eventdb.cursor()
    eventcur.execute("SELECT event_id,description,member_category FROM event_m")
    desc_dict = {x[0]: (x[1], x[2]) for x in eventcur.fetchall()}
    loged_eventid = fetch_logged_eventid()
    try:
        ieb_eventlist = rq.get(IEB_EVENT_API).json()
    except Exception as e:
        print("ieb_eventlist get failed", str(e))
        return
    ieb_eventlist.sort(key=lambda x: x['begin']['timestamp'])
    added_event = []
    for event in ieb_eventlist:
        event_id = int(event['event_id'])
        if event_id in loged_eventid or event['end']['timestamp'] <= PLL_LOG_STARTTIME or event['begin'][
            'timestamp'] > curr_time + 3600 * 48:
            continue

        cur.execute("""INSERT INTO event_list (`name`,event_id, event_category_id, begin_date,  begin_time,end_date,end_time, description, mgd) 
        VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}')
        """.format(
            event['title'],
            event_id,
            int(event['type']),
            event['begin']['time'],
            event['begin']['timestamp'],
            event['end']['time'],
            event['end']['timestamp'],
            desc_dict[event_id][0],
            desc_dict[event_id][1]
        ))
        db.commit()
        if __name__ == "__main__":
            print(event['title'])
        added_event.append(event_id)
    return added_event


if __name__ == "__main__":
    tranevent_from_ieb()
