from flask import Blueprint
import os
from flakon.util import send_request

static_file_dir = os.path.dirname(os.path.realpath(__file__))
home = Blueprint('home', __name__)


@home.route('/')
def render_static():
    res = send_request('http://127.0.0.1:5002/user/1', 'PUT', {'id': 1, 'strava_token': 'ciao'})
    print(res)
    return res.text
