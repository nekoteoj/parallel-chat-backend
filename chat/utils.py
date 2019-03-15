def query_dict(query):
    q = query.copy()
    q['_id'] = str(q['_id'])
    return q