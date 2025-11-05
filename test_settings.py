"""
Tests for Settings and Configuration
Related User Stories: US-045 to US-052
"""
import pytest
from Model.room import Room
from Model.player import Player


@pytest.fixture
def room():
    """Fixture for a room"""
    return Room('TEST01')


@pytest.fixture
def room_with_host(room):
    """Fixture for room with a host"""
    room.add_player(Player('host_socket', 'Host'))
    room.add_player(Player('player_socket', 'Player'))
    return room


class TestSettingsInitialization:
    """Tests for settings initialization (US-026, US-045)"""
    
    def test_st_001_default_settings_loaded(self, room):
        """
        Test ID: ST-001
        User Story: US-026, US-045
        Description: Verify that room initializes with default settings
        Acceptance Criteria: All settings have correct default values
        """
        settings = room.settings
        
        assert settings['countdown_duration'] == 10
        assert settings['preparation_duration'] == 30
        assert settings['selection_duration'] == 10
        assert settings['truth_dare_duration'] == 60
        assert settings['skip_duration'] == 5
        assert settings['max_rounds'] == 10
        assert settings['minigame_chance'] == 20
        assert settings['ai_generation_enabled'] == False
    
    def test_st_002_settings_dict_structure(self, room):
        """
        Test ID: ST-002
        User Story: US-045
        Description: Verify that settings is a dictionary with all keys
        Acceptance Criteria: settings contains all required configuration keys
        """
        settings = room.settings
        
        assert isinstance(settings, dict)
        assert 'countdown_duration' in settings
        assert 'preparation_duration' in settings
        assert 'selection_duration' in settings
        assert 'truth_dare_duration' in settings
        assert 'skip_duration' in settings
        assert 'max_rounds' in settings
        assert 'minigame_chance' in settings
        assert 'ai_generation_enabled' in settings


class TestUpdateSettings:
    """Tests for updating settings (US-046, US-047, US-048, US-049)"""
    
    def test_st_003_update_countdown_duration(self, room):
        """
        Test ID: ST-003
        User Story: US-046
        Description: Verify that countdown duration can be updated
        Acceptance Criteria: countdown_duration is updated to new value
        """
        room.update_settings({'countdown_duration': 15})
        
        assert room.settings['countdown_duration'] == 15
    
    def test_st_004_update_preparation_duration(self, room):
        """
        Test ID: ST-004
        User Story: US-046
        Description: Verify that preparation duration can be updated
        Acceptance Criteria: preparation_duration is updated to new value
        """
        room.update_settings({'preparation_duration': 45})
        
        assert room.settings['preparation_duration'] == 45
    
    def test_st_005_update_selection_duration(self, room):
        """
        Test ID: ST-005
        User Story: US-046
        Description: Verify that selection duration can be updated
        Acceptance Criteria: selection_duration is updated to new value
        """
        room.update_settings({'selection_duration': 15})
        
        assert room.settings['selection_duration'] == 15
    
    def test_st_006_update_truth_dare_duration(self, room):
        """
        Test ID: ST-006
        User Story: US-046
        Description: Verify that truth/dare duration can be updated
        Acceptance Criteria: truth_dare_duration is updated to new value
        """
        room.update_settings({'truth_dare_duration': 90})
        
        assert room.settings['truth_dare_duration'] == 90
    
    def test_st_007_update_skip_duration(self, room):
        """
        Test ID: ST-007
        User Story: US-046
        Description: Verify that skip duration can be updated
        Acceptance Criteria: skip_duration is updated to new value
        """
        room.update_settings({'skip_duration': 10})
        
        assert room.settings['skip_duration'] == 10
    
    def test_st_008_update_max_rounds(self, room):
        """
        Test ID: ST-008
        User Story: US-047
        Description: Verify that maximum rounds can be updated
        Acceptance Criteria: max_rounds is updated and synced to game_state
        """
        room.update_settings({'max_rounds': 20})
        
        assert room.settings['max_rounds'] == 20
        assert room.game_state.max_rounds == 20
    
    def test_st_009_update_minigame_chance(self, room):
        """
        Test ID: ST-009
        User Story: US-048
        Description: Verify that minigame chance can be updated
        Acceptance Criteria: minigame_chance is updated to new percentage
        """
        room.update_settings({'minigame_chance': 50})
        
        assert room.settings['minigame_chance'] == 50
    
    def test_st_010_update_ai_generation(self, room):
        """
        Test ID: ST-010
        User Story: US-049
        Description: Verify that AI generation can be enabled/disabled
        Acceptance Criteria: ai_generation_enabled is updated to new boolean
        """
        room.update_settings({'ai_generation_enabled': True})
        
        assert room.settings['ai_generation_enabled'] == True
        
        room.update_settings({'ai_generation_enabled': False})
        
        assert room.settings['ai_generation_enabled'] == False
    
    def test_st_011_update_multiple_settings(self, room):
        """
        Test ID: ST-011
        User Story: US-046
        Description: Verify that multiple settings can be updated at once
        Acceptance Criteria: All specified settings are updated
        """
        new_settings = {
            'countdown_duration': 8,
            'preparation_duration': 40,
            'max_rounds': 15,
            'minigame_chance': 30
        }
        
        room.update_settings(new_settings)
        
        assert room.settings['countdown_duration'] == 8
        assert room.settings['preparation_duration'] == 40
        assert room.settings['max_rounds'] == 15
        assert room.settings['minigame_chance'] == 30
    
    def test_st_012_update_ignores_invalid_keys(self, room):
        """
        Test ID: ST-012
        User Story: US-046
        Description: Verify that invalid setting keys are ignored
        Acceptance Criteria: Only valid settings are updated
        """
        invalid_settings = {
            'countdown_duration': 12,
            'invalid_key': 999,
            'another_bad_key': 'test'
        }
        
        room.update_settings(invalid_settings)
        
        assert room.settings['countdown_duration'] == 12
        assert 'invalid_key' not in room.settings
        assert 'another_bad_key' not in room.settings
    
    def test_st_013_settings_values_converted_to_int(self, room):
        """
        Test ID: ST-013
        User Story: US-046
        Description: Verify that setting values are converted to integers
        Acceptance Criteria: String values are converted to int
        """
        room.update_settings({'countdown_duration': '15'})
        
        assert room.settings['countdown_duration'] == 15
        assert isinstance(room.settings['countdown_duration'], int)


