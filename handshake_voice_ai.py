#!/usr/bin/env python3
"""
Handshake-triggered Voice AI Assistant for IEEE EPIC Project
Integrates proximity sensor as handshake detector with voice recognition system
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import os
import sys
import time
from datetime import datetime
from typing import Optional, Tuple

# GPIO imports for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Running in development mode without proximity sensor.")

# Ensure the local 'src' directory is importable when running this script directly
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from loguru import logger

try:
    from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
    from ieee_epic.core.simple_tts import SimpleTextToSpeech
    from ieee_epic.core.ai_response import AIResponseSystem
    from ieee_epic.core.config import Settings
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


class ProximitySensor:
    """Handles proximity sensor functionality for handshake detection"""
    
    def __init__(self, pin: int = 17):
        self.pin = pin
        self.is_active = False
        self.detection_callback = None
        self.gpio_available = GPIO_AVAILABLE
        
        if self.gpio_available:
            try:
                # Set GPIO mode to BCM
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # Set the sensor pin as an input
                GPIO.setup(self.pin, GPIO.IN)
                
                logger.info(f"✅ Proximity sensor initialized on GPIO pin {self.pin}")
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}")
                self.gpio_available = False
        else:
            logger.warning("GPIO not available - proximity sensor disabled")
    
    def set_detection_callback(self, callback):
        """Set callback function to be called when object is detected"""
        self.detection_callback = callback
    
    def start_monitoring(self):
        """Start monitoring proximity sensor in a separate thread"""
        if not self.gpio_available:
            logger.warning("Cannot start proximity monitoring - GPIO not available")
            return
        
        self.is_active = True
        monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitoring_thread.start()
        logger.info("🔍 Proximity sensor monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring proximity sensor"""
        self.is_active = False
        logger.info("🔍 Proximity sensor monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop for proximity sensor"""
        last_state = None
        detection_time = None
        
        while self.is_active:
            try:
                # Read sensor state
                # The sensor output is LOW (0) when it detects an object
                # and HIGH (1) when there is no object.
                current_state = GPIO.input(self.pin) == 0  # True when object detected
                
                # Detect state change from no object to object detected
                if current_state and not last_state:
                    detection_time = time.time()
                    logger.info("👋 Object detected - potential handshake!")
                    
                    # Call the callback if set
                    if self.detection_callback:
                        self.detection_callback()
                
                # Reset detection after object moves away
                elif not current_state and last_state:
                    if detection_time:
                        duration = time.time() - detection_time
                        logger.info(f"👋 Object moved away after {duration:.1f} seconds")
                        detection_time = None
                
                last_state = current_state
                time.sleep(0.1)  # Check every 100ms for responsiveness
                
            except Exception as e:
                logger.error(f"Error in proximity monitoring: {e}")
                time.sleep(1)  # Wait longer on error
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_monitoring()
        if self.gpio_available:
            try:
                GPIO.cleanup()
                logger.info("🧹 GPIO cleanup completed")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")


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
    
    def listen_and_recognize(self, language: str = "auto", timeout: int = 5) -> Tuple[Optional[str], Optional[str]]:
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
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


class HandshakeVoiceAI:
    """Main application class for handshake-triggered voice AI assistant"""
    
    def __init__(self):
        self.setup_backends()
        self.setup_proximity_sensor()
        self.setup_gui()
        self.conversation_active = False
        self.handshake_detected_time = None
        self.conversation_turns = 0
        self.last_activity_time = None
        self.max_turns_before_asking = 3  # Ask about continuing after 3 exchanges
        self.inactivity_timeout = 60  # Ask about continuing after 60 seconds of inactivity
    
    def setup_backends(self):
        """Setup STT, TTS, and AI backends"""
        try:
            if SIMPLE_MODULES_AVAILABLE:
                # Initialize core systems
                self.settings = Settings()
                self.stt = SimpleSpeechRecognizer()
                self.tts = SimpleTextToSpeech()
                
                # Initialize AI response system
                self.ai_system = AIResponseSystem(self.settings)
                
                logger.info("Using simple modules with AI response system")
            elif FALLBACK_AVAILABLE:
                self.stt = FallbackSpeechRecognizer()
                self.tts = FallbackTextToSpeech()
                self.ai_system = None  # No AI in fallback mode
                logger.info("Using fallback modules without AI")
            else:
                raise ImportError("No speech recognition modules available")
                
            self.backend_available = True
            
        except Exception as e:
            logger.error(f"Failed to initialize backends: {e}")
            self.backend_available = False
            self.stt = None
            self.tts = None
            self.ai_system = None
    
    def setup_proximity_sensor(self):
        """Setup proximity sensor for handshake detection"""
        self.proximity_sensor = ProximitySensor(pin=17)  # GPIO pin 17
        self.proximity_sensor.set_detection_callback(self.on_handshake_detected)
    
    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("🤝 Handshake Voice AI Assistant - IEEE EPIC")
        self.root.geometry("950x650")
        self.root.configure(bg="#f8f9fa")
        
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🤝 Handshake Voice AI Assistant",
            font=("Arial", 22, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Wave your hand near the sensor to start conversation",
            font=("Arial", 14),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#f8f9fa")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Sensor status
        sensor_status_frame = tk.Frame(status_frame, bg="#f8f9fa")
        sensor_status_frame.pack(fill=tk.X)
        
        self.sensor_status_label = tk.Label(
            sensor_status_frame,
            text="Sensor Status: Initializing...",
            font=("Arial", 11, "bold"),
            bg="#f8f9fa",
            fg="#e67e22"
        )
        self.sensor_status_label.pack(side=tk.LEFT)
        
        # AI status
        self.ai_status_label = tk.Label(
            sensor_status_frame,
            text="AI Status: Initializing...",
            font=("Arial", 11),
            bg="#f8f9fa",
            fg="#27ae60"
        )
        self.ai_status_label.pack(side=tk.RIGHT)
        
        # Conversation area
        conv_frame = tk.Frame(main_frame, bg="#f8f9fa")
        conv_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 20))
        
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
        
        # Control buttons
        self.sensor_button = tk.Button(
            button_frame,
            text="🔍 Start Sensor",
            font=("Arial", 12, "bold"),
            command=self.toggle_sensor,
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        self.sensor_button.pack(side=tk.LEFT, padx=(0, 10))
        
        manual_button = tk.Button(
            button_frame,
            text="🎤 Manual Chat",
            font=("Arial", 12),
            command=self.start_manual_conversation,
            bg="#3498db",
            fg="white",
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        manual_button.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear",
            font=("Arial", 12),
            command=self.clear_conversation,
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status and help buttons
        help_button = tk.Button(
            button_frame,
            text="❓ Help",
            font=("Arial", 12),
            command=self.show_help,
            bg="#95a5a6",
            fg="white",
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        help_button.pack(side=tk.RIGHT)
        
        # Initialize status labels
        self.update_sensor_status()
        self.update_ai_status()
        
        # Add welcome messages
        self.add_system_message("🤝 Welcome to Handshake Voice AI Assistant!")
        self.add_system_message("• Wave your hand near the proximity sensor to start a conversation")
        self.add_system_message("• The AI will greet you and wait for your response")
        self.add_system_message("• Use 'Manual Chat' button for direct voice interaction")
        self.add_system_message("• Supports both Malayalam and English")
        
        if not self.proximity_sensor.gpio_available:
            self.add_system_message("⚠️ Running in development mode - GPIO not available")
            self.add_system_message("Use 'Manual Chat' button to test voice functionality")
        
        if not self.backend_available:
            self.add_system_message("⚠️ Speech recognition backend not available")
        elif self.ai_system is None:
            self.add_system_message("⚠️ Set GOOGLE_API_KEY for AI responses")
        else:
            status = self.ai_system.get_status()
            if status['gemini_available']:
                self.add_system_message("✅ AI system ready with Gemini")
            else:
                self.add_system_message("⚠️ AI system available but API not configured")
    
    def update_sensor_status(self):
        """Update sensor status label"""
        if self.proximity_sensor.gpio_available:
            if hasattr(self, 'proximity_sensor') and self.proximity_sensor.is_active:
                self.sensor_status_label.config(
                    text="🔍 Sensor: Active - Ready for handshake",
                    fg="#27ae60"
                )
            else:
                self.sensor_status_label.config(
                    text="🔍 Sensor: Inactive",
                    fg="#e67e22"
                )
        else:
            self.sensor_status_label.config(
                text="🔍 Sensor: Not Available (Dev Mode)",
                fg="#95a5a6"
            )
    
    def update_ai_status(self):
        """Update AI status label"""
        if self.ai_system and self.ai_system.get_status()['gemini_available']:
            self.ai_status_label.config(
                text="🤖 AI: Connected & Ready",
                fg="#27ae60"
            )
        elif self.backend_available:
            self.ai_status_label.config(
                text="🤖 AI: Backend Ready (No API)",
                fg="#e67e22"
            )
        else:
            self.ai_status_label.config(
                text="🤖 AI: Not Available",
                fg="#e74c3c"
            )
    
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
    
    def on_handshake_detected(self):
        """Called when proximity sensor detects a handshake"""
        if self.conversation_active:
            logger.info("Conversation already active, ignoring handshake")
            return
        
        self.handshake_detected_time = datetime.now()
        self.add_system_message("👋 Handshake detected! Starting conversation...")
        
        # Start conversation in separate thread
        conversation_thread = threading.Thread(target=self.handle_handshake_conversation, daemon=True)
        conversation_thread.start()
    
    def handle_handshake_conversation(self):
        """Handle the conversation flow after handshake detection"""
        if not self.backend_available:
            self.add_system_message("❌ Cannot start conversation - speech backend not available")
            return
        
        self.conversation_active = True
        # Reset conversation tracking
        self.conversation_turns = 0
        self.last_activity_time = time.time()
        
        try:
            # Generate and speak greeting
            greeting = self.generate_greeting()
            self.add_message("AI Assistant", greeting, "#27ae60")
            
            # Speak the greeting
            language = self.detect_language(greeting)
            success = self.tts.speak(greeting, language)
            
            if not success:
                self.add_system_message("⚠️ TTS greeting failed")
            
            # Listen for user response
            self.listen_for_response()
            
        except Exception as e:
            logger.error(f"Error in handshake conversation: {e}")
            self.add_system_message(f"❌ Conversation error: {str(e)}")
        finally:
            self.conversation_active = False
    
    def generate_greeting(self):
        """Generate a greeting message"""
        greetings = [
            "Hello! I detected your handshake. How can I help you today?",
            "Hi there! I see you waved at me. What would you like to talk about?",
            "Greetings! Your handshake activated me. What can I do for you?",
            "Hello! I'm here to assist you. What's on your mind?",
        ]
        
        import random
        return random.choice(greetings)
    
    def listen_for_response(self):
        """Listen for user response after greeting"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts and self.conversation_active:
            attempt += 1
            
            try:
                self.add_system_message(f"🎤 Listening for your response... (Attempt {attempt}/{max_attempts})")
                
                # Check for inactivity timeout
                if self.last_activity_time and (time.time() - self.last_activity_time) > self.inactivity_timeout:
                    if self.ask_continue_conversation():
                        # Reset counters and continue listening
                        self.conversation_turns = 0
                        self.last_activity_time = time.time()
                        attempt = 0
                        continue
                    else:
                        break
                
                language = self.language_var.get()
                text, detected_lang = self.stt.listen_and_recognize(language, timeout=10)
                
                if text and detected_lang:
                    # Update activity tracking
                    self.last_activity_time = time.time()
                    self.conversation_turns += 1
                    
                    lang_name = "Malayalam" if detected_lang == "ml" else "English"
                    self.add_message(f"You ({lang_name})", text, "#2980b9")
                    
                    # Check if user wants to end conversation naturally
                    if self.should_end_conversation(text):
                        self.add_system_message("👋 Ending conversation as requested")
                        break
                    
                    # Generate AI response
                    self.add_system_message("🧠 AI thinking...")
                    
                    response = self.generate_ai_response(text, detected_lang)
                    self.add_message(f"AI Assistant ({lang_name})", response, "#27ae60")
                    
                    # Speak response
                    success = self.tts.speak(response, detected_lang)
                    
                    if not success:
                        self.add_system_message("⚠️ TTS response failed")
                    
                    # Check if we should ask about continuing
                    should_ask_continue = False
                    
                    # Ask after multiple turns
                    if self.conversation_turns >= self.max_turns_before_asking:
                        should_ask_continue = True
                        
                    # Don't ask immediately, just continue naturally and let inactivity timeout handle it
                    if should_ask_continue:
                        self.add_system_message("💬 Feel free to ask me anything else...")
                        # Reset turn counter but continue conversation
                        self.conversation_turns = 0
                    
                    # Continue conversation naturally
                    attempt = 0
                    continue
                        
                else:
                    self.add_system_message(f"❌ Could not understand speech (Attempt {attempt}/{max_attempts})")
                    if attempt < max_attempts:
                        self.add_system_message("Please try speaking again...")
                        time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error during listening: {e}")
                self.add_system_message(f"❌ Listening error: {str(e)}")
                break
        
        # End conversation
        self.conversation_turns = 0
        self.last_activity_time = None
        self.add_system_message("👋 Conversation ended. Wave again to start a new one!")
    
    def ask_continue_conversation(self):
        """Ask if user wants to continue the conversation"""
        continue_prompt = "Is there anything else I can help you with today?"
        self.add_message("AI Assistant", continue_prompt, "#27ae60")
        
        # Speak the prompt
        self.tts.speak(continue_prompt, "en")
        
        try:
            self.add_system_message("🎤 Listening for your response...")
            text, detected_lang = self.stt.listen_and_recognize("en", timeout=10)
            
            if text:
                text_lower = text.lower()
                if any(word in text_lower for word in ["yes", "yeah", "sure", "okay", "more", "another", "continue"]):
                    self.add_message("You", text, "#2980b9")
                    self.add_system_message("✅ Continuing our conversation...")
                    return True
                elif any(word in text_lower for word in ["no", "nothing", "stop", "end", "bye", "goodbye", "done", "that's all"]):
                    self.add_message("You", text, "#2980b9")
                    self.add_system_message("👋 Thank you for chatting! Wave again anytime.")
                    return False
                else:
                    # If user asks another question, continue naturally
                    # Don't consume this input - let it be processed as a new question
                    return True
            else:
                self.add_system_message("🔇 I'll assume you're done for now - wave again anytime!")
                return False
                
        except Exception as e:
            logger.error(f"Error asking to continue: {e}")
            return False
    
    def should_end_conversation(self, text: str) -> bool:
        """Check if user wants to end conversation naturally"""
        end_phrases = [
            "goodbye", "bye", "see you", "talk later", "that's all",
            "thanks", "thank you", "stop", "end", "quit", "done",
            "വിട", "നന്ദി"  # Malayalam goodbye phrases
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in end_phrases)
    
    def generate_ai_response(self, text: str, language: str) -> str:
        """Generate AI response to user input"""
        if self.ai_system and self.ai_system.get_status()['gemini_available']:
            try:
                response = self.ai_system.generate_response(text)
                return response
            except Exception as e:
                logger.error(f"AI response generation failed: {e}")
                # Fall back to simple echo
                if language == "ml":
                    return f"AI പിശക്. നിങ്ങൾ പറഞ്ഞത്: {text}"
                else:
                    return f"I heard you say: {text}. Sorry, I'm having trouble with my AI system right now."
        else:
            # Simple echo response when AI is not available
            if language == "ml":
                return f"നിങ്ങൾ പറഞ്ഞത്: {text}"
            else:
                return f"You said: {text}"
    
    def detect_language(self, text: str) -> str:
        """Simple language detection for Malayalam vs English."""
        malayalam_chars = set("അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ")
        text_chars = set(text)
        
        if malayalam_chars.intersection(text_chars):
            return "ml"
        return "en"
    
    def toggle_sensor(self):
        """Toggle proximity sensor monitoring"""
        if not self.proximity_sensor.gpio_available:
            messagebox.showwarning("Sensor Not Available", 
                                 "GPIO not available. Running in development mode.\n"
                                 "Use 'Manual Chat' for voice interaction.")
            return
        
        if self.proximity_sensor.is_active:
            self.proximity_sensor.stop_monitoring()
            self.sensor_button.config(
                text="🔍 Start Sensor",
                bg="#27ae60"
            )
        else:
            self.proximity_sensor.start_monitoring()
            self.sensor_button.config(
                text="⏹️ Stop Sensor",
                bg="#e74c3c"
            )
        
        self.update_sensor_status()
    
    def start_manual_conversation(self):
        """Start manual conversation without handshake detection"""
        if not self.backend_available:
            messagebox.showerror("Error", "Speech recognition backend not available!")
            return
        
        if self.conversation_active:
            messagebox.showwarning("Conversation Active", "A conversation is already in progress!")
            return
        
        # Start manual conversation in separate thread
        manual_thread = threading.Thread(target=self.handle_manual_conversation, daemon=True)
        manual_thread.start()
    
    def handle_manual_conversation(self):
        """Handle manual conversation flow"""
        self.conversation_active = True
        # Reset conversation tracking
        self.conversation_turns = 0
        self.last_activity_time = time.time()
        self.add_system_message("🎤 Manual conversation started - speak now!")
        
        try:
            self.listen_for_response()
        except Exception as e:
            logger.error(f"Error in manual conversation: {e}")
            self.add_system_message(f"❌ Manual conversation error: {str(e)}")
        finally:
            self.conversation_active = False
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_box.config(state=tk.NORMAL)
        self.conversation_box.delete(1.0, tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        
        # Clear AI conversation history if available
        if self.ai_system and hasattr(self.ai_system, 'conversation'):
            try:
                self.ai_system.conversation.clear()
                self.add_system_message("🗑️ Conversation and AI history cleared!")
            except Exception as e:
                logger.error(f"Failed to clear AI history: {e}")
                self.add_system_message("🗑️ Conversation cleared!")
        else:
            self.add_system_message("🗑️ Conversation cleared!")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
🤝 Handshake Voice AI Assistant Help

🔍 Handshake Detection:
• Wave your hand near the proximity sensor to start conversation
• The AI will greet you and wait for your response
• Supports multiple conversation turns
• Wave again after conversation ends to start a new one

🎤 Manual Mode:
• Use 'Manual Chat' button for direct voice interaction
• No handshake detection required
• Same AI capabilities as handshake mode

🌐 Language Support:
• Auto: Automatic detection (tries Malayalam first, then English)
• English (en): English recognition only
• Malayalam (ml): Malayalam recognition only

🤖 AI Features:
• Intelligent responses powered by Google Gemini
• Conversation context awareness
• Bilingual support (English & Malayalam)

🎛️ Controls:
• Start/Stop Sensor: Toggle proximity sensor monitoring
• Manual Chat: Start conversation without handshake
• Clear: Clear conversation history
• Help: Show this help dialog

🔧 Hardware Requirements:
• Raspberry Pi with GPIO support
• IR proximity sensor connected to GPIO pin 17
• Microphone and speakers for voice interaction

💡 Troubleshooting:
• Ensure proximity sensor is properly connected
• Set GOOGLE_API_KEY environment variable for AI responses
• Check microphone and speaker connections
• Speak clearly and avoid background noise
        """
        
        messagebox.showinfo("Help", help_text)
    
    def run(self):
        """Run the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Auto-start sensor if available
            if self.proximity_sensor.gpio_available:
                self.proximity_sensor.start_monitoring()
                self.sensor_button.config(
                    text="⏹️ Stop Sensor",
                    bg="#e74c3c"
                )
                self.update_sensor_status()
                self.add_system_message("🔍 Proximity sensor started automatically")
            
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
    
    def on_closing(self):
        """Handle window closing"""
        self.conversation_active = False
        if hasattr(self, 'proximity_sensor'):
            self.proximity_sensor.cleanup()
        self.root.destroy()


def main():
    """Main function"""
    try:
        logger.info("Starting Handshake Voice AI Assistant...")
        
        app = HandshakeVoiceAI()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())