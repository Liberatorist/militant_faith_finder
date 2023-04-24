import json
import re
import time
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template
import requests

app = Flask(__name__)

current_url = None
last_request = datetime.utcnow()
with open("data/useful_seeds", "r") as file:
    useful_seeds = json.loads(file.read())

# try:
#     with open("current_league.txt", "r") as file:
#         current_league = file.read()
# except FileNotFoundError:
#     current_league = None
current_league = "Crucible"

@app.route('/')
def endpoint():
    global current_url, last_request
    # if current_league is None:
    #     return render_template("404_page.html"), 404
    # try:
    if current_url is None or datetime.utcnow() - last_request >= timedelta(minutes=1):
        current_url = grab_jewels()
        last_request = datetime.utcnow()
    return redirect(current_url)
    # except ConnectionError:
    #     return render_template("404_page.html"), 404


headers = {
    'content-type': 'application/json',
    'user-agent': 'liberatorist@gmail.com',
}

@app.errorhandler(500)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


def grab_jewels():
    with open("data/initial_post_query.json", "r") as file:
        json_data = json.loads(file.read())

    response = requests.post(f'https://www.pathofexile.com/api/trade/search/{current_league}', headers=headers, json=json_data)
    if response.status_code >= 400:
        raise ConnectionError(response.text)
    params = {'query': response.json()["id"]}
    results = response.json()["result"]
    count = 0
    non_bricks = []
    for url in [','.join(results[n: n + 10]) for n in range(0, len(results), 10)]:
        response = fetch_trade(url, params)
        for result in response.json()["result"]:
            m = re.match(r"Carved to glorify (\d+) new faithful converted by High Templar (.*)\n", result["item"]["explicitMods"][0])
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


current_states = ""
policies = '12:4:10,16:12:300'


def wait_for_request(policies, current_states):
    if not current_states:
        return
    for policy, state in zip(reversed(policies.split(',')), reversed(current_states.split(','))):
        request_limit, interval, _ = policy.split(':')
        current_hits = state.split(':')[0]
        if int(current_hits) >= int(request_limit) - 1:
            time.sleep(int(interval))
            return


def fetch_trade(url, params):
    global policies, current_states
    wait_for_request(policies, current_states)
    response = requests.get(
        f'https://www.pathofexile.com/api/trade/fetch/{url}',
        params=params,
        headers=headers,
    )
    if response.status_code >= 400:
        raise ConnectionError
    policies, current_states = response.headers["X-Rate-Limit-Ip"], response.headers["X-Rate-Limit-Ip-State"]
    return response


if __name__ == '__main__':
    app.run()