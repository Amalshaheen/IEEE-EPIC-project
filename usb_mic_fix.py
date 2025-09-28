#!/usr/bin/env python3
"""
USB Microphone Fix Script for IEEE EPIC Project
Diagnoses and fixes common USB microphone issues on Linux
"""

import subprocess
import sys
import os
import time
from pathlib import Path
import speech_recognition as sr


def run_command(cmd, capture_output=True, show_output=True):
    """Run a shell command and return result"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if show_output and result.stdout:
                print(result.stdout)
            if show_output and result.stderr:
                print(f"STDERR: {result.stderr}")
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return False, "", str(e)


def check_audio_system():
    """Check the current audio system configuration"""
    print("🔍 CHECKING AUDIO SYSTEM CONFIGURATION")
    print("=" * 50)
    
    # Check if PipeWire/PulseAudio is running
    success, output, _ = run_command("pgrep -f pipewire")
    if success and output:
        print("✅ PipeWire is running")
        pipewire_running = True
    else:
        success, output, _ = run_command("pgrep -f pulseaudio")
        if success and output:
            print("✅ PulseAudio is running")
            pipewire_running = False
        else:
            print("❌ Neither PipeWire nor PulseAudio is running")
            return False
    
    # List audio devices
    print("\n📋 AUDIO RECORDING DEVICES:")
    run_command("arecord -l")
    
    return True


def check_usb_microphone():
    """Check USB microphone specifically"""
    print("\n🎤 CHECKING USB MICROPHONE")
    print("=" * 50)
    
    # Check if USB audio device exists
    success, output, _ = run_command("lsusb | grep -i audio")
    if success and output:
        print("✅ USB Audio device found:")
        print(output)
    else:
        print("❌ No USB Audio device found in lsusb")
    
    # Check ALSA devices
    success, output, _ = run_command("cat /proc/asound/cards")
    print("\n📋 ALSA Sound Cards:")
    print(output)
    
    # Find USB audio card
    usb_card = None
    for line in output.split('\n'):
        if 'USB' in line and 'Audio' in line:
            usb_card = line.split(':')[0].strip()
            break
    
    if usb_card:
        print(f"✅ Found USB audio card: {usb_card}")
        return usb_card
    else:
        print("❌ No USB audio card found")
        return None


def test_microphone_access():
    """Test if microphone can be accessed"""
    print("\n🧪 TESTING MICROPHONE ACCESS")
    print("=" * 50)
    
    try:
        # Test with speech_recognition library
        print("Testing with speech_recognition library...")
        
        mic_list = sr.Microphone.list_microphone_names()
        print(f"Found {len(mic_list)} microphones:")
        
        usb_mic_found = False
        usb_mic_index = None
        
        for i, name in enumerate(mic_list):
            print(f"  {i}: {name}")
            if 'USB' in name or 'PnP' in name:
                usb_mic_found = True
                usb_mic_index = i
        
        if usb_mic_found:
            print(f"✅ USB microphone found at index {usb_mic_index}")
            
            # Try to initialize the microphone
            print("Testing microphone initialization...")
            try:
                mic = sr.Microphone(device_index=usb_mic_index)
                with mic as source:
                    print("✅ Microphone accessible")
                    return True
            except Exception as e:
                print(f"❌ Failed to access microphone: {e}")
                return False
        else:
            print("❌ No USB microphone found in speech_recognition list")
            return False
            
    except Exception as e:
        print(f"❌ Error testing microphone: {e}")
        return False


def fix_pipewire_permissions():
    """Fix PipeWire permissions and configuration"""
    print("\n🔧 FIXING PIPEWIRE CONFIGURATION")
    print("=" * 50)
    
    # Add user to audio group
    username = os.getenv('USER', 'user')
    print(f"Adding user '{username}' to audio group...")
    run_command(f"sudo usermod -a -G audio {username}")
    
    # Restart PipeWire services
    print("Restarting PipeWire services...")
    run_command("systemctl --user restart pipewire pipewire-pulse")
    
    time.sleep(2)
    
    print("✅ PipeWire services restarted")


def fix_alsa_configuration():
    """Fix ALSA configuration for USB microphone"""
    print("\n🔧 FIXING ALSA CONFIGURATION")
    print("=" * 50)
    
    # Create/update .asoundrc for USB microphone priority
    home_dir = Path.home()
    asoundrc_path = home_dir / ".asoundrc"
    
    asoundrc_content = '''# USB Microphone Configuration
pcm.usb {
    type hw
    card 1
    device 0
}

pcm.!default {
    type asym
    capture.pcm "usb"
    playback.pcm "hw:0,0"
}

ctl.!default {
    type hw
    card 0
}
'''
    
    try:
        with open(asoundrc_path, 'w') as f:
            f.write(asoundrc_content)
        print(f"✅ Created/updated {asoundrc_path}")
    except Exception as e:
        print(f"❌ Failed to create .asoundrc: {e}")


def test_recording():
    """Test actual recording with the USB microphone"""
    print("\n🎯 TESTING ACTUAL RECORDING")
    print("=" * 50)
    
    # Test with arecord directly to USB device
    test_file = "usb_mic_test.wav"
    
    print("Testing direct USB microphone recording (5 seconds)...")
    print("Please speak into the microphone...")
    
    # Try different approaches
    commands_to_try = [
        f"arecord -D plughw:1,0 -d 5 -f cd {test_file}",
        f"arecord -D hw:1,0 -d 5 -r 44100 -f S16_LE -c 1 {test_file}",
        f"arecord -d 5 -f cd {test_file}",
    ]
    
    for cmd in commands_to_try:
        print(f"\nTrying: {cmd}")
        success, stdout, stderr = run_command(cmd)
        
        if success and os.path.exists(test_file):
            print("✅ Recording successful!")
            
            # Test playback
            print("Testing playback...")
            run_command(f"aplay {test_file}")
            
            # Clean up
            os.remove(test_file)
            return True
        else:
            print(f"❌ Failed: {stderr}")
    
    print("❌ All recording attempts failed")
    return False


def run_diagnostics():
    """Run complete USB microphone diagnostics"""
    print("🚀 USB MICROPHONE DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Check audio system
    if not check_audio_system():
        print("❌ Audio system check failed")
        return False
    
    # Check USB microphone hardware
    usb_card = check_usb_microphone()
    if not usb_card:
        print("❌ USB microphone hardware not detected")
        return False
    
    # Test microphone access
    if not test_microphone_access():
        print("❌ Microphone access test failed")
        
        # Try fixes
        print("\n🔧 ATTEMPTING FIXES...")
        fix_pipewire_permissions()
        fix_alsa_configuration()
        
        print("\n⚠️  Please log out and log back in for group changes to take effect")
        print("Then run this script again to test")
        return False
    
    # Test recording
    if not test_recording():
        print("❌ Recording test failed")
        return False
    
    print("\n✅ ALL TESTS PASSED!")
    print("Your USB microphone should now work with the IEEE EPIC project")
    return True


def show_manual_fixes():
    """Show manual troubleshooting steps"""
    print("\n📋 MANUAL TROUBLESHOOTING STEPS")
    print("=" * 50)
    print("If automatic fixes didn't work, try these manual steps:")
    print()
    print("1. Check USB connection:")
    print("   - Unplug and replug the USB microphone")
    print("   - Try a different USB port")
    print("   - Check if LED (if any) lights up on the microphone")
    print()
    print("2. Check volume levels:")
    print("   - Run: alsamixer")
    print("   - Press F6 to select sound card")
    print("   - Select your USB device")
    print("   - Press F4 to show capture controls")
    print("   - Use arrow keys to increase microphone volume")
    print()
    print("3. Test with PulseAudio/PipeWire:")
    print("   - Run: pavucontrol (install if needed: sudo apt install pavucontrol)")
    print("   - Go to Input Devices tab")
    print("   - Make sure USB microphone is not muted")
    print("   - Set as default if needed")
    print()
    print("4. Restart audio services:")
    print("   - systemctl --user restart pipewire pipewire-pulse")
    print("   - Or: pulseaudio --kill && pulseaudio --start")
    print()
    print("5. Check permissions:")
    print("   - Make sure you're in audio group: groups $USER")
    print("   - If not: sudo usermod -a -G audio $USER")
    print("   - Log out and back in")


if __name__ == "__main__":
    try:
        success = run_diagnostics()
        
        if not success:
            show_manual_fixes()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)