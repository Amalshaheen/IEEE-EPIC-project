# IEEE EPIC Project - Offline Speech-to-Text System

## 🎯 Overview
This project implements an offline Speech-to-Text (STT) system using Vosk models for Malayalam and English languages, designed to run on Raspberry Pi without internet connectivity.

## 🍓 **NEW: Raspberry Pi Optimized Setup Available!**
- **Quick Setup**: `./setup_rpi.sh` - Complete automated RPi setup
- **Interactive STT**: `python3 rpi_stt.py` - RPi-optimized speech recognition
- **Audio Testing**: `python3 test_audio.py` - Test microphone setup
- **Documentation**: See `README_RPi.md` for detailed RPi instructions

## ✅ Setup Complete
- ✅ Python virtual environment configured
- ✅ Required packages installed (vosk, sounddevice)
- ✅ English STT model downloaded and configured
- ✅ Audio input devices detected and working
- ✅ Raspberry Pi optimization scripts added
- ✅ Malayalam language support integrated

## 📁 Project Structure
```
IEEE-EPIC-project/
├── main.py              # Enhanced main entry point with RPi detection
├── stt_test.py          # Original STT testing script
├── rpi_stt.py           # NEW: RPi-optimized STT with Malayalam support
├── setup_rpi.sh         # NEW: Complete automated RPi setup script
├── rpi_setup.py         # NEW: Python-based RPi setup
├── test_audio.py        # NEW: Audio testing utility
├── test_setup.py        # Setup verification script
├── requirements.txt     # Updated Python dependencies
├── README_RPi.md        # NEW: Comprehensive RPi documentation
├── vosk-en/            # English STT model
├── vosk-ml/            # Malayalam STT model (downloaded by setup)
├── models/             # Model storage directory
├── whisper.cpp/        # Optional: Whisper.cpp for better performance
└── .venv/              # Python virtual environment
```

## 🚀 Usage

### Raspberry Pi (Recommended)
```bash
# First time setup
./setup_rpi.sh

# Interactive Malayalam/English STT
python3 rpi_stt.py

# Test audio setup
python3 test_audio.py
```

### General Usage
```bash
# Enhanced main interface (detects RPi automatically)
python3 main.py

# Original STT test
python3 stt_test.py

# Verify setup
python3 test_setup.py
```

### Virtual Environment Usage
```bash
# Using the configured virtual environment
cd /home/amal-shaheen/Documents/IEEE-EPIC-project
/home/amal-shaheen/Documents/IEEE-EPIC-project/.venv/bin/python main.py
```

## 🎤 How It Works
1. **Multilingual Support**: Malayalam and English speech recognition
2. **Auto Language Detection**: Automatically detects spoken language
3. **Offline Processing**: All speech recognition happens locally
4. **Real-time Audio**: Uses sounddevice for live microphone input
5. **RPi Optimized**: Memory and CPU optimized for Raspberry Pi
6. **Robust Error Handling**: Graceful fallbacks and error reporting

## 📋 Current Status
- ✅ English STT model: Working (Small model for RPi efficiency)
- ✅ Malayalam STT model: Setup script downloads if available
- ✅ Audio input: Functional with auto-configuration
- ✅ Dependencies: All required packages included
- ✅ Raspberry Pi: Fully optimized and tested
- ✅ Interactive Mode: User-friendly speech recognition interface

## 🔧 Malayalam Support
- **Automatic Download**: Setup script attempts to download Malayalam Vosk model
- **Whisper Integration**: Fallback to Whisper.cpp for Malayalam if Vosk unavailable
- **Manual Setup**: Instructions provided for custom Malayalam models

## 🎮 Controls
- **Interactive Mode**: Choose language (ml/en/auto) or quit
- **Auto Detection**: Tries both languages and returns best result
- **Stop Early**: Press Ctrl+C to interrupt
- **Audio Duration**: Configurable (default 5 seconds)

## 🔊 Audio Requirements
- Microphone access (USB microphone recommended for RPi)
- 16kHz sample rate (handled automatically)
- Mono channel recording
- Audio group permissions (handled by setup script)

## 🍓 Raspberry Pi Features
- **Memory Optimized**: Uses lightweight models
- **Auto Setup**: Complete system configuration
- **Service Mode**: Can run as background service
- **Performance Monitoring**: Built-in resource checking
- **Audio Troubleshooting**: Comprehensive audio testing

## 🎁 Next Steps
- ✅ Offline Malayalam speech recognition
- ✅ Raspberry Pi optimization complete
- 🔄 Ready for TTS (Text-to-Speech) integration
- 🔄 Web API interface for remote access
- 🔄 Home Assistant integration examples

## 🤝 Contributing
This project is part of the IEEE EPIC initiative for educational purposes. Contributions welcome!

## 📄 License
Educational use under IEEE EPIC project guidelines.
Ready for offline TTS (Text-to-Speech) integration for complete conversational AI system!