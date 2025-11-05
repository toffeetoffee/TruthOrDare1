"""
Tests for Room Management functionality
Related User Stories: US-001 to US-007
"""
import pytest
from Model.game_manager import GameManager
from Model.room import Room
from Model.player import Player


@pytest.fixture
def game_manager():
    """Fixture to provide a fresh GameManager instance"""
    return GameManager()


@pytest.fixture
def sample_room(game_manager):
    """Fixture to provide a room with one player"""
    code = game_manager.create_room()
    game_manager.add_player_to_room(code, 'socket_1', 'Alice')
    return game_manager.get_room(code)


class TestRoomCreation:
    """Tests for room creation (US-001)"""
    
    def test_rm_001_create_room_generates_code(self, game_manager):
        """
        Test ID: RM-001
        User Story: US-001
        Description: Verify that creating a room generates a unique 6-character code
        Acceptance Criteria: Room code must be 6 alphanumeric characters
        """
        code = game_manager.create_room()
        
        assert code is not None
        assert len(code) == 6
        assert code.isalnum()
        assert code.isupper() or code.isdigit()
    
    def test_rm_002_create_room_unique_codes(self, game_manager):
        """
        Test ID: RM-002
        User Story: US-001
        Description: Verify that each created room has a unique code
        Acceptance Criteria: Room code must be unique across all active rooms
        """
        code1 = game_manager.create_room()
        code2 = game_manager.create_room()
        code3 = game_manager.create_room()
        
        assert code1 != code2
        assert code1 != code3
        assert code2 != code3
    
    def test_rm_003_room_creator_becomes_host(self, game_manager):
        """
        Test ID: RM-003
        User Story: US-001
        Description: Verify that the first player to join becomes the host
        Acceptance Criteria: Room creator becomes the host with administrative privileges
        """
        code = game_manager.create_room()
        room = game_manager.add_player_to_room(code, 'socket_123', 'Alice')
        
        assert room.host_sid == 'socket_123'
        assert room.is_host('socket_123')
    
    def test_rm_004_room_exists_in_manager(self, game_manager):
        """
        Test ID: RM-004
        User Story: US-001
        Description: Verify that created room is stored in game manager
        Acceptance Criteria: Room is accessible through game manager
        """
        code = game_manager.create_room()
        
        assert game_manager.room_exists(code)
        assert game_manager.get_room(code) is not None


class TestRoomJoining:
    """Tests for joining rooms (US-002)"""
    
    def test_rm_005_join_existing_room(self, game_manager):
        """
        Test ID: RM-005
        User Story: US-002
        Description: Verify that a user can join an existing room with valid code
        Acceptance Criteria: Users are added to the room's player list upon successful join
        """
        code = game_manager.create_room()
        room = game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        
        assert len(room.players) == 1
        assert room.players[0].name == 'Alice'
        assert room.players[0].socket_id == 'socket_1'
    
    def test_rm_006_join_room_creates_if_not_exists(self, game_manager):
        """
        Test ID: RM-006
        User Story: US-002
        Description: Verify that joining a non-existent room creates it
        Acceptance Criteria: Room is created if it doesn't exist when joining
        """
        code = 'ABC123'
        assert not game_manager.room_exists(code)
        
        room = game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        
        assert game_manager.room_exists(code)
        assert room is not None
    
    def test_rm_007_multiple_players_join_room(self, game_manager):
        """
        Test ID: RM-007
        User Story: US-002, US-003
        Description: Verify that multiple players can join the same room
        Acceptance Criteria: Multiple users can join and be added to player list
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        game_manager.add_player_to_room(code, 'socket_2', 'Bob')
        room = game_manager.add_player_to_room(code, 'socket_3', 'Charlie')
        
        assert len(room.players) == 3
        player_names = [p.name for p in room.players]
        assert 'Alice' in player_names
        assert 'Bob' in player_names
        assert 'Charlie' in player_names
    
    def test_rm_008_duplicate_socket_not_added_twice(self, game_manager):
        """
        Test ID: RM-008
        User Story: US-002
        Description: Verify that the same socket cannot join twice
        Acceptance Criteria: Player with same socket_id is not duplicated
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        room = game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        
        assert len(room.players) == 1


