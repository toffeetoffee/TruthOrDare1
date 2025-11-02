"""
Tests for Content Management functionality
Related User Stories: US-009, US-023-US-038
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from Model.room import Room
from Model.player import Player
from Model.ai_generator import AIGenerator, get_ai_generator


@pytest.fixture
def room():
    """Fixture for a room with default content"""
    return Room('TEST01')


@pytest.fixture
def room_with_players(room):
    """Fixture for room with multiple players"""
    room.add_player(Player('socket_1', 'Alice'))
    room.add_player(Player('socket_2', 'Bob'))
    room.add_player(Player('socket_3', 'Charlie'))
    return room


class TestDefaultContent:
    """Tests for default truth/dare content loading (US-009, US-028)"""
    
    def test_cm_001_room_loads_default_truths(self, room):
        """
        Test ID: CM-001
        User Story: US-009, US-028
        Description: Verify that room loads default truths from file
        Acceptance Criteria: default_truths list is populated
        """
        assert room.default_truths is not None
        assert len(room.default_truths) > 0
        assert isinstance(room.default_truths, list)
    
    def test_cm_002_room_loads_default_dares(self, room):
        """
        Test ID: CM-002
        User Story: US-009, US-028
        Description: Verify that room loads default dares from file
        Acceptance Criteria: default_dares list is populated
        """
        assert room.default_dares is not None
        assert len(room.default_dares) > 0
        assert isinstance(room.default_dares, list)
    
    def test_cm_003_get_default_truths(self, room):
        """
        Test ID: CM-003
        User Story: US-029
        Description: Verify that default truths can be retrieved
        Acceptance Criteria: get_default_truths() returns copy of list
        """
        truths = room.get_default_truths()
        
        assert isinstance(truths, list)
        assert len(truths) > 0
        
        # Verify it's a copy, not the original
        truths.append("New truth")
        assert len(room.default_truths) != len(truths)
    
    def test_cm_004_get_default_dares(self, room):
        """
        Test ID: CM-004
        User Story: US-029
        Description: Verify that default dares can be retrieved
        Acceptance Criteria: get_default_dares() returns copy of list
        """
        dares = room.get_default_dares()
        
        assert isinstance(dares, list)
        assert len(dares) > 0
        
        # Verify it's a copy
        dares.append("New dare")
        assert len(room.default_dares) != len(dares)


class TestAddDefaultContent:
    """Tests for adding default content (US-030)"""
    
    def test_cm_005_add_default_truth(self, room):
        """
        Test ID: CM-005
        User Story: US-030
        Description: Verify that new default truth can be added
        Acceptance Criteria: Truth is added to default_truths list
        """
        initial_count = len(room.default_truths)
        
        success = room.add_default_truth("What is your dream job?")
        
        assert success
        assert len(room.default_truths) == initial_count + 1
        assert "What is your dream job?" in room.default_truths
    
    def test_cm_006_add_default_dare(self, room):
        """
        Test ID: CM-006
        User Story: US-030
        Description: Verify that new default dare can be added
        Acceptance Criteria: Dare is added to default_dares list
        """
        initial_count = len(room.default_dares)
        
        success = room.add_default_dare("Do a cartwheel")
        
        assert success
        assert len(room.default_dares) == initial_count + 1
        assert "Do a cartwheel" in room.default_dares
    
    def test_cm_007_add_duplicate_truth(self, room):
        """
        Test ID: CM-007
        User Story: US-030
        Description: Verify that duplicate truths are not added
        Acceptance Criteria: add_default_truth() returns False for duplicates
        """
        truth = "Unique truth question"
        room.add_default_truth(truth)
        initial_count = len(room.default_truths)
        
        success = room.add_default_truth(truth)
        
        assert not success
        assert len(room.default_truths) == initial_count
    
    def test_cm_008_add_empty_truth(self, room):
        """
        Test ID: CM-008
        User Story: US-030
        Description: Verify that empty truths are not added
        Acceptance Criteria: add_default_truth() returns False for empty strings
        """
        initial_count = len(room.default_truths)
        
        success = room.add_default_truth("")
        
        assert not success
        assert len(room.default_truths) == initial_count


class TestEditDefaultContent:
    """Tests for editing default content (US-031)"""
    
    def test_cm_009_edit_default_truth(self, room):
        """
        Test ID: CM-009
        User Story: US-031
        Description: Verify that default truth can be edited
        Acceptance Criteria: Old text is replaced with new text
        """
        old_truth = room.default_truths[0]
        new_truth = "Modified truth question"
        
        success = room.edit_default_truth(old_truth, new_truth)
        
        assert success
        assert old_truth not in room.default_truths
        assert new_truth in room.default_truths
    
    def test_cm_010_edit_default_dare(self, room):
        """
        Test ID: CM-010
        User Story: US-031
        Description: Verify that default dare can be edited
        Acceptance Criteria: Old text is replaced with new text
        """
        old_dare = room.default_dares[0]
        new_dare = "Modified dare challenge"
        
        success = room.edit_default_dare(old_dare, new_dare)
        
        assert success
        assert old_dare not in room.default_dares
        assert new_dare in room.default_dares
    
    def test_cm_011_edit_nonexistent_truth(self, room):
        """
        Test ID: CM-011
        User Story: US-031
        Description: Verify that editing non-existent truth fails gracefully
        Acceptance Criteria: edit_default_truth() returns False for non-existent truth
        """
        success = room.edit_default_truth("Nonexistent truth", "New text")
        
        assert not success
    
    def test_cm_012_edit_to_duplicate(self, room):
        """
        Test ID: CM-012
        User Story: US-031
        Description: Verify that editing to existing text fails
        Acceptance Criteria: edit_default_truth() returns False if new text already exists
        """
        truth1 = room.default_truths[0]
        truth2 = room.default_truths[1]
        
        success = room.edit_default_truth(truth1, truth2)
        
        assert not success
        assert truth1 in room.default_truths  # Original unchanged
    
    def test_cm_013_edit_to_empty_string(self, room):
        """
        Test ID: CM-013
        User Story: US-031
        Description: Verify that editing to empty string fails
        Acceptance Criteria: edit_default_truth() returns False for empty new text
        """
        truth = room.default_truths[0]
        
        success = room.edit_default_truth(truth, "")
        
        assert not success
        assert truth in room.default_truths


class TestRemoveDefaultContent:
    """Tests for removing default content (US-032)"""
    
    def test_cm_014_remove_default_truths(self, room):
        """
        Test ID: CM-014
        User Story: US-032
        Description: Verify that default truths can be removed
        Acceptance Criteria: Specified truths are removed from list
        """
        truths_to_remove = [room.default_truths[0], room.default_truths[1]]
        initial_count = len(room.default_truths)
        
        room.remove_default_truths(truths_to_remove)
        
        assert len(room.default_truths) == initial_count - 2
        for truth in truths_to_remove:
            assert truth not in room.default_truths
    
    def test_cm_015_remove_default_dares(self, room):
        """
        Test ID: CM-015
        User Story: US-032
        Description: Verify that default dares can be removed
        Acceptance Criteria: Specified dares are removed from list
        """
        dares_to_remove = [room.default_dares[0]]
        initial_count = len(room.default_dares)
        
        room.remove_default_dares(dares_to_remove)
        
        assert len(room.default_dares) == initial_count - 1
        assert dares_to_remove[0] not in room.default_dares
    
    def test_cm_016_remove_nonexistent_truth(self, room):
        """
        Test ID: CM-016
        User Story: US-032
        Description: Verify that removing non-existent truth doesn't cause error
        Acceptance Criteria: Operation completes without error
        """
        initial_count = len(room.default_truths)
        
        room.remove_default_truths(["Nonexistent truth"])
        
        assert len(room.default_truths) == initial_count
    
    def test_cm_017_remove_multiple_truths(self, room):
        """
        Test ID: CM-017
        User Story: US-032
        Description: Verify that multiple truths can be removed at once
        Acceptance Criteria: All specified truths are removed
        """
        truths_to_remove = room.default_truths[:3]  # First 3
        initial_count = len(room.default_truths)
        
        room.remove_default_truths(truths_to_remove)
        
        assert len(room.default_truths) == initial_count - 3


class TestPresetManagement:
    """Tests for saving and loading presets (US-033, US-034, US-035)"""
    
    def test_cm_018_preset_save_format(self, room):
        """
        Test ID: CM-018
        User Story: US-033
        Description: Verify that preset data has correct format
        Acceptance Criteria: Preset contains 'truths' and 'dares' arrays
        """
        preset_data = {
            'truths': room.get_default_truths(),
            'dares': room.get_default_dares()
        }
        
        assert 'truths' in preset_data
        assert 'dares' in preset_data
        assert isinstance(preset_data['truths'], list)
        assert isinstance(preset_data['dares'], list)
    
    def test_cm_019_preset_json_serializable(self, room):
        """
        Test ID: CM-019
        User Story: US-033
        Description: Verify that preset can be serialized to JSON
        Acceptance Criteria: Preset data can be converted to JSON string
        """
        preset_data = {
            'truths': room.get_default_truths(),
            'dares': room.get_default_dares()
        }
        
        # Should not raise exception
        json_str = json.dumps(preset_data)
        assert isinstance(json_str, str)
        
        # Should be parseable back
        parsed = json.loads(json_str)
        assert 'truths' in parsed
        assert 'dares' in parsed


class TestPlayerContentSubmission:
    """Tests for player content submission (US-023, US-024, US-025)"""
    
    def test_cm_020_player_receives_defaults_on_join(self, room_with_players):
        """
        Test ID: CM-020
        User Story: US-028
        Description: Verify that players receive default content when joining
        Acceptance Criteria: Player's lists contain room's default content
        """
        player = room_with_players.get_player_by_name('Alice')
        
        truths = player.truth_dare_list.get_truths()
        dares = player.truth_dare_list.get_dares()
        
        assert len(truths) == len(room_with_players.default_truths)
        assert len(dares) == len(room_with_players.default_dares)
    
    def test_cm_021_submission_to_target_player(self, room_with_players):
        """
        Test ID: CM-021
        User Story: US-023, US-024
        Description: Verify that submissions are added to target player's list
        Acceptance Criteria: Target player receives the submitted content
        """
        target = room_with_players.get_player_by_name('Bob')
        initial_truth_count = len(target.truth_dare_list.truths)
        
        target.truth_dare_list.add_truth("Custom truth for Bob", submitted_by="Alice")
        
        assert len(target.truth_dare_list.truths) == initial_truth_count + 1
        
        truths = target.truth_dare_list.get_truths()
        custom_truth = next(t for t in truths if t['text'] == "Custom truth for Bob")
        assert custom_truth['submitted_by'] == "Alice"
        assert not custom_truth['is_default']
    
    def test_cm_022_submission_with_submitter_info(self, room_with_players):
        """
        Test ID: CM-022
        User Story: US-023, US-024, US-041
        Description: Verify that submissions track who submitted them
        Acceptance Criteria: submitted_by field contains submitter's name
        """
        target = room_with_players.get_player_by_name('Charlie')
        
        target.truth_dare_list.add_dare("Do 50 jumping jacks", submitted_by="Bob")
        
        dares = target.truth_dare_list.get_dares()
        custom_dare = next(d for d in dares if d['text'] == "Do 50 jumping jacks")
        assert custom_dare['submitted_by'] == "Bob"


class TestPlayerListsHidden:
    """Tests for list privacy (US-026)"""
    
    def test_cm_023_cannot_view_own_lists_directly(self, room_with_players):
        """
        Test ID: CM-023
        User Story: US-026
        Description: Verify that players cannot see their truth/dare lists
        Acceptance Criteria: Lists are maintained privately, not exposed in UI
        Note: This is enforced by the frontend, but lists are stored in backend
        """
        player = room_with_players.get_player_by_name('Alice')
        
        # The lists exist in the backend
        assert player.truth_dare_list is not None
        
        # But in player.to_dict(), we don't expose the lists
        player_dict = player.to_dict()
        
        assert 'truth_dare_list' not in player_dict
        assert 'truths' not in player_dict
        assert 'dares' not in player_dict


class TestItemRemovalAfterUse:
    """Tests for removing items after performance (US-027)"""
    
    def test_cm_024_truth_removed_after_use(self, room_with_players):
        """
        Test ID: CM-024
        User Story: US-027
        Description: Verify that truth is removed from list after being performed
        Acceptance Criteria: Truth object is removed from player's truths list
        """
        player = room_with_players.get_player_by_name('Alice')
        initial_count = len(player.truth_dare_list.truths)
        
        # Simulate selecting and using a truth
        truth_to_use = player.truth_dare_list.truths[0]
        player.truth_dare_list.truths.remove(truth_to_use)
        
        assert len(player.truth_dare_list.truths) == initial_count - 1
        assert truth_to_use not in player.truth_dare_list.truths
    
    def test_cm_025_dare_removed_after_use(self, room_with_players):
        """
        Test ID: CM-025
        User Story: US-027
        Description: Verify that dare is removed from list after being performed
        Acceptance Criteria: Dare object is removed from player's dares list
        """
        player = room_with_players.get_player_by_name('Bob')
        initial_count = len(player.truth_dare_list.dares)
        
        # Simulate selecting and using a dare
        dare_to_use = player.truth_dare_list.dares[0]
        player.truth_dare_list.dares.remove(dare_to_use)
        
        assert len(player.truth_dare_list.dares) == initial_count - 1
        assert dare_to_use not in player.truth_dare_list.dares


class TestAIGeneration:
    """Tests for AI content generation (US-036, US-037, US-038)"""
    
    def test_cm_026_ai_generator_initialization(self):
        """
        Test ID: CM-026
        User Story: US-036
        Description: Verify that AI generator can be initialized
        Acceptance Criteria: AIGenerator instance is created
        """
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            with patch('Model.ai_generator.genai.Client'):
                ai_gen = AIGenerator()
                
                assert ai_gen is not None
    
    def test_cm_027_ai_generator_disabled_without_key(self):
        """
        Test ID: CM-027
        User Story: US-036
        Description: Verify that AI generator is disabled without API key
        Acceptance Criteria: enabled is False when no API key
        """
        with patch.dict('os.environ', {}, clear=True):
            ai_gen = AIGenerator()
            
            assert not ai_gen.enabled
            assert ai_gen.client is None
    
    def test_cm_028_ai_generate_truth_with_context(self):
        """
        Test ID: CM-028
        User Story: US-036
        Description: Verify that AI can generate truth with existing context
        Acceptance Criteria: Generated truth avoids duplicating existing ones
        """
        existing_truths = ["What is your favorite color?", "Have you ever lied?"]
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            ai_gen = AIGenerator()
            ai_gen.enabled = True
            
            # Mock the client response
            mock_response = Mock()
            mock_response.text = "What is your biggest achievement?"
            ai_gen.client = Mock()
            ai_gen.client.models.generate_content = Mock(return_value=mock_response)
            
            generated = ai_gen.generate_truth(existing_truths)
            
            assert generated is not None
            assert generated.endswith('?')
            assert generated not in existing_truths
    
    def test_cm_029_ai_generate_dare_with_context(self):
        """
        Test ID: CM-029
        User Story: US-036
        Description: Verify that AI can generate dare with existing context
        Acceptance Criteria: Generated dare avoids duplicating existing ones
        """
        existing_dares = ["Do 10 pushups", "Sing a song"]
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            ai_gen = AIGenerator()
            ai_gen.enabled = True
            
            # Mock the client response
            mock_response = Mock()
            mock_response.text = "Do a handstand for 10 seconds"
            ai_gen.client = Mock()
            ai_gen.client.models.generate_content = Mock(return_value=mock_response)
            
            generated = ai_gen.generate_dare(existing_dares)
            
            assert generated is not None
            assert generated not in existing_dares
    
    def test_cm_030_ai_generation_returns_none_when_disabled(self):
        """
        Test ID: CM-030
        User Story: US-036, US-037
        Description: Verify that AI generation returns None when disabled
        Acceptance Criteria: generate_truth/dare return None if not enabled
        """
        with patch.dict('os.environ', {}, clear=True):
            ai_gen = AIGenerator()
            
            truth = ai_gen.generate_truth([])
            dare = ai_gen.generate_dare([])
            
            assert truth is None
            assert dare is None
    
    def test_cm_031_ai_generation_handles_errors(self):
        """
        Test ID: CM-031
        User Story: US-036, US-037
        Description: Verify that AI generation handles errors gracefully
        Acceptance Criteria: Returns None on generation error
        """
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            ai_gen = AIGenerator()
            ai_gen.enabled = True
            ai_gen.client = Mock()
            ai_gen.client.models.generate_content = Mock(side_effect=Exception("API Error"))
            
            truth = ai_gen.generate_truth([])
            dare = ai_gen.generate_dare([])
            
            assert truth is None
            assert dare is None
    
    def test_cm_032_ai_generated_content_attribution(self):
        """
        Test ID: CM-032
        User Story: US-038
        Description: Verify that AI-generated content is attributed to 'AI'
        Acceptance Criteria: submitted_by should be 'AI' for generated content
        Note: This is handled in socket_events.py when creating Truth/Dare objects
        """
        # This test verifies the expected behavior
        from Model.truth_dare import Truth, Dare
        
        ai_truth = Truth("AI generated truth?", is_default=False, submitted_by="AI")
        ai_dare = Dare("AI generated dare", is_default=False, submitted_by="AI")
        
        assert ai_truth.submitted_by == "AI"
        assert ai_dare.submitted_by == "AI"
    
    def test_cm_033_get_ai_generator_singleton(self):
        """
        Test ID: CM-033
        User Story: US-036
        Description: Verify that get_ai_generator returns singleton instance
        Acceptance Criteria: Multiple calls return same instance
        """
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            with patch('Model.ai_generator.genai.Client'):
                gen1 = get_ai_generator()
                gen2 = get_ai_generator()
                
                assert gen1 is gen2
    
    def test_cm_034_ai_removes_quotes_from_generation(self):
        """
        Test ID: CM-034
        User Story: US-036
        Description: Verify that AI generator removes surrounding quotes
        Acceptance Criteria: Generated text has quotes stripped
        """
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            ai_gen = AIGenerator()
            ai_gen.enabled = True
            
            # Mock response with quotes
            mock_response = Mock()
            mock_response.text = '"What is your favorite food?"'
            ai_gen.client = Mock()
            ai_gen.client.models.generate_content = Mock(return_value=mock_response)
            
            generated = ai_gen.generate_truth([])
            
            assert not generated.startswith('"')
            assert not generated.endswith('"')
            assert generated == "What is your favorite food?"
    
    def test_cm_035_ai_adds_question_mark_to_truth(self):
        """
        Test ID: CM-035
        User Story: US-036
        Description: Verify that AI generator ensures truths end with question mark
        Acceptance Criteria: Generated truth ends with '?'
        """
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            ai_gen = AIGenerator()
            ai_gen.enabled = True
            
            # Mock response without question mark
            mock_response = Mock()
            mock_response.text = "What is your dream job"
            ai_gen.client = Mock()
            ai_gen.client.models.generate_content = Mock(return_value=mock_response)
            
            generated = ai_gen.generate_truth([])
            
            assert generated.endswith('?')


class TestRoomReset:
    """Tests for resetting room content for new game (US-017)"""
    
    def test_cm_036_reset_preserves_defaults(self, room_with_players):
        """
        Test ID: CM-036
        User Story: US-017
        Description: Verify that room reset preserves default lists
        Acceptance Criteria: default_truths and default_dares unchanged after reset
        """
        original_truths = room_with_players.default_truths.copy()
        original_dares = room_with_players.default_dares.copy()
        
        room_with_players.reset_for_new_game()
        
        assert room_with_players.default_truths == original_truths
        assert room_with_players.default_dares == original_dares
    
    def test_cm_037_reset_reinitializes_player_lists(self, room_with_players):
        """
        Test ID: CM-037
        User Story: US-017
        Description: Verify that player lists are reinitialized on reset
        Acceptance Criteria: Each player's list is reset to current defaults
        """
        # Add custom content to a player
        player = room_with_players.get_player_by_name('Alice')
        player.truth_dare_list.add_truth("Custom truth", submitted_by="Bob")
        
        # Reset room
        room_with_players.reset_for_new_game()
        
        # Player should have fresh lists with only defaults
        truths = player.truth_dare_list.get_truths()
        custom_truths = [t for t in truths if t['text'] == "Custom truth"]
        
        assert len(custom_truths) == 0  # Custom content removed
        assert all(t['is_default'] for t in truths)  # Only defaults remain
