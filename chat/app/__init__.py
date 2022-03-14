"""chat.app.__init__"""
import logging
import datetime
from functools import wraps

from flask import Flask
from flask_cors import CORS
from flask_session import Session

from .config import get_config

sess = Session()

# Creating and Configuring Flask App
flask_app = Flask(__name__)
flask_app.config.from_object(get_config())

CORS(flask_app)

# Logging configuration
logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

def run_app(port:int, host:str='0.0.0.0', debug:bool=True):
    # initializing session
    sess.init_app(flask_app)
    # start server
    flask_app.run(host=host, port=port, debug=debug, use_reloader=True)

from . import api
