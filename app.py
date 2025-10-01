from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import string, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-this-with-a-secret'
socketio = SocketIO(app, cors_allowed_origins='*')

# In-memory store: room_code -> {'host_sid': str, 'players': list}
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
    rooms[code] = {'host_sid': None, 'players': []}
    return redirect(url_for('room', code=code, name=name))

@app.route('/join', methods=['POST'])
def join_post():
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    if not code or not name:
        return redirect(url_for('index'))
    # Create room if missing
    if code not in rooms:
        rooms[code] = {'host_sid': None, 'players': []}
    return redirect(url_for('room', code=code, name=name))

@app.route('/room/<code>')
def room(code):
    name = request.args.get('name', '')
    if not name:
        return redirect(url_for('index'))
    code = code.strip().upper()
    if code not in rooms:
        rooms[code] = {'host_sid': None, 'players': []}
    return render_template('room.html', code=code, name=name)

# --- Socket events ---
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    name = data.get('name', 'Anonymous')
    if not room:
        return
    
    join_room(room)
    
    if room not in rooms:
        rooms[room] = {'host_sid': None, 'players': []}
    
    # Add player to room
    player = {'sid': request.sid, 'name': name}
    
    # Check if player already exists (reconnect)
    existing = [p for p in rooms[room]['players'] if p['sid'] == request.sid]
    if not existing:
        rooms[room]['players'].append(player)
    
    # Set host if this is the first player
    if rooms[room]['host_sid'] is None:
        rooms[room]['host_sid'] = request.sid
    
    # Send player list and host info to everyone
    broadcast_room_state(room)

@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if not room or room not in rooms:
        return
    
    # Remove player
    rooms[room]['players'] = [p for p in rooms[room]['players'] if p['sid'] != request.sid]
    leave_room(room)
    
    # If host left, transfer to next player or close room
    if rooms[room]['host_sid'] == request.sid:
        if len(rooms[room]['players']) > 0:
            # Transfer host to first remaining player
            rooms[room]['host_sid'] = rooms[room]['players'][0]['sid']
        else:
            # No players left, delete room
            del rooms[room]
            return
    
    # Broadcast updated state
    broadcast_room_state(room)
    
    # Notify the leaving player
    emit('left_room', {}, to=request.sid)

@socketio.on('destroy_room')
def on_destroy_room(data):
    room = data.get('room')
    if not room or room not in rooms:
        return
    
    # Only host can destroy
    if rooms[room]['host_sid'] != request.sid:
        return
    
    # Notify all players
    emit('room_destroyed', {}, room=room)
    
    # Delete room
    del rooms[room]

@socketio.on('disconnect')
def on_disconnect():
    # Remove player from all rooms
    for room_code in list(rooms.keys()):
        original_count = len(rooms[room_code]['players'])
        rooms[room_code]['players'] = [p for p in rooms[room_code]['players'] if p['sid'] != request.sid]
        
        # If player was removed
        if len(rooms[room_code]['players']) < original_count:
            # If host disconnected, transfer or delete room
            if rooms[room_code]['host_sid'] == request.sid:
                if len(rooms[room_code]['players']) > 0:
                    rooms[room_code]['host_sid'] = rooms[room_code]['players'][0]['sid']
                else:
                    del rooms[room_code]
                    continue
            
            # Broadcast updated state
            broadcast_room_state(room_code)

def broadcast_room_state(room_code):
    """Send updated player list and host info to all players in room"""
    if room_code not in rooms:
        return
    
    player_names = [p['name'] for p in rooms[room_code]['players']]
    host_sid = rooms[room_code]['host_sid']
    
    emit('player_list', {
        'players': player_names,
        'host_sid': host_sid
    }, room=room_code)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)