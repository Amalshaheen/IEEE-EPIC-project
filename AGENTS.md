
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
