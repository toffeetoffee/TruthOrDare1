import os
from flask import request, jsonify, send_from_directory


def register_routes(app, game_manager):
    """
    Register HTTP routes for the Truth or Dare app.
    Compatible with React + Tailwind SPA frontend.
    """

    # -----------------------------------------------------------
    # Serve React SPA entry (index.html)
    # -----------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        """Serve the React SPA entrypoint."""
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "View", "dist")
        index_path = os.path.join(dist_dir, "index.html")

        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        else:
            return (
                "<h1>React build not found</h1>"
                "<p>Run <code>npm run build</code> inside the View folder before starting the app.</p>",
                500,
            )

    # -----------------------------------------------------------
    # Create new room (API endpoint)
    # -----------------------------------------------------------
    @app.route("/create", methods=["POST"])
    def create_room():
        """
        Create a new game room.
        Returns JSON:
        {
          "success": true,
          "room_code": "ABC123",
          "name": "Player"
        }
        """
        name = request.form.get("name", "").strip() or "Anonymous"
        code = game_manager.create_room()

        return jsonify(success=True, room_code=code, name=name)

    # -----------------------------------------------------------
    # Join existing room (API endpoint)
    # -----------------------------------------------------------
    @app.route("/join", methods=["POST"])
    def join_room_route():
        """
        Join an existing room by code.
        Returns JSON if successful or an error.
        """
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip() or "Anonymous"

        if not code:
            return jsonify(success=False, error="Missing room code"), 400
        if not game_manager.room_exists(code):
            return jsonify(success=False, error="Room not found"), 404

        return jsonify(success=True, room_code=code, name=name)

    # -----------------------------------------------------------
    # React Router Fallback (room route)
    # -----------------------------------------------------------
    @app.route("/room/<code>", methods=["GET"])
    def room(code):
        """
        Serve the React SPA for any /room/<code> path.
        The frontend handles reading ?name= from URL and joining via Socket.IO.
        """
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "View", "dist")
        index_path = os.path.join(dist_dir, "index.html")

        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        else:
            return (
                "<h1>React build missing</h1>"
                "<p>Run <code>npm run build</code> inside View/ before deploying.</p>",
                500,
            )

    # -----------------------------------------------------------
    # Serve React static assets (CSS, JS, etc.)
    # -----------------------------------------------------------
    @app.route("/assets/<path:path>")
    def serve_react_assets(path):
        """Serve JS/CSS assets built by React."""
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "View", "dist", "assets")
        return send_from_directory(assets_dir, path)
