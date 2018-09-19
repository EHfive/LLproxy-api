import sqlite3
import json


def tran_dict(dbpath='db/live/live.db_', jpdb='db/live/live_jp.db_'):
    db = sqlite3.connect(dbpath)
    # db.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
    cur = db.cursor()
    cur.execute("SELECT live_track_id,name FROM live_track_m")
    cn_name = dict(cur.fetchall())
    jp_db = sqlite3.connect(jpdb)
    jp_cur = jp_db.cursor()
    jp_cur.execute('SELECT live_track_id,name FROM live_track_m')
    jp_name = dict(jp_cur.fetchall())
    print(jp_name)
    name_dict = {
        "key_name": {},
        "key_id": {}
    }
    for tid, cname in cn_name.items():
        name_dict['key_name'][cname] = (jp_name[tid], tid)
        name_dict['key_id'][tid] = (cname, jp_name[tid])
    json.dump(name_dict, open('datasource/name_zh_jp.json', 'w'))
    json.dump(name_dict, open('datasource/name_zh_jp_readable.json', 'w'),indent=4,ensure_ascii=False)


if __name__ == '__main__':
    tran_dict()
