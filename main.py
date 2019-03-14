from flask import Flask, jsonify
import socketio
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import os

async_mode = 'gevent'

PORT = os.environ.get('PORT', 3000)
SECRET_KEY = os.environ.get('SECRET_KEY', 'schwanfc')

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/ping')
def ping_api():
    return jsonify({ 'message': 'pong' })

@sio.on('connect')
def connect_sio(sid, message):
    print(f'{sid} connected!')

@sio.on('pingg')
def ping_sio(sid, message):
    sio.emit('pongg', { 'message': message })

if __name__ == '__main__':
    print(f'Server is running on port {PORT}')
    pywsgi.WSGIServer(('', PORT), app, handler_class=WebSocketHandler).serve_forever()