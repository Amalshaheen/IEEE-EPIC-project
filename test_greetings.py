#!/usr/bin/env python3
"""
Test script to verify SARAS greetings and farewells
"""

import sys
import os
sys.path.append('src')

def test_greetings():
    """Test the greeting and farewell messages."""
    try:
        # This will only work if GPIO imports don't fail completely
        from simple_handshake_ai import SimpleVoiceAI
        
        print("🤖 Testing SARAS Greetings and Farewells...")
        print("="*50)
        
        # We need to handle the GPIO import gracefully
        voice_ai = SimpleVoiceAI()
        
        print("📢 Sample Greeting:")
        greeting = voice_ai.get_greeting()
        print(f"'{greeting}'")
        print()
        
        print("👋 Sample Farewell:")
        farewell = voice_ai.get_farewell()
        print(f"'{farewell}'")
        print()
        
        # Check if SARAS is mentioned
        if "SARAS" in greeting:
            print("✅ Greeting includes SARAS identity!")
        else:
            print("⚠️  Greeting doesn't mention SARAS")
            
        if "SARAS" in farewell:
            print("✅ Farewell includes SARAS identity!")
        else:
            print("⚠️  Farewell doesn't mention SARAS")
            
    except Exception as e:
        print(f"❌ Error testing greetings: {e}")
        print("This might be due to missing dependencies or GPIO import issues.")

if __name__ == "__main__":
    test_greetings()