"""
Enhanced Speech-to-Text Engine for IEEE EPIC STT system.

This module provides a unified interface for different STT backends
including Vosk (offline), Whisper (offline), and Google Cloud Speech-to-Text (online),
with real-time streaming capabilities and optimizations for bilingual support.
"""

import io
import json
import queue
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union, Generator

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
    """Google Cloud Speech-to-Text backend implementation with streaming support."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._streaming_config = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Speech client."""
        try:
            from google.cloud import speech
            from google.api_core import client_options
            import os
            
            # Set up credentials if provided
            if self.settings.models.google_cloud_credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
                    self.settings.models.google_cloud_credentials
                )
            
            # Initialize client with optional regional endpoint
            self._client = speech.SpeechClient()
            
            logger.success("✅ Google Cloud Speech client initialized successfully")
            
        except ImportError:
            logger.error("Google Cloud Speech library not available. Please install: pip install google-cloud-speech")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Speech client: {e}")
    
    def recognize(self, audio_data: np.ndarray, language: str = "en") -> str:
        """Recognize speech using Google Cloud Speech-to-Text."""
        if not self._client:
            return ""
        
        try:
            from google.cloud import speech
            
            # Convert numpy array to audio content
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_content = audio_int16.tobytes()
            
            # Map language codes
            language_map = {
                "en": "en-US",
                "ml": "ml-IN",  # Malayalam (India)
                "auto": "en-US"  # Default to English for auto
            }
            language_code = language_map.get(language, "en-US")
            
            # Configure recognition request
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.settings.audio.sample_rate,
                language_code=language_code,
                model="latest_long",  # Use latest model for better accuracy
                use_enhanced=True,    # Enhanced model for better quality
                enable_automatic_punctuation=True,
                audio_channel_count=self.settings.audio.channels,
            )
            
            # Perform recognition
            response = self._client.recognize(config=config, audio=audio)
            
            # Extract best result
            for result in response.results:
                if result.alternatives:
                    transcript = result.alternatives[0].transcript.strip()
                    confidence = result.alternatives[0].confidence
                    logger.info(f"Recognition confidence: {confidence:.2f}")
                    return transcript
            
            return ""
            
        except Exception as e:
            logger.error(f"Google Cloud Speech recognition failed: {e}")
            return ""
    
    def stream_recognize(self, audio_generator: Generator[bytes, None, None], language: str = "en") -> Iterator[str]:
        """Perform streaming speech recognition."""
        if not self._client:
            return
        
        try:
            from google.cloud import speech
            
            # Map language codes
            language_map = {
                "en": "en-US",
                "ml": "ml-IN",
                "auto": "en-US"
            }
            language_code = language_map.get(language, "en-US")
            
            # Configure streaming recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.settings.audio.sample_rate,
                language_code=language_code,
                model="latest_long",
                use_enhanced=True,
                enable_automatic_punctuation=True,
                audio_channel_count=self.settings.audio.channels,
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True,
                single_utterance=False,
            )
            
            # Create streaming requests
            def request_generator():
                for chunk in audio_generator:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
            
            # Perform streaming recognition
            responses = self._client.streaming_recognize(
                config=streaming_config,
                requests=request_generator()
            )
            
            # Process responses
            for response in responses:
                if not response.results:
                    continue
                
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                transcript = result.alternatives[0].transcript
                
                if result.is_final:
                    logger.info(f"Final: {transcript}")
                    yield transcript
                else:
                    logger.debug(f"Interim: {transcript}")
                    # Optionally yield interim results
                    # yield f"[interim] {transcript}"
                    
        except Exception as e:
            logger.error(f"Streaming recognition failed: {e}")
    
    def is_available(self, language: str = "en") -> bool:
        """Check if Google Cloud Speech is available."""
        return self._client is not None
    
    def get_backend_type(self) -> str:
        """Return backend type."""
        return "online"


