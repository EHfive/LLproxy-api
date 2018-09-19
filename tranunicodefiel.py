import requests as rq

r = rq.get("http://127.0.0.1:5000/llproxy/unitsExport/?uid=865384")
string = r.json()['result']['mergetoolString']

open('/home/cimoc/桌面/SH/test.666', 'w',encoding='utf-16').write(string)
