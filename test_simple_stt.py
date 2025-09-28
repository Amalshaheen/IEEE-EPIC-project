#!/usr/bin/env python3
"""
Test script for SimpleSpeechRecognizer
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
from loguru import logger

def test_initialization():
    """Test if SimpleSpeechRecognizer initializes without errors"""
    try:
        logger.info("Testing SimpleSpeechRecognizer initialization...")
        recognizer = SimpleSpeechRecognizer()
        
        logger.info(f"Microphone available: {recognizer.is_available()}")
        logger.info("Getting available microphones...")
        mics = recognizer.get_available_microphones()
        
        if recognizer.is_available():
            logger.success("✅ SimpleSpeechRecognizer initialized successfully!")
            return True
        else:
            logger.warning("⚠️ SimpleSpeechRecognizer initialized but no microphone available")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize SimpleSpeechRecognizer: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Testing Simple Speech Recognition Module")
    success = test_initialization()
    
    if success:
        logger.success("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Tests failed!")
        sys.exit(1)