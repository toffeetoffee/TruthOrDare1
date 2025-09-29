from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import string, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-this-with-a-secret'
socketio = SocketIO(app, cors_allowed_origins='*')

# In-memory store: room_code -> list of players
# Each player: {'sid': socket_id, 'name': username}
rooms = {}

def gen_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('index'))
    code = gen_code(6)
    rooms[code] = []
    return redirect(url_for('room', code=code, name=name))

@app.route('/join', methods=['POST'])
def join_post():
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    if not code or not name:
        return redirect(url_for('index'))
    # Create room if missing
    rooms.setdefault(code, [])
    return redirect(url_for('room', code=code, name=name))

@app.route('/room/<code>')
def room(code):
    name = request.args.get('name', '')
    if not name:
        return redirect(url_for('index'))
    code = code.strip().upper()
    rooms.setdefault(code, [])
    return render_template('room.html', code=code, name=name)

# --- Socket events ---
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    name = data.get('name', 'Anonymous')
    if not room:
        return
    
    join_room(room)
    
    # Add player to room
    player = {'sid': request.sid, 'name': name}
    rooms.setdefault(room, [])
    
    # Check if player already exists (reconnect), otherwise add
    existing = [p for p in rooms[room] if p['sid'] == request.sid]
    if not existing:
        rooms[room].append(player)
    
    # Broadcast updated player list to everyone in room
    player_names = [p['name'] for p in rooms[room]]
    emit('player_list', {'players': player_names}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    # Remove player from all rooms
    for room_code in rooms:
        rooms[room_code] = [p for p in rooms[room_code] if p['sid'] != request.sid]
        # Broadcast updated list
        player_names = [p['name'] for p in rooms[room_code]]
        emit('player_list', {'players': player_names}, room=room_code)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)