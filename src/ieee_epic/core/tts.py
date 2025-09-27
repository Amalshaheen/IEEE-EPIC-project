"""
Text-to-Speech (TTS) Engine for IEEE EPIC STT system.

This module provides TTS backends with minimal setup options:
- pyttsx3 (offline, no keys)
- gTTS (simple online, MP3)
- Edge TTS (optional online, MP3)
"""

import asyncio
import io
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
import json

from loguru import logger

from .config import Settings


class TTSBackend(ABC):
    """Abstract base class for TTS backends."""
    
    @abstractmethod
    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> bytes:
        """Synthesize speech from text and return audio bytes."""
        pass
    
    @abstractmethod
    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "en", voice: Optional[str] = None) -> bool:
        """Synthesize speech and save to file."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass
    
    @abstractmethod
    def get_available_voices(self, language: str = "en") -> List[str]:
        """Get list of available voices for language."""
        pass
    
    @abstractmethod
    def get_backend_type(self) -> str:
        """Return backend type (online/offline)."""
        pass


class Pyttsx3Backend(TTSBackend):
    """Offline TTS using pyttsx3 (no internet, no API keys)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None
        self._initialize()

    def _initialize(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            # Adjust rate/volume
            rate = self._engine.getProperty('rate')
            self._engine.setProperty('rate', int(rate * self.settings.tts.voice_speed))
            self._engine.setProperty('volume', float(self.settings.tts.voice_volume))
            logger.success("✅ pyttsx3 backend initialized")
        except Exception as e:
            logger.error(f"pyttsx3 init failed: {e}")
            self._engine = None

    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> bytes:
        if not self._engine:
            return b""
        try:
            # pyttsx3 outputs directly to speakers; for bytes, save to a WAV file via driver
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            self._engine.save_to_file(text, tmp_path)
            self._engine.runAndWait()
            with open(tmp_path, 'rb') as f:
                data = f.read()
            Path(tmp_path).unlink(missing_ok=True)
            return data
        except Exception as e:
            logger.error(f"pyttsx3 synth failed: {e}")
            return b""

    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "en", voice: Optional[str] = None) -> bool:
        if not self._engine:
            return False
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._engine.save_to_file(text, str(output_path))
            self._engine.runAndWait()
            return output_path.exists() and output_path.stat().st_size > 0
        except Exception as e:
            logger.error(f"pyttsx3 save failed: {e}")
            return False

    def is_available(self) -> bool:
        return self._engine is not None

    def get_available_voices(self, language: str = "en") -> List[str]:
        try:
            voices = []
            for v in self._engine.getProperty('voices'):
                voices.append(v.id)
            return voices
        except Exception:
            return []

    def get_backend_type(self) -> str:
        return "offline"

    def speak(self, text: str, language: str = "en", voice: Optional[str] = None) -> bool:
        """Speak directly using pyttsx3 without generating bytes/files."""
        if not self._engine:
            return False
        try:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"pyttsx3 speak failed: {e}")
            return False


