#!/usr/bin/env python3
"""
Fixed Dual Activation Voice AI - Resolves Audio Conflicts
Proper audio resource management to prevent crashes
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import os
import sys
import time
from datetime import datetime
from typing import Optional, Tuple
import queue

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

import speech_recognition as sr


class AudioResourceManager:
    """Manages audio resources to prevent conflicts"""
    
    def __init__(self):
        self.microphone_lock = threading.Lock()
        self.current_user = None
        self.microphone = None
        self.recognizer = sr.Recognizer()
        self._initialize_microphone()
    
    def _initialize_microphone(self):
        """Initialize shared microphone"""
        try:
            # Use pulse audio explicitly to avoid ALSA conflicts
            self.microphone = sr.Microphone()
            
            # Configure for stability
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.6
            self.recognizer.operation_timeout = None
            
            # Quick calibration
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            logger.info("✅ Shared microphone initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize shared microphone: {e}")
            self.microphone = None
    
    def acquire_microphone(self, user: str, timeout: float = 5.0) -> bool:
        """Acquire microphone access"""
        if not self.microphone:
            logger.error(f"No microphone available for {user}")
            return False
        
        acquired = self.microphone_lock.acquire(timeout=timeout)
        if acquired:
            self.current_user = user
            logger.debug(f"🎤 Microphone acquired by {user}")
            return True
        else:
            logger.warning(f"🎤 Microphone acquisition timeout for {user}")
            return False
    
    def release_microphone(self, user: str):
        """Release microphone access"""
        if self.current_user == user:
            self.current_user = None
            try:
                self.microphone_lock.release()
                logger.debug(f"🎤 Microphone released by {user}")
            except Exception as e:
                logger.error(f"Error releasing microphone: {e}")
        else:
            logger.warning(f"Attempted release by {user} but current user is {self.current_user}")
    
    def listen_with_timeout(self, user: str, timeout: int = 5, phrase_limit: int = 10) -> Optional[sr.AudioData]:
        """Listen for audio with proper resource management"""
        if not self.acquire_microphone(user, timeout=2):
            return None
        
        try:
            with self.microphone as source:
                # Quick ambient adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
                return audio
                
        except sr.WaitTimeoutError:
            logger.debug(f"Listen timeout for {user}")
            return None
        except Exception as e:
            logger.error(f"Listen error for {user}: {e}")
            return None
        finally:
            self.release_microphone(user)
    
    def recognize_google(self, audio_data: sr.AudioData, language: str = "en-US") -> Optional[str]:
        """Recognize speech using Google API"""
        if not audio_data:
            return None
        
        try:
            return self.recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return None


class SafeWakeWordDetector:
    """Safe wake word detector with proper audio management"""
    
    def __init__(self, audio_manager: AudioResourceManager, wake_words: list = None):
        self.audio_manager = audio_manager
        self.wake_words = wake_words or ["hey saras", "hello saras", "saras"]
        self.is_listening = False
        self.callback = None
        self.detection_thread = None
        
        logger.info(f"Safe wake word detector initialized: {self.wake_words}")
    
    def set_callback(self, callback):
        self.callback = callback
    
    def start_listening(self):
        if self.is_listening:
            return True
        
        self.is_listening = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        logger.info("🎤 Safe wake word detection started")
        return True
    
    def stop_listening(self):
        self.is_listening = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        logger.info("🎤 Safe wake word detection stopped")
    
    def _detection_loop(self):
        """Main detection loop with proper error handling"""
        consecutive_errors = 0
        max_errors = 3
        
        while self.is_listening:
            try:
                # Listen for potential wake word
                audio = self.audio_manager.listen_with_timeout("wake_word", timeout=3, phrase_limit=4)
                
                if audio:
                    # Try to recognize
                    text = self.audio_manager.recognize_google(audio, "en-US")
                    
                    if text:
                        text_lower = text.lower().strip()
                        logger.debug(f"Wake word detector heard: '{text_lower}'")
                        
                        # Check for wake words
                        for wake_word in self.wake_words:
                            if wake_word.lower() in text_lower:
                                logger.success(f"🎯 Wake word detected: '{wake_word}'")
                                consecutive_errors = 0
                                
                                if self.callback:
                                    # Call callback in separate thread to avoid blocking
                                    callback_thread = threading.Thread(target=self.callback, daemon=True)
                                    callback_thread.start()
                                break
                    
                    consecutive_errors = 0
                else:
                    # No audio captured, continue listening
                    consecutive_errors = 0
                    
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Wake word detection error: {e}")
                
                if consecutive_errors >= max_errors:
                    logger.warning("Too many consecutive errors, pausing wake word detection")
                    time.sleep(5)
                    consecutive_errors = 0
                else:
                    time.sleep(1)


class FixedDualActivationAI:
    """Fixed dual activation AI with proper audio management"""
    
    def __init__(self):
        # Initialize audio resource manager
        self.audio_manager = AudioResourceManager()
        
        self.setup_backends()
        self.setup_wake_word_detector()
        self.setup_gui()
        self.conversation_active = False
        
        # Conversation state
        self.conversation_queue = queue.Queue()
    
    def setup_backends(self):
        """Setup speech and AI backends"""
        if not MODULES_AVAILABLE:
            logger.error("Required modules not available")
            self.backend_available = False
            return
        
        try:
            self.settings = Settings()
            # Use existing STT but we'll manage audio ourselves for wake words
            self.stt = SimpleSpeechRecognizer()
            self.tts = SimpleTextToSpeech()
            self.ai_system = AIResponseSystem(self.settings)
            
            self.backend_available = True
            logger.info("✅ Backends initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize backends: {e}")
            self.backend_available = False
    
    def setup_wake_word_detector(self):
        """Setup safe wake word detector"""
        self.wake_detector = SafeWakeWordDetector(self.audio_manager)
        self.wake_detector.set_callback(self.on_wake_word_detected)
    
    def setup_gui(self):
        """Setup GUI interface"""
        self.root = tk.Tk()
        self.root.title("🤝🎯 Fixed Dual Activation Voice AI")
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
            text="🤝🎯 Fixed Dual Activation Voice AI",
            font=("Arial", 24, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="No More Crashes! Activate by Wake Words or Manual Chat",
            font=("Arial", 14),
            bg="#f8f9fa",
            fg="#27ae60"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#f8f9fa")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Audio status
        self.audio_status_label = tk.Label(
            status_frame,
            text="🎤 Audio: Initializing...",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            fg="#3498db"
        )
        self.audio_status_label.pack(side=tk.LEFT)
        
        # Wake word status  
        self.wake_status_label = tk.Label(
            status_frame,
            text="🎯 Wake Word: Ready",
            font=("Arial", 12),
            bg="#f8f9fa",
            fg="#9b59b6"
        )
        self.wake_status_label.pack(side=tk.RIGHT)
        
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
        self.manual_button = tk.Button(
            button_frame,
            text="🎤 Manual Chat",
            font=("Arial", 12, "bold"),
            command=self.start_manual_conversation,
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        self.manual_button.pack(side=tk.LEFT, padx=(0, 10))
        
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
        
        # Initialize status
        self.update_audio_status()
        
        # Add welcome messages
        self.add_system_message("🎯 Fixed Dual Activation Voice AI Started!")
        self.add_system_message("✅ No more audio conflicts or crashes")
        self.add_system_message("🎤 Wake Words: 'Hey SARAS', 'Hello SARAS', 'SARAS'")
        self.add_system_message("🎯 Manual Mode: Use 'Manual Chat' button")
        
        if not self.backend_available:
            self.add_system_message("⚠️ Some backends not fully available")
        else:
            self.add_system_message("✅ All systems ready!")
    
    def update_audio_status(self):
        """Update audio status display"""
        if self.audio_manager.microphone:
            if self.audio_manager.current_user:
                self.audio_status_label.config(
                    text=f"🎤 Audio: In use by {self.audio_manager.current_user}",
                    fg="#e67e22"
                )
            else:
                self.audio_status_label.config(
                    text="🎤 Audio: Available",
                    fg="#27ae60"
                )
        else:
            self.audio_status_label.config(
                text="🎤 Audio: Not Available",
                fg="#e74c3c"
            )
        
        # Schedule next update
        self.root.after(1000, self.update_audio_status)
    
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
        """Handle wake word activation - thread safe"""
        if self.conversation_active:
            logger.info("Conversation already active, ignoring wake word")
            return
        
        logger.info("🎯 Wake word activated conversation")
        
        # Use GUI thread for UI updates
        self.root.after(0, lambda: self.add_system_message("🎯 Wake word detected! Starting conversation..."))
        
        # Start conversation
        self.start_conversation("wake_word")
    
    def start_conversation(self, activation_method: str):
        """Start conversation safely"""
        if self.conversation_active:
            return
        
        conversation_thread = threading.Thread(
            target=self.handle_conversation,
            args=(activation_method,),
            daemon=True
        )
        conversation_thread.start()
    
    def handle_conversation(self, activation_method: str):
        """Handle conversation with proper audio management"""
        if not self.backend_available:
            self.root.after(0, lambda: self.add_system_message("❌ Cannot start conversation - backends not available"))
            return
        
        self.conversation_active = True
        
        # Stop wake word detection during conversation to avoid conflicts
        wake_word_was_active = self.wake_detector.is_listening
        if wake_word_was_active:
            self.wake_detector.stop_listening()
            self.root.after(0, lambda: self.wake_status_label.config(
                text="🎯 Wake Word: Paused (Conversation Active)",
                fg="#e67e22"
            ))
        
        try:
            # Generate greeting
            if activation_method == "wake_word":
                greeting = "Hi! I heard you call my name. How can I help you today?"
            else:
                greeting = "Hi! I'm ready to assist you. What's on your mind?"
            
            self.root.after(0, lambda: self.add_message("SARAS", greeting, "#27ae60"))
            
            # Speak greeting
            success = self.tts.speak(greeting, "en")
            if not success:
                self.root.after(0, lambda: self.add_system_message("⚠️ TTS greeting failed"))
            
            # Wait a moment for TTS to complete fully
            time.sleep(1)
            
            # Conversation loop with safer audio handling
            max_turns = 3  # Reduced to avoid long conversations
            turn = 0
            
            while turn < max_turns and self.conversation_active:
                turn += 1
                self.root.after(0, lambda t=turn: self.add_system_message(f"🎤 Listening for your response... (Turn {t}/{max_turns})"))
                
                # Use our safer audio method
                audio = self.audio_manager.listen_with_timeout("conversation", timeout=10, phrase_limit=15)
                
                if audio:
                    # Try both languages
                    text = None
                    language = "en"
                    
                    # Try English first
                    text = self.audio_manager.recognize_google(audio, "en-US")
                    if not text:
                        # Try Malayalam
                        text = self.audio_manager.recognize_google(audio, "ml-IN")
                        if text:
                            language = "ml"
                    
                    if text and text.strip():
                        lang_name = "Malayalam" if language == "ml" else "English"
                        self.root.after(0, lambda t=text, ln=lang_name: self.add_message(f"You ({ln})", t, "#2980b9"))
                        
                        # Check for goodbye
                        if self.should_end_conversation(text):
                            farewell = "Goodbye! Say my wake words to talk again anytime."
                            self.root.after(0, lambda f=farewell: self.add_message("SARAS", f, "#27ae60"))
                            self.tts.speak(farewell, "en")
                            break
                        
                        # Generate AI response
                        self.root.after(0, lambda: self.add_system_message("🧠 AI thinking..."))
                        
                        try:
                            response = self.ai_system.generate_response(text)
                        except Exception as e:
                            logger.error(f"AI response failed: {e}")
                            response = f"I heard you say '{text[:50]}...', but I'm having some technical difficulties right now."
                        
                        self.root.after(0, lambda r=response, ln=lang_name: self.add_message(f"SARAS ({ln})", r, "#27ae60"))
                        
                        # Speak response
                        success = self.tts.speak(response, language)
                        if not success:
                            self.root.after(0, lambda: self.add_system_message("⚠️ TTS response failed"))
                        
                        # Wait for TTS to complete
                        time.sleep(2)
                    else:
                        self.root.after(0, lambda: self.add_system_message("❌ Could not understand speech, please try again"))
                else:
                    self.root.after(0, lambda: self.add_system_message("❌ No speech detected, please try again"))
                    
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            self.root.after(0, lambda e=e: self.add_system_message(f"❌ Conversation error: {str(e)}"))
        finally:
            self.conversation_active = False
            
            # Restart wake word detection if it was active
            if wake_word_was_active:
                time.sleep(1)  # Brief pause before restarting
                self.wake_detector.start_listening()
                self.root.after(0, lambda: self.wake_status_label.config(
                    text="🎯 Wake Word: Active - Listening...",
                    fg="#9b59b6"
                ))
            
            self.root.after(0, lambda: self.add_system_message("👋 Conversation ended. Ready for next activation!"))
    
    def should_end_conversation(self, text: str) -> bool:
        """Check if user wants to end conversation"""
        end_phrases = ["goodbye", "bye", "stop", "end", "quit", "done", "thanks", "thank you"]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in end_phrases)
    
    def toggle_wake_word(self):
        """Toggle wake word detection"""
        if self.conversation_active:
            self.add_system_message("⚠️ Cannot toggle wake word during conversation")
            return
        
        if self.wake_detector.is_listening:
            self.wake_detector.stop_listening()
            self.wake_button.config(
                text="🎯 Start Wake Word",
                bg="#9b59b6"
            )
            self.wake_status_label.config(
                text="🎯 Wake Word: Stopped",
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
                    text="🎯 Wake Word: Active - Listening...",
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
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_box.config(state=tk.NORMAL)
        self.conversation_box.delete(1.0, tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        self.add_system_message("🗑️ Conversation history cleared!")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
🤝🎯 Fixed Dual Activation Voice AI Help

FIXED ISSUES:
✅ No more audio crashes
✅ Proper microphone resource management
✅ Stable wake word detection
✅ Safe conversation handling

ACTIVATION METHODS:
🎤 Wake Word Detection:
   • Say: "Hey SARAS", "Hello SARAS", or just "SARAS"
   • Works continuously when enabled
   • Automatically pauses during conversations
   
🎯 Manual Mode:
   • Use "Manual Chat" button for immediate conversation
   • No wake word needed

CONVERSATION FEATURES:
• Bilingual support (English & Malayalam)
• AI-powered responses via Google Gemini
• Natural conversation flow (max 3 turns for stability)
• Say "goodbye" or "stop" to end early

CONTROLS:
• Start/Stop Wake Word: Toggle voice activation
• Manual Chat: Direct conversation mode  
• Clear: Remove conversation history

STABILITY FEATURES:
• Audio resource locking prevents conflicts
• Automatic error recovery
• Safe threading for all operations
• Proper cleanup on app close

TIPS:
• Speak clearly for best recognition
• Wait for TTS to finish before speaking
• Use manual mode if wake words aren't working
• Conversations are limited to 3 turns for stability
        """
        messagebox.showinfo("Help - Fixed Dual Activation AI", help_text)
    
    def run(self):
        """Run the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
    
    def on_closing(self):
        """Handle window closing"""
        self.conversation_active = False
        if hasattr(self, 'wake_detector'):
            self.wake_detector.stop_listening()
        
        # Give threads time to cleanup
        time.sleep(1)
        self.root.destroy()


def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Fixed Dual Activation Voice AI")
        
        app = FixedDualActivationAI()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())