import json
from datetime import datetime
import os

from flask import Flask, render_template
from trade_crawler import initialize_scheduler

template_dir = os.getcwd()
app = Flask(__name__, template_folder=template_dir)

calls = 0
@app.route('/')
def endpoint():
    global calls
    calls += 1
    with open("static/trade_links.json", "r") as file:
        data = json.loads(file.read())
    data["calls"] = calls
    with open("static/trade_links.json", "w") as file:
        file.write(json.dumps(data))
    return render_template('index.html')


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
