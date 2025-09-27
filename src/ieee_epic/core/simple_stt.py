"""
Simplified Speech Recognition Module for IEEE EPIC Project
Uses SpeechRecognition library with Google's free API
"""

import speech_recognition as sr
from typing import Optional, Tuple
from loguru import logger
import time


class SimpleSpeechRecognizer:
    """Simple speech recognizer using Google's free API"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self._initialize_microphone()
    
    def _initialize_microphone(self):
        """Initialize and calibrate the microphone"""
        try:
            self.microphone = sr.Microphone()
            
            # Calibrate for ambient noise
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.success("Microphone calibrated successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            self.microphone = None
    
    def listen_for_speech(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[sr.AudioData]:
        """Listen for speech input"""
        if not self.microphone:
            logger.error("Microphone not available")
            return None
        
        try:
            with self.microphone as source:
                logger.info("🎤 Listening for speech...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                logger.info("✅ Audio captured")
                return audio
                
        except sr.WaitTimeoutError:
            logger.warning("⏰ Listening timeout - no speech detected")
            return None
        except Exception as e:
            logger.error(f"❌ Error while listening: {e}")
            return None
    
    def recognize_speech(self, audio_data: sr.AudioData, language: str = "auto") -> Tuple[Optional[str], Optional[str]]:
        """
        Recognize speech from audio data
        
        Args:
            audio_data: Audio data to recognize
            language: Target language ('ml', 'en', or 'auto')
        
        Returns:
            Tuple of (recognized_text, detected_language)
        """
        if not audio_data:
            return None, None
        
        if language == "auto":
            # Try Malayalam first, then English
            return self._try_bilingual_recognition(audio_data)
        elif language == "ml":
            return self._recognize_single_language(audio_data, "ml-IN", "ml")
        elif language == "en":
            return self._recognize_single_language(audio_data, "en-IN", "en")
        else:
            logger.warning(f"Unsupported language: {language}")
            return None, None
    
    def _try_bilingual_recognition(self, audio_data: sr.AudioData) -> Tuple[Optional[str], Optional[str]]:
        """Try recognition in both Malayalam and English"""
        # Try Malayalam first
        text, lang = self._recognize_single_language(audio_data, "ml-IN", "ml")
        if text:
            return text, lang
        
        # Fall back to English
        text, lang = self._recognize_single_language(audio_data, "en-IN", "en")
        return text, lang
    
    def _recognize_single_language(self, audio_data: sr.AudioData, google_lang: str, lang_code: str) -> Tuple[Optional[str], Optional[str]]:
        """Recognize speech in a single language"""
        try:
            logger.info(f"🔍 Trying recognition in {lang_code}...")
            text = self.recognizer.recognize_google(audio_data, language=google_lang)
            
            if text and text.strip():
                logger.success(f"✅ {lang_code.upper()} recognized: {text}")
                return text.strip(), lang_code
            else:
                return None, None
                
        except sr.UnknownValueError:
            logger.warning(f"❌ Could not understand audio in {lang_code}")
            return None, None
        except sr.RequestError as e:
            logger.error(f"❌ Recognition service error for {lang_code}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"❌ Unexpected error in {lang_code} recognition: {e}")
            return None, None
    
    def listen_and_recognize(self, language: str = "auto", timeout: int = 5) -> Tuple[Optional[str], Optional[str]]:
        """
        Listen for speech and recognize it
        
        Args:
            language: Target language ('ml', 'en', or 'auto')
            timeout: Listening timeout in seconds
        
        Returns:
            Tuple of (recognized_text, detected_language)
        """
        # Listen for audio
        audio_data = self.listen_for_speech(timeout=timeout)
        if not audio_data:
            return None, None
        
        # Recognize speech
        return self.recognize_speech(audio_data, language)
    
    def is_available(self) -> bool:
        """Check if the speech recognizer is available"""
        return self.microphone is not None
    
    def get_available_microphones(self):
        """Get list of available microphones"""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            logger.info("Available microphones:")
            for i, name in enumerate(mic_list):
                logger.info(f"  {i}: {name}")
            return mic_list
        except Exception as e:
            logger.error(f"Failed to get microphone list: {e}")
            return []


# Convenience functions for easy usage
def listen_and_recognize_auto() -> Tuple[Optional[str], Optional[str]]:
    """Quick function to listen and recognize speech automatically"""
    recognizer = SimpleSpeechRecognizer()
    if not recognizer.is_available():
        logger.error("Speech recognizer not available")
        return None, None
    
    return recognizer.listen_and_recognize("auto")


def listen_and_recognize_language(language: str) -> Tuple[Optional[str], Optional[str]]:
    """Quick function to listen and recognize speech in specific language"""
    recognizer = SimpleSpeechRecognizer()
    if not recognizer.is_available():
        logger.error("Speech recognizer not available")
        return None, None
    
    return recognizer.listen_and_recognize(language)