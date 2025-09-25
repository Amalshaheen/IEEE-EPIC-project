"""
Test configuration and settings functionality.
"""

import pytest
import tempfile
from pathlib import Path

from ieee_epic.core.config import Settings, AudioSettings, ModelSettings, AISettings


class TestAudioSettings:
    """Test audio configuration settings."""
    
    def test_default_values(self):
        """Test default audio settings."""
        audio = AudioSettings()
        assert audio.sample_rate == 16000
        assert audio.channels == 1
        assert audio.duration == 5.0
        assert audio.device_id is None
    
    def test_sample_rate_validation(self):
        """Test sample rate validation."""
        with pytest.raises(ValueError, match="Sample rate must be one of"):
            AudioSettings(sample_rate=12000)
    
    def test_channels_validation(self):
        """Test channels validation."""
        with pytest.raises(ValueError, match="Channels must be 1"):
            AudioSettings(channels=3)


class TestModelSettings:
    """Test model configuration settings."""
    
    def test_default_values(self):
        """Test default model settings."""
        models = ModelSettings()
        assert models.default_language == "en"
        assert "en" in models.supported_languages
        assert "ml" in models.supported_languages
        assert models.english_model_path == Path("vosk-en")
        assert models.malayalam_model_path == Path("vosk-ml")
    
    def test_language_validation(self):
        """Test language validation."""
        with pytest.raises(ValueError, match="Default language must be one of"):
            ModelSettings(default_language="fr", supported_languages=["en", "ml"])


class TestAISettings:
    """Test AI configuration settings."""
    
    def test_default_values(self):
        """Test default AI settings."""
        ai = AISettings()
        assert ai.enabled is True
        assert ai.model == "gpt-3.5-turbo"
        assert ai.temperature == 0.7
        assert ai.offline_mode is True
    
    def test_temperature_validation(self):
        """Test temperature validation."""
        with pytest.raises(ValueError, match="Temperature must be between"):
            AISettings(temperature=3.0)


class TestSettings:
    """Test main settings class."""
    
    def test_default_initialization(self):
        """Test default settings initialization."""
        settings = Settings()
        
        assert isinstance(settings.audio, AudioSettings)
        assert isinstance(settings.models, ModelSettings)
        assert isinstance(settings.ai, AISettings)
        assert settings.app_name == "IEEE EPIC STT"
        assert settings.version == "0.2.0"
    
    def test_get_model_path(self):
        """Test model path retrieval."""
        settings = Settings()
        
        en_path = settings.get_model_path("en")
        assert en_path == Path("vosk-en")
        
        ml_path = settings.get_model_path("ml")
        assert ml_path == Path("vosk-ml")
        
        unknown_path = settings.get_model_path("fr")
        assert unknown_path is None
    
    def test_is_model_available(self):
        """Test model availability checking."""
        settings = Settings()
        
        # Models won't exist in test environment
        assert settings.is_model_available("en") is False
        assert settings.is_model_available("ml") is False
    
    def test_save_and_load_config(self):
        """Test configuration save and load."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
            config_path = Path(tmp_file.name)
        
        try:
            # Create and save settings
            original_settings = Settings()
            original_settings.audio.duration = 10.0
            original_settings.ai.temperature = 0.5
            
            success = original_settings.save_to_file(config_path)
            assert success is True
            
            # Load settings
            loaded_settings = Settings.load_from_file(config_path)
            
            assert loaded_settings.audio.duration == 10.0
            assert loaded_settings.ai.temperature == 0.5
            
        finally:
            if config_path.exists():
                config_path.unlink()
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration file."""
        nonexistent_path = Path("nonexistent_config.json")
        settings = Settings.load_from_file(nonexistent_path)
        
        # Should return default settings
        assert isinstance(settings, Settings)
        assert settings.audio.duration == 5.0  # Default value


@pytest.fixture
def sample_settings():
    """Fixture providing sample settings for testing."""
    return Settings(
        audio=AudioSettings(duration=3.0),
        ai=AISettings(temperature=0.3, offline_mode=False)
    )