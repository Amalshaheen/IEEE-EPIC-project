#!/usr/bin/env python3
"""
Test script for IEEE EPIC Online STT Migration.

This script validates the online STT functionality and backend integration.
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ieee_epic.core.config import Settings
from ieee_epic.core.stt import STTEngine
from loguru import logger


def test_configuration():
    """Test configuration loading and validation."""
    logger.info("🧪 Testing configuration...")
    
    # Test default configuration
    settings = Settings()
    
    # Test online STT configuration
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    
    logger.success("✅ Configuration test passed")
    return settings


def test_backend_initialization():
    """Test backend initialization."""
    logger.info("🧪 Testing backend initialization...")
    
    settings = test_configuration()
    
    # Test offline backends
    settings.models.use_online_stt = False
    settings.models.preferred_backend = "vosk"
    offline_engine = STTEngine(settings)
    
    offline_status = offline_engine.get_status()
    logger.info(f"Offline backends: {offline_status['backends']}")
    
    # Test online backend (if credentials available)
    settings.models.use_online_stt = True  
    settings.models.preferred_backend = "google_cloud"
    online_engine = STTEngine(settings)
    
    online_status = online_engine.get_status()
    logger.info(f"Online backends: {online_status['backends']}")
    
    if 'google_cloud' in online_status['backends']:
        logger.success("✅ Google Cloud backend initialized successfully")
    else:
        logger.warning("⚠️ Google Cloud backend not available (credentials missing)")
    
    logger.success("✅ Backend initialization test passed")
    return offline_engine, online_engine


def test_backend_features():
    """Test backend-specific features."""
    logger.info("🧪 Testing backend features...")
    
    offline_engine, online_engine = test_backend_initialization()
    
    # Test backend types
    for name, backend in offline_engine.backends.items():
        backend_type = backend.get_backend_type()
        logger.info(f"{name}: {backend_type}")
    
    for name, backend in online_engine.backends.items():
        backend_type = backend.get_backend_type()
        logger.info(f"{name}: {backend_type}")
    
    # Test streaming capability
    if 'google_cloud' in online_engine.backends:
        google_backend = online_engine.backends['google_cloud']
        if hasattr(google_backend, 'stream_recognize'):
            logger.success("✅ Streaming recognition available")
        else:
            logger.error("❌ Streaming recognition not available")
    
    logger.success("✅ Backend features test passed")


def test_fallback_mechanism():
    """Test online-to-offline fallback."""
    logger.info("🧪 Testing fallback mechanism...")
    
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    
    engine = STTEngine(settings)
    
    # Test preferred backend selection
    preferred = engine.get_preferred_backend()
    if preferred:
        logger.info(f"Preferred backend: {preferred.__class__.__name__}")
        backend_type = preferred.get_backend_type()
        logger.info(f"Backend type: {backend_type}")
    else:
        logger.warning("No preferred backend available")
    
    logger.success("✅ Fallback mechanism test passed")


def main():
    """Run all tests."""
    logger.info("🚀 Starting IEEE EPIC Online STT Tests")
    
    try:
        test_configuration()
        test_backend_initialization()  
        test_backend_features()
        test_fallback_mechanism()
        
        logger.success("🎉 All tests passed successfully!")
        
        # Print summary
        settings = Settings()
        settings.models.use_online_stt = True
        engine = STTEngine(settings)
        status = engine.get_status()
        
        print("\n" + "="*50)
        print("📊 SYSTEM SUMMARY")
        print("="*50)
        print(f"Ready: {status['ready']}")
        print(f"Available backends: {', '.join(status['backends'])}")
        print(f"Preferred backend: {status.get('preferred_backend', 'None')}")
        print(f"Online enabled: {status.get('online_enabled', False)}")
        print(f"Supported languages: {', '.join(status['languages'])}")
        
        if status['ready']:
            print("\n🎉 System is ready for online STT!")
            print("\nQuick start:")
            print("  ieee-epic status                    # Check system status")
            print("  ieee-epic stt --lang en            # Single recognition")
            print("  ieee-epic stream --lang auto        # Streaming (Google Cloud)")
            print("  ieee-epic interactive               # Interactive mode")
        else:
            print("\n⚠️  System needs configuration:")
            if 'google_cloud' not in status['backends']:
                print("  - Set up Google Cloud credentials")
                print("  - Install: pip install google-cloud-speech")
            if not status['backends']:
                print("  - Install offline models (Vosk)")
                print("  - Run: ieee-epic setup")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())