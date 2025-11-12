
from flask import Flask, send_from_directory
from flask_socketio import SocketIO
import os

from Controller.routes import register_routes
from Controller.socket_events import register_socket_events
from Model.game_manager import GameManager

app = Flask(__name__, static_folder='View/dist/assets', template_folder='View')
app.config['SECRET_KEY'] = 'prts-is-watching-you'
socketio = SocketIO(app, cors_allowed_origins='*')

game_manager = GameManager()

register_routes(app, game_manager)
register_socket_events(socketio, game_manager)

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'View', 'dist')

@app.route('/')
def spa_index():
    index_path = os.path.join(DIST_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(DIST_DIR, 'index.html')
    return ('<h1>Build the React app first</h1>'
            '<p>Run: <code>cd View && npm ci && npm run build</code></p>', 200)

@app.route('/app')
def app_alias():
    return spa_index()

@app.route('/assets/<path:path>')
def spa_assets(path):
    return send_from_directory(app.static_folder, path)

@app.route('/healthz')
def healthz():
    return 'ok', 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
