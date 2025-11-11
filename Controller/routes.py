from flask import render_template, request, redirect, url_for, flash


def register_routes(app, game_manager):
    """Register HTTP routes for the Truth or Dare app."""

    @app.route("/", methods=["GET"])
    def index():
        """Home page: create / join room."""
        return render_template("index.html")

    @app.route("/create", methods=["POST"])
    def create_room():
        """
        Handle 'Create New Room' form.
        Form fields (from index.html):
          - name
        """
        name = request.form.get("name", "").strip() or "Anonymous"

        # Create room in GameManager
        code = game_manager.create_room()

        # Redirect to the room page with the player's name in query params
        return redirect(url_for("room", code=code, name=name))

    @app.route("/join", methods=["POST"])
    def join_room_route():
        """
        Handle 'Join Room' form.
        Form fields (from index.html):
          - name
          - code   <-- IMPORTANT: this matches <input name="code">
        """
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip() or "Anonymous"

        if not code:
            flash("Please enter a room code.")
            return redirect(url_for("index"))

        # Check that the room actually exists
        if not game_manager.room_exists(code):
            flash("Room not found. Check the code and try again.")
            return redirect(url_for("index"))

        # Redirect into the room
        return redirect(url_for("room", code=code, name=name))

    @app.route("/room/<code>", methods=["GET"])
    def room(code):
        """
        Room page where the actual game UI lives.
        URL: /room/<code>?name=<player name>
        """
        name = request.args.get("name", "").strip() or "Anonymous"

        code = code.strip().upper()

        # If the room somehow doesn't exist (e.g. destroyed), go home
        if not game_manager.room_exists(code):
            flash("Room does not exist or has already ended.")
            return redirect(url_for("index"))

        # Pass 'room_code' so room.html + JS can use it
        return render_template("room.html", room_code=code, name=name)
