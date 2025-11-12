import os
from flask import request, redirect, url_for, flash, send_from_directory


def register_routes(app, game_manager):
    """Register HTTP routes for the Truth or Dare app (React frontend version)."""

    # -----------------------------------------------------------
    # Serve React SPA entry (index.html)
    # -----------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        """Serve the React single-page app."""
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "View", "dist")
        index_path = os.path.join(dist_dir, "index.html")

        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        else:
            return (
                "<h1>React build not found</h1>"
                "<p>Run <code>npm run build</code> inside the View folder.</p>",
                500,
            )

    # -----------------------------------------------------------
    # REST-like backend routes (used by frontend forms if needed)
    # -----------------------------------------------------------
    @app.route("/create", methods=["POST"])
    def create_room():
        """
        Handle 'Create New Room' form or frontend request.
        Body fields:
          - name
        """
        name = request.form.get("name", "").strip() or "Anonymous"

        # Create room in GameManager
        code = game_manager.create_room()

        # Redirect or respond JSON depending on frontend type
        if request.accept_mimetypes["application/json"]:
            return {"room_code": code, "name": name}
        return redirect(url_for("room", code=code, name=name))

    @app.route("/join", methods=["POST"])
    def join_room_route():
        """
        Handle 'Join Room' form or frontend request.
        Body fields:
          - name
          - code
        """
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip() or "Anonymous"

        if not code:
            flash("Please enter a room code.")
            return redirect(url_for("index"))

        if not game_manager.room_exists(code):
            flash("Room not found. Check the code and try again.")
            return redirect(url_for("index"))

        if request.accept_mimetypes["application/json"]:
            return {"room_code": code, "name": name}
        return redirect(url_for("room", code=code, name=name))

    @app.route("/room/<code>", methods=["GET"])
    def room(code):
        """
        Redirect directly to the React SPA.
        The frontend will handle reading room_code and player_name from query params.
        """
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "View", "dist")
        index_path = os.path.join(dist_dir, "index.html")

        name = request.args.get("name", "").strip() or "Anonymous"
        code = code.strip().upper()

        if not game_manager.room_exists(code):
            flash("Room does not exist or has already ended.")
            return redirect(url_for("index"))

        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        else:
            return (
                "<h1>React build missing</h1>"
                "<p>Run <code>npm run build</code> in the View directory before deploying.</p>",
                500,
            )

    # -----------------------------------------------------------
    # Optional: serve static assets from React build
    # -----------------------------------------------------------
    @app.route("/assets/<path:path>")
    def serve_react_assets(path):
        """Serve JS/CSS assets built by React."""
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "View", "dist", "assets")
        return send_from_directory(dist_dir, path)

