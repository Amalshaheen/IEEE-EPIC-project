# IEEE EPIC Project - Offline Speech-to-Text System

## 🎯 Overview
This project implements an offline Speech-to-Text (STT) system using Vosk models for Malayalam and English languages, designed to run on Raspberry Pi without internet connectivity.

## ✅ Setup Complete
- ✅ Python virtual environment configured
- ✅ Required packages installed (vosk, sounddevice)
- ✅ English STT model downloaded and configured
- ✅ Audio input devices detected and working

## 📁 Project Structure
```
IEEE-EPIC-project/
├── main.py              # Main entry point
├── stt_test.py          # STT testing script
├── test_setup.py        # Setup verification script
├── requirements.txt     # Python dependencies
├── vosk-en/            # English STT model
└── .venv/              # Python virtual environment
```

## 🚀 Usage

### Quick Test
```bash
cd /home/amal-shaheen/Documents/IEEE-EPIC-project
/home/amal-shaheen/Documents/IEEE-EPIC-project/.venv/bin/python main.py
```

### Direct STT Test
```bash
/home/amal-shaheen/Documents/IEEE-EPIC-project/.venv/bin/python stt_test.py
```

### Verify Setup
```bash
/home/amal-shaheen/Documents/IEEE-EPIC-project/.venv/bin/python test_setup.py
```

## 🎤 How It Works
1. **Bilingual Support**: First tries Malayalam (if model available), then falls back to English
2. **Offline Processing**: All speech recognition happens locally
3. **Real-time Audio**: Uses sounddevice for live microphone input
4. **Robust Error Handling**: Graceful fallbacks and error reporting

## 📋 Current Status
- ✅ English STT model: Working
- ⚠️  Malayalam STT model: Not available (will need to find correct model URL)
- ✅ Audio input: Functional
- ✅ Dependencies: Installed

## 🔧 Adding Malayalam Support
To add Malayalam support later, download the correct Malayalam model and extract it to `vosk-ml/` directory.

## 🎮 Controls
- **Start Recognition**: Run the script and speak when prompted
- **Stop Early**: Press Ctrl+C to interrupt
- **Audio Duration**: Default 6 seconds for Malayalam, 6 seconds for English fallback

## 🔊 Audio Requirements
- Microphone access required
- 16kHz sample rate (handled automatically)
- Mono channel recording

## 🎁 Next Steps
Ready for offline TTS (Text-to-Speech) integration for complete conversational AI system!