import string
import random
import threading
from Model.room import Room
from Model.player import Player

class GameManager:
    """Manages all game rooms with thread-safe operations"""
    
    def __init__(self):
        self.rooms = {}
        self._lock = threading.RLock()
    
    def create_room(self):
        """Create a new room and return the room code"""
        with self._lock:
            code = self._generate_code()
            self.rooms[code] = Room(code)
            return code
    
    def get_room(self, code):
        """Get a room by code (thread-safe)"""
        with self._lock:
            return self.rooms.get(code)
    
    def room_exists(self, code):
        """Check if a room exists"""
        with self._lock:
            return code in self.rooms
    
    def delete_room(self, code):
        """Delete a room"""
        with self._lock:
            if code in self.rooms:
                del self.rooms[code]
    
    def add_player_to_room(self, code, socket_id, name):
        """Add a player to a room"""
        with self._lock:
            if code not in self.rooms:
                self.rooms[code] = Room(code)
            
            player = Player(socket_id, name)
            self.rooms[code].add_player(player)
            return self.rooms[code]
    
    def remove_player_from_room(self, code, socket_id):
        """Remove a player from a room"""
        with self._lock:
            if code not in self.rooms:
                return None
            
            room = self.rooms[code]
            room.remove_player(socket_id)
            
            # Delete room if empty
            if room.is_empty():
                self.delete_room(code)
                return None
            
            return room
    
    def remove_player_from_all_rooms(self, socket_id):
        """Remove a player from all rooms (used on disconnect)"""
        with self._lock:
            # Create snapshot of room codes to avoid iteration during modification
            room_codes = list(self.rooms.keys())
            rooms_to_delete = []
            updated_rooms = []
            
            for code in room_codes:
                # Re-check existence in case another thread deleted it
                if code not in self.rooms:
                    continue
                    
                room = self.rooms[code]
                # Check if player is in this room
                if any(p.socket_id == socket_id for p in room.players):
                    room.remove_player(socket_id)
                    if room.is_empty():
                        rooms_to_delete.append(code)
                    else:
                        updated_rooms.append(code)
            
            # Delete empty rooms
            for code in rooms_to_delete:
                if code in self.rooms:  # Re-check existence
                    del self.rooms[code]
            
            return updated_rooms
    
    def _generate_code(self, length=6):
        """Generate a random room code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def to_dict(self):
        """Convert all rooms to dictionary format (for testing compatibility)"""
        with self._lock:
            return {code: room.to_dict() for code, room in self.rooms.items()}