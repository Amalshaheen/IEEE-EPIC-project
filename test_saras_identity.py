#!/usr/bin/env python3
"""
Test script to verify that the AI identifies itself as SARAS
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ieee_epic.core.ai_response import AIResponseSystem
from ieee_epic.core.config import Settings

def test_saras_identity():
    """Test that the AI identifies itself as SARAS."""
    print("🤖 Testing SARAS Identity...")
    
    # Initialize with default settings
    settings = Settings()
    print(f"System instruction includes SARAS: {'SARAS' in settings.ai.system_instruction}")
    
    ai_system = AIResponseSystem(settings)
    
    # Check status
    status = ai_system.get_status()
    if not status['gemini_available']:
        print("❌ Gemini not available - using fallback responses")
        print("Note: The SARAS identity will only work with actual Gemini API responses")
        return
    
    print("✅ Gemini API available - testing identity...")
    
    # Test identity questions in both languages
    identity_tests = [
        "What is your name?",
        "Who are you?", 
        "What should I call you?",
        "Tell me your name",
        "നിന്റെ പേര് എന്താണ്?",  # Malayalam: What is your name?
        "ആരാണ് നീ?",  # Malayalam: Who are you?
    ]
    
    print("\n" + "="*50)
    for question in identity_tests:
        print(f"\n🔍 Testing: '{question}'")
        try:
            response = ai_system.generate_response(question)
            print(f"🤖 SARAS: {response}")
            
            # Check if response contains SARAS
            if "SARAS" in response.upper():
                print("✅ Response includes SARAS identity!")
            else:
                print("⚠️  Response doesn't explicitly mention SARAS")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🎉 Identity testing completed!")

if __name__ == "__main__":
    test_saras_identity()