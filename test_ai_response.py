#!/usr/bin/env python3
"""
Test the AI response system directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ieee_epic.core.ai_response import AIResponseSystem
from ieee_epic.core.config import Settings

def test_ai_system():
    """Test the AI response system."""
    print("🤖 Testing AI Response System...")
    
    # Initialize with default settings
    settings = Settings()
    print(f"Using model: {settings.ai.model}")
    print(f"API key configured: {bool(settings.ai.gemini_api_key)}")
    
    ai_system = AIResponseSystem(settings)
    
    # Check status
    status = ai_system.get_status()
    print("AI System Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if not status['gemini_available']:
        print("❌ Gemini not available")
        return
    
    # Test responses in both languages
    test_inputs = [
        ("Hello, how are you?", "en"),
        ("നമസ്കാരം", "ml"),
        ("What is 2+2?", "en"),
        ("മനസ്സിലാക്കണം", "ml")
    ]
    
    for text, lang in test_inputs:
        print(f"\n🔍 Testing: '{text}' ({lang})")
        try:
            response = ai_system.generate_response(text)
            print(f"✅ Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ai_system()