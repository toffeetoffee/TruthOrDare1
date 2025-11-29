from flask import render_template, request, redirect, url_for, flash


def register_routes(app, game_manager):

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/create", methods=["POST"])
    def create_room():
        nm = request.form.get("name", "").strip() or "Anonymous"

        code = game_manager.create_room()

        # just pass the name via query so JS can grab it
        return redirect(url_for("room", code=code, name=nm))

    @app.route("/join", methods=["POST"])
    def join_room_route():
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip() or "Anonymous"

        if not code:
            flash("Please enter a room code.")
            return redirect(url_for("index"))

        if not game_manager.room_exists(code):
            flash("Room not found. Check the code and try again.")
            return redirect(url_for("index"))

        return redirect(url_for("room", code=code, name=name))

    @app.route("/room/<code>", methods=["GET"])
    def room(code):
        name = request.args.get("name", "").strip() or "Anonymous"

        code = code.strip().upper()

        if not game_manager.room_exists(code):
            flash("Room does not exist or has already ended.")
            return redirect(url_for("index"))

        return render_template("room.html", room_code=code, name=name)
