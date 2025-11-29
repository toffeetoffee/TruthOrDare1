from flask import Flask
from flask_socketio import SocketIO

from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events

# Set up Flask app — templates and static files live in /View
app = Flask(__name__, template_folder='View', static_folder='View/static')
app.config['SECRET_KEY'] = 'prts-is-watching-you'  # might to move this to env later

# Initialize Socket.IO with cross-origin enabled
socketio = SocketIO(app, cors_allowed_origins='*')

# Create main game manager object
game_manager = GameManager()
print(f"[INIT] GameManager instance created (id={id(game_manager)})")

# Attach routes and socket handlers
register_routes(app, game_manager)
register_socket_events(socketio, game_manager)

# Catch-all error handler for Socket.IO events
@socketio.on_error_default
def default_error_handler(e):
    print(f"[SOCKET.IO ERROR] Uncaught error: {e}")
    import traceback
    traceback.print_exc()

# Run the app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
