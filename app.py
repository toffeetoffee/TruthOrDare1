# app.py
import os
from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO
from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events

# Serve SPA from View/dist (built by Vite)
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "View", "dist")

# Important: static_url_path="" so /assets/* are served correctly
app = Flask(
    __name__,
    static_folder=DIST_DIR,
    static_url_path="",
)

# Socket.IO (eventlet on Render)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",  # important for gunicorn -k eventlet
)

game_manager = GameManager()

# Your existing REST routes (if any)
register_routes(app, game_manager)

# Your socket events
register_socket_events(socketio, game_manager)

# ---- SPA static file handling ----
# Serve index.html on root
@app.route("/")
def index():
    return send_from_directory(DIST_DIR, "index.html")

# Serve any file that exists in dist directly; otherwise fall back to index.html
@app.route("/<path:path>")
def static_proxy(path):
    full_path = os.path.join(DIST_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(DIST_DIR, path)
    # SPA fallback (React Router, deep links)
    return send_from_directory(DIST_DIR, "index.html")

if __name__ == "__main__":
    # Local dev run
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
