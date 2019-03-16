
## API (every API receives JSON)
### find_user
    Login to the system (register if username not in database) 
| Body | Type | Value |
|:---:|:---:|:---:|
| username | string |User's username |
#### Object description
Event 'user_created' (no user in database)
```
{
    "_id": user's id,
    "username": user's username
}
```
Event 'user_found' (found user in database) // group_list might be add in very recent future
```
{
    "_id": user's database id,
    "username": user's username
}
```

### create_group
    create group recieving username and name the group that wanted to be created
| Body | Type | Value |
|:---:|:---:|:---:|
| username | string | User's username |
| group_name | string | desired group name |

#### Object description
Event 'name_not_found' (no username in database)
```
Null
```

Event 'group_already_created' (group has already been created in database)
```
Null
```

Event 'group_created' (successful group creation)
```
{
  "group_name" : group's name,
  "user" : 
        [ 
         { 
            "name_ID" : username of user that is used to created group,
            "last_read" : the time that the group is created (current time in iso format) 
         }
        ]
}
```

### send_message
    send message to the group receiving group's name, username, text as input
    
| Body | Type | Value |
|:---:|:---:|:---:|
| username | string | User's username |
| group_name | string | group that user type the text into |
| text | string | text that user types |

#### Object description
Event 'message_sent' 
```
{
      "_id" : database message's id(might be used for total ordering)
      "group_name" : same as group_name above,
      "username" : same as username above,
      "text" : same as text above,
      "timestamp" : (String) The time that a message arrives at backend 
}
```

### visit_group
    visit another group, temporary leave current group
    
| Body | Type | Value |
|:---:|:---:|:---:|
| username | string | User's username |
| group_name | string | group that user want to visit |

#### Object description
Event 'already_in_the_group' (user already in that group) // (this might be changed in recent future in case that we want to retrieve message here)
```
Null
```

Event 'group not found' (group that user want to visit can not be found in database)
```
Null
```

Event 'user_visited' (user successfully enter new group) 
```
{
      "username" : same as username above,
      "group_name" : same as group_name above,
      "last_time_read_in_visiting_group" : (String) Last time that user visit that group (used for fetching unread message)  
}
```