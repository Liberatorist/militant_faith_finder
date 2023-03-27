import requests


def set_league():
    response = requests.get("https://api.pathofexile.com/leagues", headers={'user-agent': 'liberatorist@gmail.com'})
    for league in response.json():
        if league['rules'] == [] and "This is the default Path of Exile league" in league["description"]:
            with open("current_league.txt", "w") as file:
                file.write(league["id"])


if __name__ == '__main__':
    set_league()