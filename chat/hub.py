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
# { username}
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

    # {username, group_name, text}
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

    # {username, group_name}
    @sio.on('visit_group') #eqivalent to temporary leave new group
    def visit_group_sio(sid, message):
        db = get_db()
        json_message = json.loads(message)
        posts_user = db.User
        posts_group = db.Group

        username = json_message["username"]
        user_state = posts_user.find_one({"username" : username})
        group_name_leave = None
        group_state_leave = None
        if user_state["current_group"] is not None:
            print("origin group found")
            group_name_leave = user_state["current_group"]
            group_state_leave = posts_group.find_one({"group_name" : group_name_leave})

        group_name_visit = json_message["group_name"]
        group_state_visit = posts_group.find_one({"group_name" : group_name_visit})
        
        if group_state_visit is not None:
            if(group_name_visit != group_name_leave):
                print("----------Original------------")
                print(user_state)
                print(group_state_leave)

                user_state["current_group"] = group_name_visit
                #update old group
                if(group_state_leave is not None):
                    for user_status in group_state_leave["user"]:
                        if(user_status["name_ID"] == username):
                            user_status["last_read"] = utils.get_current_time()

                #get last read time from new group
                visit_group_last_read = None
                for user_status in group_state_visit["user"]:
                    if(user_status["name_ID"] == username):
                        visit_group_last_read = user_status["last_read"]

                print("----------Updated------------")
                print(user_state)        
                print(group_state_leave)
                
                posts_user.update_one({"username" : username}, {"$set" : user_state} )
                posts_group.update_one({"group_name" : group_name_leave}, {"$set" : group_state_leave} )
                sio.emit('user_visited', { "userstate" : utils.query_dict(user_state),
                 "last_time_read_in_visit_group" : visit_group_last_read},  room=sid)
            else:
                sio.emit('already_in_the_group', None,  room=sid)
        else:
            sio.emit('group_not_found', None,  room=sid)

        