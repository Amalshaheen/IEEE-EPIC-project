# Online STT Migration Guide

## Overview

The IEEE EPIC STT system has been successfully migrated to support online Speech-to-Text services alongside the existing offline capabilities. This migration adds Google Cloud Speech-to-Text integration with real-time streaming support while maintaining full backward compatibility.

## New Features

### 🌐 Online STT Support
- **Google Cloud Speech-to-Text**: High-accuracy cloud-based recognition
- **Real-time streaming**: Continuous speech recognition with live transcription
- **Enhanced accuracy**: Leverages Google's latest speech models
- **Bilingual support**: Optimized for both English and Malayalam

### 🔄 Intelligent Backend Selection
- **Preferred backend configuration**: Choose between offline (Vosk/Whisper) and online (Google Cloud)
- **Automatic fallback**: Falls back to offline backends if online service is unavailable
- **Smart language detection**: Automatically selects appropriate language models

### 📡 Streaming Recognition
- **Real-time transcription**: Live speech-to-text with interim results
- **Low latency**: Optimized for real-time applications
- **Continuous listening**: Stream audio indefinitely until stopped

## Configuration

### Basic Configuration

Create a configuration file (`config.json`) or use environment variables:

```json
{
  "models": {
    "use_online_stt": true,
    "preferred_backend": "google_cloud",
    "google_cloud_credentials": "/path/to/credentials.json",
    "supported_languages": ["en", "ml"]
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1
  }
}
```

### Environment Variables

Set up authentication and preferences:

```bash
# Google Cloud authentication
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Backend preferences
export IEEE_EPIC__MODELS__USE_ONLINE_STT=true
export IEEE_EPIC__MODELS__PREFERRED_BACKEND="google_cloud"
```

### Google Cloud Setup

1. **Create a Google Cloud Project**
2. **Enable Speech-to-Text API**
3. **Create a Service Account**
4. **Download credentials JSON file**
5. **Set GOOGLE_APPLICATION_CREDENTIALS environment variable**

## Usage Examples

### Command Line Interface

#### Basic Speech Recognition
```bash
# Use default offline backend (Vosk)
ieee-epic stt --lang en --duration 5

# Use online backend with config
ieee-epic stt --config config.json --lang auto

# Real-time streaming (requires Google Cloud)
ieee-epic stream --lang en
```

#### Interactive Mode
```bash
# Interactive mode with streaming support
ieee-epic interactive

# Available commands in interactive mode:
# - 'en' / 'ml' / 'auto': Single recognition
# - 'stream': Start streaming mode
# - 'quit': Exit
```

#### System Status
```bash
# Check system status and available backends
ieee-epic status --config config.json
```

### Python API

#### Basic Recognition
```python
from ieee_epic.core.config import Settings
from ieee_epic.core.stt import STTEngine

# Configure for online STT
settings = Settings()
settings.models.use_online_stt = True
settings.models.preferred_backend = "google_cloud"

# Initialize engine
engine = STTEngine(settings)

# Single recognition
results = engine.recognize_speech(language="en")
best_result = engine.get_best_result(results)
print(f"Recognized: {best_result}")
```

#### Streaming Recognition
```python
# Real-time streaming
for transcript in engine.stream_recognize(language="auto"):
    print(f"Live: {transcript}")
```

## Backend Comparison

| Feature | Vosk (Offline) | Whisper (Offline) | Google Cloud (Online) |
|---------|----------------|-------------------|----------------------|
| **Accuracy** | Good | Excellent | Excellent |
| **Speed** | Fast | Moderate | Fast |
| **Languages** | Limited | Many | 120+ |
| **Internet** | Not required | Not required | Required |
| **Streaming** | No | No | **Yes** |
| **Cost** | Free | Free | Pay-per-use |
| **Privacy** | Local | Local | Cloud-based |

## Migration Benefits

### ✅ Improved Accuracy
- Google Cloud Speech-to-Text provides state-of-the-art accuracy
- Enhanced punctuation and formatting
- Better handling of noisy environments

### ✅ Real-time Capabilities
- Streaming recognition for live applications
- Interim results for immediate feedback
- Continuous transcription support

### ✅ Scalability
- Cloud-based processing eliminates local resource constraints
- Automatic scaling based on demand
- No local model storage requirements

### ✅ Multilingual Support
- Support for 120+ languages and dialects
- Automatic language detection
- Regional accent recognition

## Backward Compatibility

The migration maintains full backward compatibility:

- **Existing offline backends** (Vosk, Whisper) continue to work
- **Configuration format** remains the same with optional new fields
- **API interface** unchanged - existing code works without modification
- **Graceful fallback** to offline backends when online services unavailable

## Performance Considerations

### Online STT (Google Cloud)
- **Pros**: Higher accuracy, real-time streaming, no local storage
- **Cons**: Requires internet connection, pay-per-use pricing
- **Best for**: Production applications, real-time transcription

### Offline STT (Vosk/Whisper)  
- **Pros**: No internet required, free, private
- **Cons**: Lower accuracy, larger storage requirements
- **Best for**: Development, offline environments, privacy-sensitive applications

## Security and Privacy

### Online Processing
- Audio data sent to Google Cloud for processing
- Subject to Google Cloud privacy policies
- Consider data residency requirements

### Offline Processing
- All processing happens locally
- No data leaves your system
- Full privacy control

## Troubleshooting

### Common Issues

#### "Google Cloud client not available"
```bash
pip install google-cloud-speech
```

#### "Authentication failed"
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

#### "No backends available"
- Check if models are installed for offline backends
- Verify Google Cloud credentials for online backend
- Run `ieee-epic status` to diagnose issues

### Debug Mode
```bash
# Enable debug logging
export IEEE_EPIC__SYSTEM__LOG_LEVEL=DEBUG
ieee-epic status
```

## Migration Checklist

- [ ] Install Google Cloud Speech library: `pip install google-cloud-speech`
- [ ] Set up Google Cloud project and credentials
- [ ] Update configuration to enable online STT
- [ ] Test basic recognition: `ieee-epic stt --config config.json`
- [ ] Test streaming: `ieee-epic stream`
- [ ] Verify fallback behavior by disabling internet
- [ ] Update application code to use new streaming features

## Future Enhancements

- Azure Speech Services integration
- AWS Transcribe support  
- Custom model training
- Voice activity detection
- Speaker diarization
- Confidence scoring

## Support

For issues and questions:
- Check system status: `ieee-epic status`
- Enable debug logging: `IEEE_EPIC__SYSTEM__LOG_LEVEL=DEBUG`
- Review logs in `logs/` directory
- Consult Google Cloud Speech documentation for API issues

This migration provides a robust foundation for both offline and online speech recognition, enabling the IEEE EPIC system to scale from development to production environments while maintaining flexibility and reliability.