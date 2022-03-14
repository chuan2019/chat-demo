"""chat.app.api"""
from functools import wraps
from flask import (
    render_template,
    request,
    jsonify,
    session
)

from . import flask_app
from . import redis_utils

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session is None or not 'user' in session:
            return jsonify({'message': 'login required'}), 403
        return fn(*args, **kwargs)
    return wrapper

@flask_app.route("/")
def index():
    return render_template('index.html')

@flask_app.route("/me")
def get_me():
    """
    purpose: check whoami in the session
    """
    user = session.get("user", None)
    return jsonify(user)

@flask_app.route('/client/login', methods=["POST"])
def client_login():
    """
    purpose: handle client login event
             if client is not online, add nickname into the online clients list
             if client is online, continue the existing conversations
    """
    data = request.get_json()
    nickname = data['nickname']
    code, room_id = redis_utils.initiate_chat(nickname)
    if code == 0:
        # session initiated, messages can be sent now
        session['user'] = {'nickname': nickname, 'user_type':'client'}
        return jsonify({'message':f'{nickname} logged in, room: {room_id}.'}), 200
    else:
        return jsonify({'message': f'client "{nickname}" login failed, error code: {code}.'}), 404

@flask_app.route('/analyst/login', methods=["POST"])
def analyst_login():
    """
    purpose: handle analyst login event
             add nickname and current timestamp into the (sorted) online analyst list
             which is ordered by timestamp
    """
    data = request.get_json()
    if data is None or data['nickname'] is None:
        return jsonify({'message': 'nickname is not provided'}), 400
    nickname = data['nickname']
    if redis_utils.refresh_online_status('analyst', nickname) == 1:
        return jsonify({'message': f'analyst "{nickname}" login failed, nickname must be alphanumeric.'}), 400
    session['user'] = {'nickname': nickname, 'user_type':'analyst'}
    return jsonify({'message': f'analyst "{nickname}" logged in.'}), 200

@flask_app.route('/client/logout', methods=["POST"])
@login_required
def client_logout():
    """
    purpose: handle client logout event
             if client is online, remove nickname from the online clients list
             if any chat room is open, close it
             deactive the session
    """
    # after `login_status` applied, a client must be currently online
    nickname = session['user']['nickname']
    user_type = session['user']['user_type']
    if user_type != 'client':
        msg = f'user: "{nickname}" is not a client'
        return jsonify({'message': msg}), 500
    if redis_utils.go_offline('client', nickname) != 0:
        return jsonify({'message': f'nickname "{nickname}" must be alphanumeric.'}), 400
    session['user'] = None
    session.clear()
    return jsonify({'message': f'client "{nickname}" logged out.'}), 200

@flask_app.route('/analyst/logout', methods=["POST"])
@login_required
def analyst_logout():
    """
    purpose: handle analyst logout event
             analyst will not be able to logout untill all chat rooms have been closed
    """
    # after `login_required` applied, an analyst must be currently online
    nickname = session['user']['nickname']
    user_type = session['user']['user_type']
    if user_type != 'analyst':
        msg = f'user: "{nickname}" is not an analyst'
        return jsonify({'message': msg}), 500

    if redis_utils.go_offline('analyst', nickname) != 0:
        msg = f'analyst "{nickname}" cannot logout yet, some conversation still ongoing.'
        return jsonify({'message': msg}), 400
    session['user'] = None
    session.clear()
    return jsonify({'message': f'analyst "{nickname}" logged out.'}), 200

@flask_app.route('/send_msg', methods=["POST"])
@login_required
def send_msg():
    """
    purpose: send a message from current logged in user (client or analyst) into the room
             if requesting user is a client, as only one unique room is opened for him/her,
             roomid can be determined directly, hence no need to read data
             if requesting user is an analyst, as he/she may have joined multiple rooms,
             target client must be specified, hence need to get this information from data
    """
    # after `login_required` applied, a client must be currently online
    data = request.get_json()
    message = data['message']
    nickname = session['user']['nickname']
    user_type = session['user']['user_type']
    if (user_type != 'client' and user_type != 'analyst'):
        msg = f'user type: \"{user_type}\" of user \"{nickname}\" is not a valid type'
        return jsonify({'message': msg}), 500
    if user_type == 'client':
        rooms = redis_utils.get_rooms('client', nickname)
        if len(rooms) != 1:
            msg = f'client {nickname} must have exactly one room, but {len(rooms)} is found.'
            return jsonify({'message': msg}), 500
        room_id = rooms[0].decode('UTF-8')
    if user_type == 'analyst':
        if data is None or not 'to' in data:
            msg = f'a message from analyst "{nickname}" must specify to whom the message is sent'
            return jsonify({'message': msg}), 400
        client_name = data['to']
        rooms = redis_utils.get_rooms('client', client_name)
        if len(rooms) != 1:
            msg = f'client {client_name} must have exactly one room, but {len(rooms)} is found.'
            return jsonify({'message': msg}), 500
        room_id = rooms[0].decode('UTF-8')
        if room_id.split(':')[1] != nickname:
            msg = f'client {client_name} is not communicating with {nickname} now.'
            return jsonify({'message':msg}), 400
    redis_utils.publish(room_id=room_id, from_=nickname, message=message)
    return jsonify({'message':f'message from "{nickname}" is sent to "{room_id}"'}), 200

@flask_app.route("/get_messages", methods=["GET"])
@login_required
def get_messages():
    """
    purpose: for clients, retrieve all messages from their own room
             for analysts, retrieve all messages from all active rooms
    """
    # step 1: determine user type
    user_type = session['user']['user_type']
    nickname  = session['user']['nickname']
    # step 2: retrieve messages depending on user type respectively
    rooms = []
    if user_type == 'client':
        rooms = redis_utils.get_rooms('client', nickname)
    if user_type == 'analyst':
        rooms = redis_utils.get_rooms('analyst', nickname)
    messages = {}
    for room_id in rooms:
        if isinstance(room_id, bytes):
            room_id = room_id.decode('UTF-8')
        message = redis_utils.get_messages(room_id=room_id)
        messages[room_id] = message
    return jsonify(messages), 200


@flask_app.route("/pop_messages", methods=["GET"])
@login_required
def pop_messages():
    """
    purpose: retrieve all messages from their own room(s) then remove all the messages
    """
    # step 1: determine user type
    user_type = session['user']['user_type']
    nickname  = session['user']['nickname']
    # step 2: retrieve messages depending on user type respectively
    rooms = []
    if user_type == 'client':
        rooms = redis_utils.get_rooms('client', nickname)
    if user_type == 'analyst':
        rooms = redis_utils.get_rooms('analyst', nickname)
    messages = {}
    for room_id in rooms:
        if isinstance(room_id, bytes):
            room_id = room_id.decode('UTF-8')
        message = redis_utils.pop_messages(room_id=room_id)
        messages[room_id] = message
    return jsonify(messages), 200
