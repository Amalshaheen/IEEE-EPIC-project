"""
Speech-to-Text Engine for IEEE EPIC STT system.

This module provides a unified interface for different STT backends
including Vosk and Whisper, with language detection and optimization
for Raspberry Pi.
"""

import json
import queue
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union

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


class VoskSTTBackend(STTBackend):
    """Vosk STT backend implementation."""
    
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


class WhisperSTTBackend(STTBackend):
    """Whisper STT backend implementation."""
    
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


class AudioRecorder:
    """Audio recording utility with real-time processing."""
    
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
    """Main Speech-to-Text engine with multiple backend support."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.recorder = AudioRecorder(self.settings)
        self.backends: Dict[str, STTBackend] = {}
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize all available STT backends."""
        # Vosk backend
        vosk_backend = VoskSTTBackend(self.settings)
        if any(vosk_backend.is_available(lang) for lang in self.settings.models.supported_languages):
            self.backends['vosk'] = vosk_backend
            logger.info("✅ Vosk backend initialized")
        
        # Whisper backend
        whisper_backend = WhisperSTTBackend(self.settings)
        if whisper_backend.is_available():
            self.backends['whisper'] = whisper_backend
            logger.info("✅ Whisper backend initialized")
        
        if not self.backends:
            logger.error("❌ No STT backends available!")
    
    def recognize_from_audio(self, audio_data: np.ndarray, language: str = "auto") -> Dict[str, str]:
        """Recognize speech from audio data."""
        results = {}
        
        if language == "auto":
            # Try all supported languages
            languages_to_try = self.settings.models.supported_languages
        else:
            languages_to_try = [language]
        
        for lang in languages_to_try:
            # Try Vosk first (more efficient)
            if 'vosk' in self.backends and self.backends['vosk'].is_available(lang):
                text = self.backends['vosk'].recognize(audio_data, lang)
                if text:
                    results[f'{lang}_vosk'] = text
            
            # Try Whisper as fallback
            if 'whisper' in self.backends and not results:
                text = self.backends['whisper'].recognize(audio_data, lang)
                if text:
                    results[f'{lang}_whisper'] = text
        
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
    
    def get_best_result(self, results: Dict[str, str]) -> Optional[str]:
        """Get the best recognition result from multiple backends/languages."""
        if not results:
            return None
        
        # Priority order: English Vosk -> Malayalam Vosk -> Whisper results
        priority_order = ['en_vosk', 'ml_vosk', 'en_whisper', 'ml_whisper']
        
        for key in priority_order:
            if key in results and results[key].strip():
                return results[key].strip()
        
        # Return first non-empty result
        for text in results.values():
            if text.strip():
                return text.strip()
        
        return None
    
    def interactive_mode(self):
        """Run interactive speech recognition mode."""
        logger.info("🎤 Interactive Speech Recognition Mode")
        logger.info("Available languages: " + ", ".join(self.settings.models.supported_languages))
        logger.info("Commands: 'en' (English), 'ml' (Malayalam), 'auto', 'quit'")
        
        # List audio devices
        self.recorder.list_audio_devices()
        
        while True:
            try:
                command = input("\n📝 Enter command (en/ml/auto/quit): ").strip().lower()
                
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
            'languages': [],
            'models': {}
        }
        
        for lang in self.settings.models.supported_languages:
            available_backends = []
            for name, backend in self.backends.items():
                if backend.is_available(lang):
                    available_backends.append(name)
            
            if available_backends:
                status['languages'].append(lang)
                status['models'][lang] = available_backends
        
        return status