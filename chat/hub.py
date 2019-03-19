from socketio import Server
from .db import get_db
from . import utils
from bson.objectid import ObjectId
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
        json_message["current_group"] = None
        name_search = posts.find_one(json_message)
        if not name_search:
            posts.insert_one(json_message).inserted_id
            name_search = posts.find_one(json_message)
            name_search['group_list'] = []
            sio.emit('user_created', utils.query_dict(name_search), room = sid)
        else:
            posts_group = db.Group
            group_all = list(posts_group.find())
            print(list(group_all))
            group_user = []
            for group in group_all:
                if json_message["username"] in map(lambda x: x['name_ID'], group['user']):
                    group_user.append(group["group_name"])
            name_search["current_group"] = None
            name_search["group_list"] = group_user            
            sio.emit('user_found', utils.query_dict(name_search), room = sid)
        

# { group_name, username }
    @sio.on("join_group")
    def join_group_sio(sid, message):
        message_json = json.loads(message)
        group_name = message_json["group_name"]
        name_id = message_json["username"]
        db = get_db()
        group_collection = db.Group
        group = group_collection.find_one({ "group_name": group_name })
        if not group:
            sio.emit("join_error", {
               "error": "Group Not Found!"
            }, room=sid)
            return
        if name_id not in set(map(lambda x: x['name_ID'], group['user'])):
            group_collection.update_one({
                "group_name": group_name
            }, {
                "$push": {
                    "user": {
                        "name_ID": name_id,
                        "last_read": utils.get_current_time()
                    }
                }
            })
        sio.emit("join_success", {
            "group_id": str(group["_id"]),
            "group_name": group["group_name"]
        }, room=sid)

    @sio.on("leave_group")
    def leave_group_sio(sid, message):
        message_json = json.loads(message)
        group_name = message_json["group_name"]
        name_id = message_json["username"]
        db = get_db()
        group_collection = db.Group
        user_collection = db.User
        user = user_collection.find_one({ "username": name_id })
        if not user:
            sio.emit("leave_error", {
               "error": "User Not Found!"
            }, room=sid)
            return
        group = group_collection.find_one({ "group_name": group_name })
        if not group:
            sio.emit("leave_error", {
               "error": "Group Not Found!"
            }, room=sid)
            return
        if name_id not in set(map(lambda x: x['name_ID'], group['user'])):
            sio.emit("leave_error", {
                "error": "User not in group"
            }, room="sid")
            return
        group_collection.update_one({
            "group_name": group_name
        }, {
            "$pull": {
                "user": {
                    "name_ID": name_id
                }
            }
        })
        print("Removed user from group")
        if user.get("current_group", None) == group_name:
            user_collection.update_one({
                "_id": user["_id"]
            }, {
                "$set": {
                    "current_group": None
                }
            })
            print("Removed user's current group")
        sio.emit("leave_success", {
            "group_id": str(group["_id"]),
            "group_name": group["group_name"]
        }, room=sid)

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
            sio.emit('name_not_found', {'Error' : 'User could not be found.'}, room=sid)
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
                sio.emit('group_already_created', {'Error' : 'Group has already been created.'}, room=sid)

    # {username, group_name, text}
    @sio.on('send_message')
    def send_message_sio(sid, message):
        print("--> message recieved <--")
        db = get_db()
        json_message = json.loads(message)
        group_name = json_message['group_name']
        posts_text = db.Text

        text_message ={
                        "group_name" : json_message["group_name"],
                        "username" : json_message["username"],
                        "text" : json_message["text"],
                        "timestamp" : utils.get_current_time()
                    }

        posts_text.insert_one(text_message).inserted_id
        # id is included for total ordering
        sio.emit('message_sent', json.dumps(utils.query_dict(text_message)),  room=group_name)

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
        if user_state.get("current_group", None) is not None:
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
                
                if user_state is not None:
                    posts_user.update_one({"username" : username}, {"$set" : user_state} )
                if group_state_leave is not None:
                    posts_group.update_one({"group_name" : group_name_leave}, {"$set" : group_state_leave} )

                user_state['last_time_read_in_visiting_group'] = visit_group_last_read
                sio.leave_room(sid, group_name_leave)
                sio.emit('user_visited', utils.query_dict(user_state), room=sid)
                sio.enter_room(sid, group_name_visit)
            else:
                sio.emit('already_in_the_group', {'Error' : 'User is already in selected chatroom.'},  room=sid)
        else:
            sio.emit('group_not_found', {'Error' : 'Group that user selects can not be found.'},  room=sid)


    @sio.on('enter_group')
    def enter_group_sio(sid, message):
        db = get_db()
        json_message = json.loads(message)
        posts_user = db.User
        posts_group = db.Group
        posts_text = db.Text
        username = json_message["username"]
        group_name = json_message["group_name"]
        user_state = posts_user.find_one({"username" : username})
        user_current_group = user_state.get("current_group", None) 
        if user_current_group != group_name:
            posts_user.update_one({"username" : username}, {"$set" : user_state} )
        group_state = posts_group.find_one({"group_name" : group_name})
        last_read = None
        for user in group_state['user']:
            if user["name_ID"] == username:
                last_read = user["last_read"]
                user["last_read"] = utils.get_current_time()
        if last_read is not None:
            current_time = utils.get_current_time()
            unread_cursor = posts_text.find({'group_name':group_name, 'timestamp':{"$gt":last_read, "$lte":current_time}})
            read_cursor = posts_text.find({'group_name':group_name, 'timestamp':{"$lte":last_read}}).limit(100)
            unread_message = []
            read_message = []
            for m in unread_cursor:
                message = dict()
                message['timestamp'] = m['timestamp']
                message['username'] = m['username']
                message['group_name'] = m['group_name']
                message['text'] = m['text']
                unread_message.append(message)
            for m in read_cursor:
                message = dict()
                message['timestamp'] = m['timestamp']
                message['username'] = m['username']
                message['group_name'] = m['group_name']
                message['text'] = m['text']
                read_message.append(message)
            json_messages = json.dumps([unread_message, read_message])
            sio.emit("enter_group", json_messages, room=sid)
            posts_group.update_one({"group_name" : group_name}, {"$set" : group_state} )
            if group_name not in sio.rooms(sid):
                sio.enter_room(sid, group_name)
        else:
            sio.emit('group_not_join', None,  room=sid)