from flask import Blueprint, redirect
import os

static_file_dir = os.path.dirname(os.path.realpath(__file__))
home = Blueprint('home', __name__)


@home.route('/')
def render_static():
    return redirect('/api/doc')
