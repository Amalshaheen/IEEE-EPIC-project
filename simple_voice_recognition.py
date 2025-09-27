#!/usr/bin/env python3
"""
Simple Voice Recognition Implementation for IEEE EPIC Project
Implements bilingual (Malayalam + English) speech recognition with GUI
"""

import speech_recognition as sr
from gtts import gTTS
import os
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
import threading
import tempfile
import subprocess
from loguru import logger

class SimpleVoiceRecognition:
    """Simple voice recognition class with bilingual support"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with self.microphone as source:
            logger.info("Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source)
    
    def listen_and_recognize(self):
        """Listen for audio and attempt recognition in both languages"""
        try:
            with self.microphone as source:
                logger.info("Listening...")
                # Listen for the first phrase and extract it into audio data
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Try Malayalam first
            try:
                text = self.recognizer.recognize_google(audio, language="ml-IN")
                logger.success(f"Malayalam recognized: {text}")
                return text, "ml"
            except sr.UnknownValueError:
                # Malayalam failed, try English
                try:
                    text = self.recognizer.recognize_google(audio, language="en-IN")
                    logger.success(f"English recognized: {text}")
                    return text, "en"
                except sr.UnknownValueError:
                    logger.warning("Could not understand audio in either language")
                    return None, None
            except sr.RequestError as e:
                logger.error(f"Recognition service error: {e}")
                return None, None
                
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout - no speech detected")
            return None, None
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return None, None
    
    def speak_text(self, text: str, language: str = "en"):
        """Convert text to speech and play it"""
        try:
            # Map language codes
            tts_lang = "ml" if language == "ml" else "en"
            
            # Create TTS
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            
            # Use temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Try different audio players
            audio_players = ["mpg123", "ffplay", "aplay", "paplay"]
            played = False
            
            for player in audio_players:
                try:
                    if player == "mpg123":
                        subprocess.run([player, "-q", temp_filename], check=True)
                    elif player == "ffplay":
                        subprocess.run([player, "-nodisp", "-autoexit", "-v", "quiet", temp_filename], check=True)
                    else:
                        subprocess.run([player, temp_filename], check=True)
                    played = True
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if not played:
                logger.warning("No suitable audio player found. Install mpg123, ffplay, or pulseaudio")
            
            # Clean up
            try:
                os.unlink(temp_filename)
            except:
                pass
                
        except Exception as e:
            logger.error(f"TTS error: {e}")


class VoiceRecognitionGUI:
    """GUI for the voice recognition system"""
    
    def __init__(self):
        self.voice_recognition = SimpleVoiceRecognition()
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main window
        self.root = tk.Tk()
        self.root.title("Interactive Robo - Malayalam + English")
        self.root.geometry("800x500")
        self.root.configure(bg="#f0f0f0")
        
        # Title
        title_label = tk.Label(
            self.root, 
            text="🤖 Voice Recognition Assistant", 
            font=("Arial", 18, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        title_label.pack(pady=10)
        
        # Subtitle
        subtitle_label = tk.Label(
            self.root, 
            text="Supports Malayalam & English", 
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Conversation display
        self.conversation_box = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            font=("Arial", 12),
            bg="white",
            fg="black",
            height=20
        )
        self.conversation_box.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Button frame
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=10)
        
        # Listen button
        self.listen_button = tk.Button(
            button_frame,
            text="🎤 Ask a Question",
            font=("Arial", 16, "bold"),
            command=self.start_listening,
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            relief="raised",
            cursor="hand2"
        )
        self.listen_button.pack(side=tk.LEFT, padx=10)
        
        # Clear button
        clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear",
            font=("Arial", 12),
            command=self.clear_conversation,
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=10,
            relief="raised",
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT, padx=10)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Ready to listen",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#27ae60"
        )
        self.status_label.pack(pady=5)
        
        # Add initial message
        self.add_message("System", "Welcome! Click 'Ask a Question' to start speaking.", "#2c3e50")
        self.add_message("System", "I can understand both Malayalam and English.", "#2c3e50")
    
    def add_message(self, speaker: str, message: str, color: str = "black"):
        """Add a message to the conversation box"""
        self.conversation_box.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format message
        formatted_message = f"[{timestamp}] {speaker}: {message}\n\n"
        
        # Insert message
        self.conversation_box.insert(tk.END, formatted_message)
        
        # Auto-scroll to bottom
        self.conversation_box.see(tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        
        # Update display
        self.root.update()
    
    def update_status(self, status: str, color: str = "#27ae60"):
        """Update the status label"""
        self.status_label.config(text=status, fg=color)
        self.root.update()
    
    def start_listening(self):
        """Start the voice recognition in a separate thread"""
        # Disable button to prevent multiple simultaneous recordings
        self.listen_button.config(state=tk.DISABLED, text="🎤 Listening...")
        self.update_status("Listening... Please speak now", "#e67e22")
        
        # Start listening in a separate thread
        threading.Thread(target=self.listen_and_process, daemon=True).start()
    
    def listen_and_process(self):
        """Listen for speech and process it"""
        try:
            # Listen for speech
            self.add_message("System", "🎤 Listening... Please speak now")
            
            query, lang = self.voice_recognition.listen_and_recognize()
            
            if query and lang:
                # Display recognized speech
                language_name = "Malayalam" if lang == "ml" else "English"
                self.add_message(f"You ({language_name})", query, "#2980b9")
                
                # Generate simple response
                if lang == "ml":
                    response = f"നിങ്ങൾ പറഞ്ഞത്: {query}"
                else:
                    response = f"You said: {query}"
                
                # Display response
                self.add_message(f"Assistant ({language_name})", response, "#27ae60")
                
                # Update status
                self.update_status("Speaking response...", "#8e44ad")
                
                # Speak response
                self.voice_recognition.speak_text(response, lang)
                
                self.update_status("Ready to listen", "#27ae60")
                
            else:
                self.add_message("System", "❌ Could not understand. Please try again.", "#e74c3c")
                self.update_status("Could not understand - try again", "#e74c3c")
                
        except Exception as e:
            logger.error(f"Error in listen_and_process: {e}")
            self.add_message("System", f"❌ Error: {str(e)}", "#e74c3c")
            self.update_status("Error occurred", "#e74c3c")
        
        finally:
            # Re-enable button
            self.listen_button.config(state=tk.NORMAL, text="🎤 Ask a Question")
    
    def clear_conversation(self):
        """Clear the conversation box"""
        self.conversation_box.config(state=tk.NORMAL)
        self.conversation_box.delete(1.0, tk.END)
        self.conversation_box.config(state=tk.DISABLED)
        self.add_message("System", "Conversation cleared. Ready to start again!", "#2c3e50")
        self.update_status("Ready to listen", "#27ae60")
    
    def run(self):
        """Run the GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        except Exception as e:
            logger.error(f"GUI error: {e}")


def main():
    """Main function to run the voice recognition GUI"""
    try:
        logger.info("Starting Simple Voice Recognition System...")
        
        # Create and run GUI
        app = VoiceRecognitionGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())