class TestPlayerList:
    """Tests for player list management (US-003)"""
    
    def test_rm_009_get_player_names(self, sample_room):
        """
        Test ID: RM-009
        User Story: US-003
        Description: Verify that player names can be retrieved from room
        Acceptance Criteria: Player names list is accurate and current
        """
        sample_room.add_player(Player('socket_2', 'Bob'))
        sample_room.add_player(Player('socket_3', 'Charlie'))
        
        names = sample_room.get_player_names()
        
        assert len(names) == 3
        assert 'Alice' in names
        assert 'Bob' in names
        assert 'Charlie' in names
    
    def test_rm_010_player_count_accurate(self, sample_room):
        """
        Test ID: RM-010
        User Story: US-003
        Description: Verify that player count is accurate
        Acceptance Criteria: Current player count reflects actual number of players
        """
        assert len(sample_room.players) == 1
        
        sample_room.add_player(Player('socket_2', 'Bob'))
        assert len(sample_room.players) == 2
        
        sample_room.add_player(Player('socket_3', 'Charlie'))
        assert len(sample_room.players) == 3
    
    def test_rm_011_get_player_by_socket_id(self, sample_room):
        """
        Test ID: RM-011
        User Story: US-003
        Description: Verify that players can be retrieved by socket ID
        Acceptance Criteria: Correct player is returned for given socket ID
        """
        player = sample_room.get_player_by_sid('socket_1')
        
        assert player is not None
        assert player.name == 'Alice'
        assert player.socket_id == 'socket_1'
    
    def test_rm_012_get_player_by_name(self, sample_room):
        """
        Test ID: RM-012
        User Story: US-003
        Description: Verify that players can be retrieved by name
        Acceptance Criteria: Correct player is returned for given name
        """
        player = sample_room.get_player_by_name('Alice')
        
        assert player is not None
        assert player.name == 'Alice'


class TestLeaveRoom:
    """Tests for leaving rooms (US-004)"""
    
    def test_rm_013_player_can_leave_room(self, game_manager):
        """
        Test ID: RM-013
        User Story: US-004
        Description: Verify that a player can leave a room
        Acceptance Criteria: Player is removed from room's player list
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        game_manager.add_player_to_room(code, 'socket_2', 'Bob')
        
        room = game_manager.remove_player_from_room(code, 'socket_1')
        
        assert room is not None
        assert len(room.players) == 1
        assert room.players[0].name == 'Bob'
    
    def test_rm_014_remove_nonexistent_player(self, game_manager):
        """
        Test ID: RM-014
        User Story: US-004
        Description: Verify that removing a non-existent player doesn't crash
        Acceptance Criteria: No error when removing player not in room
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        
        room = game_manager.remove_player_from_room(code, 'socket_999')
        
        assert room is not None
        assert len(room.players) == 1
    
    def test_rm_015_remove_player_from_nonexistent_room(self, game_manager):
        """
        Test ID: RM-015
        User Story: US-004
        Description: Verify handling of removing player from non-existent room
        Acceptance Criteria: Returns None when room doesn't exist
        """
        room = game_manager.remove_player_from_room('INVALID', 'socket_1')
        
        assert room is None


