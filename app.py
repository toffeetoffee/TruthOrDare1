# app.py
from flask import Flask
from flask_socketio import SocketIO

from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events

# Initialize Flask app
app = Flask(__name__, template_folder='View', static_folder='View/static')
app.config['SECRET_KEY'] = 'prts-is-watching-you'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins='*')

# Initialize Game Manager (Model)
game_manager = GameManager()

# Register routes (Controller)
register_routes(app, game_manager)

# Register socket events (Controller)
register_socket_events(socketio, game_manager)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
