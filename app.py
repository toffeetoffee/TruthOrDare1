from flask import Flask
from flask_socketio import SocketIO

from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events

app = Flask(__name__, template_folder='View', static_folder='View/static')
app.config['SECRET_KEY'] = 'prts-is-watching-you'

socketio = SocketIO(app, cors_allowed_origins='*')

game_manager = GameManager()
print(f"[INIT] GameManager instance created: {id(game_manager)}")

register_routes(app, game_manager)

register_socket_events(socketio, game_manager)

# Global error handler for all Socket.IO events
@socketio.on_error_default
def default_error_handler(e):
    print(f'[SOCKET.IO ERROR] {e}')
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)