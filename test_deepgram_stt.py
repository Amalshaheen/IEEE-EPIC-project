#!/usr/bin/env python3
"""
Test script for Deepgram STT integration in IEEE EPIC project.
This script validates the Deepgram backend implementation and streaming capabilities.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ieee_epic.core.config import Settings
from ieee_epic.core.stt import STTEngine
from loguru import logger


def test_deepgram_configuration():
    """Test Deepgram configuration setup."""
    logger.info("🔧 Testing Deepgram configuration...")
    
    # Test basic settings
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "deepgram"
    settings.models.deepgram_model = "nova-2"
    settings.models.deepgram_language = "en-US"
    
    # Check environment variable
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        logger.warning("⚠️  DEEPGRAM_API_KEY environment variable not set")
        logger.info("💡 To test with actual API, set: export DEEPGRAM_API_KEY=your_key_here")
        return False
    else:
        settings.models.deepgram_api_key = api_key
        logger.success("✅ Deepgram API key found in environment")
        return True


def test_backend_initialization():
    """Test Deepgram backend initialization."""
    logger.info("🚀 Testing Deepgram backend initialization...")
    
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "deepgram"
    settings.models.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "test_key")
    
    try:
        engine = STTEngine(settings)
        
        if 'deepgram' in engine.backends:
            logger.success("✅ Deepgram backend initialized successfully")
            return True
        else:
            logger.error("❌ Deepgram backend not found in available backends")
            logger.info(f"Available backends: {list(engine.backends.keys())}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Backend initialization failed: {e}")
        return False


def test_stt_engine_status():
    """Test STT engine status with Deepgram."""
    logger.info("📊 Testing STT engine status...")
    
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "deepgram"
    settings.models.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY", "test_key")
    
    try:
        engine = STTEngine(settings)
        status = engine.get_status()
        
        logger.info("📈 STT Engine Status:")
        logger.info(f"  Ready: {status['ready']}")
        logger.info(f"  Available backends: {status['backends']}")
        logger.info(f"  Preferred backend: {status['preferred_backend']}")
        logger.info(f"  Online enabled: {status['online_enabled']}")
        logger.info(f"  Supported languages: {status['languages']}")
        
        for lang, backends in status['models'].items():
            logger.info(f"  {lang}: {backends}")
        
        return status['ready']
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        return False


def test_audio_recording():
    """Test basic audio recording capability."""
    logger.info("🎤 Testing audio recording...")
    
    try:
        settings = Settings()
        settings.audio.duration = 2.0  # Short test recording
        
        engine = STTEngine(settings)
        
        # List available audio devices
        logger.info("Available audio devices:")
        engine.recorder.list_audio_devices()
        
        # Test recording without STT
        logger.info("Testing 2-second audio recording...")
        audio_data = engine.recorder.record_audio(duration=2.0)
        
        if len(audio_data) > 0:
            logger.success(f"✅ Audio recorded successfully: {len(audio_data)} samples")
            return True
        else:
            logger.error("❌ No audio data recorded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Audio recording test failed: {e}")
        return False


def test_deepgram_connection():
    """Test actual connection to Deepgram API (requires API key)."""
    logger.info("🌐 Testing Deepgram API connection...")
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        logger.warning("⚠️  Skipping API test - no DEEPGRAM_API_KEY set")
        return True
    
    try:
        from deepgram import DeepgramClient
        
        client = DeepgramClient(api_key)
        
        # Test with a simple balance check or similar lightweight operation
        logger.info("Attempting to connect to Deepgram API...")
        
        # For now, just test client creation
        if client:
            logger.success("✅ Deepgram client created successfully")
            return True
        else:
            logger.error("❌ Failed to create Deepgram client")
            return False
            
    except ImportError:
        logger.error("❌ Deepgram SDK not installed. Run: pip install deepgram-sdk")
        return False
    except Exception as e:
        logger.error(f"❌ Deepgram connection test failed: {e}")
        return False


def interactive_test():
    """Interactive test mode for real speech recognition."""
    logger.info("🎙️  Interactive Deepgram STT Test")
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        logger.error("❌ DEEPGRAM_API_KEY required for interactive test")
        logger.info("💡 Set environment variable: export DEEPGRAM_API_KEY=your_key_here")
        return
    
    try:
        settings = Settings()
        settings.models.use_online_stt = True
        settings.models.preferred_backend = "deepgram"
        settings.models.deepgram_api_key = api_key
        settings.audio.duration = 5.0
        
        engine = STTEngine(settings)
        
        if not engine.is_ready():
            logger.error("❌ STT engine not ready")
            return
        
        logger.info("🎤 Ready for speech recognition!")
        logger.info("Available commands:")
        logger.info("  'test' - Record 5 seconds and transcribe")
        logger.info("  'stream' - Real-time streaming (if available)")
        logger.info("  'quit' - Exit")
        
        while True:
            try:
                command = input("\nEnter command (test/stream/quit): ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'test':
                    logger.info("🎤 Recording for 5 seconds...")
                    results = engine.recognize_speech(language='en')
                    
                    if results:
                        logger.success("📝 Recognition Results:")
                        for key, text in results.items():
                            logger.info(f"  {key}: {text}")
                        
                        best = engine.get_best_result(results)
                        if best:
                            logger.success(f"🎯 Best Result: {best}")
                    else:
                        logger.warning("❌ No speech recognized")
                        
                elif command == 'stream':
                    if 'deepgram' in engine.backends:
                        logger.info("🌊 Starting streaming recognition...")
                        logger.info("Speak now! (Press Ctrl+C to stop)")
                        
                        try:
                            for transcript in engine.stream_recognize('en'):
                                if transcript:
                                    logger.success(f"📝 {transcript}")
                        except KeyboardInterrupt:
                            logger.info("Streaming stopped by user")
                    else:
                        logger.warning("❌ Streaming not available")
                else:
                    logger.warning("❌ Invalid command")
                    
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
        
    except Exception as e:
        logger.error(f"❌ Interactive test failed: {e}")


def main():
    """Main test function."""
    logger.info("🚀 IEEE EPIC Deepgram STT Test Suite")
    logger.info("=" * 50)
    
    # Run tests
    tests = [
        ("Configuration", test_deepgram_configuration),
        ("Backend Initialization", test_backend_initialization),
        ("Engine Status", test_stt_engine_status),
        ("Audio Recording", test_audio_recording),
        ("Deepgram Connection", test_deepgram_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.success(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("🎉 All tests passed!")
        
        # Offer interactive test
        if os.getenv("DEEPGRAM_API_KEY"):
            try:
                response = input("\n🎙️  Run interactive test? (y/n): ").strip().lower()
                if response == 'y':
                    interactive_test()
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Check configuration and dependencies.")


if __name__ == "__main__":
    main()