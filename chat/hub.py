from socketio import Server
from .db import get_db
from . import utils
from bson.objectid import ObjectId
import json
import datetime

def init(sio: Server):
    @sio.on('connect')
    def connect_sio(sid, message):
        print(f'{sid} connected!')

    @sio.on('pingg')
    def ping_sio(sid, message):
        sio.emit('pongg', { 'message': message })

    @sio.on('add_name')
    def add_name_sio(sid, message):
        db = get_db()
        posts = db.User
        json_message = json.loads(message)
        name_search = posts.find_one(json_message)
        if not name_search:
            posts.insert_one(json_message).inserted_id
            name_search = posts.find_one(json_message)
        sio.emit('name', utils.query_dict(name_search), room=sid)

    @sio.on('join_group')
    def join_group_sio(sid, message):
        message_json = json.loads(message)
        group_name = message_json["group_name"]
        user_id = message_json["name_id"]
        db = get_db()
        group_collection = db.Group
        group_collection.update_one({
            "group_name": group_name
        }, {
            "$push": {
                "User": {
                    "name_ID": user_id,
                    "last_read": datetime.datetime.now().isoformat()
                }
            }
        })
        group = group_collection.find_one({ "group_name": group_name })
        sio.enter_room(sid, group_name)
        sio.emit("join_success", {
            "group_id": group._id,
            "group_name": group.group_name
        }, room=sid)