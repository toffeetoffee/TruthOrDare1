"""Tests for SocketIO events"""
import pytest
from app import socketio, game_manager


def test_socket_join_room(socketio_client, sample_room):
    """Test player joining via socket"""
    socketio_client.emit('join', {'room': sample_room, 'name': 'Alice'})
    received = socketio_client.get_received()
    
    # Should receive player_list event
    assert len(received) > 0
    player_list_event = received[0]
    assert player_list_event['name'] == 'player_list'
    assert 'Alice' in player_list_event['args'][0]['players']
    
    # Verify player was added to room
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'


def test_first_player_becomes_host(socketio_client, sample_room):
    """Test that the first player to join becomes host"""
    socketio_client.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    room = game_manager.get_room(sample_room)
    # Host should be set (not None)
    assert room.host_sid is not None
    # First player should be Alice
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'


def test_multiple_players_join(sample_room):
    """Test multiple players joining the same room"""
    from app import app
    
    # First player joins
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    # Second player joins
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    # Both players should be in the room
    assert len(room.players) == 2
    names = [p.name for p in room.players]
    assert 'Alice' in names
    assert 'Bob' in names
    
    # First player should still be host
    assert room.host_sid == room.players[0].socket_id


def test_player_leave_room(sample_room):
    """Test player leaving a room"""
    from app import app
    
    # Two players join
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 2
    
    # Bob leaves
    client2.emit('leave', {'room': sample_room})
    
    # Only Alice should remain
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'


def test_host_leaves_transfers_host(sample_room):
    """Test that when host leaves, host is transferred to next player"""
    from app import app
    
    # Two players join
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    # Store original host (should be first player)
    original_host = room.host_sid
    first_player_sid = room.players[0].socket_id
    assert original_host == first_player_sid
    
    # Alice (host) leaves
    client1.emit('leave', {'room': sample_room})
    
    # Bob should now be host
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 1
    assert room.players[0].name == 'Bob'
    assert room.host_sid == room.players[0].socket_id


def test_last_player_leaves_deletes_room(sample_room):
    """Test that room is deleted when last player leaves"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    assert sample_room in game_manager.rooms
    
    # Alice leaves (she's the only player)
    client1.emit('leave', {'room': sample_room})
    
    # Room should be deleted
    assert sample_room not in game_manager.rooms


def test_host_destroy_room(sample_room):
    """Test host can destroy room"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    assert sample_room in game_manager.rooms
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 2
    
    # Host destroys room
    client1.emit('destroy_room', {'room': sample_room})
    
    # Room should be deleted
    assert sample_room not in game_manager.rooms


def test_non_host_cannot_destroy_room(sample_room):
    """Test that non-host cannot destroy room"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    # Bob (non-host) tries to destroy room
    client2.emit('destroy_room', {'room': sample_room})
    
    # Room should still exist
    assert sample_room in game_manager.rooms
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 2


def test_socket_disconnect_removes_player(sample_room):
    """Test disconnecting removes player from room"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 2
    
    # Bob disconnects
    client2.disconnect()
    
    # Only Alice should remain
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 1
    assert room.players[0].name == 'Alice'


def test_host_disconnect_transfers_host(sample_room):
    """Test that when host disconnects, host is transferred"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    # Verify Alice is host (first player)
    assert room.host_sid == room.players[0].socket_id
    assert room.players[0].name == 'Alice'
    
    # Alice disconnects
    client1.disconnect()
    
    # Bob should be the new host
    room = game_manager.get_room(sample_room)
    assert len(room.players) == 1
    assert room.players[0].name == 'Bob'
    assert room.host_sid == room.players[0].socket_id


def test_update_settings_by_host(sample_room):
    """Test that host can update settings via socket"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    room = game_manager.get_room(sample_room)
    
    # Alice (host) updates settings
    client1.emit('update_settings', {
        'room': sample_room,
        'settings': {
            'countdown_duration': 20,
            'preparation_duration': 60
        }
    })
    
    # Settings should be updated
    assert room.settings['countdown_duration'] == 20
    assert room.settings['preparation_duration'] == 60


def test_non_host_cannot_update_settings(sample_room):
    """Test that non-host cannot update settings"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client2 = socketio.test_client(app)
    client2.emit('join', {'room': sample_room, 'name': 'Bob'})
    
    room = game_manager.get_room(sample_room)
    original_countdown = room.settings['countdown_duration']
    
    # Bob (non-host) tries to update settings
    client2.emit('update_settings', {
        'room': sample_room,
        'settings': {
            'countdown_duration': 999
        }
    })
    
    # Settings should remain unchanged
    assert room.settings['countdown_duration'] == original_countdown


def test_get_settings(sample_room):
    """Test getting current room settings"""
    from app import app
    
    client1 = socketio.test_client(app)
    client1.emit('join', {'room': sample_room, 'name': 'Alice'})
    
    client1.emit('get_settings', {'room': sample_room})
    
    received = client1.get_received()
    # Should receive settings_updated event
    settings_event = None
    for event in received:
        if event['name'] == 'settings_updated':
            settings_event = event
            break
    
    assert settings_event is not None
    assert 'settings' in settings_event['args'][0]