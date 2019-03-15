from socketio import Server
from .db import get_db
from . import utils
import json
from bson.objectid import ObjectId
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
            sio.emit('created', utils.query_dict(name_search), room = sid)
        else:
            sio.emit('name', utils.query_dict(name_search), room = sid)

    @sio.on('create_group')
    def add_group_sio(sid, message):
        print(message)
        db = get_db()
        json_message = json.loads(message)
        posts_user = db.User   
        name_search = posts_user.find_one({"username" : json_message["username"]})
        print(name_search)
        if not name_search:
            sio.emit('Error-name_not_found', None, room=sid)
        else:
            posts_group = db.Group
            group_search = posts_group.find_one({"group_name" : json_message["group_name"]})
            if not group_search:
                group_message =     {
                                        "group_name" : json_message["group_name"],
                                        "user" : 
                                            [ 
                                                { 
                                                    "name_ID" : str(name_search['_id']),
                                                    "last_read" : utils.get_current_time()
                                                }
                                            ]
                                    }
                print(json.dumps(group_message))
                posts_group.insert_one(group_message).inserted_id
                group_val = posts_group.find_one({"group_name" : json_message["group_name"]})
                sio.emit('group_created', utils.query_dict(group_val), room=sid)

            else:
                sio.emit('Error-group_already_created', None, room=sid)




        # else:
        #     posts_user.insert_one(json_message).inserted_id
        #     name_search = posts_user.find_one(json_message)

