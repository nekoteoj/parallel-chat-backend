from flask import Flask, jsonify
import socketio
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import os

from chat import hub, route

async_mode = 'gevent'

PORT = os.environ.get('PORT', 3000)
SECRET_KEY = os.environ.get('SECRET_KEY', 'schwanfc')

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
app.config['SECRET_KEY'] = SECRET_KEY

hub.init(sio)
route.init(app)

if __name__ == '__main__':
    print(f'Server is running on port {PORT}')
    pywsgi.WSGIServer(('', PORT), app, handler_class=WebSocketHandler).serve_forever()