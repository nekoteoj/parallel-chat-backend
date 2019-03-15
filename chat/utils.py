import datetime
def get_current_time():
    return datetime.datetime.now().isoformat()
def query_dict(query):
    q = query.copy()
    q['_id'] = str(q['_id'])
    return q
