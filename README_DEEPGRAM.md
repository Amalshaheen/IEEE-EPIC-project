# Deepgram STT Integration Guide

## Overview

IEEE EPIC project has been enhanced with **Deepgram Speech-to-Text** integration, providing reliable online STT capabilities with real-time streaming support. Deepgram offers superior accuracy, low latency, and extensive language support compared to other cloud STT services.

## Key Features

### 🎯 **High-Performance STT**
- **Nova-2 Model**: State-of-the-art accuracy with enhanced punctuation and formatting
- **Real-time Streaming**: WebSocket-based live transcription with minimal latency  
- **Multiple Models**: Choose from nova-2, nova, enhanced, base, or whisper models
- **Smart Formatting**: Automatic punctuation, capitalization, and number formatting

### 🌐 **Language Support**
- **Primary**: English (en-US) with excellent accuracy
- **Bilingual**: English-India (en-IN) for Malayalam content recognition
- **Auto-detection**: Intelligent language switching
- **Extensible**: Easy to add more language codes

### 🔄 **Intelligent Fallbacks**
- **Online → Offline**: Automatic fallback to Vosk/Whisper if Deepgram unavailable
- **Error Recovery**: Graceful handling of network issues and API limits
- **Backend Selection**: Smart preference ordering with fallback chains

## Configuration

### Environment Variables
```bash
# Required for Deepgram functionality
export DEEPGRAM_API_KEY="your_deepgram_api_key_here"
```

### Settings Configuration
```python
# In config.py or environment
IEEE_EPIC__MODELS__USE_ONLINE_STT=true
IEEE_EPIC__MODELS__PREFERRED_BACKEND="deepgram"
IEEE_EPIC__MODELS__DEEPGRAM_MODEL="nova-2"
IEEE_EPIC__MODELS__DEEPGRAM_LANGUAGE="en-US"
IEEE_EPIC__MODELS__ENABLE_STREAMING=true
```

### Programmatic Configuration
```python
from ieee_epic.core.config import Settings

settings = Settings()
settings.models.use_online_stt = True
settings.models.preferred_backend = "deepgram"
settings.models.deepgram_api_key = "your_api_key"
settings.models.deepgram_model = "nova-2"
settings.models.deepgram_language = "en-US"
settings.models.enable_streaming = True
```

## Installation

### Install Dependencies
```bash
# Install Deepgram SDK and WebSocket support
pip install deepgram-sdk>=3.0.0 websockets>=11.0

# Or install all project dependencies
pip install -e .
```

### Verify Installation
```bash
python test_deepgram_stt.py
```

## Usage Examples

### Basic Speech Recognition
```python
from ieee_epic.core.config import Settings
from ieee_epic.core.stt import STTEngine

# Configure for Deepgram
settings = Settings()
settings.models.use_online_stt = True
settings.models.preferred_backend = "deepgram"
settings.models.deepgram_api_key = "your_api_key"

# Create engine
engine = STTEngine(settings)

# Recognize speech from microphone
results = engine.recognize_speech(duration=5.0, language='en')
best_result = engine.get_best_result(results)
print(f"Transcription: {best_result}")
```

### Real-time Streaming STT
```python
# Start streaming recognition
for transcript in engine.stream_recognize(language='en'):
    print(f"Live: {transcript}")
```

### CLI Commands
```bash
# Enable online STT with Deepgram
ieee-epic stt --online --backend deepgram

# Real-time streaming mode
ieee-epic stream --language en

# Interactive mode with Deepgram
ieee-epic interactive --online
```

## API Models Comparison

| Model | Description | Best For | Latency |
|-------|-------------|----------|---------|
| `nova-2` | Latest enhanced model | General transcription | Low |
| `nova` | Previous enhanced model | Good accuracy | Low |
| `enhanced` | Higher accuracy model | Business/professional | Medium |
| `base` | Cost-effective option | Basic transcription | Low |
| `whisper` | OpenAI Whisper-based | Academic/research | Medium |

**Recommended**: `nova-2` for best balance of accuracy and speed.

## Language Codes

| Language | Code | Support Level |
|----------|------|---------------|
| English (US) | `en-US` | ⭐⭐⭐⭐⭐ Full |
| English (India) | `en-IN` | ⭐⭐⭐⭐ Good for Malayalam |
| English (UK) | `en-GB` | ⭐⭐⭐⭐⭐ Full |

## Streaming Architecture

### WebSocket Connection Flow
```
Client → Deepgram WebSocket → Real-time Results
   ↑                               ↓
Audio Stream ←------ Transcripts ←--
```

### Implementation Details
```python
# Async WebSocket streaming with event handlers
async def on_message(self, result, **kwargs):
    if result.is_final:
        yield result.channel.alternatives[0].transcript

# Threading for sync compatibility
def stream_recognize(audio_generator):
    # Run async streaming in thread
    # Queue results for sync access
```

