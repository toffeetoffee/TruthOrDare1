from flask import Flask
from flask_socketio import SocketIO
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events
from Model.game_manager import GameManager

app = Flask(__name__, template_folder='View', static_folder='static')
app.config['SECRET_KEY'] = 'prts-is-watching-you'
socketio = SocketIO(app, cors_allowed_origins='*')

game_manager = GameManager()

register_routes(app, game_manager)
register_socket_events(socketio, game_manager)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
