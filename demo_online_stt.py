#!/usr/bin/env python3
"""
Demo script for IEEE EPIC Online STT capabilities.

This script demonstrates the new online STT features including:
- Google Cloud Speech-to-Text integration
- Real-time streaming recognition
- Intelligent backend fallback
- Configuration management
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ieee_epic.core.config import Settings
from ieee_epic.core.stt import STTEngine
from loguru import logger
import time


def demo_configuration():
    """Demonstrate configuration options for online STT."""
    print("🔧 CONFIGURATION DEMO")
    print("=" * 50)
    
    # Create settings with online STT enabled
    settings = Settings()
    
    # Configure for online STT
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    
    print(f"Online STT enabled: {settings.models.use_online_stt}")
    print(f"Preferred backend: {settings.models.preferred_backend}")
    print(f"Supported languages: {settings.models.supported_languages}")
    print(f"Audio sample rate: {settings.audio.sample_rate} Hz")
    
    return settings


def demo_backend_comparison():
    """Demonstrate different backends and their capabilities."""
    print("\n🔀 BACKEND COMPARISON DEMO")
    print("=" * 50)
    
    settings = Settings()
    
    # Test offline configuration
    print("\n📴 OFFLINE CONFIGURATION:")
    settings.models.use_online_stt = False
    settings.models.preferred_backend = "vosk"
    offline_engine = STTEngine(settings)
    offline_status = offline_engine.get_status()
    
    print(f"  Ready: {offline_status['ready']}")
    print(f"  Backends: {', '.join(offline_status['backends'])}")
    print(f"  Languages: {', '.join(offline_status['languages'])}")
    
    # Test online configuration  
    print("\n🌐 ONLINE CONFIGURATION:")
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    online_engine = STTEngine(settings)
    online_status = online_engine.get_status()
    
    print(f"  Ready: {online_status['ready']}")
    print(f"  Backends: {', '.join(online_status['backends'])}")
    print(f"  Online enabled: {online_status.get('online_enabled', False)}")
    
    return offline_engine, online_engine


def demo_fallback_mechanism():
    """Demonstrate intelligent fallback from online to offline."""
    print("\n🔄 FALLBACK MECHANISM DEMO")
    print("=" * 50)
    
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    
    engine = STTEngine(settings)
    
    # Show preferred backend
    preferred = engine.get_preferred_backend()
    if preferred:
        backend_name = preferred.__class__.__name__
        backend_type = preferred.get_backend_type()
        print(f"Preferred backend: {backend_name} ({backend_type})")
    
    # Show fallback options
    print("Available backends:")
    for name, backend in engine.backends.items():
        backend_type = backend.get_backend_type()
        print(f"  - {name}: {backend.__class__.__name__} ({backend_type})")
    
    return engine


def demo_streaming_capability():
    """Demonstrate streaming recognition capability."""
    print("\n🌊 STREAMING CAPABILITY DEMO")
    print("=" * 50)
    
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    
    engine = STTEngine(settings)
    
    # Check if streaming is available
    if 'google_cloud' in engine.backends:
        google_backend = engine.backends['google_cloud']
        if hasattr(google_backend, 'stream_recognize'):
            print("✅ Real-time streaming recognition is available!")
            print("   Use 'ieee-epic stream' to start streaming mode")
        else:
            print("❌ Streaming not available in this backend")
    else:
        print("⚠️  Google Cloud backend not available")
        print("   Streaming requires Google Cloud Speech credentials")
    
    return engine


def demo_api_usage():
    """Demonstrate programmatic API usage."""
    print("\n💻 API USAGE DEMO")
    print("=" * 50)
    
    settings = Settings()
    engine = STTEngine(settings)
    
    print("Basic recognition example:")
    print("""
    from ieee_epic.core.config import Settings
    from ieee_epic.core.stt import STTEngine
    
    # Configure settings
    settings = Settings()
    settings.models.use_online_stt = True
    settings.models.preferred_backend = "google_cloud"
    
    # Initialize engine
    engine = STTEngine(settings)
    
    # Single recognition
    results = engine.recognize_speech(language="en", duration=5.0)
    best_result = engine.get_best_result(results)
    print(f"You said: {best_result}")
    
    # Streaming recognition
    for transcript in engine.stream_recognize(language="auto"):
        print(f"Live: {transcript}")
    """)


def demo_cli_commands():
    """Demonstrate CLI command usage."""
    print("\n⚡ CLI COMMANDS DEMO")
    print("=" * 50)
    
    print("Available commands:")
    commands = [
        ("ieee-epic status", "Check system status and backends"),
        ("ieee-epic stt --lang en", "Single recognition (English)"),
        ("ieee-epic stt --lang auto --duration 10", "Auto-detect language, 10s duration"),
        ("ieee-epic stream --lang en", "Real-time streaming (Google Cloud)"),
        ("ieee-epic interactive", "Interactive mode with streaming support"),
        ("ieee-epic conversation", "Full conversational AI assistant"),
        ("python3 test_online_stt.py", "Run validation tests"),
    ]
    
    for cmd, desc in commands:
        print(f"  {cmd:<40} # {desc}")


def main():
    """Run the comprehensive demo."""
    print("🚀 IEEE EPIC ONLINE STT DEMONSTRATION")
    print("=" * 50)
    print("This demo showcases the new online STT capabilities")
    print("integrated with the existing offline system.\n")
    
    try:
        # Run demos
        settings = demo_configuration()
        offline_engine, online_engine = demo_backend_comparison()
        engine = demo_fallback_mechanism()
        demo_streaming_capability()
        demo_api_usage()
        demo_cli_commands()
        
        # Summary
        print("\n🎯 MIGRATION SUMMARY")
        print("=" * 50)
        print("✅ Successfully migrated from offline-only to hybrid STT system")
        print("✅ Added Google Cloud Speech-to-Text with streaming support")
        print("✅ Maintained full backward compatibility with existing code")
        print("✅ Implemented intelligent fallback mechanisms")
        print("✅ Enhanced CLI with new streaming commands")
        
        print("\n🚀 NEXT STEPS")
        print("=" * 30)
        print("1. Set up Google Cloud credentials:")
        print("   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'")
        print("\n2. Install dependencies:")
        print("   pip install google-cloud-speech")
        print("\n3. Test the system:")
        print("   python3 test_online_stt.py")
        print("\n4. Try streaming recognition:")
        print("   ieee-epic stream --lang auto")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())