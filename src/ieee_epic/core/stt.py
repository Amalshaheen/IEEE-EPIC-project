"""
Online Speech-to-Text Engine for IEEE EPIC system.

This module provides a simplified, online-only STT engine using
Google Cloud Speech-to-Text with bilingual (English/Malayalam) support.
"""

import io
import json
import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional, Generator

import numpy as np
import sounddevice as sd
from loguru import logger

from .config import Settings


class STTBackend(ABC):
    """Abstract base class for STT backends."""
    
    @abstractmethod
    def recognize(self, audio_data: np.ndarray, language: str = "en") -> str:
        """Recognize speech from audio data."""
        pass
    
    @abstractmethod
    def is_available(self, language: str = "en") -> bool:
        """Check if backend is available for specified language."""
        pass
    
    @abstractmethod
    def get_backend_type(self) -> str:
        """Return backend type (offline/online)."""
        pass


class GoogleCloudSTTBackend(STTBackend):
    """Google Cloud Speech-to-Text backend (online)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            from google.cloud import speech
            self._speech = speech
            self._client = speech.SpeechClient()
            logger.success("✅ Google Cloud Speech client initialized")
        except ImportError:
            logger.error("google-cloud-speech not installed. Run: pip install google-cloud-speech")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Speech client: {e}")
            self._client = None

    def recognize(self, audio_data: np.ndarray, language: str = "auto") -> str:
        if not self._client:
            return ""

        try:
            # Convert float32 [-1,1] to int16 bytes
            audio_int16 = (audio_data * 32767).astype(np.int16)
            content = audio_int16.tobytes()

            primary = self.settings.models.google_primary_language
            alternatives = self.settings.models.google_alternative_languages

            config = self._speech.RecognitionConfig(
                encoding=self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.settings.audio.sample_rate,
                language_code=primary,
                alternative_language_codes=alternatives,
                enable_automatic_punctuation=self.settings.models.enable_automatic_punctuation,
            )

            audio = self._speech.RecognitionAudio(content=content)
            response = self._client.recognize(config=config, audio=audio)

            for result in response.results:
                if result.alternatives:
                    transcript = result.alternatives[0].transcript.strip()
                    if transcript:
                        return transcript
            return ""
        except Exception as e:
            logger.error(f"Google STT recognize failed: {e}")
            return ""

    def is_available(self, language: str = "en") -> bool:
        return self._client is not None

    def get_backend_type(self) -> str:
        return "online"


## Offline backends removed for simplicity (online-only)


class AudioRecorder:
    """Enhanced audio recording utility with streaming support."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_recording = False
        self._audio_queue = queue.Queue()
        self._recording_thread = None
    
    def _audio_callback(self, indata, frames, time, status):
        """Audio input callback."""
        if status:
            logger.warning(f"Audio status: {status}")
        
        if self.is_recording:
            self._audio_queue.put(indata.copy())
    
    def record_audio(self, duration: Optional[float] = None) -> np.ndarray:
        """Record audio for specified duration."""
        duration = duration or self.settings.audio.duration
        
        logger.info(f"🎤 Recording for {duration} seconds...")
        
        try:
            with sd.InputStream(
                device=self.settings.audio.device_id,
                channels=self.settings.audio.channels,
                samplerate=self.settings.audio.sample_rate,
                callback=self._audio_callback,
                dtype=np.float32
            ):
                self.is_recording = True
                
                # Collect audio data
                audio_chunks = []
                start_time = time.time()
                
                while time.time() - start_time < duration:
                    try:
                        chunk = self._audio_queue.get(timeout=0.1)
                        audio_chunks.append(chunk)
                    except queue.Empty:
                        continue
                
                self.is_recording = False
                
                if audio_chunks:
                    audio_data = np.concatenate(audio_chunks, axis=0)
                    if self.settings.audio.channels == 2:
                        # Convert stereo to mono
                        audio_data = np.mean(audio_data, axis=1)
                    else:
                        audio_data = audio_data.flatten()
                    
                    logger.info("✅ Recording completed")
                    return audio_data
                else:
                    logger.warning("No audio data captured")
                    return np.array([])
                    
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return np.array([])
        finally:
            self.is_recording = False
    
    def stream_audio(self) -> Generator[bytes, None, None]:
        """Stream audio in real-time chunks for streaming recognition."""
        try:
            with sd.InputStream(
                device=self.settings.audio.device_id,
                channels=self.settings.audio.channels,
                samplerate=self.settings.audio.sample_rate,
                dtype=np.float32,
                blocksize=1024,  # Small chunks for streaming
            ) as stream:
                logger.info("🎤 Starting audio streaming...")
                
                while self.is_recording:
                    audio_chunk, overflowed = stream.read(1024)
                    if overflowed:
                        logger.warning("Audio buffer overflowed")
                    
                    if audio_chunk.size > 0:
                        # Convert to mono if stereo
                        if self.settings.audio.channels == 2:
                            audio_chunk = np.mean(audio_chunk, axis=1)
                        
                        # Convert to 16-bit PCM bytes
                        audio_int16 = (audio_chunk.flatten() * 32767).astype(np.int16)
                        yield audio_int16.tobytes()
                    
        except Exception as e:
            logger.error(f"Audio streaming failed: {e}")
        finally:
            self.is_recording = False
    
    def list_audio_devices(self):
        """List available audio devices."""
        try:
            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for i, device in enumerate(devices):
                device_type = "🎤" if device['max_input_channels'] > 0 else "🔊"
                logger.info(f"  {i}: {device_type} {device['name']}")
            return devices
        except Exception as e:
            logger.error(f"Failed to list audio devices: {e}")
            return []


