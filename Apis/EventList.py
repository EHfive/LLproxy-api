from flask_restful import Resource, reqparse, fields, marshal, marshal_with
import datetime
import time
import pymysql
import sys
from json import loads

sys.path.append("..")
import config as cfg


def timeisofmt(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat()


class EventList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', type=int, help='活动类型')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        etype = args['type']
        typefmt = "where `event_category_id` = %d" % etype if etype else ''
        cur.execute(
            "select * from event_list {} order by id desc".format(typefmt)
        )
        resultlist = []
        fetchres = cur.fetchall()
        curr_event = fetchres[0]['event_id'] if fetchres else None
        curr_time = time.time()
        for event in fetchres:
            resultlist.append({
                "event_id": event['event_id'],
                "title": event['name'],
                "begin": {
                    "time": event['begin_date'].isoformat(),
                    "timestamp": event['begin_time']
                },
                "end": {
                    "time": event['end_date'].isoformat(),
                    "timestamp": event['end_time']
                },
                # "desc": event['description'],
                "mgd": event['mgd'],
                "type": event['event_category_id']
            })
            if event['end_time'] + 3600 * 24 * 4 > curr_time \
                    or abs(event['begin_time'] - curr_time) < 24 * 3600:
                curr_event = event['event_id']
                etype = event['event_category_id']

        return {
            "result": {
                "event_list": resultlist,
                "sltevent": curr_event,
                "sltevent_type": etype
            }
        }


class LovecaRecovery(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('begin', type=int, help='开始时间戳')
    parser.add_argument('end', type=int, help='结束时间戳')
    parser.add_argument('uid', required=True, type=int, help='用户user_id')
    parser.add_argument('group', type=str, help='记录最小范围')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=False)
        curr_year = datetime.datetime.now().year

        begin = args['begin'] or int(datetime.datetime(curr_year, 1, 1).timestamp())
        begin_year = time.localtime(begin).tm_year
        end = args['end'] or int(datetime.datetime(begin_year + 1, 1, 1).timestamp())
        group = pymysql.escape_string(args['group'] or '%Y-%m-%d %H:')
        time.time()
        sql = """\
SELECT count(id) `count`,FROM_UNIXTIME(
update_time,
'{}' #    %Y-%m-%d
) AS `time_range` 
FROM recovery WHERE uid={} AND update_time>={} AND update_time<{}
GROUP BY time_range ORDER BY id DESC""".format(
            group,
            args['uid'],
            begin,
            end
        )

        cur.execute(sql)
        resfetch = cur.fetchall() or []
        return {
            "result": {
                "logs": resfetch,
                "begin": begin,
                "end": end,
                'timefmt': group
            }
        }


class EventBattle(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('uid', required=True, type=int, help='用户user_id')
    parser.add_argument('eventid', required=True, type=int, help='为event_id')
    parser.add_argument('page', type=int, help='分页')
    parser.add_argument('limit', type=int, help='每页项数')

    def get(self):
        args = self.parser.parse_args(strict=True)
        page = 1
        limit = 8
        min_status = 0
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']
        event_id = args['eventid']
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()

        sql = """\
SELECT sm.*,smrm.matching_user FROM `score_match` AS sm JOIN `score_match_rooms` smrm ON \
sm.event_battle_room_id = smrm.event_battle_room_id WHERE sm.uid = %s AND sm.`event_id`= %s AND sm.`status` >= %s \
ORDER BY `id` DESC  LIMIT %s OFFSET %s \
"""

        sqlcnt = """\
SELECT count(*) FROM `score_match` WHERE uid = %s AND `event_id`= %s AND `status` >= %s \
"""
        cur.execute(sql, (args['uid'], event_id, min_status, limit, (page - 1) * limit))
        lives = cur.fetchall()
        cur.execute(sqlcnt, (args['uid'], event_id, min_status))
        count = cur.fetchone()['count(*)']
        res = []

        for x in lives:
            x['update_time'] = datetime.datetime.fromtimestamp(x['update_time']).isoformat()
            x['matching_user'] = x['matching_user'] and loads(x['matching_user'])
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


class EventQuest(Resource):
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
        if args['page'] and args['page'] > 0:
            page = args['page']
        if args['limit'] and args['limit'] > 0:
            limit = args['limit']

        sql = """
                            SELECT * FROM `event_quest` WHERE `uid` = %s AND `event_id` = %s
                            ORDER BY `update_time` DESC  LIMIT %s OFFSET %s
                            """
        sqlcnt = """
                            SELECT count(*) FROM `event_quest` WHERE `uid` = %s AND `event_id` = %s
                            """
        cur.execute(sql, (args['uid'], args['eventid'], limit, (page - 1) * limit))
        lives = cur.fetchall()

        cur.execute(sqlcnt, (args['uid'], args['eventid']))
        count = cur.fetchone()['count(*)']
        res = []
        for x in lives:
            x['update_time'] = timeisofmt(x['update_time'])
            for key in ['bonus', 'live_event_reward_info']:
                x[key] = x[key] and loads(x[key])
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


class LLproxyOshirase(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('level', type=int, default=0, help='必须给出用户 UID')

    def get(self):
        db = pymysql.connect(cfg.DB_HOST, cfg.DB_USER, cfg.DB_PASSWORD, cfg.DB_NAME,
                             charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor)
        cur = db.cursor()
        args = self.parser.parse_args(strict=True)
        level = args['level']
        req_time = time.time()
        if level <= 0:
            sql = "SELECT * FROM oshirase WHERE visible AND (show_forcibly OR (begin_time <= {} AND end_time >= {})) \
                  ORDER BY priority DESC, id ASC".format(
                req_time, req_time)
        elif level == 1:
            sql = "SELECT * FROM oshirase WHERE visible ORDER BY priority DESC, id ASC"
        else:
            sql = "SELECT * FROM oshirase ORDER BY priority DESC, id ASC"
        res = []
        cur.execute(sql)
        for row in cur.fetchall():
            row['update_isotime'] = timeisofmt(row['update_time'])
            res.append(row)

        return {
            "result": res
        }