class TestDestroyRoom:
    """Tests for room destruction (US-005)"""
    
    def test_rm_016_host_can_destroy_room(self, game_manager):
        """
        Test ID: RM-016
        User Story: US-005
        Description: Verify that host can destroy the room
        Acceptance Criteria: Room is deleted from game manager
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        
        game_manager.delete_room(code)
        
        assert not game_manager.room_exists(code)
        assert game_manager.get_room(code) is None
    
    def test_rm_017_is_host_check(self, sample_room):
        """
        Test ID: RM-017
        User Story: US-005
        Description: Verify that host status can be checked
        Acceptance Criteria: is_host() returns True for host, False for others
        """
        sample_room.add_player(Player('socket_2', 'Bob'))
        
        assert sample_room.is_host('socket_1')
        assert not sample_room.is_host('socket_2')


class TestAutoDeleteEmptyRoom:
    """Tests for automatic room cleanup (US-006)"""
    
    def test_rm_018_room_deleted_when_empty(self, game_manager):
        """
        Test ID: RM-018
        User Story: US-006
        Description: Verify that room is deleted when last player leaves
        Acceptance Criteria: Room is automatically deleted when it becomes empty
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        
        room = game_manager.remove_player_from_room(code, 'socket_1')
        
        assert room is None
        assert not game_manager.room_exists(code)
    
    def test_rm_019_room_not_deleted_with_remaining_players(self, game_manager):
        """
        Test ID: RM-019
        User Story: US-006
        Description: Verify that room persists when players remain
        Acceptance Criteria: Room continues to exist with remaining players
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        game_manager.add_player_to_room(code, 'socket_2', 'Bob')
        
        room = game_manager.remove_player_from_room(code, 'socket_1')
        
        assert room is not None
        assert game_manager.room_exists(code)
        assert len(room.players) == 1
    
    def test_rm_020_is_empty_check(self, sample_room):
        """
        Test ID: RM-020
        User Story: US-006
        Description: Verify that empty room check works correctly
        Acceptance Criteria: is_empty() returns correct boolean value
        """
        assert not sample_room.is_empty()
        
        sample_room.remove_player('socket_1')
        assert sample_room.is_empty()


class TestHostTransfer:
    """Tests for host transfer mechanism (US-007)"""
    
    def test_rm_021_host_transfer_on_leave(self, game_manager):
        """
        Test ID: RM-021
        User Story: US-007
        Description: Verify that host role transfers when current host leaves
        Acceptance Criteria: First remaining player becomes new host
        """
        code = game_manager.create_room()
        game_manager.add_player_to_room(code, 'socket_1', 'Alice')
        game_manager.add_player_to_room(code, 'socket_2', 'Bob')
        game_manager.add_player_to_room(code, 'socket_3', 'Charlie')
        
        room = game_manager.remove_player_from_room(code, 'socket_1')
        
        assert room.host_sid == 'socket_2'
        assert room.is_host('socket_2')
        assert not room.is_host('socket_1')
    
    def test_rm_022_no_host_when_room_empty(self, sample_room):
        """
        Test ID: RM-022
        User Story: US-007
        Description: Verify that host_sid is None when room is empty
        Acceptance Criteria: host_sid is None after last player leaves
        """
        sample_room.remove_player('socket_1')
        
        assert sample_room.host_sid is None
        assert sample_room.is_empty()
    
    def test_rm_023_remove_from_all_rooms(self, game_manager):
        """
        Test ID: RM-023
        User Story: US-004, US-007
        Description: Verify player is removed from all rooms on disconnect
        Acceptance Criteria: Player removed from all rooms, host transfers if needed
        """
        code1 = game_manager.create_room()
        code2 = game_manager.create_room()
        
        game_manager.add_player_to_room(code1, 'socket_1', 'Alice')
        game_manager.add_player_to_room(code1, 'socket_2', 'Bob')
        game_manager.add_player_to_room(code2, 'socket_1', 'Alice')
        
        updated_rooms = game_manager.remove_player_from_all_rooms('socket_1')
        
        assert code1 in updated_rooms
        assert code2 not in updated_rooms  # Room deleted because it became empty
        
        room1 = game_manager.get_room(code1)
        assert room1 is not None
        assert len(room1.players) == 1
        assert room1.players[0].name == 'Bob'
        
        room2 = game_manager.get_room(code2)
        assert room2 is None  # Deleted because it was empty


class TestRoomInitialization:
    """Tests for room initialization and default content"""
    
    def test_rm_024_room_initializes_with_defaults(self):
        """
        Test ID: RM-024
        User Story: US-028
        Description: Verify that new room loads default truths and dares
        Acceptance Criteria: Room has default_truths and default_dares populated
        """
        room = Room('TEST01')
        
        assert room.default_truths is not None
        assert room.default_dares is not None
        assert len(room.default_truths) > 0
        assert len(room.default_dares) > 0
    
    def test_rm_025_room_initializes_game_state(self):
        """
        Test ID: RM-025
        User Story: US-009
        Description: Verify that room initializes with game state
        Acceptance Criteria: Room has a GameState object in lobby phase
        """
        room = Room('TEST01')
        
        assert room.game_state is not None
        assert room.game_state.phase == 'lobby'
        assert not room.game_state.started
    
    def test_rm_026_room_initializes_settings(self):
        """
        Test ID: RM-026
        User Story: US-045
        Description: Verify that room initializes with default settings
        Acceptance Criteria: Room has settings dict with default values
        """
        room = Room('TEST01')
        
        assert room.settings is not None
        assert room.settings['countdown_duration'] == 10
        assert room.settings['preparation_duration'] == 30
        assert room.settings['selection_duration'] == 10
        assert room.settings['truth_dare_duration'] == 60
        assert room.settings['skip_duration'] == 5
        assert room.settings['max_rounds'] == 10
        assert room.settings['minigame_chance'] == 20
        assert room.settings['ai_generation_enabled'] == True
    
    def test_rm_027_player_receives_defaults_on_join(self, sample_room):
        """
        Test ID: RM-027
        User Story: US-028
        Description: Verify that players receive default content when joining
        Acceptance Criteria: Player's truth_dare_list is populated with defaults
        """
        player = sample_room.get_player_by_name('Alice')
        
        truths = player.truth_dare_list.get_truths()
        dares = player.truth_dare_list.get_dares()
        
        assert len(truths) > 0
        assert len(dares) > 0
        
        # Check that defaults are marked as defaults
        assert any(t['is_default'] for t in truths)
        assert any(d['is_default'] for d in dares)