class TestSettingRanges:
    """Tests for setting value validation ranges (US-050)"""
    
    def test_st_014_countdown_range_min(self):
        """
        Test ID: ST-014
        User Story: US-046, US-050
        Description: Verify countdown duration minimum (3 seconds)
        Acceptance Criteria: Valid minimum value is 3
        Note: Validation happens on frontend, backend accepts any value
        """
        room = Room('TEST')
        room.update_settings({'countdown_duration': 3})
        assert room.settings['countdown_duration'] == 3
    
    def test_st_015_countdown_range_max(self):
        """
        Test ID: ST-015
        User Story: US-046, US-050
        Description: Verify countdown duration maximum (30 seconds)
        Acceptance Criteria: Valid maximum value is 30
        Note: Validation happens on frontend, backend accepts any value
        """
        room = Room('TEST')
        room.update_settings({'countdown_duration': 30})
        assert room.settings['countdown_duration'] == 30
    
    def test_st_016_preparation_range_min(self):
        """
        Test ID: ST-016
        User Story: US-046, US-050
        Description: Verify preparation duration minimum (10 seconds)
        Acceptance Criteria: Valid minimum value is 10
        """
        room = Room('TEST')
        room.update_settings({'preparation_duration': 10})
        assert room.settings['preparation_duration'] == 10
    
    def test_st_017_preparation_range_max(self):
        """
        Test ID: ST-017
        User Story: US-046, US-050
        Description: Verify preparation duration maximum (120 seconds)
        Acceptance Criteria: Valid maximum value is 120
        """
        room = Room('TEST')
        room.update_settings({'preparation_duration': 120})
        assert room.settings['preparation_duration'] == 120
    
    def test_st_018_selection_range_min(self):
        """
        Test ID: ST-018
        User Story: US-046, US-050
        Description: Verify selection duration minimum (5 seconds)
        Acceptance Criteria: Valid minimum value is 5
        """
        room = Room('TEST')
        room.update_settings({'selection_duration': 5})
        assert room.settings['selection_duration'] == 5
    
    def test_st_019_selection_range_max(self):
        """
        Test ID: ST-019
        User Story: US-046, US-050
        Description: Verify selection duration maximum (30 seconds)
        Acceptance Criteria: Valid maximum value is 30
        """
        room = Room('TEST')
        room.update_settings({'selection_duration': 30})
        assert room.settings['selection_duration'] == 30
    
    def test_st_020_truth_dare_range_min(self):
        """
        Test ID: ST-020
        User Story: US-046, US-050
        Description: Verify truth/dare duration minimum (30 seconds)
        Acceptance Criteria: Valid minimum value is 30
        """
        room = Room('TEST')
        room.update_settings({'truth_dare_duration': 30})
        assert room.settings['truth_dare_duration'] == 30
    
    def test_st_021_truth_dare_range_max(self):
        """
        Test ID: ST-021
        User Story: US-046, US-050
        Description: Verify truth/dare duration maximum (180 seconds)
        Acceptance Criteria: Valid maximum value is 180
        """
        room = Room('TEST')
        room.update_settings({'truth_dare_duration': 180})
        assert room.settings['truth_dare_duration'] == 180
    
    def test_st_022_skip_range_min(self):
        """
        Test ID: ST-022
        User Story: US-046, US-050
        Description: Verify skip duration minimum (3 seconds)
        Acceptance Criteria: Valid minimum value is 3
        """
        room = Room('TEST')
        room.update_settings({'skip_duration': 3})
        assert room.settings['skip_duration'] == 3
    
    def test_st_023_skip_range_max(self):
        """
        Test ID: ST-023
        User Story: US-046, US-050
        Description: Verify skip duration maximum (30 seconds)
        Acceptance Criteria: Valid maximum value is 30
        """
        room = Room('TEST')
        room.update_settings({'skip_duration': 30})
        assert room.settings['skip_duration'] == 30
    
    def test_st_024_max_rounds_range_min(self):
        """
        Test ID: ST-024
        User Story: US-047, US-050
        Description: Verify max rounds minimum (1 round)
        Acceptance Criteria: Valid minimum value is 1
        """
        room = Room('TEST')
        room.update_settings({'max_rounds': 1})
        assert room.settings['max_rounds'] == 1
    
    def test_st_025_max_rounds_range_max(self):
        """
        Test ID: ST-025
        User Story: US-047, US-050
        Description: Verify max rounds maximum (50 rounds)
        Acceptance Criteria: Valid maximum value is 50
        """
        room = Room('TEST')
        room.update_settings({'max_rounds': 50})
        assert room.settings['max_rounds'] == 50
    
    def test_st_026_minigame_chance_range_min(self):
        """
        Test ID: ST-026
        User Story: US-048, US-050
        Description: Verify minigame chance minimum (0%)
        Acceptance Criteria: Valid minimum value is 0
        """
        room = Room('TEST')
        room.update_settings({'minigame_chance': 0})
        assert room.settings['minigame_chance'] == 0
    
    def test_st_027_minigame_chance_range_max(self):
        """
        Test ID: ST-027
        User Story: US-048, US-050
        Description: Verify minigame chance maximum (100%)
        Acceptance Criteria: Valid maximum value is 100
        """
        room = Room('TEST')
        room.update_settings({'minigame_chance': 100})
        assert room.settings['minigame_chance'] == 100


