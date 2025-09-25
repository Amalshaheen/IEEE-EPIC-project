# Malayalam Voice Recognition for Raspberry Pi

This project provides **offline Malayalam speech recognition** optimized for Raspberry Pi, supporting both Malayalam and English languages.

## 🎯 Features

- **Offline Processing**: No internet connection required
- **Malayalam Support**: Dedicated Malayalam speech recognition
- **Raspberry Pi Optimized**: Efficient memory and CPU usage
- **Multiple Backends**: Supports Vosk and Whisper.cpp
- **Real-time Recognition**: Interactive speech-to-text
- **Auto Language Detection**: Automatically detect Malayalam vs English

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the complete setup script
./setup_rpi.sh
```

### Option 2: Manual Setup
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install system dependencies
sudo apt install -y python3-pip python3-pyaudio portaudio19-dev alsa-utils pulseaudio ffmpeg

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Run the Python setup
python3 rpi_setup.py
```

## 📋 System Requirements

### Minimum Requirements
- **Hardware**: Raspberry Pi 3B+ or newer
- **RAM**: 1GB (2GB+ recommended)
- **Storage**: 2GB free space for models
- **Audio**: USB microphone or HAT with microphone

### Recommended Requirements
- **Hardware**: Raspberry Pi 4B (4GB RAM)
- **Storage**: 4GB free space
- **Audio**: High-quality USB microphone

## 🎤 Usage

### 1. Test Audio Setup
```bash
python3 test_audio.py
```

### 2. Interactive Speech Recognition
```bash
python3 rpi_stt.py
```

### 3. Original Interface
```bash
python3 main.py
```

## 🗣️ Commands

In interactive mode (`rpi_stt.py`):
- `ml` or `malayalam` - Malayalam speech recognition
- `en` or `english` - English speech recognition  
- `auto` - Auto-detect language
- `quit` - Exit

## 📁 Project Structure

```
IEEE-EPIC-project/
├── main.py                 # Original main script
├── stt_test.py            # Speech recognition test
├── rpi_stt.py             # RPi-optimized STT script
├── rpi_setup.py           # Python setup script
├── setup_rpi.sh           # Bash setup script
├── test_audio.py          # Audio testing utility
├── requirements.txt       # Python dependencies
├── models/                # Downloaded model files
├── vosk-en/              # English Vosk model
├── vosk-ml/              # Malayalam Vosk model (if available)
└── whisper.cpp/          # Whisper.cpp (optional)
```

## 🔧 Troubleshooting

### Audio Issues
```bash
# Check audio devices
python3 test_audio.py

# Check ALSA mixer
alsamixer

# Add user to audio group (then reboot)
sudo usermod -a -G audio $USER
```

### Model Issues
```bash
# Check if models exist
ls -la vosk-*

# Re-download models
python3 rpi_setup.py
```

### Performance Issues
```bash
# Check system resources
htop

# Use smaller model for English
# Edit script to use 'vosk-model-small-en-us-0.15'

# Enable GPU memory split (for RPi 4)
sudo raspi-config
# Advanced Options > Memory Split > 128
```

### Malayalam Model
The Malayalam model availability depends on the Vosk model repository. If not available:

1. **Alternative Sources**: Check other Malayalam ASR model repositories
2. **Whisper Alternative**: Use Whisper.cpp with multilingual model
3. **Custom Training**: Train your own model with Malayalam data

### Whisper.cpp Setup (Better Performance)
```bash
cd whisper.cpp
./models/download-ggml-model.sh small
./build/bin/whisper-cli -m models/ggml-small.bin -l ml -f audio.wav
```

## 📊 Performance Optimization

### For Raspberry Pi 3B+
- Use `vosk-model-small-en-us-0.15` (English)
- Limit recording duration to 5-10 seconds
- Close unnecessary applications

### For Raspberry Pi 4B
- Can handle medium-sized models
- Enable longer recording sessions
- Consider running as background service

### Memory Management
```bash
# Check memory usage
free -h

# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🔄 Service Mode (Optional)

Run as background service:
```bash
# Enable service
sudo systemctl enable malayalam-stt

# Start service
sudo systemctl start malayalam-stt

# Check status
sudo systemctl status malayalam-stt
```

## 📱 Integration Examples

### Home Assistant Integration
```python
# Add to Home Assistant configuration.yaml
shell_command:
  malayalam_stt: "cd /home/pi/IEEE-EPIC-project && python3 rpi_stt.py --single-shot"
```

### API Server
```python
# Create simple Flask API
from flask import Flask, request, jsonify
from rpi_stt import RPiSpeechRecognizer

app = Flask(__name__)
recognizer = RPiSpeechRecognizer()

@app.route('/recognize', methods=['POST'])
def recognize():
    # Handle audio upload and return transcription
    pass
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Test on actual Raspberry Pi hardware
4. Submit pull request

## 📄 License

This project is part of the IEEE EPIC initiative for educational purposes.

## 🔗 Resources

- [Vosk Models](https://alphacephei.com/vosk/models)
- [Whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [Raspberry Pi Audio Guide](https://www.raspberrypi.org/documentation/configuration/audio-config.md)
- [Malayalam Language Resources](https://github.com/AI4Bharat)

---

**Note**: This setup is optimized for Raspberry Pi but should work on other ARM-based systems with minimal modifications.