## Error Handling

### Graceful Fallbacks
1. **Network Issues**: Automatic retry with exponential backoff
2. **API Limits**: Switch to offline backends (Vosk → Whisper)
3. **Authentication Errors**: Clear error messages with setup guidance
4. **Audio Issues**: Device detection and alternative suggestions

### Common Error Codes
```python
# Authentication
"Invalid API key" → Check DEEPGRAM_API_KEY environment variable

# Network 
"Connection timeout" → Falling back to offline STT

# Audio
"Unsupported format" → Check sample rate and encoding settings
```

## Performance Optimization

### Audio Settings
```python
# Optimized for Deepgram
settings.audio.sample_rate = 16000  # Supported: 8000-48000
settings.audio.channels = 1         # Mono recommended
settings.audio.duration = 5.0       # Chunk size for batch processing
```

### Streaming Settings
```python
# Real-time optimization
options = LiveOptions(
    interim_results=True,     # Get partial results
    smart_format=True,        # Auto punctuation
    punctuate=True,          # Enhanced formatting
    model="nova-2"           # Latest model
)
```

## Cost Considerations

### Pricing Estimates (as of 2024)
- **Pay-per-use**: ~$0.0125 per minute of audio
- **Streaming**: Same rate as batch processing
- **Free Tier**: Available for testing and development

### Cost Optimization Tips
1. **Batch Processing**: Use prerecorded API for non-real-time needs
2. **Model Selection**: `base` model for cost-sensitive applications  
3. **Audio Quality**: Higher quality audio = better accuracy = fewer retries
4. **Chunking**: Optimize audio chunk sizes to minimize API calls

## Testing

### Automated Testing
```bash
# Run comprehensive test suite
python test_deepgram_stt.py

# Test with your API key
export DEEPGRAM_API_KEY="your_key"
python test_deepgram_stt.py
```

### Manual Testing
```bash
# Quick CLI test
ieee-epic demo --backend deepgram

# Interactive testing
ieee-epic interactive --online
```

### Test Coverage
- ✅ Configuration validation
- ✅ Backend initialization  
- ✅ Audio recording
- ✅ API connectivity
- ✅ Real-time streaming
- ✅ Error handling
- ✅ Fallback mechanisms

## Troubleshooting

### Common Issues

**1. "Deepgram SDK not available"**
```bash
pip install deepgram-sdk>=3.0.0
```

**2. "API key not provided"**
```bash
export DEEPGRAM_API_KEY="your_api_key_here"
# Or set in configuration file
```

**3. "Streaming not working"**
```bash
pip install websockets>=11.0
# Ensure firewall allows WebSocket connections
```

**4. "No audio detected"**
```bash
# Check audio devices
ieee-epic status
# Test audio recording
python test_deepgram_stt.py
```

### Debug Mode
```bash
# Enable verbose logging
IEEE_EPIC__SYSTEM__LOG_LEVEL=DEBUG ieee-epic interactive
```

## Migration from Google Cloud

### Automatic Migration
- Configuration automatically maps from Google Cloud settings
- Existing audio processing pipeline unchanged
- Fallback mechanisms preserved

### Key Differences
| Feature | Google Cloud | Deepgram |
|---------|-------------|----------|
| Setup | Complex credentials | Simple API key |
| Latency | Medium | Low |
| Models | Limited selection | Multiple options |
| Streaming | Complex setup | Built-in WebSocket |
| Cost | Higher | More affordable |

### Migration Steps
1. ✅ Remove Google Cloud dependencies
2. ✅ Install Deepgram SDK  
3. ✅ Update configuration
4. ✅ Test functionality
5. ✅ Deploy new backend

## Future Enhancements

### Planned Features
- **Multi-language Detection**: Automatic language switching during streaming
- **Custom Vocabulary**: Domain-specific terminology support
- **Speaker Diarization**: Multi-speaker identification
- **Confidence Thresholds**: Adaptive quality-based fallbacks

### Integration Roadmap
- **AssemblyAI**: Alternative online STT provider
- **Azure Speech**: Enterprise integration option
- **Custom Models**: Training with IEEE EPIC specific vocabulary
- **Offline Deepgram**: Local model deployment options

## Support

### Documentation
- [Deepgram Python SDK](https://developers.deepgram.com/docs/python-sdk)
- [WebSocket Streaming](https://developers.deepgram.com/docs/streaming)
- [Model Comparison](https://developers.deepgram.com/docs/model)

### Community
- GitHub Issues: Report bugs and feature requests
- IEEE EPIC Discord: Community support and discussions
- Deepgram Community: Technical deep-dives and best practices

---

**Deepgram Integration Status**: ✅ **Production Ready**

*This integration provides enterprise-grade speech recognition capabilities while maintaining the simplicity and reliability that IEEE EPIC users expect.*