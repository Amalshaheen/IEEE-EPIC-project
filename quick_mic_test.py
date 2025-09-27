#!/usr/bin/env python3
"""
Quick microphone test for Raspberry Pi
Test this before running the full voice recognition
"""

import speech_recognition as sr
import time
from loguru import logger

def quick_mic_test():
    """Quick microphone test with RPi optimized settings"""
    logger.info("🔧 Quick Raspberry Pi Microphone Test")
    
    try:
        # Create recognizer with RPi settings
        r = sr.Recognizer()
        r.energy_threshold = 200  # Lower threshold
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.5   # Shorter pause
        r.operation_timeout = None
        
        # List available microphones
        mics = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphones: {len(mics)}")
        for i, mic in enumerate(mics):
            logger.info(f"  [{i}] {mic}")
        
        # Try to find USB microphone (better for RPi)
        usb_mic = None
        for i, mic in enumerate(mics):
            if 'usb' in mic.lower() or 'webcam' in mic.lower():
                usb_mic = i
                logger.info(f"Found USB microphone at index {i}: {mic}")
                break
        
        # Use USB mic if found, otherwise default
        if usb_mic is not None:
            microphone = sr.Microphone(device_index=usb_mic)
            logger.info(f"Using USB microphone: {mics[usb_mic]}")
        else:
            microphone = sr.Microphone()
            logger.info("Using default microphone")
        
        # Test microphone
        with microphone as source:
            logger.info("Calibrating microphone (3 seconds)...")
            r.adjust_for_ambient_noise(source, duration=3)
            threshold = r.energy_threshold
            logger.info(f"Energy threshold set to: {threshold}")
            
            if threshold < 100:
                logger.warning("Energy threshold very low - microphone might be too quiet")
                r.energy_threshold = 300  # Force higher threshold
                logger.info(f"Forced energy threshold to: {r.energy_threshold}")
            
            logger.info("🎤 Say 'HELLO TESTING' loudly and clearly (10 seconds)...")
            logger.info("Speak close to the microphone!")
            
            try:
                audio = r.listen(source, timeout=10, phrase_time_limit=5)
                logger.info("✅ Audio captured! Processing...")
                
                # Try recognition
                text = r.recognize_google(audio, language="en-IN")
                logger.success(f"🎉 SUCCESS! Recognized: '{text}'")
                
                return True, usb_mic
                
            except sr.WaitTimeoutError:
                logger.error("❌ TIMEOUT - No speech detected")
                logger.info("💡 Try:")
                logger.info("  1. Speak MUCH LOUDER")
                logger.info("  2. Get closer to microphone") 
                logger.info("  3. Increase mic volume: alsamixer -> F4 -> select mic -> increase volume")
                return False, usb_mic
                
            except sr.UnknownValueError:
                logger.warning("❓ Audio detected but not understood")
                logger.info("💡 Try speaking more clearly")
                return False, usb_mic
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False, None

if __name__ == "__main__":
    success, mic_index = quick_mic_test()
    
    if success:
        print(f"\n🎉 MICROPHONE WORKS!")
        if mic_index is not None:
            print(f"💡 Use device index {mic_index} in your applications")
        print("✅ You can now run the voice recognition applications")
    else:
        print(f"\n❌ MICROPHONE NEEDS FIXING")
        print("🔧 Run these commands to fix:")
        print("1. alsamixer")
        print("2. Press F4")
        print("3. Select microphone with arrow keys") 
        print("4. Press + to increase volume to 80-100%")
        print("5. Press M to unmute if needed")
        print("6. Press Esc to exit")
        print("7. Test again: arecord -d 3 test.wav && aplay test.wav")