class GTTSBackend(TTSBackend):
    """Simple online TTS using gTTS, returns MP3 bytes."""

    def __init__(self, settings: Settings):
        self.settings = settings
        try:
            from gtts import gTTS  # noqa: F401
            self._ok = True
            logger.success("✅ gTTS backend ready")
        except Exception as e:
            logger.error(f"gTTS import failed: {e}")
            self._ok = False

    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> bytes:
        if not self._ok:
            return b""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='ml' if language == 'ml' else 'en')
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp_path = tmp.name
            tts.save(tmp_path)
            with open(tmp_path, 'rb') as f:
                data = f.read()
            Path(tmp_path).unlink(missing_ok=True)
            return data
        except Exception as e:
            logger.error(f"gTTS synth failed: {e}")
            return b""

    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "en", voice: Optional[str] = None) -> bool:
        if not self._ok:
            return False
        try:
            from gtts import gTTS
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tts = gTTS(text=text, lang='ml' if language == 'ml' else 'en')
            tts.save(str(output_path))
            return output_path.exists() and output_path.stat().st_size > 0
        except Exception as e:
            logger.error(f"gTTS save failed: {e}")
            return False

    def is_available(self) -> bool:
        return self._ok

    def get_available_voices(self, language: str = "en") -> List[str]:
        return []

    def get_backend_type(self) -> str:
        return "online"


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS backend with multilingual support."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Edge TTS client."""
        try:
            import edge_tts
            self._client = edge_tts
            logger.success("✅ Edge TTS backend initialized successfully")
        except ImportError:
            logger.error("Edge TTS not available. Please install: pip install edge-tts")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Edge TTS: {e}")
            self._client = None
    
    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> bytes:
        """Synthesize speech using Edge TTS."""
        if not self._client:
            return b""
        
        try:
            # Select voice based on language
            if not voice:
                voice = self._get_default_voice(language)
            
            # Create Edge TTS communicate instance
            communicate = self._client.Communicate(text, voice)
            
            # Collect audio chunks
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            # Combine all chunks
            audio_data = b"".join(audio_chunks)
            logger.success(f"✅ Edge TTS synthesis completed: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Edge TTS synthesis failed: {e}")
            return b""
    
    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "en", voice: Optional[str] = None) -> bool:
        """Synthesize speech and save to file."""
        if not self._client:
            return False
        
        try:
            # Run async synthesis
            audio_data = asyncio.run(self.synthesize(text, language, voice))
            
            if audio_data:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                logger.success(f"✅ Audio saved to: {output_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            return False
    
    def _get_default_voice(self, language: str) -> str:
        """Get default voice for language."""
        voice_map = {
            "en": self.settings.tts.voice_en,
            "ml": self.settings.tts.voice_ml,
        }
        return voice_map.get(language, "en-IN-NeerjaNeural")
    
    def is_available(self) -> bool:
        """Check if Edge TTS is available."""
        return self._client is not None
    
    def get_available_voices(self, language: str = "en") -> List[str]:
        """Get available voices for language."""
        if not self._client:
            return []
        
        try:
            # Common voices for each language
            voice_lists = {
                "en": [
                    "en-IN-NeerjaNeural",  # Indian English Female
                    "en-IN-PrabhatNeural",  # Indian English Male
                    "en-US-JennyNeural",    # US English Female
                    "en-US-GuyNeural",      # US English Male
                    "en-GB-SoniaNeural",    # British English Female
                    "en-GB-RyanNeural",     # British English Male
                ],
                "ml": [
                    "ml-IN-SobhanaNeural",  # Malayalam Female
                    "ml-IN-MidhunNeural",   # Malayalam Male
                ],
            }
            return voice_lists.get(language, [])
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return []
    
    def get_backend_type(self) -> str:
        """Return backend type."""
        return "online"


## System/Realtime backends removed for simplicity (Edge-only)


class TTSEngine:
    """Main TTS engine with multiple backend support."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.backends: Dict[str, TTSBackend] = {}
        self.player = None
        
        # Initialize audio player
        self._initialize_player()
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_player(self):
        """Initialize pygame for audio playback."""
        try:
            # Import pygame lazily to avoid import-time errors if not installed
            import pygame  # type: ignore
            pygame.mixer.init(
                frequency=self.settings.tts.sample_rate,
                size=-16,
                channels=1,
                buffer=1024
            )
            self.player = pygame.mixer
            logger.success("✅ Audio player initialized")
        except Exception as e:
            logger.warning(f"Pygame mixer not available, will use backend direct playback when possible: {e}")
            self.player = None
    
    def _initialize_backends(self):
        """Initialize all available TTS backends."""
        # pyttsx3 (offline, default)
        pyttsx3_backend = Pyttsx3Backend(self.settings)
        if pyttsx3_backend.is_available():
            self.backends['pyttsx3'] = pyttsx3_backend
            logger.info("✅ pyttsx3 backend initialized")

        # gTTS (simple online)
        gtts_backend = GTTSBackend(self.settings)
        if gtts_backend.is_available():
            self.backends['gtts'] = gtts_backend
            logger.info("✅ gTTS backend initialized")

        # Edge TTS backend (online, multilingual, optional)
        edge_backend = EdgeTTSBackend(self.settings)
        if edge_backend.is_available():
            self.backends['edge'] = edge_backend
            logger.info("✅ Edge TTS backend initialized")
        if not self.backends:
            logger.error("❌ No TTS backends available!")
    
    def get_preferred_backend(self) -> Optional[TTSBackend]:
        """Get the preferred backend based on configuration."""
        preferred = self.settings.tts.preferred_engine
        if preferred in self.backends:
            return self.backends[preferred]
        # Fallback priority
        for backend_name in ['pyttsx3', 'gtts', 'edge']:
            if backend_name in self.backends:
                logger.warning(f"Preferred backend '{preferred}' not available, using '{backend_name}'")
                return self.backends[backend_name]
        
        return None
    
    async def synthesize_speech(self, text: str, language: str = "auto") -> Optional[bytes]:
        """Synthesize speech from text."""
        if not text.strip():
            logger.warning("Empty text provided for TTS")
            return None
        
        # Auto-detect language if needed
        if language == "auto":
            language = self._detect_language(text)
        
        backend = self.get_preferred_backend()
        if not backend:
            logger.error("No TTS backend available")
            return None
        
        try:
            logger.info(f"🔊 Synthesizing speech with {type(backend).__name__}")
            audio_data = await backend.synthesize(text, language)
            
            if audio_data:
                logger.success(f"✅ Speech synthesis completed: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error("Speech synthesis returned empty data")
                return None
                
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            return None
    
    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "auto") -> bool:
        """Synthesize speech and save to file."""
        if not text.strip():
            logger.warning("Empty text provided for TTS")
            return False
        
        # Auto-detect language if needed
        if language == "auto":
            language = self._detect_language(text)
        
        backend = self.get_preferred_backend()
        if not backend:
            logger.error("No TTS backend available")
            return False
        
        try:
            logger.info(f"🔊 Synthesizing speech to file with {type(backend).__name__}")
            success = backend.synthesize_to_file(text, output_path, language)
            
            if success:
                logger.success(f"✅ Speech saved to: {output_path}")
                return True
            else:
                logger.error("Failed to save speech to file")
                return False
                
        except Exception as e:
            logger.error(f"Speech synthesis to file failed: {e}")
            return False
    
    async def speak(self, text: str, language: str = "auto") -> bool:
        """Synthesize and immediately play speech."""
        backend = self.get_preferred_backend()
        # If backend can handle playback natively (pyttsx3), use it
        if backend and hasattr(backend, 'speak'):
            try:
                # type: ignore[attr-defined]
                return bool(backend.speak(text, language))
            except Exception as e:
                logger.error(f"Backend direct speak failed: {e}")
                # fall through to generic path

        audio_data = await self.synthesize_speech(text, language)
        
        if audio_data and self.player:
            try:
                # Save to temporary file based on content heuristics
                # Prefer MP3 for gTTS/Edge, WAV for pyttsx3
                is_mp3 = audio_data[:3] == b"ID3" or audio_data[:2] == b"\xff\xfb"
                suffix = '.mp3' if is_mp3 else '.wav'
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                
                # Play audio using music module for MP3, Sound for WAV
                try:
                    import pygame  # type: ignore
                except Exception as e:
                    logger.warning(f"Pygame not available for playback: {e}")
                    Path(tmp_path).unlink(missing_ok=True)
                    return True
                if suffix == '.mp3':
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                else:
                    sound = self.player.Sound(tmp_path)
                    sound.play()
                    while self.player.get_busy():
                        time.sleep(0.1)
                
                # Clean up
                Path(tmp_path).unlink(missing_ok=True)
                
                logger.success("✅ Speech playback completed")
                return True
                
            except Exception as e:
                logger.error(f"Speech playback failed: {e}")
                return False
        
        return False
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection for Malayalam vs English."""
        # Count Malayalam Unicode characters
        malayalam_chars = 0
        total_chars = len(text)
        
        for char in text:
            # Malayalam Unicode range: U+0D00–U+0D7F
            if 0x0D00 <= ord(char) <= 0x0D7F:
                malayalam_chars += 1
        
        # If more than 30% Malayalam characters, consider it Malayalam
        if total_chars > 0 and (malayalam_chars / total_chars) > 0.3:
            logger.info(f"Detected Malayalam text ({malayalam_chars}/{total_chars} Malayalam chars)")
            return "ml"
        else:
            logger.info(f"Detected English text ({malayalam_chars}/{total_chars} Malayalam chars)")
            return "en"
    
    def get_available_voices(self, language: str = "en") -> Dict[str, List[str]]:
        """Get available voices from all backends."""
        voices = {}
        
        for backend_name, backend in self.backends.items():
            try:
                backend_voices = backend.get_available_voices(language)
                if backend_voices:
                    voices[backend_name] = backend_voices
            except Exception as e:
                logger.error(f"Failed to get voices from {backend_name}: {e}")
        
        return voices
    
    def is_ready(self) -> bool:
        """Check if TTS engine is ready to use."""
        return len(self.backends) > 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status information."""
        status = {
            'ready': self.is_ready(),
            'enabled': self.settings.tts.enabled,
            'backends': list(self.backends.keys()),
            'preferred_backend': self.settings.tts.preferred_engine,
            'audio_player': self.player is not None,
            'available_voices': {},
        }
        
        # Get voices for each language
        for lang in ['en', 'ml']:
            status['available_voices'][lang] = self.get_available_voices(lang)
        
        return status
    
    def demo_tts(self, test_texts: Optional[Dict[str, str]] = None):
        """Run a TTS demonstration."""
        if not test_texts:
            test_texts = {
                'en': "Hello! This is a demonstration of the IEEE EPIC text-to-speech system.",
                'ml': "ഹലോ! ഇത് IEEE EPIC ടെക്സ്റ്റ് ടു സ്പീച്ച് സിസ്റ്റത്തിന്റെ പ്രദർശനമാണ്.",
            }
        
        logger.info("🎤 Starting TTS demonstration...")
        
        for lang, text in test_texts.items():
            logger.info(f"Testing {lang}: {text}")
            
            try:
                # Use asyncio to run the async function
                success = asyncio.run(self.speak(text, lang))
                
                if success:
                    logger.success(f"✅ {lang} TTS demo successful")
                else:
                    logger.error(f"❌ {lang} TTS demo failed")
                    
                # Small delay between demos
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ {lang} TTS demo error: {e}")


def get_tts_engine(settings: Optional[Settings] = None) -> TTSEngine:
    """Get a TTS engine instance."""
    return TTSEngine(settings)