class VoskSTTBackend(STTBackend):
    """Enhanced Vosk STT backend implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._recognizers: Dict[str, any] = {}
        self._models: Dict[str, any] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Vosk models for available languages."""
        try:
            import vosk
        except ImportError:
            logger.error("Vosk not available. Please install: pip install vosk")
            return
        
        for lang in self.settings.models.supported_languages:
            model_path = self.settings.get_model_path(lang)
            
            if model_path and model_path.exists():
                try:
                    logger.info(f"Loading {lang} model from {model_path}")
                    model = vosk.Model(str(model_path))
                    recognizer = vosk.KaldiRecognizer(
                        model, 
                        self.settings.audio.sample_rate
                    )
                    recognizer.SetWords(True)
                    
                    self._models[lang] = model
                    self._recognizers[lang] = recognizer
                    logger.success(f"✅ {lang.upper()} model loaded successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to load {lang} model: {e}")
            else:
                logger.warning(f"Model not found for {lang}: {model_path}")
    
    def recognize(self, audio_data: np.ndarray, language: str = "en") -> str:
        """Recognize speech using Vosk."""
        if language not in self._recognizers:
            logger.error(f"No recognizer available for language: {language}")
            return ""
        
        try:
            recognizer = self._recognizers[language]
            
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            
            # Process audio
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
                return result.get('text', '').strip()
            else:
                partial_result = json.loads(recognizer.PartialResult())
                return partial_result.get('partial', '').strip()
                
        except Exception as e:
            logger.error(f"Vosk recognition failed: {e}")
            return ""
    
    def is_available(self, language: str = "en") -> bool:
        """Check if Vosk is available for language."""
        return language in self._recognizers
    
    def get_backend_type(self) -> str:
        """Return backend type."""
        return "offline"


