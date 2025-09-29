"""
Fixed Wake Word Detection Module for IEEE EPIC Project
Improved audio handling and error recovery
"""

import speech_recognition as sr
import threading
import time
import os
from loguru import logger
from typing import Callable, Optional


class FixedWakeWordDetector:
    """Improved wake word detector with better audio handling"""
    
    def __init__(self, wake_words: list = None, sensitivity_threshold: int = 3):
        """
        Initialize wake word detector
        
        Args:
            wake_words: List of wake words to listen for (default: ["hey saras", "hello saras"])
            sensitivity_threshold: How long to listen for each attempt (seconds)
        """
        self.wake_words = wake_words or ["hey saras", "hello saras", "saras"]
        self.sensitivity_threshold = sensitivity_threshold
        self.is_listening = False
        self.callback = None
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self._running = True
        
        # Set environment variables for better audio handling
        os.environ.setdefault('PULSE_LATENCY_MSEC', '30')
        
        self._initialize_microphone()
        
    def _initialize_microphone(self):
        """Initialize microphone for wake word detection with error handling"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing microphone for wake word (attempt {attempt + 1}/{max_retries})...")
                
                # Try to get available microphones first
                try:
                    available_mics = sr.Microphone.list_microphone_names()
                    logger.info(f"Available microphones: {len(available_mics)}")
                except Exception as list_e:
                    logger.warning(f"Could not list microphones: {list_e}")
                
                # Initialize with default microphone
                self.microphone = sr.Recognizer().recognize_google
                
                # Actually create the microphone object
                test_mic = sr.Microphone()
                
                # Test the microphone by trying to open it briefly
                with test_mic as source:
                    # Quick test to see if device works
                    self.recognizer = sr.Recognizer()
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # If we get here, the microphone works
                self.microphone = test_mic
                
                # Configure recognizer settings for wake word detection
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.4  # Shorter pauses
                self.recognizer.operation_timeout = None  # No timeout
                
                logger.success(f"Wake word microphone initialized successfully on attempt {attempt + 1}")
                return
                
            except Exception as e:
                logger.error(f"Failed to initialize wake word microphone on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error("Could not initialize microphone for wake word detection")
                    self.microphone = None
    
    def set_callback(self, callback: Callable):
        """Set callback function to be called when wake word is detected"""
        self.callback = callback
    
    def start_listening(self):
        """Start continuous listening for wake words"""
        if not self.microphone:
            logger.error("Cannot start wake word listening - microphone not available")
            return False
        
        if self.is_listening:
            logger.warning("Wake word detection already running")
            return True
        
        self.is_listening = True
        self._running = True
        
        # Start listening thread
        listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listening_thread.start()
        
        logger.info(f"🎤 Wake word detection started - listening for: {', '.join(self.wake_words)}")
        return True
    
    def stop_listening(self):
        """Stop wake word detection"""
        self.is_listening = False
        self._running = False
        logger.info("🎤 Wake word detection stopped")
    
    def _listen_loop(self):
        """Main wake word detection loop with improved error handling"""
        consecutive_failures = 0
        max_consecutive_failures = 3
        recovery_delay = 2
        
        while self.is_listening and self._running:
            try:
                # Check if microphone is still available
                if not self.microphone:
                    logger.error("Microphone lost during wake word detection")
                    break
                
                # Listen for potential wake word with shorter timeout
                try:
                    with self.microphone as source:
                        logger.debug("👂 Listening for wake word...")
                        
                        # Quick ambient noise adjustment
                        try:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        except Exception as ambient_e:
                            logger.debug(f"Ambient adjustment skipped: {ambient_e}")
                        
                        # Listen for audio
                        audio = self.recognizer.listen(
                            source, 
                            timeout=self.sensitivity_threshold,
                            phrase_time_limit=2  # Short phrases only for wake words
                        )
                    
                    # Quick recognition attempt
                    try:
                        text = self.recognizer.recognize_google(
                            audio, 
                            language="en-US"  # English only for wake words
                        )
                        
                        if text:
                            text_lower = text.lower().strip()
                            logger.debug(f"Heard: '{text_lower}'")
                            
                            # Check if any wake word is detected
                            for wake_word in self.wake_words:
                                if wake_word.lower() in text_lower:
                                    logger.success(f"🎯 Wake word detected: '{wake_word}' in '{text}'")
                                    consecutive_failures = 0  # Reset failure counter
                                    
                                    # Call callback in separate thread to avoid blocking
                                    if self.callback:
                                        callback_thread = threading.Thread(
                                            target=self._safe_callback, 
                                            daemon=True
                                        )
                                        callback_thread.start()
                                    break
                        
                        consecutive_failures = 0
                        
                    except sr.UnknownValueError:
                        # This is normal - no clear speech detected
                        consecutive_failures = 0
                        pass
                    except sr.RequestError as e:
                        logger.warning(f"Speech recognition service error: {e}")
                        consecutive_failures += 1
                        
                except Exception as listen_e:
                    logger.error(f"Listening error: {listen_e}")
                    consecutive_failures += 1
                    
            except sr.WaitTimeoutError:
                # Timeout is normal for continuous listening
                consecutive_failures = 0
                pass
            except Exception as e:
                logger.error(f"Wake word detection error: {e}")
                consecutive_failures += 1
            
            # Handle consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                logger.warning(f"Too many consecutive failures ({consecutive_failures}), attempting recovery...")
                
                # Try to reinitialize microphone
                self._reinitialize_microphone()
                
                # Take a break
                time.sleep(recovery_delay)
                consecutive_failures = 0
            else:
                # Short delay between attempts
                time.sleep(0.1)
    
    def _safe_callback(self):
        """Safely execute callback"""
        try:
            if self.callback:
                self.callback()
        except Exception as e:
            logger.error(f"Error in wake word callback: {e}")
    
    def _reinitialize_microphone(self):
        """Try to reinitialize microphone after errors"""
        try:
            logger.info("Attempting to reinitialize wake word microphone...")
            old_mic = self.microphone
            self.microphone = None
            
            # Brief delay
            time.sleep(1)
            
            # Reinitialize
            self._initialize_microphone()
            
            if self.microphone:
                logger.success("Wake word microphone reinitialized successfully")
            else:
                logger.error("Failed to reinitialize wake word microphone")
                
        except Exception as e:
            logger.error(f"Error during wake word microphone reinitialization: {e}")
            self.microphone = None
    
    def is_available(self) -> bool:
        """Check if wake word detection is available"""
        return self.microphone is not None and self._running


# Replace the original WakeWordDetector with the fixed version
WakeWordDetector = FixedWakeWordDetector


if __name__ == "__main__":
    # Test the fixed wake word detector
    def test_callback():
        print("Wake word detected!")
    
    detector = FixedWakeWordDetector()
    detector.set_callback(test_callback)
    
    if detector.start_listening():
        print("Wake word detection started. Say 'hey saras' to test...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
            detector.stop_listening()
    else:
        print("Failed to start wake word detection")