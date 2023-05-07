import atexit
import datetime
import json
import re
from time import time, sleep
from typing import List

import requests
from apscheduler.schedulers.background import BackgroundScheduler

headers = {
    'content-type': 'application/json',
    'user-agent': 'liberatorist@gmail.com',
}
cookies = {}
current_states_get = ''
current_states_post = ''
policies_get = '12:4:60,16:12:60'
policies_post = '8:10:60,15:60:120,60:300:1800'
current_league = ''


with open('data/mappings.json', 'r') as file:
    mappings = json.loads(file.read())
    templar2num = mappings['templar2num']
    num2templarmod = mappings['num2templarmod']
    modtranslation2num = mappings['modtranslation2num']
    num2explicitmod = mappings['num2explicitmod']

with open('data/useful_seeds', 'r') as file:
    useful_seeds = set(json.loads(file.read()))

class Jewel:
    seed: int
    templar: int
    price: int
    mod1: int
    mod2: int

    def __init__(self, trade_result):
        m = re.match(r'Carved to glorify (\d+) new faithful converted by High Templar (.*)\n', trade_result['item']['explicitMods'][0])
        seed, templar = m.group(1), m.group(2)
        self.seed = int(seed)
        self.templar = templar2num[templar]
        self.price = get_price_in_chaos(trade_result)
        self.mod1 = modtranslation2num[trade_result['item']['explicitMods'][1]]
        self.mod2 = modtranslation2num[trade_result['item']['explicitMods'][2]]
        

    def to_trade_filter_element(self):
        return {
            'id': num2templarmod[self.templar],
            'value': {
                'min': self.seed,
                'max': self.seed
            },
            'disabled': False
        }

def set_league():
    response = make_request('https://api.pathofexile.com/leagues', 'GET')
    for league in response.json():
        if league['rules'] == [] and 'This is the default Path of Exile league' in league['description']:
            global current_league
            current_league = league['id']
            return


def get_price_in_chaos(result):
    price_data = result['listing']['price']
    div_price = 220
    if price_data['currency'] == 'chaos':
        return round(price_data['amount'])
    elif price_data['currency'] == 'divine':
        return round(price_data['amount'] * div_price)
    return 9999999




def wait_for_request(policies, current_states):
    if not current_states:
        return
    for policy, state in zip(reversed(policies.split(',')), reversed(current_states.split(','))):
        request_limit, interval, _ = policy.split(':')
        current_hits = state.split(':')[0]
        if int(current_hits) >= int(request_limit) - 1:
            sleep(int(interval))
            return


def make_request(url, method, data=None):
    if method == 'GET':
        global policies_get, current_states_get
        wait_for_request(policies_get, current_states_get)
        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code > 399:
            raise ConnectionError(response.text)
        policies_get, current_states_get = response.headers['X-Rate-Limit-Ip'], response.headers['X-Rate-Limit-Ip-State']
    elif method == 'POST':
        global policies_post, current_states_post
        wait_for_request(policies_post, current_states_post)
        response = requests.post(url, headers=headers, cookies=cookies, json=data)
        if response.status_code > 399:
            raise ConnectionError(response.text)
        policies_post, current_states_post = response.headers['X-Rate-Limit-Ip'], response.headers['X-Rate-Limit-Ip-State']
    else:
        return None
    return response


def trade_fetch(post_response):
    url_hash = post_response.json()['id']
    results = post_response.json()['result']
    for items in [','.join(results[n: n + 10]) for n in range(0, len(results), 10)]:
        url = f'https://www.pathofexile.com/api/trade/fetch/{items}?query={url_hash}'
        response = make_request(url, 'GET')
        for result in response.json()['result']:
            yield result


def make_post_request(seed_range, mods):
    query_data = {
        'query':{
            'status':{
                'option':'online'
            },
            'stats':[
                {
                    'type':'and',
                    'filters':[
                    {
                        'id':  num2explicitmod[modtranslation2num[mod]]
                    } for mod in mods
                    ]
                },
                {
                    'filters':[
                    {
                        'id':'explicit.pseudo_timeless_jewel_avarius',
                        'value':{
                            'min':seed_range[0],
                            'max':seed_range[1]
                        },
                        'disabled':False
                    },
                    {
                        'id':'explicit.pseudo_timeless_jewel_dominus',
                        'value':{
                            'min':seed_range[0],
                            'max':seed_range[1]
                        },
                        'disabled':False
                    },
                    {
                        'id':'explicit.pseudo_timeless_jewel_maxarius',
                        'value':{
                            'min':seed_range[0],
                            'max':seed_range[1]
                        },
                        'disabled':False
                    }
                    ],
                    'type':'count',
                    'value':{
                    'min':1
                    }
                }
            ]
        },
        'sort':{
            'price':'asc'
        }
    }
    url = f'https://www.pathofexile.com/api/trade/search/{current_league}'
    return make_request(url, 'POST', query_data)


def generate_trade_link(jewels: List[Jewel], mods):
    query_data = {
        'query':{
            'status':{
                'option':'online'
            },
            'stats':[
                {
                    'type':'and',
                    'filters':[
                    {
                        'id':  num2explicitmod[modtranslation2num[mod]]
                    } for mod in mods
                    ]
                },
                {
                    'filters':[
                        jewel.to_trade_filter_element() for jewel in [j for j in jewels if j.seed in useful_seeds][:35]
                    ],
                    'type':'count',
                    'value':{
                    'min':1
                    }
                }
            ]
        },
        'sort':{
            'price':'asc'
        }
    }
    url = f'https://www.pathofexile.com/api/trade/search/{current_league}'
    response = make_request(url, 'POST', query_data)
    return  f'https://www.pathofexile.com/trade/search/{current_league}/{response.json()["id"]}'


def crawl_trade(mods, num_splits):
    jewels = []
    for seed_range in [(round(2000 + k * 8000 / num_splits), round(2000 + (k+1) * 8000 / num_splits)) for k in range(0, num_splits)]:
        post_response = make_post_request(seed_range, mods)
        for result in trade_fetch(post_response):
            jewels.append(Jewel(result))
    return generate_trade_link(sorted(jewels, key=lambda x: x.price), mods)


def grab_jewels():
    set_league()
    generic_link = crawl_trade(['1% increased effect of Non-Curse Auras per 10 Devotion'], 3)
    mana_link = crawl_trade(['1% increased effect of Non-Curse Auras per 10 Devotion', '1% reduced Mana Cost of Skills per 10 Devotion'], 3)
    with open('data/trade_links.json', 'w') as file:
        file.write(json.dumps({'generic_link': generic_link, 'mana_link': mana_link, 'time_since_last_update': str(datetime.datetime.utcnow())}))


def initialize_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=grab_jewels, trigger='interval', minutes=5)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    t = time()
    grab_jewels()
    print(time()-t)