"""
Simplified Text-to-Speech Module for IEEE EPIC Project
Uses gTTS (Google Text-to-Speech) with local audio playback
"""

from gtts import gTTS
import tempfile
import os
import subprocess
import asyncio
from typing import Optional
from loguru import logger


class SimpleTextToSpeech:
    """Simple TTS using gTTS and system audio players"""
    
    def __init__(self):
        self.available_players = self._detect_audio_players()
        
    def _detect_audio_players(self) -> list:
        """Detect available audio players on the system"""
        players = ["mpg123", "ffplay", "aplay", "paplay", "vlc"]
        available = []
        
        for player in players:
            try:
                subprocess.run([player, "--version"], 
                             capture_output=True, 
                             check=True, 
                             timeout=2)
                available.append(player)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if available:
            logger.info(f"Available audio players: {', '.join(available)}")
        else:
            logger.warning("No suitable audio players found. Install mpg123, ffplay, or pulseaudio")
            
        return available
    
    def _play_audio_file(self, filename: str) -> bool:
        """Play audio file using available system players"""
        if not self.available_players:
            logger.error("No audio players available")
            return False
        
        for player in self.available_players:
            try:
                if player == "mpg123":
                    subprocess.run([player, "-q", filename], check=True)
                elif player == "ffplay":
                    subprocess.run([player, "-nodisp", "-autoexit", "-v", "quiet", filename], check=True)
                elif player == "vlc":
                    subprocess.run([player, "--intf", "dummy", "--play-and-exit", filename], check=True)
                else:
                    subprocess.run([player, filename], check=True)
                
                return True
                
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning(f"Player {player} failed: {e}")
                continue
        
        logger.error("All audio players failed")
        return False
    
    def speak(self, text: str, language: str = "en", slow: bool = False) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            language: Language code ('en', 'ml', etc.)
            slow: Speak slowly
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return False
        
        try:
            # Map language codes
            tts_lang = self._map_language_code(language)
            
            logger.info(f"🗣️ Speaking in {tts_lang}: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # Create TTS
            tts = gTTS(text=text, lang=tts_lang, slow=slow)
            
            # Use temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Play audio
            success = self._play_audio_file(temp_filename)
            
            # Clean up
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            if success:
                logger.success("✅ TTS completed successfully")
            else:
                logger.error("❌ TTS playback failed")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return False
    
    async def speak_async(self, text: str, language: str = "en", slow: bool = False) -> bool:
        """Async version of speak method"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak, text, language, slow)
    
    def _map_language_code(self, language: str) -> str:
        """Map internal language codes to gTTS language codes"""
        lang_map = {
            "ml": "ml",      # Malayalam
            "en": "en",      # English
            "hi": "hi",      # Hindi
            "ta": "ta",      # Tamil
            "te": "te",      # Telugu
            "kn": "kn",      # Kannada
            "auto": "en"     # Default to English for auto
        }
        
        return lang_map.get(language.lower(), "en")
    
    def is_available(self) -> bool:
        """Check if TTS is available"""
        return len(self.available_players) > 0
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return ["en", "ml", "hi", "ta", "te", "kn"]


# Convenience functions for easy usage
def speak_text(text: str, language: str = "en") -> bool:
    """Quick function to speak text"""
    tts = SimpleTextToSpeech()
    if not tts.is_available():
        logger.error("TTS not available")
        return False
    
    return tts.speak(text, language)


async def speak_text_async(text: str, language: str = "en") -> bool:
    """Quick async function to speak text"""
    tts = SimpleTextToSpeech()
    if not tts.is_available():
        logger.error("TTS not available")
        return False
    
    return await tts.speak_async(text, language)