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

# Initialize Game Manager
game_manager = GameManager()

# Register HTTP routes (Controller)
register_routes(app, game_manager)

# Register SocketIO events (Controller)
register_socket_events(socketio, game_manager)

# Run server
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
