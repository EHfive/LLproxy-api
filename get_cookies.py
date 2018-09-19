import requests
import json
import urllib.parse


def get_deck_code(deck):
    url = 'http://c.dash.moe/editDeck/new'
    if type(deck) is str:
        data = {
            'deck': deck
        }
    elif type(deck) is dict:
        data = {
            'deck': json.dumps(deck)
        }
    else:
        return False
    resp = requests.get(url, data=data, allow_redirects=False)

    try:
        code = urllib.parse.unquote(resp.cookies['deck'])
    except KeyError:
        return False
    else:
        # print(code)
        return code


if __name__ == "__main__":
    str = """[{"unit_id":985,"rank":1,"level":"80","skill_level":"3","love":500},{"unit_id":958,"rank":1,"level":"100","skill_level":"1","love":1000},{"unit_id":735,"rank":0,"level":"80","skill_level":"1","love":500},{"unit_id":866,"rank":1,"level":"80","skill_level":"1","love":500},{"unit_id":330,"rank":0,"level":"80","skill_level":"1","love":500},{"unit_id":940,"rank":0,"level":"70","skill_level":"1","love":375},{"unit_id":156,"rank":0,"level":"80","skill_level":"1","love":500},{"unit_id":986,"rank":1,"level":"90","skill_level":"1","love":750},{"unit_id":1039,"rank":1,"level":"80","skill_level":"3","love":500}]"""

    get_deck_code(json.loads(str))