class STTEngine:
    """Online-only Speech-to-Text engine using Google Cloud Speech."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.recorder = AudioRecorder(self.settings)
        self.backends: Dict[str, STTBackend] = {}
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize Google Cloud STT backend."""
        if self.settings.models.use_online_stt:
            google_backend = GoogleCloudSTTBackend(self.settings)
            if google_backend.is_available():
                self.backends['google'] = google_backend
                logger.info("✅ Google Cloud STT backend initialized")
        if not self.backends:
            logger.error("❌ No online STT backend available! Check credentials.")
    
    def get_preferred_backend(self) -> Optional[STTBackend]:
        """Get the preferred backend based on configuration."""
        preferred = self.settings.models.preferred_backend
        return self.backends.get(preferred)
    
    def recognize_from_audio(self, audio_data: np.ndarray, language: str = "auto") -> Dict[str, str]:
        """Recognize speech from audio data using preferred backend."""
        results = {}
        preferred_backend = self.get_preferred_backend()
        
        if not preferred_backend:
            logger.error("No preferred backend available")
            return results
        
        # Always try auto with Google backend; let API detect language
        lang_key = (language if language in ['en', 'ml'] else 'auto')
        text = preferred_backend.recognize(audio_data, lang_key)
        if text:
            results[f'{lang_key}_google'] = text
        return results
    
    def recognize_speech(self, duration: Optional[float] = None, language: str = "auto") -> Dict[str, str]:
        """Record audio and recognize speech."""
        try:
            audio_data = self.recorder.record_audio(duration)
            
            if len(audio_data) == 0:
                logger.warning("No audio recorded")
                return {}
            
            logger.info("🧠 Processing speech...")
            results = self.recognize_from_audio(audio_data, language)
            
            if results:
                logger.success(f"Recognition completed: {len(results)} results")
            else:
                logger.warning("No speech recognized")
            
            return results
            
        except KeyboardInterrupt:
            logger.info("Recognition cancelled by user")
            return {}
        except Exception as e:
            logger.error(f"Recognition failed: {e}")
            return {}
    
    def stream_recognize(self, language: str = "auto") -> Iterator[str]:
        """Perform streaming speech recognition."""
        logger.warning("Streaming recognition not implemented for Google backend in this build")
        return
    
    def get_best_result(self, results: Dict[str, str]) -> Optional[str]:
        """Get the best recognition result from multiple backends/languages."""
        if not results:
            return None
        
        # With single backend, just return the first non-empty
        for text in results.values():
            if text and text.strip():
                return text.strip()
        return None
    
    def interactive_mode(self):
        """Run interactive speech recognition mode with streaming support."""
        logger.info("🎤 Interactive Speech Recognition Mode (Google Cloud)")
        logger.info("Commands: 'en' (English), 'ml' (Malayalam), 'auto', 'quit'")
        logger.info(f"Backend: {self.settings.models.preferred_backend}")
        
        # List audio devices
        self.recorder.list_audio_devices()
        
        while True:
            try:
                command = input("\n📝 Enter command (en/ml/auto/stream/quit): ").strip().lower()
                
                if command == 'quit':
                    logger.info("👋 Goodbye!")
                    break
                elif command in ['en', 'ml', 'auto']:
                    results = self.recognize_speech(language=command)
                    
                    if results:
                        logger.info("🎯 Recognition Results:")
                        for key, text in results.items():
                            logger.info(f"  {key}: {text}")
                        
                        best_result = self.get_best_result(results)
                        if best_result:
                            logger.success(f"📝 Best Result: {best_result}")
                    else:
                        logger.warning("❌ No speech detected")
                else:
                    logger.warning("❌ Invalid command")
                    
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def is_ready(self) -> bool:
        """Check if STT engine is ready to use."""
        return len(self.backends) > 0
    
    def get_status(self) -> Dict[str, any]:
        """Get detailed status information."""
        status = {
            'ready': self.is_ready(),
            'backends': list(self.backends.keys()),
            'preferred_backend': self.settings.models.preferred_backend,
            'online_enabled': self.settings.models.use_online_stt,
        }
        return status