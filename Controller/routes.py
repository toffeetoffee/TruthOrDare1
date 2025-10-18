"""
HTTP routes for the application.
"""

from flask import render_template, request, redirect, url_for
from Model.structural.room import Room


def register_routes(app, game_manager):
    """Register Flask routes"""
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/create', methods=['POST'])
    def create():
        name = request.form.get('name', '').strip()
        if not name:
            return redirect(url_for('index'))
        
        code = game_manager.create_room()
        return redirect(url_for('room', code=code, name=name))
    
    @app.route('/join', methods=['POST'])
    def join_post():
        code = request.form.get('code', '').strip().upper()
        name = request.form.get('name', '').strip()
        
        if not code or not name:
            return redirect(url_for('index'))
        
        # Create room if it doesn't exist
        if not game_manager.room_exists(code):
            game_manager.rooms[code] = Room(code)
        
        return redirect(url_for('room', code=code, name=name))
    
    @app.route('/room/<code>')
    def room(code):
        name = request.args.get('name', '')
        if not name:
            return redirect(url_for('index'))
        
        code = code.strip().upper()
        
        # Create room if it doesn't exist
        if not game_manager.room_exists(code):
            game_manager.rooms[code] = Room(code)
        
        return render_template('room.html', code=code, name=name)