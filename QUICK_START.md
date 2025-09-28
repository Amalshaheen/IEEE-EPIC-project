# Quick Start - IEEE EPIC Voice Assistant

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

```bash
python enhanced_voice_recognition.py
```

## Sample Questions

**English:**
- "How do I create a Python function?"
- "What is React?"
- "Explain machine learning"

**Malayalam:**
- "പൈത്തൺ എന്താണ്?"
- "റിയാക്റ്റ് എങ്ങനെ ഉപയോഗിക്കാം?"

## Troubleshooting

- **No AI**: Set `GOOGLE_API_KEY`
- **No microphone**: Check connections, try `alsamixer`
- **No audio**: Install `mpg123` or `ffmpeg`