"""chat.app.redis_utils"""
import time
import json
import threading
from typing import List, Tuple

from flask import session

from . import logging
from .config import get_config

redis_client = get_config().redis_client

threads = {}
subscribers = {}

def initiate_chat(nickname:str) -> Tuple[int, str]:
    """
    purpose: create a (private) chat room, if any analyst is online
    """
    # step 1: validate nickname
    if not nickname.isalnum():
        logging.error(f'"{nickname}" is not alphanumeric. Nickname has to be alphanumeric.')
        return 1, None
    rooms = get_rooms('client', nickname)
    if len(rooms) > 0:
        end_chat(nickname)
        session.clear()
        logging.error(f'"{nickname}" is online already, the session is expired, please try login again')
        return 1, None
    # step 2: find the next analyst
    if not redis_client.exists('analysts_online') or redis_client.zcard('analysts_online') == 0:
        logging.error('no analyst online yet, please try again later.')
        session['user'] = None
        session.clear()
        return 2, None
    current_analyst = redis_client.incr('current_analyst')
    if current_analyst >= redis_client.zcard('analysts_online'):
        current_analyst = 0
        redis_client.set('current_analyst', current_analyst)
    # step 3: create a private room between the analyst and requesting client
    #         we create the room "lazily", i.e. it is not actually created until
    #         either client or analyst send the first message
    analyst = redis_client.zrange('analysts_online', current_analyst, current_analyst)[0].decode("UTF-8")
    analyst = json.loads(analyst)
    room_id = f'room:{analyst["nickname"]}:{nickname}'
    if redis_client.zadd(room_id, {0: 0}) == 1:
        logging.info(f'(private) chat-room "{room_id}" is created.')
    else:
        logging.error(f'creating (private) chat-room "{room_id}" failed.')
        session.clear()
        return 3, None
    # step 4: add nickname into the clients_online set, if it does not exist yet
    if not redis_client.exists('clients_online') or \
        not redis_client.sismember('clients_online', nickname):
        try:
            redis_client.sadd('clients_online', nickname)
        except:
            logging.exception(f'adding client "{nickname}" into the online clients list failed')
            session.clear()
            return 4, None
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    subscribers[nickname] = pubsub
    threads[room_id] = threading.Thread(target=subscribe_room, args=(room_id,pubsub,))
    threads[room_id].setDaemon(True)
    threads[room_id].start()
    return 0, room_id

def end_chat(nickname:str) -> int:
    """
    purpose: close a (private) chat room, only client can close the chat room
    """
    # step 1: validate nickname
    if not nickname.isalnum():
        logging.error(f'"{nickname}" is not alphanumeric. Nickname has to be alphanumeric.')
        return 1
    # step 2: client unsubscribe from the room
    subscribers[nickname].unsubscribe() # after this step the daemon thread will stop
    # step 3: client goes offline
    redis_client.srem('clients_online', nickname)
    # step 4: closing all chat rooms the client joined
    rooms = get_rooms('client', nickname)
    if len(rooms) > 0:
        for room in rooms:
            redis_client.unlink(room)
    return 0

def refresh_online_status(user_type:str, nickname:str) -> int:
    """
    purpose: refresh online status
    """
    # validate nickname
    if not nickname.isalnum():
        logging.error(f'"{nickname}" is not alphanumeric. Nickname has to be alphanumeric.')
        return 1
    if user_type == 'client':
        redis_client.sadd('clients_online', nickname)
    if user_type == 'analyst':
        if not redis_client.exists('current_analyst'):
            redis_client.set('current_analyst', -1) # no analyst is communicated yet
        data = {'nickname': nickname, 'date': time.time()}
        redis_client.zadd('analysts_online', {json.dumps(data): int(data['date'])})
    return 0

def get_rooms(user_type:str, nickname:str) -> List[str]:
    """
    purpose: retrieve all chat rooms the user is currently joined
    """
    rooms = None
    if user_type == 'client':
        rooms = redis_client.keys(f'room:*:{nickname}')
    if user_type == 'analyst':
        rooms = redis_client.keys(f'room:{nickname}:*')
    return rooms

def go_offline(user_type:str, nickname:str) -> int:
    """
    purpose: utility function for logout operation
    """
    # validate nickname
    if not nickname.isalnum():
        logging.error(f'"{nickname}" is not alphanumeric. Nickname has to be alphanumeric.')
        return 1
    if user_type == 'client':
        return end_chat(nickname)
    if user_type == 'analyst':
        # analyst goes offline
        rooms = get_rooms('analyst', nickname)
        if (not rooms is None) and (len(rooms) > 0):
            msg = f'analyst "{nickname}" has to remain online, as some conversation is still ongoing.'
            logging.error(msg)
            return 1
        users = redis_client.zscan(name='analysts_online', match=f'*{nickname}*')
        users = [user for user in users if user != 0][0]
        user  = users[0][0]
        redis_client.zrem('analysts_online', user)
        analyst_count = redis_client.zcard('analysts_online')
        if analyst_count == 0:
            redis_client.delete('current_analyst')
        return 0

def message_add(message:dict) -> int:
    """
    purpose: add a new message into the data store
    :output: the number of new elements added
    """
    # validate message type
    if not isinstance(message, dict):
        logging.error(f'message must be dict type. [message: type:{type(message)}, content:{message}]')
        return 0
    num = redis_client.zadd(message['roomId'], {json.dumps(message): int(message['date'])})
    return num

def publish(room_id:str, from_:str, message:str) -> None:
    """
    purpose: publish message
    """
    message = {from_: message}
    redis_client.publish(f"{room_id}", json.dumps(message))

def subscribe_room(room_id:str, pubsub:object) -> None:
    """
    purpose: handle message formatting, etc.
    """
    pubsub.subscribe(room_id)
    for message in pubsub.listen():
        redis_client.zadd(room_id, {message['data']: int(time.time())})


def get_messages(room_id:str) -> List[str]:
    """
    purpose: retrieve all messages from a given room
    """
    # skip the first dummy message
    res = redis_client.zrange(room_id, 1, -1)
    messages = []
    for msg in res:
        if isinstance(msg, bytes):
            msg = msg.decode('UTF-8')
        messages.append(msg)
    return messages

def pop_messages(room_id:str) -> List[str]:
    """
    purpose: retrieve all messages from a given room, then remove all messages
    """
    # skip the first dummy message
    messages = get_messages(room_id)
    redis_client.zremrangebyrank(room_id, 1, -1)
    return messages
