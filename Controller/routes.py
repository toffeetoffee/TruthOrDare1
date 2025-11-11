from flask import render_template, request, redirect, url_for, flash


def register_routes(app, game_manager):
    """Register HTTP routes for the Truth or Dare app."""

    @app.route("/", methods=["GET"])
    def index():
        """Home page: create / join room."""
        return render_template("index.html")

    @app.route("/create", methods=["POST"])
    def create_room():
        """Create a new room and redirect the host to it."""
        name = request.form.get("name", "").strip() or "Anonymous"

        # Create room in GameManager
        room_code = game_manager.create_room()

        # Redirect to the room page with the player's name in query params
        return redirect(url_for("room", code=room_code, name=name))

    @app.route("/join", methods=["POST"])
    def join_room_route():
        """Join an existing room and redirect the player to it."""
        name = request.form.get("name", "").strip() or "Anonymous"
        room_code = request.form.get("room", "").strip().upper()

        if not room_code or not game_manager.room_exists(room_code):
            flash("Room not found. Check the code and try again.")
            return redirect(url_for("index"))

        return redirect(url_for("room", code=room_code, name=name))

    @app.route("/room/<code>", methods=["GET"])
    def room(code):
        """Room page where the actual game UI lives."""
        # We don't strictly need to check existence here; the socket layer also validates,
        # but this gives nicer behavior if someone hits /room/<code> directly.
        if not game_manager.room_exists(code):
            flash("Room does not exist or has already ended.")
            return redirect(url_for("index"))

        name = request.args.get("name", "Anonymous")
        return render_template("room.html", room_code=code, name=name)