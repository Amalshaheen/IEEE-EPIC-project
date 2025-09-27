#!/usr/bin/env python3
"""
Raspberry Pi Microphone Test and Diagnostic Tool
Helps diagnose and fix microphone issues on Raspberry Pi
"""

import speech_recognition as sr
import pyaudio
import time
import os
import subprocess
from loguru import logger


class RaspberryPiMicrophoneTest:
    """Test and diagnose microphone issues on Raspberry Pi"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def check_system_audio(self):
        """Check system audio configuration"""
        logger.info("🔍 Checking system audio configuration...")
        
        try:
            # Check ALSA devices
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("📋 Available recording devices:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")
            else:
                logger.warning("Could not list ALSA recording devices")
                
        except FileNotFoundError:
            logger.warning("arecord not found - ALSA tools not installed")
        
        try:
            # Check PulseAudio sources
            result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("📋 PulseAudio sources:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")
            else:
                logger.info("PulseAudio not running or not available")
                
        except FileNotFoundError:
            logger.info("PulseAudio not installed")
    
    def test_pyaudio_devices(self):
        """Test PyAudio device availability"""
        logger.info("🎤 Testing PyAudio devices...")
        
        try:
            p = pyaudio.PyAudio()
            
            logger.info(f"📊 PyAudio version: {pyaudio.get_version_text()}")
            logger.info(f"📊 PortAudio version: {p.get_version_text()}")
            
            device_count = p.get_device_count()
            logger.info(f"📊 Found {device_count} audio devices:")
            
            input_devices = []
            
            for i in range(device_count):
                try:
                    info = p.get_device_info_by_index(i)
                    device_type = ""
                    if info['maxInputChannels'] > 0:
                        device_type += "INPUT "
                        input_devices.append((i, info['name']))
                    if info['maxOutputChannels'] > 0:
                        device_type += "OUTPUT"
                    
                    logger.info(f"  [{i}] {info['name']} ({device_type})")
                    logger.info(f"      Sample Rate: {info['defaultSampleRate']}")
                    logger.info(f"      Input Channels: {info['maxInputChannels']}")
                    
                except Exception as e:
                    logger.warning(f"  [{i}] Error getting device info: {e}")
            
            p.terminate()
            
            if not input_devices:
                logger.error("❌ No input devices found!")
                return None
            else:
                logger.success(f"✅ Found {len(input_devices)} input devices")
                return input_devices
                
        except Exception as e:
            logger.error(f"❌ PyAudio error: {e}")
            return None
    
    def test_microphone_levels(self, device_index=None):
        """Test microphone input levels"""
        logger.info("🔊 Testing microphone levels...")
        
        try:
            if device_index is not None:
                mic = sr.Microphone(device_index=device_index)
                logger.info(f"Using device index: {device_index}")
            else:
                mic = sr.Microphone()
                logger.info("Using default microphone")
            
            with mic as source:
                logger.info("🎯 Adjusting for ambient noise (5 seconds)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=5)
                
                energy_threshold = self.recognizer.energy_threshold
                logger.info(f"📊 Energy threshold set to: {energy_threshold}")
                
                # Test listening for a short period
                logger.info("🎤 Testing microphone input (speak now for 3 seconds)...")
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    logger.success("✅ Microphone input detected!")
                    return True
                except sr.WaitTimeoutError:
                    logger.warning("⏰ No speech detected - microphone might be too quiet")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Microphone test error: {e}")
            return False
    
    def test_speech_recognition(self, device_index=None):
        """Test speech recognition with specific device"""
        logger.info("🧠 Testing speech recognition...")
        
        try:
            if device_index is not None:
                mic = sr.Microphone(device_index=device_index)
            else:
                mic = sr.Microphone()
            
            # Configure recognizer for Raspberry Pi
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            with mic as source:
                logger.info("🎯 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                
                logger.info("🎤 Say something in English (you have 10 seconds)...")
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=8)
                
                logger.info("🔍 Processing speech...")
                text = self.recognizer.recognize_google(audio, language="en-IN")
                logger.success(f"✅ Recognized: '{text}'")
                return text
                
        except sr.WaitTimeoutError:
            logger.warning("⏰ No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            logger.warning("❓ Speech was detected but not understood")
            return None
        except sr.RequestError as e:
            logger.error(f"❌ Recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Recognition error: {e}")
            return None
    
    def suggest_fixes(self):
        """Suggest fixes for common Raspberry Pi microphone issues"""
        logger.info("💡 Raspberry Pi microphone troubleshooting suggestions:")
        
        suggestions = [
            "1. Check USB microphone connection (USB mics work better than built-in)",
            "2. Increase microphone volume: alsamixer -> F4 -> select mic -> increase",
            "3. Test microphone: arecord -d 5 test.wav && aplay test.wav",
            "4. Add user to audio group: sudo usermod -a -G audio $USER",
            "5. Install audio packages: sudo apt-get install alsa-utils pulseaudio",
            "6. Check permissions: ls -la /dev/snd/",
            "7. Try different USB port for USB microphones",
            "8. Update system: sudo apt-get update && sudo apt-get upgrade",
            "9. Reboot after making changes: sudo reboot"
        ]
        
        for suggestion in suggestions:
            logger.info(f"  {suggestion}")
    
    def run_comprehensive_test(self):
        """Run all diagnostic tests"""
        logger.info("🚀 Starting comprehensive microphone test for Raspberry Pi...")
        logger.info("=" * 60)
        
        # System audio check
        self.check_system_audio()
        logger.info("-" * 40)
        
        # PyAudio device test
        input_devices = self.test_pyaudio_devices()
        logger.info("-" * 40)
        
        if input_devices:
            # Test each input device
            for device_index, device_name in input_devices:
                logger.info(f"🧪 Testing device [{device_index}]: {device_name}")
                
                # Test microphone levels
                level_ok = self.test_microphone_levels(device_index)
                
                if level_ok:
                    # Test speech recognition
                    result = self.test_speech_recognition(device_index)
                    if result:
                        logger.success(f"✅ Device [{device_index}] works perfectly!")
                        return device_index
                    else:
                        logger.warning(f"⚠️ Device [{device_index}] detects audio but recognition failed")
                else:
                    logger.warning(f"⚠️ Device [{device_index}] has low input levels")
                
                logger.info("-" * 40)
        
        # Suggest fixes
        self.suggest_fixes()
        logger.info("=" * 60)
        
        return None


def main():
    """Main function to run the test"""
    logger.info("🔧 Raspberry Pi Microphone Diagnostic Tool")
    logger.info("This tool will help diagnose microphone issues on Raspberry Pi")
    logger.info("")
    
    try:
        tester = RaspberryPiMicrophoneTest()
        working_device = tester.run_comprehensive_test()
        
        if working_device is not None:
            logger.success(f"🎉 Found working microphone at device index: {working_device}")
            logger.info(f"💡 Use this in your code: sr.Microphone(device_index={working_device})")
        else:
            logger.warning("🔍 No fully working microphone found. See suggestions above.")
            
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()