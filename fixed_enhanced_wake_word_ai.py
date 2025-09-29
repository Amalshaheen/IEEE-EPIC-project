"""
Fixed Enhanced Voice AI with both Handshake and Wake Word activation
Fixes audio initialization and memory management issues
"""

import threading
import time
import sys
import os
import signal
from typing import Optional
from loguru import logger

# Set environment variables to avoid ALSA/audio issues
os.environ['ALSA_PCM_CARD'] = '0'
os.environ['ALSA_PCM_DEVICE'] = '0'

# Disable problematic ALSA configurations
os.environ['PULSE_SERVER'] = 'unix:/run/user/%d/pulse/native' % os.getuid()

# Import the fixed wake word detector
from fixed_wake_word_detector import FixedWakeWordDetector as WakeWordDetector


class FixedEnhancedVoiceAI:
    """Enhanced voice AI supporting both handshake and wake word activation with audio fixes"""
    
    def __init__(self):
        self.handshake_ai = None
        self.wake_detector = None
        self.last_activation_method = None
        self.cleanup_done = False
        
        # Setup signal handlers for proper cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize components with error handling
        self._initialize_components()
        
    def _signal_handler(self, signum, frame):
        """Handle system signals for cleanup"""
        logger.info(f"Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(0)
        
    def _initialize_components(self):
        """Initialize components with proper error handling"""
        try:
            # Import your existing HandshakeVoiceAI
            from handshake_voice_ai import HandshakeVoiceAI
            
            # Initialize the base handshake system
            logger.info("Initializing handshake AI system...")
            self.handshake_ai = HandshakeVoiceAI()
            
            # Add wake word detection with retry mechanism
            logger.info("Initializing wake word detector...")
            self._initialize_wake_detector()
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _initialize_wake_detector(self):
        """Initialize wake word detector with error handling"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Wake word detector initialization attempt {attempt + 1}/{max_retries}")
                
                # Create wake word detector with more conservative settings
                self.wake_detector = WakeWordDetector(
                    wake_words=["hey saras", "hello saras", "saras"],
                    sensitivity_threshold=2  # Shorter listening windows to avoid timeout issues
                )
                
                # Set callback
                self.wake_detector.set_callback(self.on_wake_word_detected)
                
                # Test if it's available
                if self.wake_detector.is_available():
                    logger.success(f"Wake word detector initialized successfully on attempt {attempt + 1}")
                    return
                else:
                    logger.warning(f"Wake word detector not available on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    
            except Exception as e:
                logger.error(f"Wake word detector initialization failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.warning("Wake word detection will not be available")
                    self.wake_detector = None
    
    def on_wake_word_detected(self):
        """Handle wake word detection"""
        try:
            if self.handshake_ai and self.handshake_ai.conversation_active:
                logger.info("Conversation already active, ignoring wake word")
                return
            
            self.last_activation_method = "wake_word"
            logger.info("🎯 Wake word detected! Starting conversation...")
            
            # Use the existing conversation system but mark as wake word triggered
            if self.handshake_ai:
                self.handshake_ai.add_system_message("🎯 Wake word detected! Starting conversation...")
                
                # Start conversation using existing method
                conversation_thread = threading.Thread(
                    target=self.handshake_ai.handle_handshake_conversation, 
                    daemon=True
                )
                conversation_thread.start()
            
        except Exception as e:
            logger.error(f"Error handling wake word detection: {e}")
    
    def on_handshake_detected(self):
        """Handle handshake detection (existing functionality)"""
        try:
            self.last_activation_method = "handshake"
            logger.info("🤝 Handshake detected! Starting conversation...")
            if self.handshake_ai:
                self.handshake_ai.on_handshake_detected()
        except Exception as e:
            logger.error(f"Error handling handshake detection: {e}")
    
    def toggle_wake_word_detection(self):
        """Toggle wake word detection on/off"""
        try:
            if not self.wake_detector:
                logger.error("Wake word detector not available")
                return False
                
            if self.wake_detector.is_listening:
                self.wake_detector.stop_listening()
                logger.info("🎤 Wake word detection stopped")
                return False
            else:
                if self.wake_detector.start_listening():
                    logger.info("🎤 Wake word detection started")
                    return True
                else:
                    logger.error("❌ Failed to start wake word detection")
                    return False
                    
        except Exception as e:
            logger.error(f"Error toggling wake word detection: {e}")
            return False
    
    def run_gui_with_wake_word(self):
        """Run the GUI application with wake word support"""
        try:
            if not self.handshake_ai:
                logger.error("Handshake AI not initialized, cannot start GUI")
                return
                
            # Modify the proximity sensor callback to use our enhanced version
            if hasattr(self.handshake_ai, 'proximity_sensor') and self.handshake_ai.proximity_sensor:
                self.handshake_ai.proximity_sensor.set_detection_callback(self.on_handshake_detected)
            
            # Add wake word controls to GUI
            self._add_wake_word_gui_controls()
            
            # Auto-start wake word detection if available
            if self.wake_detector and self.wake_detector.is_available():
                if self.wake_detector.start_listening():
                    self.handshake_ai.add_system_message("🎤 Wake word detection started")
                    self.handshake_ai.add_system_message(f"Say: {', '.join(self.wake_detector.wake_words)}")
                else:
                    self.handshake_ai.add_system_message("⚠️ Wake word detection failed to start")
            else:
                self.handshake_ai.add_system_message("⚠️ Wake word detection not available")
            
            # Run the existing GUI
            self.handshake_ai.run()
            
        except Exception as e:
            logger.error(f"Error running GUI: {e}")
            raise
    
    def _add_wake_word_gui_controls(self):
        """Add wake word controls to the existing GUI"""
        try:
            import tkinter as tk
            
            # Find the button frame in the existing GUI
            button_frame = None
            for child in self.handshake_ai.root.winfo_children():
                if isinstance(child, tk.Frame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Frame):
                            # Check if this frame contains buttons
                            for button in grandchild.winfo_children():
                                if isinstance(button, tk.Button):
                                    button_frame = grandchild
                                    break
                            if button_frame:
                                break
                    if button_frame:
                        break
            
            if button_frame and self.wake_detector:
                # Add wake word toggle button
                self.wake_word_button = tk.Button(
                    button_frame,
                    text="🎯 Wake Word ON" if self.wake_detector.is_available() else "🎯 Wake Word N/A",
                    font=("Arial", 12, "bold"),
                    command=self._toggle_wake_word_gui,
                    bg="#9b59b6" if self.wake_detector.is_available() else "#95a5a6",
                    fg="white",
                    padx=20,
                    pady=8,
                    relief="flat",
                    cursor="hand2" if self.wake_detector.is_available() else "arrow"
                )
                self.wake_word_button.pack(side=tk.LEFT, padx=(0, 10))
                
                # Update help text
                original_show_help = self.handshake_ai.show_help
                def enhanced_show_help():
                    """Enhanced help with wake word information"""
                    from tkinter import messagebox
                    help_text = """
🤝 Enhanced Voice AI Assistant Help

🎯 Wake Word Activation:
• Say any of these wake words: "Hey SARAS", "Hello SARAS", "SARAS"
• The AI will respond and start conversation
• Works continuously in the background
• No physical interaction needed

🔍 Handshake Detection:
• Wave your hand near the proximity sensor
• Physical activation method
• Same conversation capabilities as wake word

🎤 Manual Mode:
• Use 'Manual Chat' button for immediate interaction
• Bypasses both wake word and handshake detection

🌐 Language Support:
• Auto: Automatic detection (Malayalam/English)
• English (en): English only
• Malayalam (ml): Malayalam only

🤖 AI Features:
• Intelligent responses powered by Google Gemini
• Conversation context awareness
• Bilingual support

🎛️ Controls:
• Start/Stop Sensor: Toggle proximity sensor
• Wake Word ON/OFF: Toggle voice activation
• Manual Chat: Direct conversation
• Clear: Clear history
• Help: Show this dialog

💡 Tips:
• Both wake word and handshake can be active simultaneously
• Speak clearly for best wake word recognition
• Use "goodbye" or "stop" to end conversations

⚠️ Troubleshooting:
• If audio doesn't work, check microphone permissions
• Try restarting if wake word detection fails
• Check system audio settings if no sound
                    """
                    messagebox.showinfo("Enhanced Help", help_text)
                
                self.handshake_ai.show_help = enhanced_show_help
                
        except Exception as e:
            logger.error(f"Error adding wake word GUI controls: {e}")
    
    def _toggle_wake_word_gui(self):
        """Toggle wake word detection from GUI"""
        try:
            if not self.wake_detector or not self.wake_detector.is_available():
                if self.handshake_ai:
                    self.handshake_ai.add_system_message("❌ Wake word detection not available")
                return
                
            if self.toggle_wake_word_detection():
                self.wake_word_button.config(
                    text="🎯 Wake Word ON",
                    bg="#9b59b6"
                )
                if self.handshake_ai:
                    self.handshake_ai.add_system_message("🎤 Wake word detection enabled")
            else:
                self.wake_word_button.config(
                    text="🎯 Wake Word OFF",
                    bg="#95a5a6"
                )
                if self.handshake_ai:
                    self.handshake_ai.add_system_message("🎤 Wake word detection disabled")
                    
        except Exception as e:
            logger.error(f"Error in wake word GUI toggle: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.cleanup_done:
            return
            
        logger.info("Cleaning up resources...")
        self.cleanup_done = True
        
        try:
            if self.wake_detector:
                self.wake_detector.stop_listening()
                
            if self.handshake_ai:
                self.handshake_ai.on_closing()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main function to run enhanced voice AI with proper error handling"""
    enhanced_ai = None
    
    try:
        logger.info("🚀 Starting Enhanced Voice AI (Handshake + Wake Word)")
        
        # Check audio system before starting
        logger.info("Checking audio system...")
        
        # Try to import required audio libraries
        try:
            import speech_recognition as sr
            import pygame
            logger.info("✅ Audio libraries available")
        except ImportError as e:
            logger.error(f"❌ Audio library missing: {e}")
            return 1
        
        # Initialize enhanced AI
        enhanced_ai = FixedEnhancedVoiceAI()
        
        # Start GUI
        enhanced_ai.run_gui_with_wake_word()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("👋 Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start enhanced voice AI: {e}")
        logger.error(f"Error type: {type(e)}")
        return 1
    finally:
        if enhanced_ai:
            enhanced_ai.cleanup()


if __name__ == "__main__":
    import sys
    sys.exit(main())