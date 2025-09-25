#!/usr/bin/env python3
"""
IEEE EPIC Project - Main Entry Point (Compatibility Layer)

This is a compatibility wrapper that maintains the old interface
while using the new structured package.
"""

import sys
from pathlib import Path

# Add src to Python path so imports work
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from ieee_epic.main import app
    from ieee_epic.core.config import Settings
    from ieee_epic.core.stt import STTEngine
    from ieee_epic.core.ai_response import AIResponseSystem
    
    def main():
        """Main entry point with backwards compatibility."""
        print("🤖 IEEE EPIC Project - Restructured Version")
        print("=" * 50)
        
        if len(sys.argv) > 1:
            # Use new CLI if arguments provided
            app()
        else:
            # Interactive mode for backwards compatibility
            print("Available commands:")
            print("  python main.py status    - Show system status")
            print("  python main.py stt       - Speech-to-text mode")
            print("  python main.py demo      - AI response demo")
            print("  python main.py setup     - Run setup")
            print("  python main.py           - This help")
            print()
            print("🆕 New CLI interface available:")
            print("  ieee-epic status         - Show detailed status")
            print("  ieee-epic conversation   - Full conversational AI")
            print("  ieee-epic interactive    - Interactive STT")
            
            # Show quick status
            try:
                settings = Settings()
                stt_engine = STTEngine(settings)
                
                print()
                print("Quick Status:")
                print(f"  English Model: {'✅' if settings.is_model_available('en') else '❌'}")
                print(f"  Malayalam Model: {'✅' if settings.is_model_available('ml') else '❌'}")
                print(f"  STT Ready: {'✅' if stt_engine.is_ready() else '❌'}")
                print(f"  Platform: {'🍓 RPi' if settings.system.is_raspberry_pi else '🖥️ Desktop'}")
            except Exception as e:
                print(f"  Status check failed: {e}")

except ImportError as e:
    print("❌ New package structure not found.")
    print("Please install the package in development mode:")
    print("  pip install -e .")
    print()
    print("Or install dependencies:")
    print("  pip install -r requirements.txt")
    print(f"\nError: {e}")
    sys.exit(1)

if __name__ == "__main__":
    main()
