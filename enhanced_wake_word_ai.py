"""
Enhanced Voice AI with both Handshake and Wake Word activation
Extends the existing HandshakeVoiceAI with wake word capabilities
"""

import threading
import time
from typing import Optional
from loguru import logger

# Import the wake word detector
from wake_word_detector import WakeWordDetector


class EnhancedVoiceAI:
    """Enhanced voice AI supporting both handshake and wake word activation"""
    
    def __init__(self):
        # Import your existing HandshakeVoiceAI
        from handshake_voice_ai import HandshakeVoiceAI
        
        # Initialize the base handshake system
        self.handshake_ai = HandshakeVoiceAI()
        
        # Add wake word detection
        self.wake_detector = WakeWordDetector(
            wake_words=["hey saras", "hello saras", "saras", "wake up"],
            sensitivity_threshold=3
        )
        self.wake_detector.set_callback(self.on_wake_word_detected)
        
        # Track activation method
        self.last_activation_method = None
        
    def on_wake_word_detected(self):
        """Handle wake word detection"""
        if self.handshake_ai.conversation_active:
            logger.info("Conversation already active, ignoring wake word")
            return
        
        self.last_activation_method = "wake_word"
        logger.info("🎯 Wake word detected! Starting conversation...")
        
        # Use the existing conversation system but mark as wake word triggered
        self.handshake_ai.add_system_message("🎯 Wake word detected! Starting conversation...")
        
        # Start conversation using existing method
        conversation_thread = threading.Thread(
            target=self.handshake_ai.handle_handshake_conversation, 
            daemon=True
        )
        conversation_thread.start()
    
    def on_handshake_detected(self):
        """Handle handshake detection (existing functionality)"""
        self.last_activation_method = "handshake"
        logger.info("🤝 Handshake detected! Starting conversation...")
        self.handshake_ai.on_handshake_detected()
    
    def toggle_wake_word_detection(self):
        """Toggle wake word detection on/off"""
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
    
    def run_gui_with_wake_word(self):
        """Run the GUI application with wake word support"""
        # Modify the proximity sensor callback to use our enhanced version
        self.handshake_ai.proximity_sensor.set_detection_callback(self.on_handshake_detected)
        
        # Add wake word controls to GUI
        self._add_wake_word_gui_controls()
        
        # Auto-start wake word detection if available
        if self.wake_detector.is_available():
            self.wake_detector.start_listening()
            self.handshake_ai.add_system_message("🎤 Wake word detection started")
            self.handshake_ai.add_system_message(f"Say: {', '.join(self.wake_detector.wake_words)}")
        else:
            self.handshake_ai.add_system_message("⚠️ Wake word detection not available")
        
        # Run the existing GUI
        self.handshake_ai.run()
    
    def _add_wake_word_gui_controls(self):
        """Add wake word controls to the existing GUI"""
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
        
        if button_frame:
            # Add wake word toggle button
            self.wake_word_button = tk.Button(
                button_frame,
                text="🎯 Wake Word ON",
                font=("Arial", 12, "bold"),
                command=self._toggle_wake_word_gui,
                bg="#9b59b6",
                fg="white",
                padx=20,
                pady=8,
                relief="flat",
                cursor="hand2"
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
                """
                messagebox.showinfo("Enhanced Help", help_text)
            
            self.handshake_ai.show_help = enhanced_show_help
    
    def _toggle_wake_word_gui(self):
        """Toggle wake word detection from GUI"""
        if self.toggle_wake_word_detection():
            self.wake_word_button.config(
                text="🎯 Wake Word ON",
                bg="#9b59b6"
            )
            self.handshake_ai.add_system_message("🎤 Wake word detection enabled")
        else:
            self.wake_word_button.config(
                text="🎯 Wake Word OFF",
                bg="#95a5a6"
            )
            self.handshake_ai.add_system_message("🎤 Wake word detection disabled")
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'wake_detector'):
            self.wake_detector.stop_listening()
        if hasattr(self, 'handshake_ai'):
            self.handshake_ai.on_closing()


def main():
    """Main function to run enhanced voice AI"""
    try:
        logger.info("🚀 Starting Enhanced Voice AI (Handshake + Wake Word)")
        
        enhanced_ai = EnhancedVoiceAI()
        enhanced_ai.run_gui_with_wake_word()
        
    except Exception as e:
        logger.error(f"Failed to start enhanced voice AI: {e}")
        return 1
    finally:
        if 'enhanced_ai' in locals():
            enhanced_ai.cleanup()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())