import hashlib
import json
from datetime import datetime
import os

from flask import Flask, render_template, request
import requests
from trade_crawler import initialize_scheduler

template_dir = os.getcwd()
app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def endpoint():
    return render_template('index.html')

@app.route('/upload', methods=["POST"])
def upload():
    data = request.json
    if verify_data(data):
        data.pop("pw")
        with open("static/trade_links.json", "w") as file:
            file.write(json.dumps(request.json))
        return "Successful Upload"
    return "Could not verify upload"


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

def verify_data(data):
    m = hashlib.sha512(data["pw"].encode('UTF-8')).hexdigest()
    return m == "3dd28c5a23f780659d83dd99981e2dcb82bd4c4bdc8d97a7da50ae84c7a7229a6dc0ae8ae4748640a4cc07ccc2d55dbdc023a99b3ef72bc6ce49e30b84253dae"

# with app.app_context():
    # initialize_scheduler()


if __name__ == '__main__':
    app.run()
