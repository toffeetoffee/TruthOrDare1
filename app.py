from flask import Flask, send_from_directory, jsonify
from flask_socketio import SocketIO
import os

# Import your MVC modules
from Model.game_manager import GameManager
from Controller.routes import register_routes
from Controller.socket_events import register_socket_events


# ------------------------------------------------------------------------------
# Flask App Setup
# ------------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="View/frontend/dist",      # Path to React build
    template_folder="View/frontend/dist"     # For serving index.html
)
app.config["SECRET_KEY"] = "prts-is-watching-you"

# ------------------------------------------------------------------------------
# Socket.IO Setup
# ------------------------------------------------------------------------------
socketio = SocketIO(app, cors_allowed_origins="*")

# ------------------------------------------------------------------------------
# Game Manager (Model)
# ------------------------------------------------------------------------------
game_manager = GameManager()

# ------------------------------------------------------------------------------
# Register MVC Components
# ------------------------------------------------------------------------------
register_routes(app, game_manager)
register_socket_events(socketio, game_manager)


# ------------------------------------------------------------------------------
# React Frontend Serving
# ------------------------------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    """
    Serve the React SPA (Vite build output).
    This catches all non-API routes and returns index.html.
    """
    frontend_dist = os.path.join(app.root_path, "View", "frontend", "dist")

    # Full path of the requested file
    file_path = os.path.join(frontend_dist, path)

    # If the requested file exists, serve it directly (e.g., CSS, JS)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(frontend_dist, path)
    # Otherwise, serve index.html (React Router SPA entry)
    return send_from_directory(frontend_dist, "index.html")


# ------------------------------------------------------------------------------
# Health Check Endpoint (useful for Render)
# ------------------------------------------------------------------------------
@app.route("/api/health")
def health_check():
    """Simple endpoint to verify the server is running."""
    return jsonify({"status": "ok"}), 200


# ------------------------------------------------------------------------------
# Main Entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Allow Render to assign PORT (or default to 5000 locally)
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Dare or Dare backend on port {port}")
    socketio.run(app, host="0.0.0.0", port=port)
