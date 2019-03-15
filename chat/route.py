from flask import Flask, jsonify
from .db import get_db

def init(app: Flask):
    @app.route('/ping')
    def ping_api():
        return jsonify({ 'message': 'pong' })
    
    @app.route('/db')
    def db_api():
        db = get_db()
        collection = db['temp']
    
