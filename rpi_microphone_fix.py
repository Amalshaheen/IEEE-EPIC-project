#!/usr/bin/env python3
"""
Quick Raspberry Pi Microphone Fix Script
Run this to test and configure your microphone for the voice recognition system
"""

import subprocess
import sys
import os
from pathlib import Path

# Ensure the local 'src' directory is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def print_header():
    print("🔧 Raspberry Pi Microphone Quick Fix")
    print("=" * 50)

def check_and_install_packages():
    """Check and install required system packages"""
    print("📦 Checking system packages...")
    
    packages_to_check = [
        ("alsa-utils", "arecord"),
        ("pulseaudio", "pactl"), 
        ("mpg123", "mpg123")
    ]
    
    missing_packages = []
    
    for package, command in packages_to_check:
        try:
            result = subprocess.run([command, "--version"], capture_output=True, timeout=2)
            if result.returncode == 0:
                print(f"✅ {package} is installed")
            else:
                missing_packages.append(package)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Run this command to install them:")
        print(f"sudo apt-get update && sudo apt-get install -y {' '.join(missing_packages)}")
        return False
    else:
        print("✅ All required system packages are installed")
        return True

def test_microphone_basic():
    """Basic microphone test"""
    print("\n🎤 Testing microphone...")
    print("This will record 3 seconds of audio and play it back")
    
    try:
        # Record test
        print("🔴 Recording... speak now!")
        result = subprocess.run(
            ["arecord", "-d", "3", "-f", "cd", "test_recording.wav"],
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Recording failed - check microphone connection")
            return False
        
        print("✅ Recording completed")
        
        # Play back test
        print("🔊 Playing back recording...")
        result = subprocess.run(
            ["aplay", "test_recording.wav"],
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Playback failed - check audio output")
        else:
            print("✅ Playback completed")
        
        # Clean up
        if os.path.exists("test_recording.wav"):
            os.remove("test_recording.wav")
        
        response = input("\n❓ Did you hear your voice played back? (y/n): ").lower()
        return response.startswith('y')
        
    except subprocess.TimeoutExpired:
        print("❌ Audio test timed out")
        return False
    except Exception as e:
        print(f"❌ Audio test error: {e}")
        return False

def show_audio_devices():
    """Show available audio devices"""
    print("\n📋 Available audio devices:")
    
    try:
        result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
        if result.returncode == 0:
            print("🎤 Recording devices:")
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('*'):
                    print(f"  {line}")
        
        print()
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        if result.returncode == 0:
            print("🔊 Playback devices:")
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('*'):
                    print(f"  {line}")
    except Exception as e:
        print(f"Error listing devices: {e}")

def test_python_recognition():
    """Test Python speech recognition"""
    print("\n🐍 Testing Python speech recognition...")
    
    try:
        import speech_recognition as sr
        
        # Create recognizer with RPi optimized settings
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8
        
        # Test microphone
        mic_list = sr.Microphone.list_microphone_names()
        print(f"📊 Found {len(mic_list)} microphones:")
        for i, name in enumerate(mic_list):
            print(f"  [{i}] {name}")
        
        # Try to find the best microphone
        best_mic = None
        for i, name in enumerate(mic_list):
            if any(keyword in name.lower() for keyword in ['usb', 'webcam', 'logitech']):
                best_mic = i
                print(f"💡 Suggesting microphone [{i}]: {name}")
                break
        
        if best_mic is not None:
            microphone = sr.Microphone(device_index=best_mic)
        else:
            microphone = sr.Microphone()
            print("💡 Using default microphone")
        
        # Test recognition
        with microphone as source:
            print("🎯 Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source, duration=2)
            print(f"📊 Energy threshold: {r.energy_threshold}")
            
            print("🎤 Say something in English (10 seconds)...")
            audio = r.listen(source, timeout=10, phrase_time_limit=8)
            
            print("🧠 Processing...")
            text = r.recognize_google(audio, language="en-IN")
            print(f"✅ Recognized: '{text}'")
            return True
            
    except ImportError:
        print("❌ SpeechRecognition not installed. Run: pip install SpeechRecognition")
        return False
    except sr.WaitTimeoutError:
        print("⏰ No speech detected - microphone might be too quiet or not working")
        return False
    except sr.UnknownValueError:
        print("❓ Speech detected but not understood - try speaking clearer")
        return False
    except Exception as e:
        print(f"❌ Recognition error: {e}")
        return False

def show_fixes():
    """Show common fixes for Raspberry Pi microphone issues"""
    print("\n💡 Common fixes for Raspberry Pi microphone issues:")
    print()
    
    fixes = [
        "1. Check microphone connection:",
        "   - Use a USB microphone if possible (better than 3.5mm)",
        "   - Try different USB ports",
        "   - Check cable connections",
        "",
        "2. Increase microphone volume:",
        "   - Run: alsamixer",
        "   - Press F4 for capture devices",
        "   - Use arrow keys to select microphone",
        "   - Use +/- to increase volume",
        "   - Press M to unmute if needed",
        "",
        "3. Add user to audio group:",
        "   - Run: sudo usermod -a -G audio $USER",
        "   - Then reboot: sudo reboot",
        "",
        "4. Install audio packages:",
        "   - Run: sudo apt-get install alsa-utils pulseaudio",
        "",
        "5. Test with different settings:",
        "   - Try USB headset with microphone",
        "   - Test in quieter environment",
        "   - Speak closer to microphone",
        "",
        "6. Check device permissions:",
        "   - Run: ls -la /dev/snd/",
        "   - Should show audio devices accessible to your user"
    ]
    
    for fix in fixes:
        print(fix)

def main():
    """Main function"""
    print_header()
    
    # Check system packages
    packages_ok = check_and_install_packages()
    
    # Show available devices
    show_audio_devices()
    
    # Test basic microphone
    if packages_ok:
        mic_ok = test_microphone_basic()
        
        if mic_ok:
            print("✅ Basic microphone test passed!")
            
            # Test Python recognition
            python_ok = test_python_recognition()
            
            if python_ok:
                print("\n🎉 SUCCESS! Your microphone is working with Python speech recognition!")
                print("💡 You can now use the voice recognition applications.")
            else:
                print("\n⚠️ Basic microphone works but Python recognition failed.")
                show_fixes()
        else:
            print("\n❌ Basic microphone test failed.")
            show_fixes()
    else:
        print("\n❌ Missing required packages. Install them first.")
    
    print("\n" + "=" * 50)
    print("🔧 Microphone test completed!")
    
    # Offer to run the diagnostic tool
    response = input("\n❓ Run comprehensive diagnostic? (y/n): ").lower()
    if response.startswith('y'):
        print("\n🚀 Running comprehensive diagnostic...")
        try:
            from rpi_microphone_test import RaspberryPiMicrophoneTest
            tester = RaspberryPiMicrophoneTest()
            tester.run_comprehensive_test()
        except Exception as e:
            print(f"❌ Diagnostic failed: {e}")

if __name__ == "__main__":
    main()