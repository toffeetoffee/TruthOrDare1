from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import string, random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-this-with-a-secret'
# allow larger socket payloads for pasted images (adjust as needed)
socketio = SocketIO(app, cors_allowed_origins='*', max_http_buffer_size=10000000)

# In-memory store: room_code -> html (contenteditable HTML)
rooms = {}

def gen_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    code = gen_code(6)
    rooms[code] = ''
    return redirect(url_for('room', code=code))

@app.route('/join', methods=['POST'])
def join_post():
    code = request.form.get('code', '').strip().upper()
    if not code:
        return redirect(url_for('index'))
    # Create room if missing (optional)
    rooms.setdefault(code, '')
    return redirect(url_for('room', code=code))

@app.route('/room/<code>')
def room(code):
    code = code.strip().upper()
    rooms.setdefault(code, '')
    return render_template('room.html', code=code)

# --- Socket events ---
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if not room:
        return
    join_room(room)
    # send current content (html) to the joining client only
    emit('init', {'html': rooms.get(room, '')}, to=request.sid)

@socketio.on('content_change')
def on_content_change(data):
    room = data.get('room')
    html = data.get('html', '')
    if not room:
        return
    rooms[room] = html
    # broadcast to everyone in room except the sender
    emit('content_change', {'html': html}, room=room, include_self=False)

if __name__ == '__main__':
    # For local dev: socketio.run(app)
    socketio.run(app, host='0.0.0.0', port=5000)