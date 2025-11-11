from flask import render_template, request, redirect, url_for, flash


def register_routes(app, game_manager):
    """Register HTTP routes for the Truth or Dare app."""

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/create", methods=["POST"])
    def create_room():
        name = request.form.get("name", "").strip() or "Anonymous"
        code = game_manager.create_room()
        return redirect(url_for("room", code=code, name=name))

    @app.route("/join", methods=["POST"])
    def join_room_route():
        name = request.form.get("name", "").strip() or "Anonymous"
        code = request.form.get("room", "").strip().upper()

        if not code or not game_manager.room_exists(code):
            flash("Room not found. Check the code and try again.")
            return redirect(url_for("index"))

        return redirect(url_for("room", code=code, name=name))

    @app.route("/room/<code>", methods=["GET"])
    def room(code):
        """Room page."""
        if not game_manager.room_exists(code):
            flash("Room does not exist or has already ended.")
            return redirect(url_for("index"))

        name = request.args.get("name", "Anonymous")
        # 👇 Pass variables exactly as template expects
        return render_template("room.html", code=code, name=name)