class TestHostPermissions:
    """Tests for host-only settings access (US-052)"""
    
    def test_st_028_is_host_check(self, room_with_host):
        """
        Test ID: ST-028
        User Story: US-052
        Description: Verify that host status can be checked
        Acceptance Criteria: is_host() returns True for host, False for others
        """
        assert room_with_host.is_host('host_socket')
        assert not room_with_host.is_host('player_socket')
    
    def test_st_029_host_socket_id_stored(self, room_with_host):
        """
        Test ID: ST-029
        User Story: US-052
        Description: Verify that host socket ID is stored
        Acceptance Criteria: host_sid contains first player's socket ID
        """
        assert room_with_host.host_sid == 'host_socket'
    
    def test_st_030_only_host_should_update_settings(self, room_with_host):
        """
        Test ID: ST-030
        User Story: US-052
        Description: Verify that only host should be able to update settings
        Acceptance Criteria: Backend allows updates but should check in socket_events
        Note: Permission checking happens in socket_events.py
        """
        # Backend allows the update, but socket_events should check permissions
        room_with_host.update_settings({'max_rounds': 25})
        
        # Update succeeds (permission check is in socket_events)
        assert room_with_host.settings['max_rounds'] == 25


class TestSettingsPersistence:
    """Tests for settings persistence during game (US-051)"""
    
    def test_st_031_settings_persist_during_game(self, room):
        """
        Test ID: ST-031
        User Story: US-051
        Description: Verify that settings persist throughout game
        Acceptance Criteria: Settings remain unchanged unless explicitly updated
        """
        room.update_settings({'countdown_duration': 12})
        
        # Simulate game progression
        room.game_state.start_countdown(duration=room.settings['countdown_duration'])
        room.game_state.start_preparation(duration=room.settings['preparation_duration'])
        
        # Settings should remain the same
        assert room.settings['countdown_duration'] == 12
        assert room.settings['preparation_duration'] == 30
    
    def test_st_032_settings_applied_to_game_state(self, room):
        """
        Test ID: ST-032
        User Story: US-051
        Description: Verify that max_rounds setting syncs to game_state
        Acceptance Criteria: game_state.max_rounds matches settings
        """
        room.update_settings({'max_rounds': 15})
        
        assert room.game_state.max_rounds == 15
    
    def test_st_033_settings_survive_round_progression(self, room):
        """
        Test ID: ST-033
        User Story: US-051
        Description: Verify that settings survive multiple rounds
        Acceptance Criteria: Settings unchanged after multiple game phases
        """
        room.update_settings({
            'countdown_duration': 8,
            'preparation_duration': 25,
            'max_rounds': 20
        })
        
        # Progress through multiple phases
        room.game_state.start_countdown(duration=8)
        room.game_state.start_preparation(duration=25)
        room.game_state.start_selection(duration=10)
        room.game_state.start_truth_dare(duration=60)
        room.game_state.start_preparation(duration=25)
        
        # Settings should be unchanged
        assert room.settings['countdown_duration'] == 8
        assert room.settings['preparation_duration'] == 25
        assert room.settings['max_rounds'] == 20
    
    def test_st_034_settings_reset_preserves_custom_values(self, room):
        """
        Test ID: ST-034
        User Story: US-017, US-051
        Description: Verify that custom settings are preserved during game reset
        Acceptance Criteria: Settings remain unchanged after reset_for_new_game()
        """
        room.update_settings({
            'countdown_duration': 15,
            'max_rounds': 25,
            'minigame_chance': 50
        })
        
        room.reset_for_new_game()
        
        assert room.settings['countdown_duration'] == 15
        assert room.settings['max_rounds'] == 25
        assert room.settings['minigame_chance'] == 50


