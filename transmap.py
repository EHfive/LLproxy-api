#! /usr/bin/python3
import json
import requests as rq
from collections import OrderedDict
import re

drop_non_chinese = True
url = "https://r.llsif.win/maps.min.json"
url_git = "https://raw.githubusercontent.com/iebb/SIFMaps/master/maps.min.json"
res = rq.get(url)
dictmaps = OrderedDict()
for smap in res.json():
    # sid = re.search("[0-9]+", smap['notes_setting_asset']).group()
    # sid = str(int(sid))
    sid= smap['live_setting_id']
    if sid not in dictmaps:
        if drop_non_chinese:
            try:
                del smap['name_translations']['english']
                del smap['name_translations']['korean']
            except KeyError as e:
                print("None ", e)
            pass
        dictmaps[sid] = smap
    else:
        print(sid + " 重复")

print("转换完成,开始写入")
json.dump(dictmaps, open("./datasource/maps_dict.min.json", "w"), separators=(',', ':'))
json.dump(dictmaps, open("./datasource/maps_dict.json", "w"), indent=2)
json.dump(dictmaps, open("./datasource/maps_dict_noacsii.json", "w"), indent=2, ensure_ascii=False)
