import os
from flask import Flask, send_from_directory
from flask_socketio import SocketIO

# Import your MVC parts
from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events

# Serve SPA from View/dist (Vite build output)
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "View", "dist")

app = Flask(
    __name__,
    static_folder=DIST_DIR,
    static_url_path=""
)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

game_manager = GameManager()

# Register your MVC routes and socket events
register_routes(app, game_manager)
register_socket_events(socketio, game_manager)

# -------------------------------------------------------------------
# React SPA serving routes (renamed endpoint to avoid collisions)
# -------------------------------------------------------------------

@app.route("/spa_root")
def serve_spa_root():
    """Serve the React single-page app (index.html)."""
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(DIST_DIR, "index.html")
    return (
        "<h1>Build the React app first</h1>"
        "<p>Run: <code>cd View && npm ci && npm run build</code></p>", 
        200
    )

@app.route("/assets/<path:path>")
def serve_assets(path):
    """Serve built JS/CSS assets."""
    return send_from_directory(os.path.join(DIST_DIR, "assets"), path)

# Catch-all: any other route not handled by backend → React router
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    """Serve SPA for any non-API route."""
    if path.startswith("api/") or path.startswith("socket.io"):
        return "Not Found", 404
    index_path = os.path.join(DIST_DIR, "index.html")
    return send_from_directory(DIST_DIR, "index.html")

# -------------------------------------------------------------------
# Healthcheck for Render
# -------------------------------------------------------------------
@app.route("/healthz")
def healthz():
    return "ok", 200

# -------------------------------------------------------------------
# Main entry
# -------------------------------------------------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