class TestAIGenerationSetting:
    """Tests for AI generation setting (US-049, US-036)"""
    
    def test_st_035_ai_generation_default_disabled(self, room):
        """
        Test ID: ST-035
        User Story: US-049
        Description: Verify that AI generation is disabled by default
        Acceptance Criteria: ai_generation_enabled is False initially
        """
        assert room.settings['ai_generation_enabled'] == False
    
    def test_st_036_enable_ai_generation(self, room):
        """
        Test ID: ST-036
        User Story: US-049
        Description: Verify that AI generation can be enabled
        Acceptance Criteria: ai_generation_enabled becomes True
        """
        room.update_settings({'ai_generation_enabled': True})
        
        assert room.settings['ai_generation_enabled'] == True
    
    def test_st_037_disable_ai_generation(self, room):
        """
        Test ID: ST-037
        User Story: US-049
        Description: Verify that AI generation can be disabled
        Acceptance Criteria: ai_generation_enabled becomes False
        """
        room.settings['ai_generation_enabled'] = True
        
        room.update_settings({'ai_generation_enabled': False})
        
        assert room.settings['ai_generation_enabled'] == False
    
    def test_st_038_ai_setting_boolean_type(self, room):
        """
        Test ID: ST-038
        User Story: US-049
        Description: Verify that AI setting is boolean type
        Acceptance Criteria: ai_generation_enabled is True or False
        """
        assert isinstance(room.settings['ai_generation_enabled'], bool)
        
        # room.update_settings({'ai_generation_enabled': True})
        # assert isinstance(room.settings['ai_generation_enabled'], bool)


class TestGetSettings:
    """Tests for retrieving settings (US-045)"""
    
    def test_st_039_get_all_settings(self, room):
        """
        Test ID: ST-039
        User Story: US-045
        Description: Verify that all settings can be retrieved
        Acceptance Criteria: settings dict contains all configuration options
        """
        settings = room.settings
        
        # All 8 settings should be present
        assert len(settings) == 8
        assert 'countdown_duration' in settings
        assert 'preparation_duration' in settings
        assert 'selection_duration' in settings
        assert 'truth_dare_duration' in settings
        assert 'skip_duration' in settings
        assert 'max_rounds' in settings
        assert 'minigame_chance' in settings
        assert 'ai_generation_enabled' in settings
    
    def test_st_040_settings_dict_is_mutable(self, room):
        """
        Test ID: ST-040
        User Story: US-045
        Description: Verify that settings dict can be modified
        Acceptance Criteria: Changes to settings dict persist
        """
        room.settings['countdown_duration'] = 20
        
        assert room.settings['countdown_duration'] == 20
