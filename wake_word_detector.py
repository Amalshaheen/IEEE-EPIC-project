"""
Wake Word Detection Module for IEEE EPIC Project
Replaces handshake detection with voice activation
"""

import speech_recognition as sr
import threading
import time
from loguru import logger
from typing import Callable, Optional


class WakeWordDetector:
    """Simple wake word detector using continuous speech recognition"""
    
    def __init__(self, wake_words: list = None, sensitivity_threshold: int = 5):
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
        self._initialize_microphone()
        
    def _initialize_microphone(self):
        """Initialize microphone for wake word detection"""
        try:
            self.microphone = sr.Microphone()
            # Lower thresholds for wake word detection
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.5  # Shorter pauses
            
            with self.microphone as source:
                logger.info("Calibrating microphone for wake word detection...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.success("Wake word microphone calibrated")
                
        except Exception as e:
            logger.error(f"Failed to initialize microphone for wake word: {e}")
            self.microphone = None
    
    def set_callback(self, callback: Callable):
        """Set callback function to be called when wake word is detected"""
        self.callback = callback
    
    def start_listening(self):
        """Start continuous listening for wake words"""
        if not self.microphone:
            logger.error("Cannot start wake word listening - microphone not available")
            return False
        
        self.is_listening = True
        listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listening_thread.start()
        logger.info(f"🎤 Wake word detection started - listening for: {', '.join(self.wake_words)}")
        return True
    
    def stop_listening(self):
        """Stop wake word detection"""
        self.is_listening = False
        logger.info("🎤 Wake word detection stopped")
    
    def _listen_loop(self):
        """Main wake word detection loop"""
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while self.is_listening:
            try:
                # Quick listen for potential wake word
                with self.microphone as source:
                    logger.debug("👂 Listening for wake word...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=self.sensitivity_threshold,
                        phrase_time_limit=3  # Short phrases only
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
                                
                                if self.callback:
                                    self.callback()
                                break
                    
                    consecutive_failures = 0
                    
                except sr.UnknownValueError:
                    # This is normal - no clear speech detected
                    consecutive_failures = 0
                    continue
                except sr.RequestError as e:
                    logger.warning(f"Speech recognition service error: {e}")
                    consecutive_failures += 1
                    
            except sr.WaitTimeoutError:
                # Timeout is normal for continuous listening
                consecutive_failures = 0
                continue
            except Exception as e:
                logger.error(f"Wake word detection error: {e}")
                consecutive_failures += 1
            
            # If too many consecutive failures, take a longer break
            if consecutive_failures >= max_consecutive_failures:
                logger.warning(f"Too many consecutive failures ({consecutive_failures}), taking a break...")
                time.sleep(5)
                consecutive_failures = 0
            else:
                time.sleep(0.1)  # Short delay between attempts
    
    def is_available(self) -> bool:
        """Check if wake word detection is available"""
        return self.microphone is not None


class WakeWordVoiceAI:
    """Voice AI with wake word activation instead of handshake"""
    
    def __init__(self, wake_words: list = None):
        # Import your existing modules
        from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
        from ieee_epic.core.simple_tts import SimpleTextToSpeech
        from ieee_epic.core.ai_response import AIResponseSystem
        from ieee_epic.core.config import Settings
        
        # Initialize components
        self.settings = Settings()
        self.stt = SimpleSpeechRecognizer()
        self.tts = SimpleTextToSpeech()
        self.ai_system = AIResponseSystem(self.settings)
        
        # Initialize wake word detector
        self.wake_detector = WakeWordDetector(wake_words)
        self.wake_detector.set_callback(self.on_wake_word_detected)
        
        self.conversation_active = False
        
    def on_wake_word_detected(self):
        """Handle wake word detection"""
        if self.conversation_active:
            logger.info("Conversation already active, ignoring wake word")
            return
        
        logger.info("🎯 Wake word detected! Starting conversation...")
        
        # Start conversation in separate thread
        conversation_thread = threading.Thread(target=self.handle_conversation, daemon=True)
        conversation_thread.start()
    
    def handle_conversation(self):
        """Handle conversation after wake word detection"""
        self.conversation_active = True
        
        try:
            # Acknowledge wake word
            greeting = "Hi! I heard you call me. How can I help you?"
            logger.info(f"🤖 AI: {greeting}")
            
            if not self.tts.speak(greeting, "en"):
                logger.warning("⚠️ TTS failed for greeting")
            
            # Listen for user input
            max_turns = 5
            turn = 0
            
            while turn < max_turns:
                logger.info(f"🎤 Listening for your request... (Turn {turn + 1}/{max_turns})")
                
                text, language = self.stt.listen_and_recognize("auto", timeout=10)
                
                if text:
                    lang_name = "Malayalam" if language == "ml" else "English"
                    logger.info(f"👤 You ({lang_name}): {text}")
                    
                    # Check for goodbye
                    if self._should_end_conversation(text):
                        farewell = "Goodbye! Just say my wake word to talk again."
                        logger.info(f"🤖 AI: {farewell}")
                        self.tts.speak(farewell, "en")
                        break
                    
                    # Generate AI response
                    logger.info("🧠 AI thinking...")
                    response = self.ai_system.generate_response(text)
                    logger.info(f"🤖 AI: {response}")
                    
                    # Speak response
                    if not self.tts.speak(response, language):
                        logger.warning("⚠️ TTS failed for AI response")
                    
                    turn += 1
                else:
                    logger.warning("❌ Could not understand speech")
                    
        except Exception as e:
            logger.error(f"Error in wake word conversation: {e}")
        finally:
            self.conversation_active = False
            logger.info("👋 Conversation ended. Say wake word to start again.")
    
    def _should_end_conversation(self, text: str) -> bool:
        """Check if conversation should end"""
        end_phrases = ["goodbye", "bye", "stop", "end", "quit", "done", "thanks"]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in end_phrases)
    
    def start(self):
        """Start the wake word voice AI system"""
        logger.info("🚀 Starting Wake Word Voice AI System")
        logger.info(f"Wake words: {', '.join(self.wake_detector.wake_words)}")
        
        if not self.wake_detector.start_listening():
            logger.error("❌ Failed to start wake word detection")
            return
        
        try:
            logger.info("✅ System ready! Say a wake word to start conversation.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")
            self.wake_detector.stop_listening()


if __name__ == "__main__":
    # Example usage
    wake_words = ["hey saras", "hello saras", "saras"]
    ai = WakeWordVoiceAI(wake_words)
    ai.start()