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

    @sio.on('find_user')
    def add_name_sio(sid, message):
        db = get_db()
        posts = db.User
        json_message = json.loads(message)
        name_search = posts.find_one(json_message)
        if not name_search:
            posts.insert_one(json_message).inserted_id
            name_search = posts.find_one(json_message)
            sio.emit('user_created', utils.query_dict(name_search), room = sid)
        else:
            sio.emit('user_found', utils.query_dict(name_search), room = sid)

# { username, group_name}
    @sio.on('create_group')
    def add_group_sio(sid, message):
        #print(message)
        db = get_db()
        json_message = json.loads(message)
        posts_user = db.User   
        name_search = posts_user.find_one({"username" : json_message["username"]})
        #print(name_search)
        if not name_search:
            sio.emit('name_not_found', None, room=sid)
        else:
            posts_group = db.Group
            group_search = posts_group.find_one({"group_name" : json_message["group_name"]})
            if not group_search:
                group_message =     {
                                        "group_name" : json_message["group_name"],
                                        "user" : 
                                            [ 
                                                { 
                                                    "name_ID" : json_message["username"],
                                                    "last_read" : utils.get_current_time()
                                                }
                                            ]
                                    }
                # print(json.dumps(group_message))
                posts_group.insert_one(group_message).inserted_id
                group_val = posts_group.find_one({"group_name" : json_message["group_name"]})
                sio.emit('group_created', utils.query_dict(group_val), room=sid)

            else:
                sio.emit('group_already_created', None, room=sid)

    # {username, groupname, text}
    @sio.on('send_message')
    def send_message_sio(sid, message):
        print("--> message recieved <--")
        db = get_db()
        json_message = json.loads(message)
        posts_text = db.Text

        text_message ={
                        "group_name" : json_message["group_name"],
                        "username" : json_message["username"],
                        "text" : json_message["text"],
                        "timestamp" : utils.get_current_time()
                    }

        posts_text.insert_one(text_message).inserted_id
        # id is included for total ordering
        sio.emit('message_sent', json.dumps(utils.query_dict(text_message)),  room=sid)

    # {username, groupname}
    @sio.on('visit_group') #eqivalent to temporary leave new group
    def visit_group_sio(sid, message):
        db = get_db()
        json_message = json.loads(message)
        posts_user = db.User
        posts_group = db.Group

        username = json_message["username"]
        group_name = json_message["group_name"]

        user_state = posts_user.find_one({"username" : username})
        group_state = posts_group.find_one({"group_name" : group_name})
        if group_state is not None:
            print(user_state)
            print(group_state)

            user_state['current_group'] = group_name
            #found_group = False
            for user_status in group_state["user"]:
                if(user_status["name_ID"] == username):
                    #found_group = True
                    user_status["last_read"] = utils.get_current_time()

            print(user_state)        
            print(group_state)
            posts_user.update_one({"username" : username}, {"$set" : user_state} )
            posts_group.update_one({"group_name" : group_name}, {"$set" : group_state} )
            sio.emit('user_visited', json.dumps(utils.query_dict(user_state)),  room=sid)
        else:
            sio.emit('group_not_found', None,  room=sid)

        