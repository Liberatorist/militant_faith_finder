import json
import re
from datetime import datetime, timedelta

import aiohttp
from flask import Flask, redirect
import requests

app = Flask(__name__)

current_url = None
last_request = datetime.utcnow()
with open("data/useful_seeds") as file:
    useful_seeds = json.loads(file.read())

with open("current_league.txt", "r") as file:
    current_league = file.read()


@app.route('/')
async def endpoint():
    global current_url, last_request
    if current_url is None or datetime.utcnow() - last_request >= timedelta(minutes=1):
        current_url = await grab_jewels()
        last_request = datetime.utcnow()
    return redirect(current_url)


headers = {
    'content-type': 'application/json',
    'user-agent': 'liberatorist@gmail.com',
}


async def grab_jewels():
    with open("data/initial_post_query.json", "r") as file:
        json_data = json.loads(file.read())

    response = requests.post(f'https://www.pathofexile.com/api/trade/search/{current_league}', headers=headers, json=json_data)
    params = {'query': response.json()["id"]}
    results = response.json()["result"]
    count = 0
    non_bricks = []
    async with aiohttp.ClientSession() as session:
        for url in [','.join(results[n: n + 10]) for n in range(0, len(results), 10)]:
            async with session.get(
                f'https://www.pathofexile.com/api/trade/fetch/{url}',
                params=params,
                headers=headers,
            ) as response:
                results = await response.json()
                for result in results["result"]:
                    m = re.match(r"Carved to glorify (\d+) new faithful converted by High Templar (.*)\n",
                                 result["item"]["explicitMods"][0])
                    number, templar = m.group(1), m.group(2)
                    if int(number) in useful_seeds:
                        non_bricks.append((number, templar))
                        count += 1
                        if count == 36:
                            break

    return create_trade_url(non_bricks)


def create_trade_url(non_bricked_jewels):
    json_data = {
        'query': {
            'status': {
                'option': 'onlineleague',
            },
            'stats': [
                {
                    'type': 'and',
                    'filters': [
                        {
                            'id': 'explicit.stat_2585926696',
                            'disabled': False,
                        },
                    ],
                    'disabled': False,
                },
                {
                    'type': 'count',
                    'filters': [
                        {
                            'id': f'explicit.pseudo_timeless_jewel_{templar.lower()}',
                            'disabled': False,
                            'value': {
                                'min': number,
                                'max': number,
                            },
                        }
                        for number, templar in non_bricked_jewels
                    ],
                    'disabled': False,
                    'value': {
                        'min': 1,
                    },
                },
            ],
        },
        'sort': {
            'price': 'asc',
        },
    }
    response = requests.post(f'https://www.pathofexile.com/api/trade/search/{current_league}', headers=headers, json=json_data)
    return f"https://www.pathofexile.com/trade/search/{current_league}/{response.json()['id']}"


if __name__ == '__main__':
    app.run()