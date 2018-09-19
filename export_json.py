import json
import sqlite3
from collections import OrderedDict

unit_db = sqlite3.connect("./db/unit/unit.db_")
unit_db.row_factory = lambda c, r: OrderedDict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
cur = unit_db.cursor()
sql = "select * from unit_removable_skill_m"

cur.execute(sql)

result = {}
for skill in cur.fetchall():
    print(skill)
    result[str(skill['unit_removable_skill_id'])] = skill

json.dump(result, open("./datasource/removable_skill.min.json", 'w'), separators=(',', ':'))
json.dump(result, open("./datasource/removable_skill.json", 'w'), indent=2, ensure_ascii=False)
