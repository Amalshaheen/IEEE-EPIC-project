
## Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Tkinter
sudo apt-get install python3-tk

# Install Python packages
pip install -r requirements.txt

# Set API key
export GOOGLE_API_KEY="your-key"

# Run setup (optional)
chmod +x ./setup_config.sh
./setup_config.sh
```

## Run

### Option 1: Original Handshake Only
```bash
python handshake_voice_ai.py
```

### Option 2: Both Handshake AND Wake Word (Recommended)
```bash
python fixed_dual_activation_ai.py
```

### Option 3: Wake Word Only
```bash
python wake_word_detector.py
```

## Wake Words
- "Hey SARAS"
- "Hello SARAS" 
- "SARAS"

## Features
- 🤝 **Handshake Detection**: Wave near proximity sensor
- 🎯 **Wake Word Activation**: Voice activation with "Hey SARAS"
- 🎤 **Manual Chat**: Button-based conversation
- 🤖 **AI Responses**: Powered by Google Gemini
- 🌐 **Bilingual**: English and Malayalam support
