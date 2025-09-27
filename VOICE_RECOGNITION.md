# Voice Recognition Implementation for IEEE EPIC Project

This project now includes multiple voice recognition implementations supporting both Malayalam and English languages.

## 🎯 Available Implementations

### 1. Simple Voice Recognition (`simple_voice_recognition.py`)
A standalone GUI application with basic voice recognition features.

**Features:**
- Bilingual support (Malayalam & English)
- Simple tkinter GUI
- Real-time speech recognition
- Text-to-speech responses

**Usage:**
```bash
python simple_voice_recognition.py
```

### 2. Enhanced Voice Recognition (`enhanced_voice_recognition.py`)
An advanced GUI with better error handling and integration with the project structure.

**Features:**
- Language selection (auto/en/ml)
- Enhanced error handling
- Better GUI design
- Fallback support
- Help system

**Usage:**
```bash
python enhanced_voice_recognition.py
```

### 3. Core Modules Integration
Modular components that can be integrated into the existing project.

**Modules:**
- `src/ieee_epic/core/simple_stt.py` - Simple Speech-to-Text
- `src/ieee_epic/core/simple_tts.py` - Simple Text-to-Speech

## 📋 Requirements

### System Requirements
- Python 3.8+
- Microphone access
- Audio output capability

### Python Packages
Install the required packages:

```bash
pip install -r requirements.txt
```

### System Audio Players
Install at least one audio player:

**Ubuntu/Debian:**
```bash
sudo apt-get install mpg123
# or
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install mpg123
# or
brew install ffmpeg
```

**Windows:**
- Install VLC or use Windows Media Player

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install SpeechRecognition gTTS
   ```

2. **Test microphone:**
   ```python
   import speech_recognition as sr
   r = sr.Recognizer()
   with sr.Microphone() as source:
       print("Say something!")
       audio = r.listen(source)
   try:
       print("You said: " + r.recognize_google(audio))
   except:
       print("Could not understand audio")
   ```

3. **Run the simple interface:**
   ```bash
   python simple_voice_recognition.py
   ```

4. **Or run the enhanced interface:**
   ```bash
   python enhanced_voice_recognition.py
   ```

## 🎛️ Language Support

### Supported Languages
- **English (en)**: English recognition and TTS
- **Malayalam (ml)**: Malayalam recognition and TTS
- **Auto**: Automatic detection (tries Malayalam first, then English)

### Language Codes
- `en` - English
- `ml` - Malayalam (മലയാളം)
- `auto` - Automatic detection

## 🔧 Configuration

### Speech Recognition Settings
- **Timeout**: 5 seconds (configurable)
- **Phrase Time Limit**: 10 seconds (configurable)
- **Language Priority**: Malayalam → English (for auto mode)

### Text-to-Speech Settings
- **Speed**: Normal (can be set to slow)
- **Voice**: Google TTS voices
- **Audio Format**: MP3

## 🛠️ Integration with Existing Project

The voice recognition can be integrated with the existing IEEE EPIC project:

```python
from ieee_epic.core.simple_stt import SimpleSpeechRecognizer
from ieee_epic.core.simple_tts import SimpleTextToSpeech

# Initialize
stt = SimpleSpeechRecognizer()
tts = SimpleTextToSpeech()

# Listen and recognize
text, language = stt.listen_and_recognize()
if text:
    print(f"Recognized ({language}): {text}")
    
    # Respond
    response = f"You said: {text}"
    tts.speak(response, language)
```

## 🎯 Features

### Voice Recognition Features
- ✅ Bilingual support (Malayalam & English)
- ✅ Automatic language detection
- ✅ Noise adaptation
- ✅ Timeout handling
- ✅ Error recovery

### GUI Features
- ✅ Real-time conversation display
- ✅ Status indicators
- ✅ Language selection
- ✅ Clear conversation history
- ✅ Help system
- ✅ Responsive design

### TTS Features
- ✅ Multiple audio player support
- ✅ Temporary file cleanup
- ✅ Error handling
- ✅ Language-specific voices

## 🐛 Troubleshooting

### Common Issues

1. **"Import speech_recognition could not be resolved"**
   ```bash
   pip install SpeechRecognition
   ```

2. **"No audio players available"**
   ```bash
   # Ubuntu
   sudo apt-get install mpg123
   
   # macOS  
   brew install mpg123
   
   # Windows - install VLC
   ```

3. **"Microphone not working"**
   - Check microphone permissions
   - Test with other applications
   - Try different microphone devices

4. **"Could not understand audio"**
   - Speak clearly and loudly
   - Reduce background noise
   - Check internet connection (uses Google API)
   - Try different language settings

5. **"Recognition service error"**
   - Check internet connection
   - Google Speech API may be temporarily unavailable
   - Try again after a few minutes

### Debug Mode
Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📡 API Usage

The recognition uses Google's free Speech Recognition API, which:
- Requires internet connection
- Has usage limits
- Supports multiple languages
- Provides good accuracy

## 🔒 Privacy Notes

- Audio is sent to Google for processing
- No audio data is stored locally
- Temporary files are automatically cleaned up
- Consider offline alternatives for sensitive applications

## 🤝 Contributing

To contribute to the voice recognition features:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This implementation follows the same license as the main IEEE EPIC project.

## 🆘 Support

For issues related to voice recognition:
1. Check this README for troubleshooting
2. Review the logs for error messages
3. Test with the simple implementation first
4. Create an issue with detailed error information

---

## Example Usage Code

### Basic Recognition
```python
from ieee_epic.core.simple_stt import listen_and_recognize_auto

text, language = listen_and_recognize_auto()
if text:
    print(f"You said ({language}): {text}")
```

### Basic TTS
```python
from ieee_epic.core.simple_tts import speak_text

speak_text("Hello World", "en")
speak_text("നമസ്കാരം", "ml")
```

### GUI Application
```python
from enhanced_voice_recognition import EnhancedVoiceRecognitionGUI

app = EnhancedVoiceRecognitionGUI()
app.run()
```