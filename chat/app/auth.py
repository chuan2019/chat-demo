"""chat.app.auth"""
from functools import wraps

from flask import jsonify, session

def auth_middleware(fn):
    """
    purpose: filter out unauthorized connections.
    """
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session['nickname']:
            return jsonify(None), 403
        return fn(*args, **kwargs)
    return inner
