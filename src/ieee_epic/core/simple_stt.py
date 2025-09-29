"""
Simplified Speech Recognition Module for IEEE EPIC Project
Uses SpeechRecognition library with Google's free API
"""

import speech_recognition as sr
from typing import Optional, Tuple
from loguru import logger
import time


class SimpleSpeechRecognizer:
    """Simple speech recognizer using Google's free API"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self._initialize_microphone()
    
    def _initialize_microphone(self):
        """Initialize and calibrate the microphone"""
        try:
            # First, list available microphones to help debug
            self.get_available_microphones()
            
            # Try to find the best microphone (prefer USB mics on RPi)
            mic_list = sr.Microphone.list_microphone_names()
            best_mic_index = None
            
            # Look for USB or external microphones first (better for RPi)
            for i, name in enumerate(mic_list):
                if any(keyword in name.lower() for keyword in ['usb', 'webcam', 'logitech', 'blue', 'audio-technica', 'plantronics', 'hyperx']):
                    best_mic_index = i
                    logger.info(f"Found preferred USB microphone: {name} (index {i})")
                    break
            
            # If no USB device found, try to find any working device
            if best_mic_index is None:
                logger.warning("No USB microphone found, trying to find best available device...")
                # Try each device to find one that works
                for i, name in enumerate(mic_list):
                    try:
                        test_mic = sr.Microphone(device_index=i)
                        if test_mic is not None:
                            with test_mic as source:
                                # Quick test - just try to access the device
                                logger.info(f"Testing device {i}: {name}")
                                time.sleep(0.1)  # Short test
                                best_mic_index = i
                                logger.info(f"Device {i} accessible: {name}")
                                break
                        else:
                            logger.warning(f"Device {i} returned None: {name}")
                    except Exception as e:
                        logger.warning(f"Device {i} not accessible: {e}")
                        continue
            
            # Initialize microphone with specific device if found
            if best_mic_index is not None:
                try:
                    self.microphone = sr.Microphone(device_index=best_mic_index)
                    logger.info(f"Using microphone index {best_mic_index}: {mic_list[best_mic_index]}")
                except Exception as mic_e:
                    logger.error(f"Failed to initialize microphone {best_mic_index}: {mic_e}")
                    # Try default microphone as fallback
                    try:
                        self.microphone = sr.Microphone()
                        logger.warning("Fallback to default microphone due to device-specific error")
                    except Exception as default_e:
                        logger.error(f"Failed to initialize default microphone: {default_e}")
                        self.microphone = None
            else:
                try:
                    self.microphone = sr.Microphone()
                    logger.warning("Using default microphone - USB microphone detection failed")
                except Exception as default_e:
                    logger.error(f"Failed to initialize default microphone: {default_e}")
                    self.microphone = None
            
            # Raspberry Pi + USB microphone specific settings
            self.recognizer.energy_threshold = 200  # Lower threshold for USB mics
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.6  # Shorter pause detection
            self.recognizer.operation_timeout = None  # Disable operation timeout
            
            # Calibrate for ambient noise with longer duration for RPi + USB mic
            if self.microphone is not None:
                try:
                    logger.info(f"Microphone object type: {type(self.microphone)}")
                    logger.info(f"Microphone device index: {getattr(self.microphone, 'device_index', 'unknown')}")
                    
                    # Test if microphone can be opened before full calibration
                    try:
                        with self.microphone as source:
                            # Quick test to see if the device can be opened
                            pass
                    except Exception as test_e:
                        logger.warning(f"USB microphone test failed: {test_e}")
                        # Try fallback to default microphone
                        logger.info("Attempting fallback to default microphone...")
                        try:
                            self.microphone = sr.Microphone()
                            logger.info("Fallback to default microphone successful")
                        except Exception as fallback_e:
                            logger.error(f"Fallback to default microphone failed: {fallback_e}")
                            self.microphone = None
                    
                    # Only proceed with calibration if microphone is still available
                    if self.microphone is not None:
                        with self.microphone as source:
                            logger.info("Calibrating microphone for ambient noise...")
                            # Shorter calibration to avoid issues
                            self.recognizer.adjust_for_ambient_noise(source, duration=1)
                            
                            # Check if energy threshold is reasonable
                            threshold = self.recognizer.energy_threshold
                            logger.info(f"Energy threshold set to: {threshold}")
                            
                            # Adjust thresholds for different microphone types
                            if threshold < 100:
                                logger.warning("Energy threshold very low - setting minimum")
                                self.recognizer.energy_threshold = 250
                            elif threshold > 4000:
                                logger.warning("Energy threshold very high - capping")
                                self.recognizer.energy_threshold = 1000
                            
                            logger.info(f"Final energy threshold: {self.recognizer.energy_threshold}")
                            logger.success("Microphone calibrated successfully")
                    
                except Exception as calib_e:
                    logger.error(f"Failed to calibrate microphone: {calib_e}")
                    logger.error(f"Exception type: {type(calib_e)}")
                    logger.warning("Continuing without calibration...")
                    # Don't set microphone to None here, keep it for listening
            else:
                logger.error("Microphone object is None - skipping calibration")
                
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            logger.error("💡 USB Microphone troubleshooting:")
            logger.error("  1. Run: python usb_mic_fix.py")
            logger.error("  2. Check: arecord -l")
            logger.error("  3. Test: arecord -d 3 test.wav && aplay test.wav")
            logger.error("  4. Volume: alsamixer -> F6 -> select USB device -> F4 -> increase volume")
            self.microphone = None
    
    def listen_for_speech(self, timeout: int = 10, phrase_time_limit: int = 15) -> Optional[sr.AudioData]:
        """Listen for speech input with improved error handling"""
        if not self.microphone:
            logger.error("Microphone not available")
            return None
        
        try:
            # Create a new context each time to avoid issues with previous contexts
            logger.info("🎤 Listening for speech...")
            
            # Try to open the microphone safely
            try:
                with self.microphone as source:
                    # Brief ambient noise adjustment
                    try:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    except Exception as ambient_e:
                        logger.warning(f"Ambient noise adjustment failed: {ambient_e}")
                    
                    # Listen for audio with error handling
                    audio = self.recognizer.listen(
                        source, 
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                    logger.info("✅ Audio captured")
                    return audio
                    
            except Exception as context_e:
                logger.error(f"❌ Microphone context error: {context_e}")
                # Try to reinitialize microphone if context fails
                logger.info("Attempting to reinitialize microphone...")
                self._reinitialize_microphone()
                return None
                
        except sr.WaitTimeoutError:
            logger.warning("⏰ Listening timeout - no speech detected")
            logger.info("💡 Try speaking louder or closer to the microphone")
            return None
        except Exception as e:
            logger.error(f"❌ Error while listening: {e}")
            # Try to recover by reinitializing
            self._reinitialize_microphone()
            return None
    
    def _reinitialize_microphone(self):
        """Reinitialize microphone after errors"""
        try:
            logger.info("Reinitializing microphone...")
            old_mic = self.microphone
            self.microphone = None
            
            # Brief delay to let resources clean up
            time.sleep(0.5)
            
            # Try to reinitialize
            self._initialize_microphone()
            
            if self.microphone:
                logger.success("Microphone reinitialized successfully")
            else:
                logger.error("Failed to reinitialize microphone")
                
        except Exception as e:
            logger.error(f"Error during microphone reinitialization: {e}")
            self.microphone = None
    
    def recognize_speech(self, audio_data: sr.AudioData, language: str = "auto") -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize speech from audio data
        
        Args:
            audio_data: Audio data to recognize
            language: Target language ('ml', 'en', or 'auto')
        
        Returns:
            Tuple of (recognized_text, detected_language)
        """
        if not audio_data:
            return None, None
        
        if language == "auto":
            # Try Malayalam first, then English
            return self._try_bilingual_recognition(audio_data)
        elif language == "ml":
            return self._recognize_single_language(audio_data, "ml-IN", "ml")
        elif language == "en":
            return self._recognize_single_language(audio_data, "en-IN", "en")
        else:
            logger.warning(f"Unsupported language: {language}")
            return None, None
    
    def _try_bilingual_recognition(self, audio_data: sr.AudioData) -> Tuple[Optional[str], Optional[str]]:
        """Try recognition in both Malayalam and English"""
        # Try Malayalam first
        text, lang = self._recognize_single_language(audio_data, "ml-IN", "ml")
        if text:
            return text, lang
        
        # Fall back to English
        text, lang = self._recognize_single_language(audio_data, "en-IN", "en")
        return text, lang
    
    def _recognize_single_language(self, audio_data: sr.AudioData, google_lang: str, lang_code: str) -> Tuple[Optional[str], Optional[str]]:
        """Recognize speech in a single language"""
        try:
            logger.info(f"🔍 Trying recognition in {lang_code}...")
            text = self.recognizer.recognize_google(audio_data, language=google_lang)
            
            if text and text.strip():
                logger.success(f"✅ {lang_code.upper()} recognized: {text}")
                return text.strip(), lang_code
            else:
                return None, None
                
        except sr.UnknownValueError:
            logger.warning(f"❌ Could not understand audio in {lang_code}")
            return None, None
        except sr.RequestError as e:
            logger.error(f"❌ Recognition service error for {lang_code}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"❌ Unexpected error in {lang_code} recognition: {e}")
            return None, None
    
    def listen_and_recognize(self, language: str = "auto", timeout: int = 10) -> Tuple[Optional[str], Optional[str]]:
        """
        Listen for speech and recognize it
        
        Args:
            language: Target language ('ml', 'en', or 'auto')
            timeout: Listening timeout in seconds
        
        Returns:
            Tuple of (recognized_text, detected_language)
        """
        # Listen for audio
        audio_data = self.listen_for_speech(timeout=timeout)
        if not audio_data:
            return None, None
        
        # Recognize speech
        return self.recognize_speech(audio_data, language)
    
    def is_available(self) -> bool:
        """Check if the speech recognizer is available"""
        return self.microphone is not None
    
    def get_available_microphones(self):
        """Get list of available microphones"""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            logger.info("Available microphones:")
            for i, name in enumerate(mic_list):
                logger.info(f"  {i}: {name}")
            return mic_list
        except Exception as e:
            logger.error(f"Failed to get microphone list: {e}")
            return []


# Convenience functions for easy usage
def listen_and_recognize_auto() -> Tuple[Optional[str], Optional[str]]:
    """Quick function to listen and recognize speech automatically"""
    recognizer = SimpleSpeechRecognizer()
    if not recognizer.is_available():
        logger.error("Speech recognizer not available")
        return None, None
    
    return recognizer.listen_and_recognize("auto")


def listen_and_recognize_language(language: str) -> Tuple[Optional[str], Optional[str]]:
    """Quick function to listen and recognize speech in specific language"""
    recognizer = SimpleSpeechRecognizer()
    if not recognizer.is_available():
        logger.error("Speech recognizer not available")
        return None, None
    
    return recognizer.listen_and_recognize(language)