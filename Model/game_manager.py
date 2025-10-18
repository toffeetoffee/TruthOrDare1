import string
import random
from Model.room import Room
from Model.player import Player

class GameManager:
    """Manages all game rooms"""
    
    def __init__(self):
        self.rooms = {}
    
    def create_room(self):
        """Create a new room and return the room code"""
        code = self._generate_code()
        self.rooms[code] = Room(code)
        return code
    
    def get_room(self, code):
        """Get a room by code"""
        return self.rooms.get(code)
    
    def room_exists(self, code):
        """Check if a room exists"""
        return code in self.rooms
    
    def delete_room(self, code):
        """Delete a room"""
        if code in self.rooms:
            del self.rooms[code]
    
    def add_player_to_room(self, code, socket_id, name):
        """Add a player to a room"""
        if code not in self.rooms:
            self.rooms[code] = Room(code)
        
        player = Player(socket_id, name)
        self.rooms[code].add_player(player)
        return self.rooms[code]
    
    def remove_player_from_room(self, code, socket_id):
        """Remove a player from a room"""
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
        rooms_to_delete = []
        updated_rooms = []
        
        for code, room in self.rooms.items():
            # Check if player is in this room
            if any(p.socket_id == socket_id for p in room.players):
                room.remove_player(socket_id)
                if room.is_empty():
                    rooms_to_delete.append(code)
                else:
                    updated_rooms.append(code)
        
        # Delete empty rooms
        for code in rooms_to_delete:
            self.delete_room(code)
        
        return updated_rooms
    
    def _generate_code(self, length=6):
        """Generate a random room code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def to_dict(self):
        """Convert all rooms to dictionary format (for testing compatibility)"""
        return {code: room.to_dict() for code, room in self.rooms.items()}
