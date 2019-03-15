from pymongo import MongoClient
client = MongoClient()

def get_db():
    return client['parallel_chat']