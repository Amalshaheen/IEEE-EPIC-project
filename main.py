"""
IEEE EPIC Project - Offline Speech-to-Text System
=================================================
This project implements an offline STT system using Vosk models
for Malayalam and English languages on Raspberry Pi.

🚀 Raspberry Pi Setup:
- Run: ./setup_rpi.sh for complete automated setup
- Or: python3 rpi_setup.py for Python-based setup
- Then: python3 rpi_stt.py for optimized RPi experience
"""

import os
import sys
from pathlib import Path

def check_rpi_setup():
    """Check if RPi-specific files exist"""
    rpi_files = [
        'rpi_stt.py',
        'setup_rpi.sh',
        'rpi_setup.py',
        'test_audio.py'
    ]
    
    missing_files = [f for f in rpi_files if not Path(f).exists()]
    
    if missing_files:
        print("⚠️  Some RPi setup files are missing:")
        for f in missing_files:
            print(f"   - {f}")
        print("\nPlease ensure all setup files are present.")
        return False
    return True

def main():
    """Main entry point for the IEEE EPIC project"""
    print("🤖 IEEE EPIC Project - Offline STT System")
    print("=========================================")
    
    # Check if we're likely on a Raspberry Pi
    is_likely_rpi = False
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                is_likely_rpi = True
    except:
        pass
    
    if is_likely_rpi:
        print("🍓 Raspberry Pi detected!")
        print("\nFor optimal RPi experience, use:")
        print("   python3 rpi_stt.py")
        print("\nFor first-time setup:")
        print("   ./setup_rpi.sh")
        print()
    
    # Check if models exist
    en_model_exists = os.path.exists("vosk-en")
    ml_model_exists = os.path.exists("vosk-ml")
    
    print(f"English Model: {'✅ Available' if en_model_exists else '❌ Missing'}")
    print(f"Malayalam Model: {'✅ Available' if ml_model_exists else '❌ Missing'}")
    
    if not en_model_exists and not ml_model_exists:
        print("\n⚠️  No models found!")
        if is_likely_rpi:
            print("🔧 Run setup: ./setup_rpi.sh")
        else:
            print("📥 Download English model:")
            print("wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
            print("unzip vosk-model-small-en-us-0.15.zip")
            print("mv vosk-model-small-en-us-0.15 vosk-en")
        return
    
    # Check RPi setup files
    check_rpi_setup()
    
    print("\n🎯 Available Scripts:")
    print("=" * 40)
    if os.path.exists("rpi_stt.py"):
        print("🍓 python3 rpi_stt.py    - RPi optimized STT")
    if os.path.exists("test_audio.py"):
        print("🔊 python3 test_audio.py - Test audio setup")
    print("🧪 python3 stt_test.py   - Original STT test")
    print("=" * 40)
    
    # Ask user what to run
    while True:
        print("\nChoose an option:")
        print("1. Run RPi optimized STT (recommended)")
        print("2. Test audio setup")
        print("3. Run original STT test")
        print("4. Exit")
        
        try:
            choice = input("\n📝 Enter choice (1-4): ").strip()
            
            if choice == '1' and os.path.exists("rpi_stt.py"):
                print("\n🚀 Starting RPi STT...")
                os.system("python3 rpi_stt.py")
                break
            elif choice == '2' and os.path.exists("test_audio.py"):
                print("\n🔊 Testing audio...")
                os.system("python3 test_audio.py")
            elif choice == '3':
                print("\n🧪 Running original STT test...")
                from stt_test import main as run_stt_test
                run_stt_test()
                break
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice or file not found")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break

if __name__ == "__main__":
    main()
