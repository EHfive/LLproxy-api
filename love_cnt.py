import sqlite3
import json


def data_init():
    try:
        live_combo = json.load(open('datasource/live_combo_m.json'))
    except FileNotFoundError:
        db = sqlite3.connect('db/live/live.db_')
        db.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
        cur = db.cursor()
        cur.execute("SELECT combo_cnt,combo_asset,score_rate,add_love_cnt FROM live_combo_m")
        res = cur.fetchall()
        json.dump(res, open('datasource/live_combo_m.json', 'w'))
        live_combo = res
    return live_combo


def love_by_combo(combo, live_combo_m=data_init()):
    love = 0
    for line in live_combo_m:
        if line['combo_cnt'] < combo:
            love += line['add_love_cnt']
        else:
            break
    print('combo:', combo, 'love:', love)
    return love


if __name__ == '__main__':
    love_by_combo(int(input("combo:")))
