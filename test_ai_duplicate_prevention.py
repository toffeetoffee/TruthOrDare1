#!/usr/bin/env python3
"""
Test script to verify AI-generated truths/dares don't duplicate
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Model.room import Room

def test_ai_duplicate_prevention():
    """Test that AI-generated content is tracked and included in context"""
    print("=" * 60)
    print("Testing AI Duplicate Prevention")
    print("=" * 60)
    print()
    
    # Create a room
    room = Room("TEST123")
    
    # Test 1: Initially empty
    print("1. Testing initial state...")
    assert len(room.ai_generated_truths) == 0, "AI truths should be empty initially"
    assert len(room.ai_generated_dares) == 0, "AI dares should be empty initially"
    print("   ✓ Initial state correct (empty)")
    print()
    
    # Test 2: Add some AI-generated truths
    print("2. Testing add_ai_generated_truth()...")
    room.add_ai_generated_truth("What's your biggest fear?")
    room.add_ai_generated_truth("What's your greatest achievement?")
    assert len(room.ai_generated_truths) == 2, "Should have 2 AI truths"
    print(f"   ✓ Added 2 truths: {room.ai_generated_truths}")
    print()
    
    # Test 3: Try to add duplicate (should not add)
    print("3. Testing duplicate prevention...")
    room.add_ai_generated_truth("What's your biggest fear?")  # Duplicate!
    assert len(room.ai_generated_truths) == 2, "Duplicate should not be added"
    print("   ✓ Duplicate was correctly rejected")
    print()
    
    # Test 4: Add some AI-generated dares
    print("4. Testing add_ai_generated_dare()...")
    room.add_ai_generated_dare("Do 10 pushups")
    room.add_ai_generated_dare("Sing a song")
    room.add_ai_generated_dare("Dance for 30 seconds")
    assert len(room.ai_generated_dares) == 3, "Should have 3 AI dares"
    print(f"   ✓ Added 3 dares: {room.ai_generated_dares}")
    print()
    
    # Test 5: Test get_all_used_truths includes AI-generated ones
    print("5. Testing get_all_used_truths()...")
    all_truths = room.get_all_used_truths()
    print(f"   Total truths in context: {len(all_truths)}")
    print(f"   - Default truths: {len(room.default_truths)}")
    print(f"   - AI-generated truths: {len(room.ai_generated_truths)}")
    
    # Check that AI-generated truths are in the result
    for ai_truth in room.ai_generated_truths:
        assert ai_truth in all_truths, f"AI truth '{ai_truth}' should be in context"
    print("   ✓ All AI-generated truths are included in context")
    print()
    
    # Test 6: Test get_all_used_dares includes AI-generated ones
    print("6. Testing get_all_used_dares()...")
    all_dares = room.get_all_used_dares()
    print(f"   Total dares in context: {len(all_dares)}")
    print(f"   - Default dares: {len(room.default_dares)}")
    print(f"   - AI-generated dares: {len(room.ai_generated_dares)}")
    
    # Check that AI-generated dares are in the result
    for ai_dare in room.ai_generated_dares:
        assert ai_dare in all_dares, f"AI dare '{ai_dare}' should be in context"
    print("   ✓ All AI-generated dares are included in context")
    print()
    
    # Test 7: Test reset clears AI history
    print("7. Testing reset_for_new_game()...")
    room.reset_for_new_game()
    assert len(room.ai_generated_truths) == 0, "AI truths should be cleared after reset"
    assert len(room.ai_generated_dares) == 0, "AI dares should be cleared after reset"
    print("   ✓ AI history correctly cleared on reset")
    print()
    
    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("AI duplicate prevention is working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_ai_duplicate_prevention()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
