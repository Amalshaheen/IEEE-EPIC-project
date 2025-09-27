#!/usr/bin/env python3
"""
Enhanced Voice Recognition GUI for IEEE EPIC Project
Integrates simple voice recognition with the existing project structure
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

# Ensure the local 'src' directory is importable when running this script directly
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from loguru import logger

try:
    from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
    from ieee_epic.core.simple_tts import SimpleTextToSpeech
    SIMPLE_MODULES_AVAILABLE = True
except ImportError:
    logger.warning("Simple modules not available, using fallback")
    SIMPLE_MODULES_AVAILABLE = False

# Fallback imports for when simple modules are not available
if not SIMPLE_MODULES_AVAILABLE:
    try:
        import speech_recognition as sr
        from gtts import gTTS
        import tempfile
        import subprocess
        FALLBACK_AVAILABLE = True
    except ImportError:
        FALLBACK_AVAILABLE = False


class FallbackSpeechRecognizer:
    """Fallback speech recognizer when simple modules are not available"""
    
    def __init__(self):
        if not FALLBACK_AVAILABLE:
            raise ImportError("Required packages not available")
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibrate microphone
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    def listen_and_recognize(self, language: str = "auto") -> Tuple[Optional[str], Optional[str]]:
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            if language == "auto":
                # Try Malayalam first
                try:
                    text = self.recognizer.recognize_google(audio, language="ml-IN")
                    return text, "ml"
                except:
                    try:
                        text = self.recognizer.recognize_google(audio, language="en-IN")
                        return text, "en"
                    except:
                        return None, None
            elif language == "ml":
                try:
                    text = self.recognizer.recognize_google(audio, language="ml-IN")
                    return text, "ml"
                except:
                    return None, None
            elif language == "en":
                try:
                    text = self.recognizer.recognize_google(audio, language="en-IN")
                    return text, "en"
                except:
                    return None, None
        except:
            return None, None


class FallbackTextToSpeech:
    """Fallback TTS when simple modules are not available"""
    
    def speak(self, text: str, language: str = "en") -> bool:
        if not FALLBACK_AVAILABLE:
            return False
        
        try:
            tts_lang = "ml" if language == "ml" else "en"
            tts = gTTS(text=text, lang=tts_lang)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Try to play
            try:
                subprocess.run(["mpg123", "-q", temp_filename], check=True)
                success = True
            except:
                try:
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", "-v", "quiet", temp_filename], check=True)
                    success = True
                except:
                    success = False
            
            # Clean up
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            return success
        except:
            return False


class EnhancedVoiceRecognitionGUI:
    """Enhanced GUI for voice recognition with better error handling"""
    
    def __init__(self):
        self.setup_backends()
        self.setup_gui()
    
    def setup_backends(self):
        """Setup STT and TTS backends"""
        try:
            if SIMPLE_MODULES_AVAILABLE:
                self.stt = SimpleSpeechRecognizer()
                self.tts = SimpleTextToSpeech()
                logger.info("Using simple modules")
            elif FALLBACK_AVAILABLE:
                self.stt = FallbackSpeechRecognizer()
                self.tts = FallbackTextToSpeech()
                logger.info("Using fallback modules")
            else:
                raise ImportError("No speech recognition modules available")
                
            self.backend_available = True
            
        except Exception as e:
            logger.error(f"Failed to initialize backends: {e}")
            self.backend_available = False
            self.stt = None
            self.tts = None
    
    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("Enhanced Voice Recognition - Malayalam + English")
        self.root.geometry("900x600")
        self.root.configure(bg="#f8f9fa")
        
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🤖 Enhanced Voice Recognition Assistant",
            font=("Arial", 20, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Advanced Malayalam & English Speech Recognition",
            font=("Arial", 12),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#f8f9fa")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = tk.Label(
            status_frame,
            text="Initializing...",
            font=("Arial", 11),
            bg="#f8f9fa",
            fg="#27ae60"
        )
        self.status_label.pack()
        
        # Update initial status
        if self.backend_available:
            self.update_status("Ready to listen", "#27ae60")
        else:
            self.update_status("Backend not available - check dependencies", "#e74c3c")
        
        # Conversation area
        conv_frame = tk.Frame(main_frame, bg="#f8f9fa")
        conv_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        conv_label = tk.Label(
            conv_frame,
            text="Conversation History",
            font=("Arial", 14, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        conv_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Create conversation box with custom styling
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
            padx=10,
            pady=10
        )
        self.conversation_box.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons frame
        button_frame = tk.Frame(main_frame, bg="#f8f9fa")
        button_frame.pack(fill=tk.X)
        
        # Language selection
        lang_frame = tk.Frame(button_frame, bg="#f8f9fa")
        lang_frame.pack(side=tk.LEFT)
        
        tk.Label(
            lang_frame,
            text="Language:",
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#2c3e50"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.language_var = tk.StringVar(value="auto")
        self.language_dropdown = tk.OptionMenu(
            lang_frame,
            self.language_var,
            "auto", "en", "ml"
        )
        self.language_dropdown.config(
            font=("Arial", 10),
            bg="#ffffff",
            relief="flat"
        )
        self.language_dropdown.pack(side=tk.LEFT, padx=(0, 20))
        
        # Main buttons
        self.listen_button = tk.Button(
            button_frame,
            text="🎤 Start Listening",
            font=("Arial", 14, "bold"),
            command=self.toggle_listening,
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        self.listen_button.pack(side=tk.LEFT, padx=(0, 10))
        
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
        
        # Add welcome message
        self.add_system_message("Welcome to Enhanced Voice Recognition!")
        self.add_system_message("• Select your preferred language or use 'auto' for automatic detection")
        self.add_system_message("• Click 'Start Listening' and speak clearly")
        self.add_system_message("• Supports both Malayalam and English")
        
        if not self.backend_available:
            self.add_system_message("⚠️ Speech recognition backend not available. Please install required packages:")
            self.add_system_message("pip install SpeechRecognition gTTS")
        
        # State variables
        self.is_listening = False
    
    def add_message(self, speaker: str, message: str, color: str = "#2c3e50"):
        """Add a message to the conversation"""
        self.conversation_box.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {speaker}: {message}\n\n"
        
        self.conversation_box.insert(tk.END, formatted_message)
        self.conversation_box.see(tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        self.root.update()
    
    def add_system_message(self, message: str):
        """Add a system message"""
        self.add_message("System", message, "#7f8c8d")
    
    def update_status(self, status: str, color: str = "#27ae60"):
        """Update status label"""
        self.status_label.config(text=status, fg=color)
        self.root.update()
    
    def toggle_listening(self):
        """Toggle listening state"""
        if not self.backend_available:
            messagebox.showerror("Error", "Speech recognition backend not available!")
            return
        
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start listening for speech"""
        self.is_listening = True
        self.listen_button.config(
            text="⏹️ Stop Listening",
            bg="#e74c3c"
        )
        self.language_dropdown.config(state="disabled")
        
        # Start listening in separate thread
        threading.Thread(target=self.listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        self.listen_button.config(
            text="🎤 Start Listening",
            bg="#3498db"
        )
        self.language_dropdown.config(state="normal")
        self.update_status("Stopped listening", "#e67e22")
    
    def listen_thread(self):
        """Listening thread"""
        language = self.language_var.get()
        
        while self.is_listening:
            try:
                self.update_status("🎤 Listening... Speak now", "#e67e22")
                
                # Listen and recognize
                if hasattr(self.stt, 'listen_and_recognize'):
                    text, detected_lang = self.stt.listen_and_recognize(language)
                else:
                    text, detected_lang = self.stt.listen_and_recognize(language)
                
                if text and detected_lang:
                    lang_name = "Malayalam" if detected_lang == "ml" else "English"
                    self.add_message(f"You ({lang_name})", text, "#2980b9")
                    
                    # Generate response
                    response = self.generate_response(text, detected_lang)
                    self.add_message(f"Assistant ({lang_name})", response, "#27ae60")
                    
                    # Speak response
                    self.update_status("🗣️ Speaking response...", "#8e44ad")
                    success = self.tts.speak(response, detected_lang)
                    
                    if not success:
                        self.add_system_message("⚠️ TTS playback failed")
                    
                    self.update_status("Ready for next input", "#27ae60")
                else:
                    self.add_system_message("❌ Could not understand speech. Please try again.")
                    self.update_status("Could not understand - try again", "#e74c3c")
                    
            except Exception as e:
                logger.error(f"Listening thread error: {e}")
                self.add_system_message(f"❌ Error: {str(e)}")
                self.update_status("Error occurred", "#e74c3c")
                break
        
        # Reset button state when loop ends
        self.root.after(0, lambda: self.listen_button.config(
            text="🎤 Start Listening",
            bg="#3498db"
        ))
        self.root.after(0, lambda: self.language_dropdown.config(state="normal"))
    
    def generate_response(self, text: str, language: str) -> str:
        """Generate a simple response to the input"""
        if language == "ml":
            return f"നിങ്ങൾ പറഞ്ഞത്: {text}"
        else:
            return f"You said: {text}"
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_box.config(state=tk.NORMAL)
        self.conversation_box.delete(1.0, tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        self.add_system_message("Conversation cleared. Ready to start again!")
        self.update_status("Ready to listen", "#27ae60")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Enhanced Voice Recognition Help

🎤 Getting Started:
1. Select your preferred language (auto/en/ml)
2. Click "Start Listening" to begin
3. Speak clearly when prompted
4. The system will recognize and respond

🌐 Language Support:
• Auto: Automatic detection (tries Malayalam first, then English)
• English (en): English recognition only
• Malayalam (ml): Malayalam recognition only

🎛️ Controls:
• Start/Stop Listening: Toggle voice input
• Clear: Clear conversation history
• Help: Show this help dialog

🔧 Troubleshooting:
• Ensure microphone is connected and working
• Check that required packages are installed
• Speak clearly and avoid background noise
• Try different language settings if recognition fails

📋 Requirements:
• SpeechRecognition library
• gTTS (Google Text-to-Speech)
• Audio playback software (mpg123, ffplay, etc.)
        """
        
        messagebox.showinfo("Help", help_text)
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_listening:
            self.stop_listening()
        self.root.destroy()


def main():
    """Main function"""
    try:
        logger.info("Starting Enhanced Voice Recognition GUI...")
        
        app = EnhancedVoiceRecognitionGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())