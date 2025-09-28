# Handshake Voice AI Assistant

This project integrates a proximity sensor as a handshake detector with your voice recognition AI system. When someone waves their hand near the sensor, the AI starts a conversation.

## Files Created

1. **`handshake_voice_ai.py`** - Full GUI version with all features
2. **`simple_handshake_ai.py`** - Command-line version optimized for Raspberry Pi

## Hardware Setup

### Proximity Sensor Connection
Connect your IR proximity sensor to the Raspberry Pi:
- **VCC** → 5V or 3.3V power pin
- **GND** → Ground pin
- **OUT** → GPIO pin 17 (or modify the pin number in code)

### Sensor Behavior
- **LOW (0)** signal = Object detected (handshake)
- **HIGH (1)** signal = No object detected

## Software Setup

### Prerequisites
Make sure you have completed the basic setup from `AGENTS.md`:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set your Google API key
export GOOGLE_API_KEY="your-gemini-api-key"
```

### Additional Raspberry Pi Setup
```bash
# Install GPIO library (Raspberry Pi only)
pip install RPi.GPIO

# Enable GPIO access (may be required)
sudo usermod -a -G gpio $USER
```

## Usage

### Option 1: Full GUI Version
```bash
python handshake_voice_ai.py
```

Features:
- Complete graphical interface
- Manual conversation mode
- Sensor control buttons
- Conversation history
- Status indicators
- Help system

### Option 2: Simple Command-Line Version (Recommended for Pi)
```bash
python simple_handshake_ai.py
```

Features:
- Lightweight command-line interface
- Optimized for Raspberry Pi
- Auto-starts handshake detection
- Fallback manual mode if GPIO unavailable

## How It Works

### Handshake Detection Flow
1. **Sensor Monitoring**: System continuously monitors GPIO pin 17
2. **Detection**: When sensor detects an object (LOW signal), it triggers handshake event
3. **Debouncing**: Prevents multiple triggers (2-second minimum between detections)
4. **Greeting**: AI speaks a random greeting message
5. **Conversation**: System listens for user response and generates AI replies
6. **Continuation**: Conversation continues until user says goodbye or max turns reached
7. **Reset**: System returns to monitoring mode, ready for next handshake

### Conversation Features
- **Bilingual Support**: English and Malayalam recognition and responses
- **AI Intelligence**: Uses Google Gemini for smart responses
- **Context Awareness**: Maintains conversation context
- **Natural Ending**: Detects goodbye phrases to end conversations gracefully
- **Fallback Responses**: Works even without AI API configured

## Configuration

### GPIO Pin Configuration
To use a different GPIO pin, modify the pin number:

```python
# In handshake_voice_ai.py
self.proximity_sensor = ProximitySensor(pin=18)  # Change from 17 to 18

# In simple_handshake_ai.py
self.handshake_detector = HandshakeDetector(pin=18)  # Change from 17 to 18
```

### Language Settings
Both versions support language selection:
- **auto**: Automatic detection (tries Malayalam first, then English)
- **en**: English only
- **ml**: Malayalam only

### AI Configuration
The system uses your existing AI configuration from `ieee_epic/core/config.py`. Make sure your `GOOGLE_API_KEY` is set for optimal AI responses.

## Troubleshooting

### Common Issues

1. **"GPIO not available" error**
   - You're not running on a Raspberry Pi
   - Use manual mode or test on actual Pi hardware

2. **"Permission denied" for GPIO**
   ```bash
   sudo usermod -a -G gpio $USER
   # Then logout and login again
   ```

3. **Sensor not detecting**
   - Check wiring connections
   - Verify sensor power (LED should light up)
   - Test with original `proximity.py` script
   - Try adjusting sensor sensitivity (if available)

4. **No AI responses**
   - Check `GOOGLE_API_KEY` environment variable
   - Verify internet connection
   - System will use fallback responses without AI

5. **Speech recognition issues**
   - Check microphone permissions
   - Ensure microphone is working
   - Reduce background noise
   - Speak clearly and close to microphone

### Testing Without Hardware

Both versions can run in development mode without GPIO:
- GUI version: Use "Manual Chat" button
- Command-line version: Press Enter to trigger conversations

## Customization

### Greeting Messages
Edit the greeting lists in the code:
```python
greetings = [
    "Hello! I saw your wave. How can I help you today?",
    # Add your custom greetings here
]
```

### Conversation Limits
Adjust conversation parameters:
```python
max_turns = 5  # Maximum conversation exchanges
debounce_time = 2.0  # Minimum time between handshake detections
timeout = 10  # Speech recognition timeout in seconds
```

### Sensor Sensitivity
Some proximity sensors have sensitivity adjustment potentiometers. Adjust as needed for your detection range requirements.

## Integration with Existing Project

These handshake detection scripts integrate seamlessly with your existing IEEE EPIC voice recognition system:

- Uses the same STT/TTS engines
- Shares AI response system
- Compatible with existing configuration
- Maintains conversation history
- Supports same language features

## Next Steps

1. **Test proximity sensor**: Use original `proximity.py` to verify sensor works
2. **Test voice system**: Run `enhanced_voice_recognition.py` to verify AI works  
3. **Combine systems**: Run handshake voice AI scripts
4. **Customize**: Adjust greetings, conversation flow, and sensor settings
5. **Deploy**: Set up on your Raspberry Pi for permanent installation

## Demo Script

For quick testing, you can use this simple test:

```bash
# Test proximity sensor only
python proximity.py

# Test voice AI only  
python enhanced_voice_recognition.py

# Test combined handshake system
python simple_handshake_ai.py
```

The system is now ready to detect handshakes and start intelligent conversations!