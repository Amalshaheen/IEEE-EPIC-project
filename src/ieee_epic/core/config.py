"""
Configuration management for IEEE EPIC STT system.

This module uses Pydantic for type validation and settings management,
following modern Python configuration best practices.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from loguru import logger


class AudioSettings(BaseModel):
    """Audio configuration settings."""
    
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    duration: float = Field(default=5.0, description="Recording duration in seconds")
    device_id: Optional[int] = Field(default=None, description="Audio device ID")
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        if v not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError("Sample rate must be one of: 8000, 16000, 22050, 44100, 48000")
        return v
    
    @validator('channels')
    def validate_channels(cls, v):
        if v not in [1, 2]:
            raise ValueError("Channels must be 1 (mono) or 2 (stereo)")
        return v


class ModelSettings(BaseModel):
    """Online-only STT configuration settings (Google Cloud Speech)."""

    # Language preferences
    default_language: str = Field(default="auto", description="Default language (en/ml/auto)")
    supported_languages: List[str] = Field(default=["en", "ml"], description="Supported languages")

    # Online STT preferences
    use_online_stt: bool = Field(default=True, description="Enable online STT services")
    preferred_backend: str = Field(default="google", description="Preferred STT backend (google)")

    # Google Cloud Speech settings
    google_primary_language: str = Field(default="en-IN", description="Primary language code for recognition")
    google_alternative_languages: List[str] = Field(default_factory=lambda: ["ml-IN", "en-US"], description="Alternative language codes")
    enable_automatic_punctuation: bool = Field(default=True, description="Enable automatic punctuation in transcripts")

    @validator('default_language')
    def validate_default_language(cls, v, values):
        supported = values.get('supported_languages', ['en', 'ml'])
        if v not in supported + ['auto']:
            raise ValueError(f"Default language must be one of: {supported + ['auto']}")
        return v
    
    @validator('preferred_backend')
    def validate_preferred_backend(cls, v):
        valid_backends = ['google']
        if v not in valid_backends:
            raise ValueError(f"Preferred backend must be one of: {valid_backends}")
        return v


class TTSSettings(BaseModel):
    """Text-to-Speech configuration settings."""
    
    enabled: bool = Field(default=True, description="Enable TTS functionality")
    preferred_engine: str = Field(default="pyttsx3", description="Preferred TTS engine (pyttsx3/gtts/edge)")
    
    # Voice settings
    voice_en: str = Field(default="en-IN-NeerjaNeural", description="English voice (Indian accent)")
    voice_ml: str = Field(default="ml-IN-SobhanaNeural", description="Malayalam voice")
    voice_speed: float = Field(default=1.0, description="Speech speed (0.5-2.0)")
    voice_volume: float = Field(default=0.8, description="Voice volume (0.0-1.0)")
    
    # Audio output settings
    output_format: str = Field(default="wav", description="Audio output format (wav/mp3)")
    sample_rate: int = Field(default=22050, description="Audio sample rate")
    
    # Edge TTS specific settings
    edge_voice_quality: str = Field(default="high", description="Edge TTS quality (low/medium/high)")
    edge_pitch: str = Field(default="0Hz", description="Voice pitch adjustment")
    edge_rate: str = Field(default="0%", description="Speech rate adjustment")
    
    # RealtimeTTS settings  
    realtime_chunk_size: int = Field(default=1024, description="Audio chunk size for streaming")
    realtime_buffer_size: int = Field(default=4096, description="Audio buffer size")
    
    @validator('voice_speed')
    def validate_voice_speed(cls, v):
        if not 0.1 <= v <= 3.0:
            raise ValueError("Voice speed must be between 0.1 and 3.0")
        return v
    
    @validator('voice_volume') 
    def validate_voice_volume(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Voice volume must be between 0.0 and 1.0")
        return v
    
    @validator('preferred_engine')
    def validate_preferred_engine(cls, v):
        valid_engines = ['pyttsx3', 'gtts', 'edge']
        if v not in valid_engines:
            raise ValueError(f"Preferred engine must be one of: {valid_engines}")
        return v


class AISettings(BaseModel):
    """AI response system configuration."""
    
    enabled: bool = Field(default=True, description="Enable AI responses")
    gemini_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        description="Google Gemini API key"
    )
    model: str = Field(default="gemini-2.0-flash-001", description="Gemini model to use")
    max_tokens: int = Field(default=150, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, description="AI response creativity")
    
    # System instruction for bilingual support
    system_instruction: str = Field(
        default=(
            "You are a friendly tutor for lower/primary school students. "
            "Answer in a simple, age-appropriate way with short sentences. "
            "Use easy words and clear examples. If the child speaks Malayalam, reply in Malayalam; "
            "if they speak English, reply in English. Be kind, encouraging, and brief."
            "do not use emojis in your response."
        ),
        description="System instruction for the AI model"
    )
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @validator('model')
    def validate_model(cls, v):
        valid_models = [
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-002", 
            "gemini-1.5-flash-001",
            "gemini-1.5-pro-001"
        ]
        if v not in valid_models:
            logger.warning(f"Unknown model: {v}. Using default.")
            return "gemini-2.0-flash-001"
        return v


class SystemSettings(BaseModel):
    """System and platform configuration."""
    
    # Platform detection
    platform: Optional[str] = Field(default=None, description="Platform (auto-detected)")
    is_raspberry_pi: bool = Field(default=False, description="Running on Raspberry Pi")
    
    # Performance settings
    memory_limit_mb: int = Field(default=512, description="Memory limit in MB")
    cpu_threads: int = Field(default=1, description="Number of CPU threads to use")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Log file path")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class PathSettings(BaseModel):
    """File and directory path configuration."""
    
    project_root: Path = Field(default=Path.cwd(), description="Project root directory")
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    models_dir: Path = Field(default=Path("models"), description="Models directory")
    logs_dir: Path = Field(default=Path("logs"), description="Logs directory")
    temp_dir: Path = Field(default=Path("temp"), description="Temporary files directory")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all directories exist."""
        for path in [self.data_dir, self.models_dir, self.logs_dir, self.temp_dir]:
            if not path.is_absolute():
                path = self.project_root / path
            path.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    """Main configuration class for IEEE EPIC STT system."""
    
    # Nested settings
    audio: AudioSettings = Field(default_factory=AudioSettings)
    models: ModelSettings = Field(default_factory=ModelSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    ai: AISettings = Field(default_factory=AISettings)
    system: SystemSettings = Field(default_factory=SystemSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    
    # Application metadata
    app_name: str = Field(default="IEEE EPIC STT", description="Application name")
    version: str = Field(default="0.2.0", description="Application version")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False
        
    def __init__(self, **data):
        super().__init__(**data)
        self._detect_platform()
        self._setup_logging()
    
    def _detect_platform(self):
        """Auto-detect platform and configure accordingly."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    self.system.is_raspberry_pi = True
                    self.system.platform = "raspberry_pi"
                    # Optimize for RPi
                    self.system.memory_limit_mb = 256
                    self.system.cpu_threads = 1
        except FileNotFoundError:
            # Not on Linux/RPi
            self.system.platform = "desktop"
            self.system.memory_limit_mb = 1024
            self.system.cpu_threads = 2
    
    def _setup_logging(self):
        """Configure logging based on settings."""
        logger.remove()  # Remove default handler
        
        # Console logging
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level=self.system.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True
        )
        
        # File logging if specified
        if self.system.log_file:
            if not self.system.log_file.is_absolute():
                log_path = self.paths.logs_dir / self.system.log_file
            else:
                log_path = self.system.log_file
                
            logger.add(
                sink=str(log_path),
                level=self.system.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation="10 MB",
                retention="1 week",
                compression="zip"
            )
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> "Settings":
        """Load settings from a TOML or JSON file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return cls()
        
        try:
            if config_path.suffix.lower() == '.toml':
                import tomli
                with open(config_path, 'rb') as f:
                    data = tomli.load(f)
            elif config_path.suffix.lower() == '.json':
                import json
                with open(config_path, 'r') as f:
                    data = json.load(f)
            else:
                logger.error(f"Unsupported config format: {config_path.suffix}")
                return cls()
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return cls()
    
    def save_to_file(self, config_path: Union[str, Path]) -> bool:
        """Save current settings to a file."""
        config_path = Path(config_path)
        
        try:
            config_data = self.dict()
            
            if config_path.suffix.lower() == '.json':
                import json
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=2, default=str)
            elif config_path.suffix.lower() == '.toml':
                import tomli_w
                with open(config_path, 'wb') as f:
                    tomli_w.dump(config_data, f)
            else:
                logger.error(f"Unsupported config format: {config_path.suffix}")
                return False
            
            logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False
    
    def get_model_path(self, language: str) -> Optional[Path]:
        """Deprecated: offline model paths removed in online-only mode."""
        logger.warning("get_model_path is deprecated in online-only mode")
        return None
    
    def is_model_available(self, language: str) -> bool:
        """Always True for online STT (no local models needed)."""
        return True


# Default settings instance
default_settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance."""
    return default_settings

def update_settings(**kwargs) -> Settings:
    """Update global settings with new values."""
    global default_settings
    data = default_settings.dict()
    data.update(kwargs)
    default_settings = Settings(**data)
    return default_settings