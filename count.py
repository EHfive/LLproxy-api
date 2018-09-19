import json
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
import config as cfg


def combo_rate():
    map_index = json.load(open('./datasource/maps_dict.min.json'))
    song_set_list = []
    info_list = [{
        'set_ids': 0,
        'times': 0,
        'difficulty': 1,
        'attribute': 1
    }]
    cnt = {
        'round_' + x:
            {
                'attr_1': [0] * 6,
                'attr_2': [0] * 6,
                'attr_3': [0] * 6
            } for x in ('1', '2', '3')
    }
    del info_list[0]
    db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME, charset=cfg.DB_CHARSET)
    cur = db.cursor()
    cur.execute("SELECT song_set_ids FROM event_festival ")
    cnt_t = 0
    for row in cur.fetchall():
        song_set_ids = json.loads(row[0])
        song_set = set(song_set_ids)
        cnt_t += 1
        try:
            i = song_set_list.index(song_set)
        except ValueError:
            set_ids = list(song_set)
            map_songs = [map_index[str(x)] for x in set_ids]
            song_set_list.append(song_set)
            diff = map_songs[0]['difficulty']
            attr = map_songs[0]['attribute_icon_id']
            round_l = len(set_ids)
            cnt['round_' + str(round_l)]['attr_' + str(attr)][diff - 1] += 1
            info_list.append({
                'set_ids': set_ids,
                'names': [x['name'] for x in map_songs],
                'combo_cnt': sum([x['s_rank_combo'] for x in map_songs]),
                'times': 1,
                'difficulty': diff,
                'attribute': attr,
                'round': round_l
            })
        else:
            item = info_list[i]
            cnt['round_' + str(item['round'])]['attr_' + str(item['attribute'])][item['difficulty'] - 1] += 1
            item['times'] += 1
    print(cnt_t)
    res = {
        'count': cnt,
        'info_list': info_list,

    }
    json.dump(res, open('./datasource/mf_sets_cnt.json', 'w'), indent=4, ensure_ascii=False)


def verify_mf_data():
    set_cnt = json.load(open('./datasource/mf_sets_cnt.json'))
    rate_list = []
    for item in set_cnt['info_list']:
        attr = item['attribute']
        diff = item['difficulty']
        round_l = item['round']
        if attr == 1 and diff == 4 and round_l == 3:
            count = set_cnt['count']['round_' + str(round_l)]['attr_' + str(attr)][diff - 1]
            rate_list.append({
                "combo": item['combo_cnt'],
                'percent': round(100 * item['times'] / count, 3),
                'names': item['names']
            })
    rate_list.sort(key=lambda x: x.get('percent'))
    for item in rate_list:
        print('Notes:', item['combo'], 'Percent:', '%.2f%%' % item['percent'],'\t\t', 'Names:', item['names'])

def reward_stats():
    def challenge_reward_tran(event_id, start=0):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME, charset=cfg.DB_CHARSET)
        cur = db.cursor()

        sql = "SELECT id,reward_item_list FROM event_challenge_pairs WHERE reward_item_list IS NOT NULL  AND id> %d" % start
        cur.execute(sql)
        mm = []
        last_id = start
        for pair in cur.fetchall():
            last_id = pair[0]
            coin = 0
            try:
                rewards = json.loads(pair[1])
            except:
                continue
            for r in rewards:
                if r['add_type'] == 3000:
                    coin += r['amount']
            cur.execute("update event_challenge_pairs set coin_reward = %s WHERE id = %s" % (coin, pair[0]))
            db.commit()
            print(last_id, "=>", coin)
        for m in mm:
            print(m)
        return last_id

if __name__ == '__main__':
    # combo_rate()
    verify_mf_data()
