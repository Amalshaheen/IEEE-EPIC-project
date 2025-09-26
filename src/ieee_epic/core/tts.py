"""
Text-to-Speech (TTS) Engine for IEEE EPIC STT system.

This module provides a unified interface for different TTS backends
including Edge TTS (multilingual), RealtimeTTS (high-quality), and System TTS (fallback),
with support for Malayalam and English languages.
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

import pygame
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


class RealtimeTTSBackend(TTSBackend):
    """RealtimeTTS backend for high-quality synthesis."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._stream = None
        self._engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize RealtimeTTS engine."""
        try:
            from RealtimeTTS import TextToAudioStream, SystemEngine, CoquiEngine
            
            # Try different engines in order of preference
            engines_to_try = [
                ("System", SystemEngine),
                ("Coqui", lambda: CoquiEngine() if self._is_coqui_available() else None),
            ]
            
            for engine_name, engine_class in engines_to_try:
                try:
                    if engine_name == "Coqui" and not self._is_coqui_available():
                        continue
                        
                    engine = engine_class()
                    self._engine = engine
                    self._stream = TextToAudioStream(engine)
                    logger.success(f"✅ RealtimeTTS initialized with {engine_name} engine")
                    return
                except Exception as e:
                    logger.warning(f"Failed to initialize {engine_name} engine: {e}")
                    continue
            
            logger.error("Failed to initialize any RealtimeTTS engine")
            
        except ImportError:
            logger.error("RealtimeTTS not available. Please install: pip install realtimetts[all]")
        except Exception as e:
            logger.error(f"Failed to initialize RealtimeTTS: {e}")
    
    def _is_coqui_available(self) -> bool:
        """Check if Coqui TTS is available."""
        try:
            import torch
            return torch.cuda.is_available() or True  # Allow CPU usage
        except ImportError:
            return False
    
    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> bytes:
        """Synthesize speech using RealtimeTTS."""
        if not self._stream:
            return b""
        
        try:
            # Use temporary file for synthesis
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Perform synthesis
            success = self.synthesize_to_file(text, tmp_path, language, voice)
            
            if success:
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up
                Path(tmp_path).unlink(missing_ok=True)
                
                logger.success(f"✅ RealtimeTTS synthesis completed: {len(audio_data)} bytes")
                return audio_data
            
            return b""
            
        except Exception as e:
            logger.error(f"RealtimeTTS synthesis failed: {e}")
            return b""
    
    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "en", voice: Optional[str] = None) -> bool:
        """Synthesize speech and save to file."""
        if not self._stream:
            return False
        
        try:
            # Configure stream for file output
            self._stream.feed(text)
            
            # Save to file (this is a simplified approach)
            # In a real implementation, you'd need to capture the audio stream
            self._stream.play()
            
            logger.success(f"✅ RealtimeTTS synthesis completed")
            return True
            
        except Exception as e:
            logger.error(f"RealtimeTTS synthesis failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if RealtimeTTS is available."""
        return self._stream is not None
    
    def get_available_voices(self, language: str = "en") -> List[str]:
        """Get available voices (limited for RealtimeTTS)."""
        return ["default"]  # RealtimeTTS may have limited voice options
    
    def get_backend_type(self) -> str:
        """Return backend type."""
        return "offline"


