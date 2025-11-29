import string
import random
import threading

from Model.room import Room
from Model.player import Player


class GameManager:
    def __init__(self):
        self.rooms = {}
        self._lock = threading.RLock()

    def create_room(self):
        with self._lock:
            code = self._gen_code()
            self.rooms[code] = Room(code)
            return code

    def get_room(self, code):
        with self._lock:
            return self.rooms.get(code)

    def room_exists(self, code):
        with self._lock:
            return code in self.rooms

    def delete_room(self, code):
        with self._lock:
            if code in self.rooms:
                del self.rooms[code]

    def add_player_to_room(self, code, socket_id, name):
        with self._lock:
            if code not in self.rooms:
                self.rooms[code] = Room(code)

            p = Player(socket_id, name)
            self.rooms[code].add_player(p)
            return self.rooms[code]

    def remove_player_from_room(self, code, socket_id):
        with self._lock:
            if code not in self.rooms:
                return None

            room = self.rooms[code]
            room.remove_player(socket_id)

            if room.is_empty():   # kill empty room
                self.delete_room(code)
                return None

            return room

    def remove_player_from_all_rooms(self, socket_id):
        with self._lock:
            codes = list(self.rooms.keys())
            to_del = []
            updated = []

            for code in codes:
                if code not in self.rooms:
                    continue

                room = self.rooms[code]
                if any(p.socket_id == socket_id for p in room.players):
                    room.remove_player(socket_id)
                    if room.is_empty():
                        to_del.append(code)
                    else:
                        updated.append(code)

            for code in to_del:
                if code in self.rooms:
                    del self.rooms[code]

            return updated

    def _gen_code(self, length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def to_dict(self):
        with self._lock:
            return {code: room.to_dict() for code, room in self.rooms.items()}
