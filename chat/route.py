from flask import Flask, jsonify

def init(app: Flask):
    @app.route('/ping')
    def ping_api():
        return jsonify({ 'message': 'pong' })