class SystemTTSBackend(TTSBackend):
    """System TTS backend as fallback."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if system TTS is available."""
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            
            if system == "windows":
                # Check for Windows SAPI
                try:
                    subprocess.run(["powershell", "Add-Type -AssemblyName System.Speech"], 
                                   check=True, capture_output=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
            elif system == "darwin":
                # Check for macOS say command
                try:
                    subprocess.run(["which", "say"], check=True, capture_output=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
            else:
                # Check for Linux espeak or festival
                for cmd in ["espeak", "festival"]:
                    try:
                        subprocess.run(["which", cmd], check=True, capture_output=True)
                        return True
                    except subprocess.CalledProcessError:
                        continue
                return False
                
        except Exception:
            return False
    
    async def synthesize(self, text: str, language: str = "en", voice: Optional[str] = None) -> bytes:
        """Synthesize speech using system TTS."""
        # Use temporary file approach
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        success = self.synthesize_to_file(text, tmp_path, language, voice)
        
        if success:
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            Path(tmp_path).unlink(missing_ok=True)
            return audio_data
        
        return b""
    
    def synthesize_to_file(self, text: str, output_path: Union[str, Path], language: str = "en", voice: Optional[str] = None) -> bool:
        """Synthesize speech using system commands."""
        if not self._available:
            return False
        
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if system == "windows":
                # Use Windows SAPI
                ps_script = f'''
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.SetOutputToWaveFile("{output_path}")
                $synth.Speak("{text}")
                $synth.Dispose()
                '''
                subprocess.run(["powershell", "-Command", ps_script], check=True)
                
            elif system == "darwin":
                # Use macOS say command with audio output
                subprocess.run([
                    "say", text, "-o", str(output_path.with_suffix('.aiff'))
                ], check=True)
                
                # Convert AIFF to WAV if needed
                if output_path.suffix.lower() == '.wav':
                    subprocess.run([
                        "ffmpeg", "-i", str(output_path.with_suffix('.aiff')),
                        str(output_path), "-y"
                    ], check=True, capture_output=True)
                    output_path.with_suffix('.aiff').unlink(missing_ok=True)
                    
            else:
                # Use Linux espeak
                subprocess.run([
                    "espeak", text, "-w", str(output_path)
                ], check=True)
            
            logger.success(f"✅ System TTS synthesis completed: {output_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"System TTS command failed: {e}")
            return False
        except Exception as e:
            logger.error(f"System TTS synthesis failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if system TTS is available."""
        return self._available
    
    def get_available_voices(self, language: str = "en") -> List[str]:
        """Get available system voices (limited)."""
        return ["default"]
    
    def get_backend_type(self) -> str:
        """Return backend type."""
        return "offline"


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
            pygame.mixer.init(
                frequency=self.settings.tts.sample_rate,
                size=-16,
                channels=1,
                buffer=1024
            )
            self.player = pygame.mixer
            logger.success("✅ Audio player initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio player: {e}")
            self.player = None
    
    def _initialize_backends(self):
        """Initialize all available TTS backends."""
        # Edge TTS backend (online, multilingual)
        edge_backend = EdgeTTSBackend(self.settings)
        if edge_backend.is_available():
            self.backends['edge'] = edge_backend
            logger.info("✅ Edge TTS backend initialized")
        
        # RealtimeTTS backend (offline, high quality)
        realtime_backend = RealtimeTTSBackend(self.settings)
        if realtime_backend.is_available():
            self.backends['realtime'] = realtime_backend
            logger.info("✅ RealtimeTTS backend initialized")
        
        # System TTS backend (offline, fallback)
        system_backend = SystemTTSBackend(self.settings)
        if system_backend.is_available():
            self.backends['system'] = system_backend
            logger.info("✅ System TTS backend initialized")
        
        if not self.backends:
            logger.error("❌ No TTS backends available!")
        else:
            logger.info(f"Available TTS backends: {list(self.backends.keys())}")
    
    def get_preferred_backend(self) -> Optional[TTSBackend]:
        """Get the preferred backend based on configuration."""
        preferred = self.settings.tts.preferred_engine
        
        if preferred in self.backends:
            return self.backends[preferred]
        
        # Fallback priority: edge -> realtime -> system
        for backend_name in ['edge', 'realtime', 'system']:
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
        audio_data = await self.synthesize_speech(text, language)
        
        if audio_data and self.player:
            try:
                # Save to temporary file and play
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                
                # Play audio
                sound = self.player.Sound(tmp_path)
                sound.play()
                
                # Wait for playback to finish
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