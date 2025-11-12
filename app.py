# app.py
from flask import Flask
from flask_socketio import SocketIO

from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events

# -------------------------------------------------------------
# Flask app and Socket.IO initialization
# -------------------------------------------------------------
app = Flask(__name__, template_folder='View/templates', static_folder='View/static')

app.config['SECRET_KEY'] = 'prts-is-watching-you'

# Create SocketIO instance
socketio = SocketIO(app, cors_allowed_origins='*')

# -------------------------------------------------------------
# Create ONE shared GameManager instance
# -------------------------------------------------------------
game_manager = GameManager()
print(f"[INIT] GameManager instance created: {id(game_manager)}")

# Register routes (Controller)
register_routes(app, game_manager)

# Register all Socket.IO events (Controller)
register_socket_events(socketio, game_manager)

# -------------------------------------------------------------
# Run server
# -------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
