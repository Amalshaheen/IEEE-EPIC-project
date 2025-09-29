#!/usr/bin/env python3
"""
Dual Activation Voice AI - Both Handshake and Wake Word
Simplified version for reliable operation
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import os
import sys
import time
from datetime import datetime
from typing import Optional, Tuple

# Ensure local imports work
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from loguru import logger

# Import existing components
try:
    from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
    from ieee_epic.core.simple_tts import SimpleTextToSpeech
    from ieee_epic.core.ai_response import AIResponseSystem
    from ieee_epic.core.config import Settings
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    MODULES_AVAILABLE = False

# Simple Wake Word Detector
import speech_recognition as sr

class SimpleWakeWordDetector:
    """Simple wake word detector for dual activation"""
    
    def __init__(self, wake_words: list = None):
        self.wake_words = wake_words or ["hey saras", "hello saras", "saras"]
        self.is_listening = False
        self.callback = None
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configure for wake word detection
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.5
        
        logger.info(f"Wake word detector initialized with words: {self.wake_words}")
    
    def set_callback(self, callback):
        self.callback = callback
    
    def start_listening(self):
        if self.is_listening:
            return True
            
        self.is_listening = True
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
        logger.info("🎤 Wake word detection started")
        return True
    
    def stop_listening(self):
        self.is_listening = False
        logger.info("🎤 Wake word detection stopped")
    
    def _listen_loop(self):
        consecutive_errors = 0
        max_errors = 3
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Quick ambient noise adjustment
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    # Listen for short phrases
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
                
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    text_lower = text.lower().strip()
                    
                    logger.debug(f"Heard: '{text_lower}'")
                    
                    # Check for wake words
                    for wake_word in self.wake_words:
                        if wake_word.lower() in text_lower:
                            logger.success(f"🎯 Wake word detected: '{wake_word}'")
                            consecutive_errors = 0
                            if self.callback:
                                threading.Thread(target=self.callback, daemon=True).start()
                            break
                    
                    consecutive_errors = 0
                    
                except sr.UnknownValueError:
                    # Normal - no clear speech
                    consecutive_errors = 0
                    continue
                except sr.RequestError as e:
                    consecutive_errors += 1
                    logger.warning(f"Recognition error: {e}")
                    if consecutive_errors >= max_errors:
                        logger.error("Too many recognition errors, pausing wake word detection")
                        time.sleep(10)
                        consecutive_errors = 0
                    
            except sr.WaitTimeoutError:
                # Normal timeout
                continue
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Wake word detection error: {e}")
                if consecutive_errors >= max_errors:
                    time.sleep(5)
                    consecutive_errors = 0
                else:
                    time.sleep(0.5)


class DualActivationVoiceAI:
    """Voice AI with both handshake and wake word activation"""
    
    def __init__(self):
        self.setup_backends()
        self.setup_wake_word_detector()
        self.setup_gui()
        self.conversation_active = False
        
    def setup_backends(self):
        """Setup speech and AI backends"""
        if not MODULES_AVAILABLE:
            logger.error("Required modules not available")
            self.backend_available = False
            return
        
        try:
            self.settings = Settings()
            self.stt = SimpleSpeechRecognizer()
            self.tts = SimpleTextToSpeech()
            self.ai_system = AIResponseSystem(self.settings)
            
            self.backend_available = True
            logger.info("✅ Backends initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize backends: {e}")
            self.backend_available = False
    
    def setup_wake_word_detector(self):
        """Setup wake word detector"""
        self.wake_detector = SimpleWakeWordDetector()
        self.wake_detector.set_callback(self.on_wake_word_detected)
    
    def setup_gui(self):
        """Setup GUI interface"""
        self.root = tk.Tk()
        self.root.title("🤝🎯 Dual Activation Voice AI - IEEE EPIC")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f8f9fa")
        
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🤝🎯 Dual Activation Voice AI",
            font=("Arial", 24, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Activate by Handshake OR Wake Words: 'Hey SARAS', 'Hello SARAS', 'SARAS'",
            font=("Arial", 14),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#f8f9fa")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Wake word status
        self.wake_status_label = tk.Label(
            status_frame,
            text="🎤 Wake Word: Initializing...",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            fg="#9b59b6"
        )
        self.wake_status_label.pack(side=tk.LEFT)
        
        # Handshake status  
        self.handshake_status_label = tk.Label(
            status_frame,
            text="🤝 Handshake: Not Available (Dev Mode)",
            font=("Arial", 12),
            bg="#f8f9fa",
            fg="#95a5a6"
        )
        self.handshake_status_label.pack(side=tk.RIGHT)
        
        # Conversation area
        conv_frame = tk.Frame(main_frame, bg="#f8f9fa")
        conv_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 20))
        
        conv_label = tk.Label(
            conv_frame,
            text="Conversation History",
            font=("Arial", 16, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        conv_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.conversation_box = scrolledtext.ScrolledText(
            conv_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#ffffff",
            fg="#2c3e50",
            selectbackground="#3498db",
            selectforeground="#ffffff",
            relief="flat",
            bd=1,
            padx=15,
            pady=15
        )
        self.conversation_box.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#f8f9fa")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Wake word toggle
        self.wake_button = tk.Button(
            button_frame,
            text="🎯 Start Wake Word",
            font=("Arial", 12, "bold"),
            command=self.toggle_wake_word,
            bg="#9b59b6",
            fg="white",
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        self.wake_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Manual chat
        manual_button = tk.Button(
            button_frame,
            text="🎤 Manual Chat",
            font=("Arial", 12, "bold"),
            command=self.start_manual_conversation,
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        manual_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Test wake word
        test_button = tk.Button(
            button_frame,
            text="🧪 Test Wake Word",
            font=("Arial", 12),
            command=self.test_wake_word,
            bg="#f39c12",
            fg="white",
            padx=15,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear conversation
        clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear",
            font=("Arial", 12),
            command=self.clear_conversation,
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Help button
        help_button = tk.Button(
            button_frame,
            text="❓ Help",
            font=("Arial", 12),
            command=self.show_help,
            bg="#95a5a6",
            fg="white",
            padx=15,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        help_button.pack(side=tk.RIGHT)
        
        # Add welcome messages
        self.add_system_message("🎯 Welcome to Dual Activation Voice AI!")
        self.add_system_message("🤝 Handshake Detection: Wave near sensor (if available)")
        self.add_system_message("🎤 Wake Words: Say 'Hey SARAS', 'Hello SARAS', or just 'SARAS'")
        self.add_system_message("🎯 Manual Mode: Use buttons for direct interaction")
        
        if not self.backend_available:
            self.add_system_message("⚠️ Speech backends not fully available")
        else:
            self.add_system_message("✅ All systems ready!")
    
    def add_message(self, speaker: str, message: str, color: str = "#2c3e50"):
        """Add message to conversation"""
        self.conversation_box.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {speaker}: {message}\n\n"
        
        self.conversation_box.insert(tk.END, formatted_message)
        self.conversation_box.see(tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        self.root.update()
    
    def add_system_message(self, message: str):
        """Add system message"""
        self.add_message("System", message, "#7f8c8d")
    
    def on_wake_word_detected(self):
        """Handle wake word activation"""
        if self.conversation_active:
            logger.info("Conversation already active, ignoring wake word")
            return
        
        logger.info("🎯 Wake word activated conversation")
        self.add_system_message("🎯 Wake word detected! Starting conversation...")
        self.start_conversation("wake_word")
    
    def on_handshake_detected(self):
        """Handle handshake activation"""
        if self.conversation_active:
            logger.info("Conversation already active, ignoring handshake")
            return
        
        logger.info("🤝 Handshake activated conversation")
        self.add_system_message("🤝 Handshake detected! Starting conversation...")
        self.start_conversation("handshake")
    
    def start_conversation(self, activation_method: str):
        """Start conversation from either activation method"""
        conversation_thread = threading.Thread(
            target=self.handle_conversation,
            args=(activation_method,),
            daemon=True
        )
        conversation_thread.start()
    
    def handle_conversation(self, activation_method: str):
        """Handle the conversation flow"""
        if not self.backend_available:
            self.add_system_message("❌ Cannot start conversation - backends not available")
            return
        
        self.conversation_active = True
        
        try:
            # Generate appropriate greeting
            if activation_method == "wake_word":
                greeting = "Hi! I heard you call my name. How can I help you today?"
            elif activation_method == "handshake":
                greeting = "Hello! I saw your wave. What can I do for you?"
            else:
                greeting = "Hi! I'm ready to assist you. What's on your mind?"
            
            self.add_message("SARAS", greeting, "#27ae60")
            
            # Speak greeting
            success = self.tts.speak(greeting, "en")
            if not success:
                self.add_system_message("⚠️ TTS greeting failed")
            
            # Conversation loop
            max_turns = 5
            turn = 0
            
            while turn < max_turns and self.conversation_active:
                turn += 1
                self.add_system_message(f"🎤 Listening for your response... (Turn {turn}/{max_turns})")
                
                # Listen for user input  
                text, language = self.stt.listen_and_recognize("auto", timeout=15)
                
                if text and text.strip():
                    lang_name = "Malayalam" if language == "ml" else "English"
                    self.add_message(f"You ({lang_name})", text, "#2980b9")
                    
                    # Check for goodbye
                    if self.should_end_conversation(text):
                        farewell = "Goodbye! You can activate me again anytime with a handshake or by saying my wake words."
                        self.add_message("SARAS", farewell, "#27ae60")
                        self.tts.speak(farewell, "en")
                        break
                    
                    # Generate AI response
                    self.add_system_message("🧠 AI thinking...")
                    
                    try:
                        response = self.ai_system.generate_response(text)
                    except Exception as e:
                        logger.error(f"AI response failed: {e}")
                        response = f"I heard you say '{text}', but I'm having some technical difficulties right now."
                    
                    self.add_message(f"SARAS ({lang_name})", response, "#27ae60")
                    
                    # Speak response
                    success = self.tts.speak(response, language)
                    if not success:
                        self.add_system_message("⚠️ TTS response failed")
                else:
                    self.add_system_message("❌ Could not understand speech, please try again")
                    
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            self.add_system_message(f"❌ Conversation error: {str(e)}")
        finally:
            self.conversation_active = False
            self.add_system_message("👋 Conversation ended. Ready for next activation!")
    
    def should_end_conversation(self, text: str) -> bool:
        """Check if user wants to end conversation"""
        end_phrases = ["goodbye", "bye", "stop", "end", "quit", "done", "thanks", "thank you"]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in end_phrases)
    
    def toggle_wake_word(self):
        """Toggle wake word detection"""
        if self.wake_detector.is_listening:
            self.wake_detector.stop_listening()
            self.wake_button.config(
                text="🎯 Start Wake Word",
                bg="#9b59b6"
            )
            self.wake_status_label.config(
                text="🎤 Wake Word: Stopped",
                fg="#95a5a6"
            )
            self.add_system_message("🎤 Wake word detection stopped")
        else:
            if self.wake_detector.start_listening():
                self.wake_button.config(
                    text="🎯 Stop Wake Word",
                    bg="#e74c3c"
                )
                self.wake_status_label.config(
                    text="🎤 Wake Word: Active - Listening...",
                    fg="#9b59b6"
                )
                self.add_system_message("🎤 Wake word detection started")
                self.add_system_message("Say: 'Hey SARAS', 'Hello SARAS', or 'SARAS'")
    
    def start_manual_conversation(self):
        """Start manual conversation"""
        if self.conversation_active:
            self.add_system_message("⚠️ Conversation already active!")
            return
        
        self.add_system_message("🎤 Manual conversation started!")
        self.start_conversation("manual")
    
    def test_wake_word(self):
        """Test wake word detection manually"""
        if not self.wake_detector.is_listening:
            self.add_system_message("⚠️ Start wake word detection first!")
            return
        
        self.add_system_message("🧪 Testing wake word - say 'SARAS' clearly now...")
        # The wake word detector will automatically trigger if it hears the word
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_box.config(state=tk.NORMAL)
        self.conversation_box.delete(1.0, tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        self.add_system_message("🗑️ Conversation history cleared!")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
🤝🎯 Dual Activation Voice AI Help

ACTIVATION METHODS:
🤝 Handshake Detection (if sensor available):
   • Wave your hand near the proximity sensor
   
🎤 Wake Word Detection:
   • Say: "Hey SARAS", "Hello SARAS", or just "SARAS"
   • Must be clear and distinct
   • Works continuously when enabled
   
🎯 Manual Mode:
   • Use "Manual Chat" button for immediate conversation

CONVERSATION FEATURES:
• Bilingual support (English & Malayalam)
• AI-powered responses via Google Gemini
• Natural conversation flow
• Say "goodbye" or "stop" to end

CONTROLS:
• Start/Stop Wake Word: Toggle voice activation
• Manual Chat: Direct conversation mode  
• Test Wake Word: Check if detection is working
• Clear: Remove conversation history

TIPS:
• Speak clearly for best recognition
• Both activation methods can work simultaneously
• Conversations auto-end after 5 turns or on goodbye
• Check microphone permissions if wake words don't work
        """
        messagebox.showinfo("Help - Dual Activation AI", help_text)
    
    def run(self):
        """Run the application"""
        try:
            # Auto-start wake word detection
            self.toggle_wake_word()
            
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
    
    def on_closing(self):
        """Handle window closing"""
        self.conversation_active = False
        if hasattr(self, 'wake_detector'):
            self.wake_detector.stop_listening()
        self.root.destroy()


def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Dual Activation Voice AI (Handshake + Wake Word)")
        
        app = DualActivationVoiceAI()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())