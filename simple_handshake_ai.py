#!/usr/bin/env python3
"""
Simple Handshake Voice AI - Command Line Version
Integrates proximity sensor as handshake detector with voice recognition system
Optimized for Raspberry Pi deployment
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, Tuple

# GPIO imports for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Running in development mode.")

# Ensure the local 'src' directory is importable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from loguru import logger

# Try to import our modules
try:
    from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
    from ieee_epic.core.simple_tts import SimpleTextToSpeech
    from ieee_epic.core.ai_response import AIResponseSystem
    from ieee_epic.core.config import Settings
    MODULES_AVAILABLE = True
    logger.info("✅ IEEE EPIC modules loaded successfully")
except ImportError as e:
    MODULES_AVAILABLE = False
    logger.error(f"❌ Failed to load IEEE EPIC modules: {e}")
    logger.info("Please ensure you've installed the requirements and set up the project correctly")
    sys.exit(1)


class HandshakeDetector:
    """Simple handshake detector using proximity sensor"""
    
    def __init__(self, pin: int = 17):
        self.pin = pin
        self.is_monitoring = False
        self.callback = None
        self.last_detection = 0
        self.debounce_time = 2.0  # Minimum time between detections
        
        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.pin, GPIO.IN)
                logger.info(f"✅ Handshake detector ready on GPIO pin {self.pin}")
            except Exception as e:
                logger.error(f"❌ GPIO initialization failed: {e}")
                GPIO_AVAILABLE = False
    
    def set_callback(self, callback):
        """Set callback function for handshake detection"""
        self.callback = callback
    
    def start_monitoring(self):
        """Start monitoring for handshakes"""
        if not GPIO_AVAILABLE:
            logger.warning("⚠️ Cannot start monitoring - GPIO not available")
            return False
        
        self.is_monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("🔍 Handshake monitoring started - wave your hand to begin!")
        return True
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        logger.info("🔍 Handshake monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        previous_state = None
        
        while self.is_monitoring:
            try:
                # Read sensor (LOW = object detected)
                current_state = GPIO.input(self.pin) == 0
                
                # Detect transition from no object to object
                if current_state and not previous_state:
                    current_time = time.time()
                    
                    # Check debounce
                    if current_time - self.last_detection > self.debounce_time:
                        self.last_detection = current_time
                        logger.info("👋 Handshake detected!")
                        
                        if self.callback:
                            self.callback()
                
                previous_state = current_state
                time.sleep(0.1)  # 100ms polling
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(1)
    
    def cleanup(self):
        """Cleanup GPIO"""
        self.stop_monitoring()
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except:
                pass


class SimpleVoiceAI:
    """Simple voice AI system for handshake interactions"""
    
    def __init__(self):
        self.conversation_active = False
        self.setup_components()
        self.setup_handshake_detector()
    
    def setup_components(self):
        """Initialize AI components"""
        try:
            self.settings = Settings()
            self.stt = SimpleSpeechRecognizer()
            self.tts = SimpleTextToSpeech()
            self.ai_system = AIResponseSystem(self.settings)
            
            logger.info("✅ Voice AI components initialized")
            
            # Check AI status
            status = self.ai_system.get_status()
            if status['gemini_available']:
                logger.info("✅ Gemini AI ready")
            else:
                logger.warning("⚠️ Gemini AI not available - using fallback responses")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI components: {e}")
            raise
    
    def setup_handshake_detector(self):
        """Initialize handshake detector"""
        self.handshake_detector = HandshakeDetector()
        self.handshake_detector.set_callback(self.on_handshake_detected)
    
    def on_handshake_detected(self):
        """Handle handshake detection"""
        if self.conversation_active:
            logger.info("⏭️ Conversation already active, ignoring handshake")
            return
        
        logger.info("🤝 Starting conversation from handshake...")
        
        # Start conversation in separate thread
        conversation_thread = threading.Thread(target=self.handle_conversation, daemon=True)
        conversation_thread.start()
    
    def handle_conversation(self):
        """Main conversation handler"""
        self.conversation_active = True
        
        try:
            # Generate and speak greeting
            greeting = self.get_greeting()
            logger.info(f"🤖 AI: {greeting}")
            
            if not self.tts.speak(greeting, "en"):
                logger.warning("⚠️ TTS failed for greeting")
            
            # Main conversation loop
            conversation_count = 0
            max_turns = 5  # Limit conversation length
            
            while conversation_count < max_turns:
                logger.info(f"🎤 Listening... (Turn {conversation_count + 1}/{max_turns})")
                
                # Listen for user input
                text, language = self.listen_for_input()
                
                if text:
                    lang_name = "Malayalam" if language == "ml" else "English"
                    logger.info(f"👤 You ({lang_name}): {text}")
                    
                    # Check for conversation end
                    if self.should_end_conversation(text):
                        farewell = self.get_farewell()
                        logger.info(f"🤖 AI: {farewell}")
                        self.tts.speak(farewell, "en")
                        break
                    
                    # Generate AI response
                    logger.info("🧠 AI thinking...")
                    response = self.generate_response(text)
                    
                    logger.info(f"🤖 AI: {response}")
                    
                    # Speak response
                    if not self.tts.speak(response, language):
                        logger.warning("⚠️ TTS failed for AI response")
                    
                    conversation_count += 1
                else:
                    logger.warning("❌ Could not understand speech")
                    
                    if conversation_count == 0:
                        # First attempt failed
                        retry_msg = "I didn't catch that. Could you please speak again?"
                        logger.info(f"🤖 AI: {retry_msg}")
                        self.tts.speak(retry_msg, "en")
                        continue
                    else:
                        # Multiple failures, end conversation
                        logger.info("🔇 Multiple speech recognition failures, ending conversation")
                        break
            
            if conversation_count >= max_turns:
                logger.info("💬 Maximum conversation turns reached")
                closing_msg = "It was great talking with you! Wave again anytime to chat."
                logger.info(f"🤖 AI: {closing_msg}")
                self.tts.speak(closing_msg, "en")
        
        except Exception as e:
            logger.error(f"❌ Error in conversation: {e}")
        
        finally:
            self.conversation_active = False
            logger.info("👋 Conversation ended - ready for next handshake!")
    
    def listen_for_input(self, timeout: int = 10):
        """Listen for user input with timeout"""
        try:
            text, language = self.stt.listen_and_recognize("auto", timeout=timeout)
            return text, language
        except Exception as e:
            logger.error(f"❌ Speech recognition error: {e}")
            return None, None
    
    def generate_response(self, text: str) -> str:
        """Generate AI response"""
        try:
            response = self.ai_system.generate_response(text)
            return response
        except Exception as e:
            logger.error(f"❌ AI response generation failed: {e}")
            return f"I heard you say '{text}', but I'm having some technical difficulties right now."
    
    def should_end_conversation(self, text: str) -> bool:
        """Check if conversation should end based on user input"""
        end_phrases = [
            "goodbye", "bye", "see you", "talk later", "that's all",
            "thanks", "thank you", "stop", "end", "quit", "done"
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in end_phrases)
    
    def get_greeting(self) -> str:
        """Get a random greeting"""
        greetings = [
            "Hello! I saw your wave. How can I help you today?",
            "Hi there! Your handshake got my attention. What's on your mind?",
            "Greetings! I'm here to assist. What would you like to talk about?",
            "Hello! Thanks for the wave. How are you doing today?",
            "Hi! I detected your handshake. What can I do for you?"
        ]
        
        import random
        return random.choice(greetings)
    
    def get_farewell(self) -> str:
        """Get a farewell message"""
        farewells = [
            "Goodbye! Wave again anytime you want to chat.",
            "See you later! I'll be here when you need me.",
            "Take care! Just wave to start another conversation.",
            "Bye for now! Looking forward to our next chat.",
            "Farewell! I'm always ready for another handshake."
        ]
        
        import random
        return random.choice(farewells)
    
    def start(self):
        """Start the handshake voice AI system"""
        logger.info("🚀 Starting Handshake Voice AI System")
        logger.info("=" * 50)
        
        try:
            # Start handshake monitoring
            if self.handshake_detector.start_monitoring():
                logger.info("✅ System ready! Wave your hand near the sensor to start conversation.")
                
                # Keep the main thread alive
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("👋 Shutting down system...")
            else:
                logger.error("❌ Failed to start handshake monitoring")
                
                # Fallback: manual mode
                logger.info("🎤 Entering manual mode - press Enter to start conversation")
                try:
                    while True:
                        input()  # Wait for Enter key
                        if not self.conversation_active:
                            logger.info("🎤 Manual conversation started")
                            self.on_handshake_detected()
                        else:
                            logger.info("⏭️ Conversation already active")
                except KeyboardInterrupt:
                    logger.info("👋 Shutting down system...")
        
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup system resources"""
        logger.info("🧹 Cleaning up system resources...")
        
        if hasattr(self, 'handshake_detector'):
            self.handshake_detector.cleanup()
        
        logger.info("✅ Cleanup completed")


def main():
    """Main function"""
    logger.info("🤝 Handshake Voice AI - Simple Version")
    logger.info("IEEE EPIC Project - Raspberry Pi Edition")
    logger.info("=" * 50)
    
    # Check requirements
    if not MODULES_AVAILABLE:
        logger.error("❌ Required modules not available")
        return 1
    
    if not GPIO_AVAILABLE:
        logger.warning("⚠️ GPIO not available - will run in manual mode")
    
    # Create and start the system
    try:
        voice_ai = SimpleVoiceAI()
        voice_ai.start()
    except Exception as e:
        logger.error(f"❌ Failed to start system: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())