class WhisperSTTBackend(STTBackend):
    """Enhanced Whisper STT backend implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Whisper model."""
        try:
            import whisper_cpp
            model_path = self.settings.models.whisper_model_path
            
            if model_path and model_path.exists():
                logger.info(f"Loading Whisper model from {model_path}")
                self._model = whisper_cpp.Whisper(str(model_path))
                logger.success("✅ Whisper model loaded successfully")
            else:
                logger.warning(f"Whisper model not found: {model_path}")
                
        except ImportError:
            logger.warning("whisper-cpp-python not available")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
    
    def recognize(self, audio_data: np.ndarray, language: str = "en") -> str:
        """Recognize speech using Whisper."""
        if not self._model:
            return ""
        
        try:
            # Whisper expects float32 audio
            audio_float32 = audio_data.astype(np.float32)
            
            # Transcribe
            result = self._model.transcribe(audio_float32)
            return result.get('text', '').strip()
            
        except Exception as e:
            logger.error(f"Whisper recognition failed: {e}")
            return ""
    
    def is_available(self, language: str = "en") -> bool:
        """Check if Whisper is available."""
        return self._model is not None
    
    def get_backend_type(self) -> str:
        """Return backend type."""
        return "offline"


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
    """Enhanced Speech-to-Text engine with multiple backend support and streaming."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.recorder = AudioRecorder(self.settings)
        self.backends: Dict[str, STTBackend] = {}
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize all available STT backends."""
        # Google Cloud backend (online)
        if self.settings.models.use_online_stt:
            google_backend = GoogleCloudSTTBackend(self.settings)
            if google_backend.is_available():
                self.backends['google_cloud'] = google_backend
                logger.info("✅ Google Cloud Speech backend initialized")
        
        # Vosk backend (offline)
        vosk_backend = VoskSTTBackend(self.settings)
        if any(vosk_backend.is_available(lang) for lang in self.settings.models.supported_languages):
            self.backends['vosk'] = vosk_backend
            logger.info("✅ Vosk backend initialized")
        
        # Whisper backend (offline)
        whisper_backend = WhisperSTTBackend(self.settings)
        if whisper_backend.is_available():
            self.backends['whisper'] = whisper_backend
            logger.info("✅ Whisper backend initialized")
        
        if not self.backends:
            logger.error("❌ No STT backends available!")
    
    def get_preferred_backend(self) -> Optional[STTBackend]:
        """Get the preferred backend based on configuration."""
        preferred = self.settings.models.preferred_backend
        
        if preferred in self.backends:
            return self.backends[preferred]
        
        # Fallback priority: online first if enabled, then offline
        if self.settings.models.use_online_stt and 'google_cloud' in self.backends:
            return self.backends['google_cloud']
        elif 'vosk' in self.backends:
            return self.backends['vosk']
        elif 'whisper' in self.backends:
            return self.backends['whisper']
        
        return None
    
    def recognize_from_audio(self, audio_data: np.ndarray, language: str = "auto") -> Dict[str, str]:
        """Recognize speech from audio data using preferred backend."""
        results = {}
        preferred_backend = self.get_preferred_backend()
        
        if not preferred_backend:
            logger.error("No preferred backend available")
            return results
        
        if language == "auto":
            languages_to_try = self.settings.models.supported_languages
        else:
            languages_to_try = [language]
        
        backend_name = self.settings.models.preferred_backend
        
        for lang in languages_to_try:
            if preferred_backend.is_available(lang):
                text = preferred_backend.recognize(audio_data, lang)
                if text:
                    results[f'{lang}_{backend_name}'] = text
                    logger.success(f"Recognition successful with {backend_name} ({lang}): {text}")
                    break
        
        # If preferred backend fails and it's online, try offline fallback
        if not results and preferred_backend.get_backend_type() == "online":
            logger.info("Online backend failed, trying offline fallback...")
            for backend_name, backend in self.backends.items():
                if backend.get_backend_type() == "offline":
                    for lang in languages_to_try:
                        if backend.is_available(lang):
                            text = backend.recognize(audio_data, lang)
                            if text:
                                results[f'{lang}_{backend_name}_fallback'] = text
                                logger.success(f"Fallback successful with {backend_name} ({lang}): {text}")
                                break
                    if results:
                        break
        
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
        preferred_backend = self.get_preferred_backend()
        
        if not preferred_backend:
            logger.error("No preferred backend available")
            return
        
        # Check if backend supports streaming
        if not isinstance(preferred_backend, GoogleCloudSTTBackend):
            logger.warning("Streaming only supported with Google Cloud backend")
            return
        
        try:
            self.recorder.is_recording = True
            audio_generator = self.recorder.stream_audio()
            
            logger.info("🎤 Starting streaming recognition...")
            yield from preferred_backend.stream_recognize(audio_generator, language)
            
        except KeyboardInterrupt:
            logger.info("Streaming recognition cancelled")
        except Exception as e:
            logger.error(f"Streaming recognition failed: {e}")
        finally:
            self.recorder.is_recording = False
    
    def get_best_result(self, results: Dict[str, str]) -> Optional[str]:
        """Get the best recognition result from multiple backends/languages."""
        if not results:
            return None
        
        # Priority order based on backend preference
        preferred = self.settings.models.preferred_backend
        priority_orders = {
            'google_cloud': [f'en_{preferred}', f'ml_{preferred}', 'en_vosk', 'ml_vosk'],
            'vosk': ['en_vosk', 'ml_vosk', f'en_{preferred}', f'ml_{preferred}'],
            'whisper': ['en_whisper', 'ml_whisper', 'en_vosk', 'ml_vosk']
        }
        
        priority_order = priority_orders.get(preferred, ['en_vosk', 'ml_vosk'])
        
        # Add fallback keys
        for key in list(results.keys()):
            if 'fallback' in key:
                priority_order.append(key)
        
        for key in priority_order:
            if key in results and results[key].strip():
                return results[key].strip()
        
        # Return first non-empty result
        for text in results.values():
            if text.strip():
                return text.strip()
        
        return None
    
    def interactive_mode(self):
        """Run interactive speech recognition mode with streaming support."""
        logger.info("🎤 Interactive Speech Recognition Mode")
        logger.info("Available languages: " + ", ".join(self.settings.models.supported_languages))
        logger.info("Commands: 'en' (English), 'ml' (Malayalam), 'auto', 'stream', 'quit'")
        logger.info(f"Current backend: {self.settings.models.preferred_backend}")
        logger.info(f"Online STT: {'enabled' if self.settings.models.use_online_stt else 'disabled'}")
        
        # List audio devices
        self.recorder.list_audio_devices()
        
        while True:
            try:
                command = input("\n📝 Enter command (en/ml/auto/stream/quit): ").strip().lower()
                
                if command == 'quit':
                    logger.info("👋 Goodbye!")
                    break
                elif command == 'stream':
                    if 'google_cloud' in self.backends:
                        logger.info("🌊 Starting streaming mode (press Ctrl+C to stop)...")
                        try:
                            for transcript in self.stream_recognize('auto'):
                                if transcript:
                                    logger.success(f"📝 Stream Result: {transcript}")
                        except KeyboardInterrupt:
                            logger.info("Streaming stopped by user")
                    else:
                        logger.warning("Streaming requires Google Cloud backend")
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
            'languages': [],
            'models': {}
        }
        
        for lang in self.settings.models.supported_languages:
            available_backends = []
            for name, backend in self.backends.items():
                if backend.is_available(lang):
                    backend_type = backend.get_backend_type()
                    available_backends.append(f"{name} ({backend_type})")
            
            if available_backends:
                status['languages'].append(lang)
                status['models'][lang] = available_backends
        
        return status