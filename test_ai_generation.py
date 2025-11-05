#!/usr/bin/env python3
"""
Test script for AI generation functionality
Run this to diagnose AI generation issues
"""

import os
import sys

def test_ai_generation():
    """Test the AI generation system"""
    print("=" * 60)
    print("Truth or Dare - AI Generation Diagnostic Test")
    print("=" * 60)
    print()
    
    # Check environment variable
    api_key = os.environ.get('GEMINI_API_KEY')
    print(f"1. Checking GEMINI_API_KEY environment variable...")
    if api_key:
        print(f"   ✓ API key found (length: {len(api_key)} characters)")
        print(f"   First 10 chars: {api_key[:10]}...")
    else:
        print(f"   ✗ API key NOT found!")
        print(f"   Please set GEMINI_API_KEY environment variable")
        return False
    
    print()
    
    # Import AI generator
    print(f"2. Importing AI generator module...")
    try:
        from Model.ai_generator import get_ai_generator, AIGenerator
        print(f"   ✓ AI generator module imported successfully")
    except Exception as e:
        print(f"   ✗ Failed to import: {e}")
        return False
    
    print()
    
    # Initialize AI generator
    print(f"3. Initializing AI generator...")
    try:
        ai_gen = get_ai_generator()
        status = ai_gen.get_status()
        print(f"   Status:")
        print(f"     - Enabled: {status['enabled']}")
        print(f"     - Model: {status['model']}")
        print(f"     - Has Client: {status['has_client']}")
        print(f"     - API Key Configured: {status['api_key_configured']}")
        
        if status['initialization_error']:
            print(f"     - Initialization Error: {status['initialization_error']}")
            return False
        else:
            print(f"   ✓ AI generator initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test generation
    print(f"4. Testing AI generation...")
    try:
        test_result = ai_gen.test_generation()
        
        if test_result['success']:
            print(f"   ✓ Test generation successful!")
            print(f"   Sample output: '{test_result['sample_output']}'")
        else:
            print(f"   ✗ Test generation failed: {test_result['error']}")
            return False
    except Exception as e:
        print(f"   ✗ Test generation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test truth generation
    print(f"5. Testing truth generation with context...")
    try:
        existing_truths = [
            "What is your biggest fear?",
            "What is the most embarrassing thing you've ever done?",
            "What is your biggest secret?"
        ]
        
        truth = ai_gen.generate_truth(existing_truths)
        
        if truth:
            print(f"   ✓ Truth generated successfully!")
            print(f"   Generated: '{truth}'")
        else:
            print(f"   ✗ Truth generation returned None")
            return False
    except Exception as e:
        print(f"   ✗ Truth generation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test dare generation
    print(f"6. Testing dare generation with context...")
    try:
        existing_dares = [
            "Do 10 pushups",
            "Sing a song loudly",
            "Dance for 30 seconds"
        ]
        
        dare = ai_gen.generate_dare(existing_dares)
        
        if dare:
            print(f"   ✓ Dare generated successfully!")
            print(f"   Generated: '{dare}'")
        else:
            print(f"   ✗ Dare generation returned None")
            return False
    except Exception as e:
        print(f"   ✗ Dare generation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("AI generation is working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_ai_generation()
    sys.exit(0 if success else 1)
