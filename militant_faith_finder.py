import json
from datetime import datetime
import os

from flask import Flask, render_template
from trade_crawler import initialize_scheduler

template_dir = os.getcwd()
app = Flask(__name__, template_folder=template_dir)

with open('data/useful_seeds', 'r') as file:
    useful_seeds = json.loads(file.read())
    
def get_human_readable_time_diff(time_string):
    diff = (datetime.utcnow() - datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S.%f')).seconds
    if (seconds := diff) < 60:
        return f"{seconds} second{'s' if seconds > 1 else ''} ago"
    elif (minutes := round(diff / 60)) < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif (hours := round(minutes / 60)) < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    days = round(hours / 24)
    return f"{days} day{'s' if round(days) > 1 else ''} ago"



@app.route('/')
def endpoint():
    with open('data/trade_links.json', 'r') as file:
        data = json.loads(file.read())
    return render_template('index.html', 
                           generic_link = data['generic_link'], 
                           mana_link = data['mana_link'], 
                           time_since_last_update=get_human_readable_time_diff(data['time_since_last_update']))


@app.errorhandler(500)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        'code': e.code,
        'name': e.name,
        'description': e.description,
    })
    response.content_type = 'application/json'
    return response


with app.app_context():
    initialize_scheduler()


if __name__ == '__main__':
    app.run()
