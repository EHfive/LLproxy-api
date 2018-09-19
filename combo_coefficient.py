import config as cfg
import pymysql

db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME, charset=cfg.DB_CHARSET)
cur = db.cursor()

basic_pt = (0, 301, 320, 339, 358, 377)
combo_multiple = (1, 1.08, 1.06, 1.04, 1.02, 1)


def combo_m(combo_rank):
    return -0.02 * combo_rank + 1.1


cur.execute(
    "SELECT round,combo_rank,count(*) as cnt FROM `event_challenge` WHERE uid = 5012675 GROUP by combo_rank,round")
count_up = 0
count_down = 0
cnt_combo_r = {x: [0, 0] for x in range(1, 6)}
for roundn, combo_r, cnt in cur.fetchall():
    pt = basic_pt[roundn]
    mtp = combo_multiple[combo_r]
    up = round(pt * mtp) * cnt
    down = cnt * pt
    count_up += up
    count_down += down
    cnt_combo_r[roundn][0] += mtp * cnt
    cnt_combo_r[roundn][1] += cnt

    # print(roundn, combo_r, cnt, up)
coefficient0 = count_up / count_down
# print(round(coefficient0, 3))
avg_combo_m = {}

for k, combom in cnt_combo_r.items():
    avg = combom[1] and round(combom[0] / combom[1], 3)
    avg_combo_m[k] = avg
    # print(avg)
