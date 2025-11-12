from flask import render_template, request, redirect, url_for

def register_routes(app, game_manager):
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.post('/create')
    def create_room():
        name = request.form.get('name', 'Anonymous').strip() or 'Anonymous'
        code = game_manager.create_room()
        return redirect(url_for('room', code=code, name=name))

    @app.post('/join')
    def join_room_form():
        name = request.form.get('name', 'Anonymous').strip() or 'Anonymous'
        code = (request.form.get('code', '').strip() or '').upper()
        if not code:
            return redirect(url_for('home'))
        if not game_manager.room_exists(code):
            # Create a temp room and then map it to requested code
            temp_code = game_manager.create_room()
            game_manager.rooms[code] = game_manager.rooms.pop(temp_code)
            game_manager.rooms[code].code = code
        return redirect(url_for('room', code=code, name=name))

    @app.get('/room/<code>')
    def room(code):
        name = request.args.get('name', 'Anonymous')
        return render_template('room.html', room_code=code, name=name)
