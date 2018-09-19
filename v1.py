from collections import OrderedDict
from flask import Flask
from flask_restful import Resource, Api, fields, marshal, marshal_with, reqparse
from flask_restful.utils import cors
import pymysql
import config as cfg
import pymysql.cursors
from pymysql import escape_string
import datetime
import json
import requests
import sqlite3
from urllib import parse
from Apis.EventList import *

app = Flask(__name__)

api = Api(app)
apiraw = Api(app)

unit_db = sqlite3.connect("./db/unit/unit.db_", check_same_thread=False)
curonce = unit_db.cursor()
curonce.execute(
    "SELECT `effect_range`,effect_type,effect_value,fixed_value_flag,target_reference_type,unit_removable_skill_id,name,icon_asset FROM unit_removable_skill_m ")
siskill = {}
for skill in curonce.fetchall():
    siskill[skill[5]] = skill
del curonce


class SearchUser(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('keyword', type=str, required=True, help='必须给出用户搜索关键字 UID/邀请码/昵称')
    parser.add_argument('limit', type=int, help='返回限制必须为整数')
    unit_info = OrderedDict([
        ("unit_id", fields.Integer),
        ("unit_number", fields.Integer),
        ("level", fields.Integer),
        ("display_rank", fields.Integer)

    ])
    users = {"result": fields.List(fields.Nested(OrderedDict([("uid", fields.Integer(attribute="user_id")),
                                                              ("name", fields.String),
                                                              ("level", fields.Integer),
                                                              ("invite_code", fields.String),
                                                              ("insert_date", fields.DateTime('iso8601')),
                                                              ("navi_unit_info", fields.Nested(unit_info)),
                                                              ("update_time", fields.DateTime('iso8601'))

                                                              ])))}

    @marshal_with(users)
    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        keyword = args['keyword']
        if keyword:
            pass

        else:
            return {"result": []}
        limit = 10
        if args['limit'] and 100 >= args['limit'] > 0:
            limit = args['limit']
        if keyword == "***":
            sql = """
                    SELECT * FROM `user_info` ORDER BY `update_time` DESC LIMIT %s 
                    """
            cur.execute(sql, args['limit'])
        else:
            keyword = escape_string(args['keyword'])
            sql = """
                                SELECT * FROM `user_info` WHERE `user_id` LIKE %s OR `name` LIKE %s OR `invite_code` LIKE %s
                                 ORDER BY `update_time` DESC LIMIT %s
                                """
            cur.execute(sql, (keyword + "%", "%" + keyword + "%", keyword + "%", limit))
        results = []
        for res in cur.fetchall():
            res['update_time'] = datetime.datetime.fromtimestamp(res['update_time'])
            if res['navi_owning_id']:
                sql2 = """
                                SELECT * FROM `unit_unitAll` WHERE `unit_owning_user_id` = %s
                                """
                cur.execute(sql2, res['navi_owning_id'])
                res2 = cur.fetchone()
                res['navi_unit_info'] = None
                if res2:
                    res2['insert_date'] = res2['insert_date'].isoformat()
                    skill = []
                    if res2['unit_removable_skill_id']:
                        for x in res2['unit_removable_skill_id'].split(','):
                            skill.append(int(x))
                        res2['unit_removable_skill_id'] = skill
                    else:
                        res2['unit_removable_skill_id'] = []
                    del res2['uid']
                    res['navi_unit_info'] = res2

            else:
                res['navi_unit_info'] = None
            results.append(res)
        return {"result": results}


class UserInfo(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        uid = args['uid']

        sql = """
        SELECT * FROM `user_info` WHERE `user_id` = %s
        """
        cur.execute(sql, uid)
        res = cur.fetchone()
        if not res:
            return {"result": res}
        res['energy_full_time'] = res['energy_full_time'].isoformat()
        res['insert_date'] = res['insert_date'].isoformat()
        res['update_date'] = res['update_date'].isoformat()
        res['update_time'] = datetime.datetime.fromtimestamp(res['update_time']).isoformat()
        if res['navi_owning_id']:
            sql2 = """
                            SELECT * FROM `unit_unitAll` WHERE `unit_owning_user_id` = %s
                            """
            cur.execute(sql2, res['navi_owning_id'])
            res2 = cur.fetchone()
            if res2:
                res2['insert_date'] = res2['insert_date'].isoformat()
                skill = []
                if res2['unit_removable_skill_id']:
                    for x in res2['unit_removable_skill_id'].split(','):
                        skill.append(int(x))
                    res2['unit_removable_skill_id'] = skill
                else:
                    res2['unit_removable_skill_id'] = []
                del res2['uid']
            res['navi_unit_info'] = res2
        else:
            res['navi_unit_info'] = None

        return {"result": res}


class UnitsInfo(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        sql = """
                SELECT * FROM `unit_unitAll` WHERE `uid` = %s AND `status`=1 AND `rarity` != 1
                ORDER BY `unit_unitAll`.`insert_date` DESC  LIMIT %s OFFSET %s
                """
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        units = cur.fetchall()
        sqlcnt = """
        SELECT count(*) FROM `unit_unitAll` WHERE uid=%s AND status =1 AND `rarity` != 1
        """
        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in units:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            x['insert_date'] = x['insert_date'].isoformat()
            res.append(x)
        return {
            "result": {
                "units": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count
            }
        }


class LiveInfo(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')
    parser.add_argument('setid', type=int, help='为live_setting_id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        if args['setid'] and args['setid'] > 0:
            sql = """
                                        SELECT * FROM `live` WHERE `uid` = %s AND `live_setting_id` ='{}'
                                        ORDER BY `live`.`update_time` DESC  LIMIT %s OFFSET %s
                                        """.format(args['setid'])
            sqlcnt = """
                                        SELECT count(*) FROM `live` WHERE uid=%s AND `live_setting_id` ='{}'
                                        """.format(args['setid'])
        else:
            sql = """
                            SELECT * FROM `live` WHERE `uid` = %s 
                            ORDER BY `live`.`update_time` DESC  LIMIT %s OFFSET %s
                            """
            sqlcnt = """
                            SELECT count(*) FROM `live` WHERE uid=%s 
                            """
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        lives = cur.fetchall()

        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in lives:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            del x['id']
            # try:
            #     x['live_setting_id'] = live_setting_id[x['live_difficulty_id']]
            # except KeyError:
            #     x['live_setting_id'] = None
            res.append(x)
        return {
            "result": {
                "lives": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count
            }
        }


class SecretBoxLog(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')
    parser.add_argument('filter', type=str, help='过滤器')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        infilter = []
        notinfilter = ["-1"]
        filters = []
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']

        if args['filter']:
            filters = args['filter'].split(',')
        try:
            for n in filters:
                n = int(n)
                if n > 0:
                    infilter.append(str(n))
                else:
                    notinfilter.append(str(-n))
        except ValueError:
            infilter = []
            notinfilter = []
        if len(infilter) > len(notinfilter):
            sql = """
                        SELECT * FROM `secretbox` WHERE `uid` = %s AND `secret_box_id` IN ({})
                        ORDER BY id DESC  LIMIT %s OFFSET %s
                        """.format(','.join(infilter))
            sqlcnt = """
                        SELECT count(*) FROM `secretbox` WHERE uid=%s AND `secret_box_id` IN ({})
                        """.format(','.join(infilter))

        else:
            sql = """
                                    SELECT * FROM `secretbox` WHERE `uid` = %s AND `secret_box_id` NOT IN ({})
                                    ORDER BY id DESC  LIMIT %s OFFSET %s
                                    """.format(",".join(notinfilter))
            sqlcnt = """
                                    SELECT count(*) FROM `secretbox` WHERE uid=%s AND `secret_box_id` NOT IN ({})
                                    """.format(",".join(notinfilter))

        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        logs = cur.fetchall()

        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in logs:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            if 'id' in x:
                del x['id']
            x['result_unit_ids'] = [int(i) for i in x['result_unit_ids'].split(',')]
            x['result_rarity_ids'] = [int(i) for i in x['result_rarity_ids'].split(',')]
            res.append(x)
        return {
            "result": {
                "logs": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count,
                "infilter": ",".join(infilter),
                "notinfilter": ",".join(notinfilter),
            }
        }


class EventMarathonInfo(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')
    parser.add_argument('eventid', type=int, help='为event_id')
    parser.add_argument('shownormal', type=bool, help='是否显示活动曲外的情况')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        eventq = "AND `event_id` ='{}'"
        eventqfmt = '\n'
        shownormalqfmt = 'AND `is_event_song` = 1'
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        sql = """\
SELECT * FROM `event_traditional` WHERE `uid` = %s {} {}
ORDER BY id DESC  LIMIT %s OFFSET %s \
"""
        sqlcnt = """\
SELECT count(*) FROM `event_traditional` WHERE uid=%s {} {}  \
"""
        if args['eventid'] and args['eventid'] > 0:
            eventqfmt = eventq.format(args['eventid'])
        if args['shownormal']:
            shownormalqfmt = '\n'
        sql = sql.format(eventqfmt, shownormalqfmt)
        sqlcnt = sqlcnt.format(eventqfmt, shownormalqfmt)
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        lives = cur.fetchall()

        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in lives:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            del x['id']
            res.append(x)
        return {
            "result": {
                "lives": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count
            }
        }


class DeckInfo(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        uid = args['uid']

        sql = """
        SELECT `uid`,`update_time`,`deck_info` FROM `deck_and_removable_Info` WHERE `uid` = %s
        """
        cur.execute(sql, uid)
        res = cur.fetchone()

        res['update_time'] = datetime.datetime.fromtimestamp(res['update_time']).isoformat()
        deck_info_array = json.loads(res['deck_info'])
        result = []
        for deck in deck_info_array:
            res_deck_units = {}
            for unit in deck['unit_owning_user_ids']:
                sql2 = """SELECT * FROM `unit_unitAll` WHERE `unit_owning_user_id` = %s
                       """
                cur.execute(sql2, unit['unit_owning_user_id'])
                res2 = cur.fetchone()
                if not res2:
                    continue

                res2['insert_date'] = res2['insert_date'].isoformat()
                res2['position'] = unit['position']
                skill = []
                if res2['unit_removable_skill_id']:
                    for x in res2['unit_removable_skill_id'].split(','):
                        skill.append(int(x))
                    res2['unit_removable_skill_id'] = skill
                else:
                    res2['unit_removable_skill_id'] = []
                del res2['uid']
                res_deck_units[str(unit['position'])] = res2
            result.append(OrderedDict([
                ('unit_deck_id', deck['unit_deck_id']),
                ('main_flag', deck['main_flag']),
                ('deck_name', deck['deck_name']),
                ('units', res_deck_units)
            ]))
        return {"result": OrderedDict([
            ('uid', res['uid']),
            ('update_time', res['update_time']),
            ('deck_info', result)
        ])}


class DeckExport(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('deck_id', type=int, required=True, help='必须给出用户 卡组id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        unit_cur = unit_db.cursor()
        args = self.parser.parse_args(strict=True)
        uid = args['uid']
        unit_deck_id = args['deck_id']
        sql = """
        SELECT `uid`,`update_time`,`deck_info` FROM `deck_and_removable_Info` WHERE `uid` = %s
        """
        cur.execute(sql, uid)
        res = cur.fetchone()

        res['update_time'] = datetime.datetime.fromtimestamp(res['update_time']).isoformat()
        deck_info_array = json.loads(res['deck_info'])
        result = []
        cardview = []
        sifstatus = [0]
        deckname = ""
        for deck in deck_info_array:

            if deck['unit_deck_id'] == unit_deck_id:
                ids = {}
                deckname = deck['deck_name']
                for units in deck['unit_owning_user_ids']:
                    ids[units['position']] = units['unit_owning_user_id']
                for position in range(1, 10):
                    if position not in ids:
                        result.append(
                            {"smile": 3900, "pure": 1590, "cool": 1720, "skilllevel": 1, "cardid": 28, "mezame": 0,
                             "gemnum": 0, "gemsinglepercent": 0, "gemallpercent": 0, "gemskill": 0, "gemacc": 0})
                        cardview.append(OrderedDict([
                            ('unit_id', 28),
                            ('rank', 1),
                            ('level', '1'),
                            ('skill_level', '1'),
                            ('love', 0)
                        ]))
                        continue
                    sql2 = """SELECT `unit_number`,`attribute_id`,`unit_removable_skill_id`,`unit_id`,`level`,`love`,
                              `unit_skill_level`,`is_rank_max`,`is_love_max`,`rank`,`unit_removable_skill_capacity` FROM `unit_unitAll` WHERE `unit_owning_user_id` = %s
                           """
                    cur.execute(sql2, ids[position])
                    res2 = cur.fetchone()

                    gemnum = 0
                    gemsinglepercent = 0
                    gemallpercent = 0
                    gemskill = 0
                    capacity = res2['unit_removable_skill_capacity'] if res2['unit_removable_skill_capacity'] else 0
                    gemacc = 0
                    removable = []
                    if res2['unit_removable_skill_id']:
                        removable = [int(x) for x in res2['unit_removable_skill_id'].split(',')]
                        for x in removable:
                            # unit_cur.execute(
                            #     "select `effect_range`,effect_type,effect_value,fixed_value_flag,target_reference_type FROM unit_removable_skill_m WHERE unit_removable_skill_id = {}".format(
                            #         x))
                            # ress = unit_cur.fetchone()
                            ress = siskill[x]
                            if ress[0] == 2:  # 全体
                                gemallpercent += ress[2] / 100
                            elif ress[3] == 1:
                                gemnum += ress[2]
                            elif ress[4] == 1:
                                gemsinglepercent += ress[2] / 100
                            elif ress[4] == 3:
                                if ress[1] in (11, 12):
                                    gemskill = 1

                    unit_cur.execute(
                        "SELECT `unit_level_up_pattern_id`,`smile_max`,`pure_max`,`cool_max` FROM unit_m WHERE `unit_id` = {}".format(
                            res2['unit_id']))
                    res_unit_m = unit_cur.fetchone()
                    pattern_id = res_unit_m[0]
                    smile_max = res_unit_m[1]  # 50
                    pure_max = res_unit_m[2]  # 25
                    cool_max = res_unit_m[3]  # 70

                    if smile_max > pure_max:
                        if smile_max > cool_max:
                            smile_max += res2['love']
                        else:
                            cool_max += res2['love']
                    else:
                        if pure_max > cool_max:
                            pure_max += res2['love']
                        else:
                            cool_max += res2['love']

                    unit_cur.execute("""SELECT `hp_diff`,`smile_diff`,`pure_diff`,`cool_diff` 
                    FROM `unit_level_up_pattern_m` WHERE `unit_level_up_pattern_id` = ? AND `unit_level` = ?
                    """, (pattern_id, res2['level']))
                    res_p = unit_cur.fetchone()
                    result.append(OrderedDict([
                        ("smile", smile_max - res_p[1]),
                        ("pure", pure_max - res_p[2]),
                        ("cool", cool_max - res_p[3]),
                        ("cardid", res2['unit_number']),
                        ("skilllevel", res2['unit_skill_level']),
                        ("mezame", res2['is_rank_max']),
                        ("gemnum", int(gemnum)),
                        ("gemsinglepercent", round(gemsinglepercent, 3)),
                        ("gemallpercent", round(gemallpercent, 3)),
                        ("gemskill", gemskill),
                        ("gemacc", gemacc),
                        ("maxcost", capacity)
                    ]))
                    cardview.append(OrderedDict([
                        ('unit_id', res2['unit_id']),
                        ('rank', res2['is_rank_max']),
                        ('level', str(res2['level'])),
                        ('skill_level', str(res2['unit_skill_level'])),
                        ('love', res2['love'])
                    ]))
                    sifstatus.append(OrderedDict([
                        ('love', res2['love']),
                        ('rank', res2['rank']),
                        ('level', res2['level']),
                        ('unit_id', res2['unit_id']),
                        ('unit_skill_level', res2['unit_skill_level']),
                        ('removable', removable)
                    ]))
                break
        return {"result": OrderedDict([
            ('uid', res['uid']),
            ('deck_name', deckname),
            ('update_time', res['update_time']),
            # ('llhelperString', parse.quote(json.dumps(result, separators=(',', ':')))),
            ('llhelperString', json.dumps(result, separators=(',', ':'))),
            ('cardviewerString', json.dumps(cardview, separators=(',', ':'))),
            ('sifstatusString', json.dumps(sifstatus, separators=(',', ':')))
        ])}


from get_cookies import get_deck_code


class CardviewerCode(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('info_string', type=str, required=True, help='必须给出卡组信息')

    def post(self):
        args = self.parser.parse_args(strict=True)
        return {
            'result': {
                'code': get_deck_code(args['info_string'])
            }
        }

    get = post


class UnitsExport(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('rarity', type=str, help='稀有度 2,3,5,4 R,SR,SSR,UR')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        unit_cur = unit_db.cursor()
        args = self.parser.parse_args(strict=True)
        rarity = []
        if args['rarity']:
            for x in args['rarity'].split(','):
                if int(x) in (2, 3, 4, 5):
                    rarity.append(x)
        else:
            rarity = ['3', '4', '5']
        if len(rarity) == 0:
            return {
                "result": {
                    "mergetoolString": None,
                }
            }

        sql = """ SELECT unit_id,level,love,unit_skill_level,unit_removable_skill_capacity,rarity FROM `unit_unitAll` WHERE `uid` = %s AND `status`=1 AND `rarity` in ({})
                ORDER BY unit_owning_user_id DESC  
                """.format(','.join(rarity))
        cur.execute(sql, args['uid'])
        units = cur.fetchall()
        sql = """ SELECT removable_info FROM `deck_and_removable_Info` WHERE `uid` = %s"""
        cur.execute(sql, args['uid'])
        removable_info = cur.fetchone()['removable_info']
        res = []
        for res2 in units:
            sqlunit_m = "select name,eponym,unit_level_up_pattern_id,smile_max,pure_max,cool_max,default_unit_skill_id,default_leader_skill_id,unit_type_id from unit_m WHERE `unit_id` = {}".format(
                res2['unit_id'])
            unit_cur.execute(sqlunit_m)
            res_unit_m = unit_cur.fetchone()

            pattern_id = res_unit_m[2]
            smile_max = res_unit_m[3]  # 50
            pure_max = res_unit_m[4]  # 25
            cool_max = res_unit_m[5]  # 70
            skill_id = res_unit_m[6]
            leader_skill = res_unit_m[7]
            type_id = res_unit_m[8]
            names = {1: '果', 2: '绘', 3: '鸟', 4: '海', 5: '凛', 6: '姬', 7: '希', 8: '花', 9: '妮',
                     101: '千', 102: '梨', 103: '南', 104: '黛', 105: '曜', 106: '善', 107: '丸', 108: '鞠', 109: '露'}
            tooltype = None
            if 9 >= type_id >= 1:
                tooltype = type_id - 1
            elif 109 >= type_id >= 101:
                tooltype = type_id - 92
            else:
                continue
            name = names[type_id] + '-' + {1: "N", 2: 'R', 3: 'SR', 4: 'UR', 5: 'SSR'}[res2['rarity']] + '' + (
                    res_unit_m[1] or '')

            if smile_max > pure_max:
                if smile_max > cool_max:
                    smile_max += res2['love']
                else:
                    cool_max += res2['love']
            else:
                if pure_max > cool_max:
                    pure_max += res2['love']
                else:
                    cool_max += res2['love']

            unit_cur.execute("""SELECT `smile_diff`,`pure_diff`,`cool_diff` 
                                FROM `unit_level_up_pattern_m` WHERE `unit_level_up_pattern_id` = ? AND `unit_level` = ?
                                """, (pattern_id, res2['level']))
            res_p = unit_cur.fetchone()
            smile = smile_max - res_p[0]
            pure = pure_max - res_p[1]
            cool = cool_max - res_p[2]
            unit_cur.execute(
                "SELECT skill_effect_type,trigger_type FROM unit_skill_m WHERE unit_skill_id = {}".format(skill_id))
            res_skill = unit_cur.fetchone()
            unit_cur.execute(
                "SELECT effect_value,discharge_time,trigger_value,activation_rate FROM unit_skill_level_m WHERE unit_skill_id = ? AND skill_level = ?",
                (skill_id, res2['unit_skill_level']))
            res_skill_value = unit_cur.fetchone()
            et = res_skill[0]
            tt = res_skill[1]
            eft_val = res_skill_value[0]
            eft_time = res_skill_value[1]
            need = res_skill_value[2]
            rate = res_skill_value[3]
            skill_t = 0

            val = 0

            if et == 11:
                val = eft_val
                if tt in (3, 4):
                    skill_t = 1
                elif tt == 6:
                    skill_t = 2
                elif tt == 1:
                    skill_t = 3
                elif tt == 5:
                    skill_t = 4
                elif tt == 12:
                    skill_t = 5
            elif et == 9:
                val = eft_val
                if tt in (3, 4):
                    skill_t = 6
                elif tt == 1:
                    skill_t = 7
                elif tt == 6:
                    skill_t = 8
            elif et in (4, 5):
                val = eft_time
                if tt in (3, 4):
                    skill_t = 9
                elif tt == 1:
                    skill_t = 10
            leader_sub = 0
            leader_main = 0
            if leader_skill:
                unit_cur.execute(
                    "SELECT effect_value FROM unit_leader_skill_m WHERE unit_leader_skill_id = {}".format(leader_skill))
                res_lead_main = unit_cur.fetchone()[0]
                unit_cur.execute(
                    "SELECT member_tag_id,effect_value FROM unit_leader_skill_extra_m WHERE unit_leader_skill_id = {}".format(
                        leader_skill))
                lsub = unit_cur.fetchone()
                leader_main = {0: 0, 9: 1, 12: 2, 7: 3, 6: 4, 3: 5}[res_lead_main]
                if lsub:

                    if lsub[0] in (4, 5):
                        if lsub[1] == 3:
                            leader_sub = 1
                        elif lsub[1] == 1:
                            leader_sub = 4
                    elif lsub[0] in (1, 2, 3):
                        if lsub[1] == 6:
                            leader_sub = 2
                        elif lsub[1] == 2:
                            leader_sub = 5
                    elif lsub[0] in (6, 7, 8, 9, 10, 11):
                        if lsub[1] == 6:
                            leader_sub = 3
                        elif lsub[1] == 2:
                            leader_sub = 6

                    pass
                else:
                    leader_sub = 0

            unit_line = [tooltype, name[:15], smile, pure, cool, skill_t, need, val, rate / 100, leader_main,
                         leader_sub,
                         res2['unit_removable_skill_capacity'], '']
            res.append("\t".join([str(x) for x in unit_line]))
        skill_a = ['-2'] + ['0'] * 39
        if removable_info:
            for sk in json.loads(removable_info)['owning_info']:
                skid = sk['unit_removable_skill_id']
                amount = sk['total_amount']

                skill_a[position(skid)] = str(amount if amount < 9 else 9)
            res.append(' '.join(skill_a))
        else:
            res.append("-2 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9")

        return {
            "result": {
                "mergetoolString": '\r\n'.join(res),
            }
        }


def position(x):
    row = (x - 1) % 3
    col = (x - 1) // 3 + 1
    if 2 >= col >= 1:
        return row * 10 + col
    elif 8 >= col >= 3:
        return row * 10 + col + 2
    elif 10 >= col >= 9:
        return row * 10 + col - 6
    elif 13 >= col >= 11:
        if row == 0:
            return 23 + col
        elif row == 1:
            return 20 + col
        elif row == 2:
            return 26 + col
    return False


class EffortBoxLog(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        sql = """
                SELECT * FROM `effort_point_box` WHERE `uid` = %s
                ORDER BY update_time DESC,id DESC  LIMIT %s OFFSET %s
                """
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        boxs = cur.fetchall()
        sqlcnt = """
        SELECT count(*) FROM `effort_point_box` WHERE uid=%s
        """
        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        unit_cur = unit_db.cursor()
        res = []
        for box in boxs:
            box['rewards'] = []
            box['update_time'] = datetime.datetime.fromtimestamp(box['update_time']).isoformat()
            for itemid, itemtype, itemamount in zip(box['rewards_item_id'].split(','),
                                                    box['rewards_add_type'].split(','),
                                                    box['rewards_amount'].split(',')):
                itemtype = int(itemtype)
                itemid = itemid and int(itemid)
                itemamount = int(itemamount)
                reward = {
                    'type': itemtype,
                    'item_id': itemid,
                    'amount': itemamount,
                    'name': str(itemtype) + '-' + str(itemid),
                    'asset': None
                }
                if itemtype == 5500:
                    reward['name'], reward['asset'] = siskill[itemid][6:8]
                elif itemtype == 3000:
                    reward['name'] = 'G'
                elif itemtype == 3002:
                    reward['name'] = '友情pt'
                elif itemtype == 3006:
                    reward['name'] = '贴纸'
                elif itemtype == 1001 and itemid:
                    unit_cur.execute("SELECT name,rarity from unit_m WHERE unit_id= {}".format(itemid))
                    res_unit_m = unit_cur.fetchone()
                    reward['name'] = {1: "N", 2: 'R', 3: 'SR', 4: 'UR', 5: 'SSR'}[res_unit_m[1]] + ' ' + res_unit_m[0]
                elif itemtype == 3001:
                    reward['name'] = 'Loveca'
                box['rewards'].append(reward)
            del box['rewards_item_id'], box['rewards_add_type'], box['rewards_amount'], box['uid']
            res.append(box)
        pub_asset = {
            '3000': 'assets/image/ui/common/com_icon_03.png',
            '3002': 'assets/image/ui/item/com_icon_32.png',
            '3006': 'assets/image/ui/exchange/ex_icon_03.png',
            '5500': 'assets/image/ui/common/com_icon_70.png',
            '1001': ''
        }
        return {
            "result": {
                "uid": args['uid'],
                "boxs": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count,
                "pub_asset": pub_asset
            }
        }


class UnitsExportJSON(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('full', type=bool)

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args()
        uid = args['uid']
        try:
            full = args['full']
        except KeyError:
            full = False
        sql = """
        SELECT * FROM `deck_and_removable_Info` WHERE `uid` = %s
        """
        cur.execute(sql, uid)
        res = cur.fetchone()
        update_time = datetime.datetime.fromtimestamp(res['update_time']).isoformat()

        unit_info = res['unit_info'] and json.loads(res['unit_info'])
        removable_info = json.loads(res['removable_info']) if res['removable_info'] else {
            'equipment_info': {},
            'owning_info': {}
        }

        if not full:
            removable_info['equipment_info'] = {}
            deck_info = []
        else:
            deck_info = json.loads(res['deck_info']) if res['deck_info'] else []

        return {"result": OrderedDict([
            ('uid', uid),
            ('update_time', update_time),
            ('JSONString', json.dumps(OrderedDict([
                ('unit_info', unit_info),
                ('removable_info', removable_info),
                ('deck_info', deck_info),

            ]), separators=(',', ':')))
        ])}


class EventChallengeLog(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')
    parser.add_argument('eventid', type=int, help='为event_id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        eventq = "AND `event_id` ='{}'"
        eventqfmt = '\n'
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        sql = """
        SELECT pair_id,round,update_time,live_setting_id,live_difficulty_id,is_random,score,
         perfect_cnt,great_cnt,good_cnt,bad_cnt,miss_cnt,max_combo,event_point,event_id,judge_card
         FROM `event_challenge` WHERE `uid` = %s {}
         ORDER BY id DESC  LIMIT %s OFFSET %s
                                                """
        sqlcnt = """
                                                SELECT count(*) FROM `event_challenge` WHERE uid=%s {}
                                                """
        if args['eventid'] and args['eventid'] > 0:
            eventqfmt = eventq.format(args['eventid'])
        sql = sql.format(eventqfmt)
        sqlcnt = sqlcnt.format(eventqfmt)
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        lives = cur.fetchall()

        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in lives:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            res.append(x)
        return {
            "result": {
                "lives": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count
            }
        }


class EventChallengePairs(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')
    parser.add_argument('eventid', type=int, help='为event_id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        eventq = "AND `event_id` ='{}'"
        eventqfmt = '\n'
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        sql = """SELECT  
        uid, pair_id, curr_round, finalized, lp_add, player_exp, game_coin, event_point, rarity_3_cnt, rarity_2_cnt, 
        rarity_1_cnt, after_event_point, added_event_point, round_setid_1, round_setid_2, round_setid_3, round_setid_4, 
        round_setid_5, update_time, event_id, total_event_point, ticket_add, coin_cost, skill_exp_add
        FROM `event_challenge_pairs` WHERE `uid` = %s {}
        ORDER BY `id` DESC  LIMIT %s OFFSET %s
        """
        sqlcnt = " SELECT count(*) FROM `event_challenge_pairs` WHERE uid=%s {} "
        if args['eventid'] and args['eventid'] > 0:
            eventqfmt = eventq.format(args['eventid'])
        sql = sql.format(eventqfmt)
        sqlcnt = sqlcnt.format(eventqfmt)
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        pairs = cur.fetchall()

        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in pairs:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            x['round_setids'] = []
            for i in range(1, 6):
                round_key = 'round_setid_' + str(i)
                x['round_setids'].append(x[round_key])
                del x[round_key]
            res.append(x)
        return {
            "result": {
                "pairs": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count
            }
        }


class EventChallengeLive(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('eventid', type=int, required=True, help='为event_id')
    parser.add_argument('pairid', type=int, help='为序号')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)

        if args['pairid'] == -1 or not args['pairid']:
            cur.execute(
                "select * from event_challenge_pairs where uid= {} AND event_id={}  ORDER BY id DESC LIMIT 1".format(
                    args['uid'], args['eventid']
                ))
        else:
            cur.execute(
                "select * from event_challenge_pairs where uid= {} AND event_id={} AND pair_id={} LIMIT 1".format(
                    args['uid'], args['eventid'], args['pairid']
                ))

        res = cur.fetchone()
        if not res:
            return {
                'result': None
            }
        for key, val in res.items():
            if key in ('reward_item_list',):
                res[key] = val and json.loads(val)
        unit_cur = unit_db.cursor()
        rewards = []

        pub_asset = {
            3000: 'assets/image/ui/common/com_icon_03.png',
            3002: 'assets/image/ui/item/com_icon_32.png',
            3006: 'assets/image/ui/exchange/ex_icon_03.png',
            5500: 'assets/image/ui/common/com_icon_70.png',
            1000: 'assets/image/ui/item/com_icon_33.png',
            1001: None
        }
        if res['reward_item_list']:
            for item in res['reward_item_list']:
                itemtype = int(item['add_type'])
                try:
                    itemid = item['item_id']
                except KeyError:
                    itemid = item['unit_id']
                itemamount = item['amount']
                reward = {
                    'rarity': item['rarity'],
                    'type': itemtype,
                    'item_id': itemid,
                    'amount': itemamount,
                    'name': str(itemtype) + '-' + str(itemid),
                    'asset': pub_asset[itemtype]
                }
                if itemtype == 5500:
                    reward['name'], reward['asset'] = siskill[itemid][6:8]
                elif itemtype == 3000:
                    reward['name'] = 'G'
                elif itemtype == 3002:
                    reward['name'] = '友情pt'
                elif itemtype == 3006:
                    reward['name'] = '贴纸'
                elif itemtype == 1001 and itemid:
                    unit_cur.execute("SELECT name,rarity from unit_m WHERE unit_id= {}".format(itemid))
                    res_unit_m = unit_cur.fetchone()
                    reward['name'] = {1: "N", 2: 'R', 3: 'SR', 4: 'UR', 5: 'SSR'}[res_unit_m[1]] + ' ' + res_unit_m[0]
                elif itemtype == 1000:
                    reward['name'] = '招募券'
                elif itemtype == 3001:
                    reward['name'] = 'Loveca'
                rewards.append(reward)
        else:
            rewards = None

        cur.execute('select * from event_challenge WHERE uid={} AND pair_id={} AND event_id={} LIMIT 5'.format(
            res['uid'], res['pair_id'], res['event_id']
        ))
        res_lives = cur.fetchall()
        res['round_setids'] = []
        res['lives'] = [None] * 5
        for reslive in res_lives:
            reslive['update_time'] = timeisofmt(reslive['update_time'])
            for key, val in reslive.items():
                if key in ('bonus_list', 'mission_result', 'reward_rarity_list', 'event_challenge_item_ids'):
                    reslive[key] = val and json.loads(val)
            fes_db = sqlite3.connect("./db/challenge/challenge.db_", check_same_thread=False)
            event_challenge_items = []
            for item_id in reslive['event_challenge_item_ids']:
                fes_cur = fes_db.cursor()
                fes_cur.execute(
                    "select name,selected_item_asset,bonus_param,description from event_challenge_item_m WHERE event_challenge_item_id = {}".format(
                        item_id))
                res_f = fes_cur.fetchone()
                fes_item = {
                    'item_id': item_id,
                    'name': res_f[0],
                    'desc': res_f[3],
                    'asset': res_f[1],
                    'bonus_param': round(res_f[2] / 100, 2) if res_f[2] >= 100 else res_f[2]
                }
                event_challenge_items.append(fes_item)
            del reslive['event_challenge_item_ids']
            mission_result = []
            for mission in reslive['mission_result']:
                mission['mission'] = {
                    1000: "SCORE S",
                    2000: "FULL COMBO",
                    4000: "体力 MAX"
                }[mission['type']]
                if mission['bonus_type'] == 3060:
                    mission['bonus_type'] = '3060' + str(mission['bonus_param'])
                mission['bonus'] = {
                    1010: "将消耗LP减少%s" % str(mission['bonus_param']),
                    2010: "提升特技的发动概率",
                    2020: "提升点击时的分数",
                    2030: "%s次内将GOOD、BAD强化为PERFECT" % str(mission['bonus_param']),
                    3010: "可以获得的EXP变为%s倍" % str(mission['bonus_param']),
                    3020: "可以获得的G变为%s倍" % str(mission['bonus_param']),
                    3030: "可以获得的活动点变为%s倍" % str(mission['bonus_param']),
                    3040: "提升奖励获得概率",
                    3041: "提升金奖励获得概率",
                    3042: "提升银奖励获得概率",
                    3043: "提升金、银奖励获得概率",
                    3050: "回复LP%s" % str(mission['bonus_param']),
                    '30601': "确定获得1个\n铜奖励",
                    '30602': "确定获得1个\n银奖励",
                    '30603': "追加1个\n金奖励"
                }[mission['bonus_type']]
            reslive['challenge_items'] = event_challenge_items
            res['lives'][reslive['round'] - 1] = reslive

        for i in range(1, 6):
            round_key = 'round_setid_' + str(i)
            res['round_setids'].append(res[round_key])
            del res[round_key]

        res['reward_item_list'] = rewards
        res['update_time'] = timeisofmt(res['update_time'])

        return {
            'result': res
        }


class EventChallengeView(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('eventid', type=int, required=True, help='为event_id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        uid = args['uid']
        event_id = args['eventid']
        sql1 = "SELECT sum(lp_add),max(total_event_point),max(pair_id),sum(ticket_add),sum(coin_cost)," \
               "sum(skill_exp_add),sum(player_exp),sum(game_coin),sum(coin_reward),avg(event_point) FROM `event_challenge_pairs` WHERE uid= %s AND " \
               "event_id=%s" % (
                   uid, event_id)
        sql2 = "SELECT max(score),count(id),avg(score),avg(perfect_cnt/(" \
               "perfect_cnt+great_cnt+good_cnt+bad_cnt+miss_cnt)),avg(event_point) FROM `event_challenge` WHERE uid=%s AND " \
               "event_id=%s" % (
                   uid, event_id)
        sql3 = "SELECT sum(`rarity_3_cnt`),sum(`rarity_2_cnt`),sum(`rarity_1_cnt`) FROM `event_challenge_pairs` WHERE " \
               "uid= %s AND finalized = 1 AND event_id=%s" % (
                   uid, event_id)
        cur.execute(sql1)
        res_1 = cur.fetchone()
        cur.execute(sql2)
        res_2 = cur.fetchone()
        cur.execute(sql3)
        res_3 = cur.fetchone()
        cur.execute(
            "SELECT round,combo_rank,count(*) AS cnt FROM `event_challenge` WHERE uid = {} AND event_id={} GROUP BY "
            "combo_rank,round".format(
                uid, event_id))
        count_up = 0
        count_down = 0
        cnt_combo_r = {x: [0, 0] for x in range(1, 6)}
        basic_pt = (0, 301, 320, 339, 358, 377)
        combo_multiple = (1, 1.08, 1.06, 1.04, 1.02, 1)
        for roundn, combo_r, cnt in cur.fetchall():
            if 5 >= roundn >= 0:
                pass
            else:
                continue
            pt = basic_pt[roundn]
            mtp = combo_multiple[combo_r]
            up = round(pt * mtp) * cnt
            down = cnt * pt
            count_up += up
            count_down += down
            cnt_combo_r[roundn][0] += mtp * cnt
            cnt_combo_r[roundn][1] += cnt

        coefficient = count_up / count_down if count_down else 0
        avg_combo_m = {}
        for k, combom in cnt_combo_r.items():
            avg = combom[1] and round(combom[0] / combom[1], 3)
            avg_combo_m[k] = avg
        # print(res_2)
        coinfmt = lambda num: "{} W".format(round(int(num) / 10000, 1))
        return {
            'result': {
                "total_lp_gain": int(res_1[0]) if res_1[0] is not None else 0,
                "total_ticket_gain": int(res_1[3]) if res_1[3] is not None else 0,
                "total_coin_cost": coinfmt(res_1[4]) if res_1[4] is not None else 0,
                "total_exp_gain": int(res_1[5]) if res_1[5] is not None else 0,
                "total_player_exp": int(res_1[6]) if res_1[6] is not None else 0,
                "total_game_coin": coinfmt(res_1[7]) if res_1[7] is not None else 0,
                "total_reward_coin": coinfmt(res_1[8]) if res_1[8] is not None else 0,
                "total_event_point": int(res_1[1]) if res_1[1] is not None else 0,
                "total_pairs": int(res_1[2]) if res_1[2] is not None else 0,
                "high_score": int(res_2[0]) if res_2[0] is not None else 0,
                "total_rounds": int(res_2[1]) if res_2[1] is not None else 0,
                "rarity_3_cnt": int(res_3[0]) if res_3[0] is not None else 0,
                "rarity_2_cnt": int(res_3[1]) if res_3[1] is not None else 0,
                "rarity_1_cnt": int(res_3[2]) if res_3[2] is not None else 0,
                "avg_score": round(res_2[2]) if res_2[2] is not None else 0,
                "avg_perfect_rate": round(float(res_2[3]), 3) if res_2[3] is not None else 0,
                "avg_pair_event_pt": round(res_1[9]) if res_1[9] is not None else 0,
                "avg_round_event_pt": round(res_2[4]) if res_2[4] is not None else 0,
                "combo_multiple": round(coefficient, 3),
                "combo_multiple_r": avg_combo_m
            }
        }


class EventFestivalInfo(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')
    parser.add_argument('eventid', type=int, help='为event_id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 20
        eventq = "AND `event_id` ='{}'"
        eventqfmt = '\n'
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        sql = """
        SELECT pair_id,update_time,song_set_ids,song_diff_ids,score,total_combo,
         perfect_cnt,great_cnt,good_cnt,bad_cnt,miss_cnt,max_combo,added_event_point,event_id,judge_card
         FROM `event_festival` WHERE `uid` = %s AND `status`=1 {}
         ORDER BY `id` DESC  LIMIT %s OFFSET %s
                                                """
        sqlcnt = """
                 SELECT count(*) FROM `event_festival` WHERE uid=%s {}
                                                """
        if args['eventid'] and args['eventid'] > 0:
            eventqfmt = eventq.format(args['eventid'])
        sql = sql.format(eventqfmt)
        sqlcnt = sqlcnt.format(eventqfmt)
        cur.execute(sql, (args['uid'], limit, (page - 1) * limit))
        lives = cur.fetchall()

        cur.execute(sqlcnt, args['uid'])
        count = cur.fetchone()['count(*)']
        res = []
        for x in lives:
            x['update_time'] = timeisofmt(x['update_time'])
            x['song_diff_ids'] = json.loads(x['song_diff_ids'])
            x['song_set_ids'] = json.loads(x['song_set_ids'])
            res.append(x)

        return {
            "result": {
                "lives": res,
                "curr_page": page,
                "all_page": int(count / limit) + 1 if (count % limit) else int(count / limit),
                "limit": limit,
                "count": count
            }
        }


class EventFestivalLive(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('eventid', required=True, type=int, help='为event_id')
    parser.add_argument('pairid', type=int, help='为序号')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)

        if args['pairid'] == -1 or not args['pairid']:
            # AND `status`=1
            cur.execute(
                "select * from event_festival where uid= {} AND event_id={} AND `status`=1 ORDER BY id DESC LIMIT 1".format(
                    args['uid'], args['eventid'], args['pairid']
                ))
        else:
            cur.execute(
                "select * from event_festival where uid= {} AND event_id={} AND pair_id={} AND `status`=1 LIMIT 1".format(
                    args['uid'], args['eventid'], args['pairid']
                ))

        res = cur.fetchone()
        if not res:
            return {
                'result': None
            }
        for key, val in res.items():
            if key in ('reward_items', 'guest_bonus', 'song_set_ids', 'song_diff_ids', 'event_festival_item_ids',
                       'sub_guest_bonus', 'sub_bonus_flag'):
                res[key] = val and json.loads(val)
        unit_cur = unit_db.cursor()
        rewards = []
        guest_bonus = []
        if res['sub_guest_bonus'] and res['sub_bonus_flag']:
            for main, sub, flag in zip(res['guest_bonus'], res['sub_guest_bonus'], res['sub_bonus_flag']):
                if flag:
                    for key, val in sub.items():
                        if key in main:
                            main[key] = val
                    guest_bonus.append(main)
                else:
                    guest_bonus.append(main)
        res['guest_bonus'] = guest_bonus
        del res['sub_guest_bonus'], res['sub_bonus_flag']
        pub_asset = {
            3000: 'assets/image/ui/common/com_icon_03.png',
            3002: 'assets/image/ui/item/com_icon_32.png',
            3006: 'assets/image/ui/exchange/ex_icon_03.png',
            5500: 'assets/image/ui/common/com_icon_70.png',
            1000: 'assets/image/ui/item/com_icon_33.png',
            1001: None
        }
        if res['reward_items']:
            for item in res['reward_items']:
                itemtype = int(item['add_type'])
                try:
                    itemid = item['item_id']
                except KeyError:
                    itemid = item['unit_id']
                itemamount = item['amount']
                reward = {
                    'rarity': item['rarity'],
                    'type': itemtype,
                    'item_id': itemid,
                    'amount': itemamount,
                    'name': str(itemtype) + '-' + str(itemid),
                    'asset': pub_asset[itemtype]
                }
                if itemtype == 5500:
                    reward['name'], reward['asset'] = siskill[itemid][6:8]
                elif itemtype == 3000:
                    reward['name'] = 'G'
                elif itemtype == 3002:
                    reward['name'] = '友情pt'
                elif itemtype == 3006:
                    reward['name'] = '贴纸'
                elif itemtype == 1001 and itemid:
                    unit_cur.execute("SELECT name,rarity from unit_m WHERE unit_id= {}".format(itemid))
                    res_unit_m = unit_cur.fetchone()
                    reward['name'] = {1: "N", 2: 'R', 3: 'SR', 4: 'UR', 5: 'SSR'}[res_unit_m[1]] + ' ' + res_unit_m[0]
                elif itemtype == 1000:
                    reward['name'] = '招募券'
                elif itemtype == 3001:
                    reward['name'] = 'Loveca'
                rewards.append(reward)
        else:
            rewards = [None, None, None]
        fes_db = sqlite3.connect("./db/event/festival.db_", check_same_thread=False)
        event_festival_items = []
        for item_id in res['event_festival_item_ids']:
            fes_cur = fes_db.cursor()
            fes_cur.execute(
                "select name,selected_item_asset,bonus_param,description from event_festival_item_m WHERE event_festival_item_id = {}".format(
                    item_id))
            res_f = fes_cur.fetchone()
            fes_item = {
                'item_id': item_id,
                'name': res_f[0],
                'desc': res_f[3],
                'asset': res_f[1],
                'bonus_param': round(res_f[2] / 100, 2) if res_f[2] >= 100 else res_f[2]
            }
            event_festival_items.append(fes_item)
        del res['event_festival_item_ids']
        res['festival_items'] = event_festival_items
        res['reward_items'] = rewards
        res['update_time'] = timeisofmt(res['update_time'])

        return {
            'result': res
        }


from combo_weight import medley_fes


class EventFestivalLast(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)

        cur.execute("select last_song_set_ids,update_time from event_festival_last WHERE `uid`={}".format(args['uid']))
        res = cur.fetchone()
        if not res:
            return {
                'result': None
            }
        set_ids = json.loads(res['last_song_set_ids'])
        res_weight = medley_fes(set_ids)
        res_weight['update_time'] = timeisofmt(res['update_time'])
        res_weight['song_set_ids'] = set_ids
        return {
            'result': res_weight
        }


from combo_coefficient import combo_m


class EventFestivalView(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', type=int, required=True, help='必须给出用户 UID')
    parser.add_argument('eventid', type=int, help='为event_id')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        uid = args['uid']
        event_id = args['eventid']
        sql1 = "SELECT sum(coin_cost),max(total_event_point),max(pair_id),sum(ticket_add),sum(skill_exp_add),sum(coin_reward) FROM `event_festival` WHERE uid= %s AND event_id=%s" % (
            uid, event_id)
        sql2 = "SELECT max(score),count(id) FROM `event_festival` WHERE uid=%s AND event_id=%s " % (
            uid, event_id)
        sql3 = "SELECT sum(`rarity_3_cnt`),sum(`rarity_2_cnt`),sum(`rarity_1_cnt`),avg(`score`),avg(perfect_cnt/(" \
               "perfect_cnt+great_cnt+good_cnt+bad_cnt+miss_cnt)),avg(added_event_point) FROM `event_festival` WHERE uid= %s AND event_id=%s AND status = 1" % (
                   uid, event_id)
        cur.execute(sql1)
        res_1 = cur.fetchone()
        cur.execute(sql2)
        res_2 = cur.fetchone()
        cur.execute(sql3)
        res_3 = cur.fetchone()
        cur.execute(
            "SELECT sum(combo_rank)/count(*) AS cnt FROM `event_festival` WHERE uid = {} AND event_id={} AND status = 1".format(
                uid, event_id))
        res_combo_rank = cur.fetchone()
        avg_combo_rank = float(res_combo_rank[0]) if res_combo_rank and res_combo_rank[0] else 5
        coefficient = combo_m(avg_combo_rank)

        return {
            'result': {
                "total_coin_cost": "{} W".format(round(int(res_1[0]) / 10000, 1)) if res_1[0] is not None else 0,
                "total_reward_coin": "{} W".format(round(int(res_1[5]) / 10000, 1)) if res_1[5] is not None else 0,
                "total_ticket_gain": int(res_1[3]) if res_1[3] is not None else 0,
                "total_exp_gain": int(res_1[4]) if res_1[4] is not None else 0,
                "total_event_point": int(res_1[1]) if res_1[1] is not None else 0,
                "max_pair": int(res_1[2]) if res_1[2] is not None else 0,
                "high_score": int(res_2[0]) if res_2[0] is not None else 0,
                "total_rounds": int(res_2[1]) if res_2[1] is not None else 0,
                "rarity_3_cnt": int(res_3[0]) if res_3[0] is not None else 0,
                "rarity_2_cnt": int(res_3[1]) if res_3[1] is not None else 0,
                "rarity_1_cnt": int(res_3[2]) if res_3[2] is not None else 0,
                "avg_score": round(res_3[3]) if res_3[3] is not None else 0,
                "avg_perfect_rate": round(float(res_3[4]), 3) if res_3[4] is not None else 0,
                "avg_round_event_pt": round(res_3[5]) if res_3[5] is not None else 0,
                "combo_multiple": round(coefficient, 3),
            }
        }




#
# def timeisofmt(timestamp):
#     return datetime.datetime.fromtimestamp(timestamp).isoformat()


# api.decorators = [cors.crossdomain(origin='*')]

if __name__ == '__main__':
    debug = False
    if debug:
        api.decorators = [cors.crossdomain(origin='*')]
    api.add_resource(SearchUser, '/llproxy/userSearch/')
    api.add_resource(UserInfo, '/llproxy/userInfo/')
    api.add_resource(UnitsInfo, '/llproxy/unitsInfo/')
    api.add_resource(LiveInfo, '/llproxy/liveInfo/')
    api.add_resource(SecretBoxLog, '/llproxy/secretBoxLog/')
    api.add_resource(EventMarathonInfo, '/llproxy/eventMarathon/')
    api.add_resource(EventChallengeLog, '/llproxy/eventChallenge/')
    api.add_resource(EventChallengeLive, '/llproxy/eventChallengeLive/')
    api.add_resource(EventChallengePairs, '/llproxy/eventChallengePairs/')
    api.add_resource(EventFestivalInfo, '/llproxy/eventFestival/')
    api.add_resource(EventFestivalLive, '/llproxy/eventFestivalLive/')
    api.add_resource(EventFestivalLast, '/llproxy/eventFestivalLast/')
    api.add_resource(EventChallengeView, '/llproxy/eventChallengeView/')
    api.add_resource(EventFestivalView, '/llproxy/eventFestivalView/')
    api.add_resource(EventBattle, '/llproxy/eventBattle/')
    api.add_resource(DeckInfo, '/llproxy/deckInfo/')
    api.add_resource(DeckExport, '/llproxy/deckExport/')
    api.add_resource(CardviewerCode, '/llproxy/cardViewerCode/')
    api.add_resource(UnitsExport, '/llproxy/unitsExport/')
    api.add_resource(EffortBoxLog, '/llproxy/effortBoxLog/')
    api.add_resource(UnitsExportJSON, '/llproxy/unitsExportJSON/')
    api.add_resource(EventList, '/llproxy/eventList/')
    api.add_resource(LovecaRecovery, '/llproxy/lovecaRecovery/')
    api.add_resource(EventQuest, '/llproxy/eventQuest/')
    api.add_resource(LLproxyOshirase, '/llproxy/oshirase/')
    app.run(debug=debug)
