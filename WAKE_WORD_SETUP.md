# Wake Word Setup Guide

## Quick Setup (Easiest)

### Option 1: Replace Handshake with Wake Word

1. **Test the simple wake word detector:**
   ```bash
   python wake_word_detector.py
   ```

2. **Use wake words:** "Hey SARAS", "Hello SARAS", or just "SARAS"

3. **The system will:**
   - Listen continuously for wake words
   - Start conversation when detected
   - Work just like handshake detection but with voice

### Option 2: Add Wake Word to Existing System

1. **Run enhanced system with both handshake AND wake word:**
   ```bash
   python enhanced_wake_word_ai.py
   ```

2. **You get both activation methods:**
   - Wave your hand (handshake detection)
   - Say wake words (voice activation)
   - Manual chat button

## Installation Requirements

### Basic Wake Word (Google Speech Recognition)
```bash
# Already have these from your existing setup
pip install SpeechRecognition
pip install google-cloud-speech  # or just use free Google API
```

### Advanced Wake Word (Offline with Pocketsphinx) - Optional
```bash
# System dependencies
sudo apt-get install swig libpulse-dev python3-dev portaudio19-dev

# Python packages
pip install pocketsphinx
pip install pyaudio
```

## Advantages of Wake Word vs Handshake

### Wake Word Benefits:
✅ **Hands-free activation** - no physical interaction needed  
✅ **Works from distance** - don't need to be near sensor  
✅ **Natural interaction** - just speak to activate  
✅ **Multiple wake words** - flexible activation phrases  
✅ **Works in any lighting** - no sensor positioning issues  

### Current Handshake Benefits:
✅ **No false activations** - requires intentional gesture  
✅ **Works in noisy environments** - no audio interference  
✅ **Privacy friendly** - no continuous listening  
✅ **Low power** - proximity sensor uses minimal resources  

## Implementation Difficulty

### Easy (1-2 hours):
- **Simple wake word**: Replace handshake with basic voice activation
- **Hybrid system**: Add wake word to existing handshake system
- **Uses your existing speech recognition setup**

### Medium (Half day):
- **Advanced wake word**: Better accuracy with offline detection
- **Custom wake phrases**: Train for specific phrases
- **Noise filtering**: Handle background noise better

### Hard (1-2 days):
- **Custom wake word models**: Train your own wake word detector
- **Edge AI**: Run completely offline with optimized models
- **Multi-language wake words**: Support Malayalam wake words

## Configuration

### Wake Words You Can Use:
```python
wake_words = [
    "hey saras",
    "hello saras", 
    "saras",
    "wake up saras",
    "hi saras"
]
```

### Sensitivity Settings:
```python
# More sensitive (may have false positives)
sensitivity_threshold = 2  # seconds

# Less sensitive (fewer false positives)  
sensitivity_threshold = 5  # seconds
```

## Testing

### Test Basic Wake Word:
```bash
# Terminal 1: Start the wake word detector
python wake_word_detector.py

# Speak any of: "Hey SARAS", "Hello SARAS", "SARAS"
# Should respond and start conversation
```

### Test Enhanced System:
```bash
# Run the GUI with both handshake and wake word
python enhanced_wake_word_ai.py

# Try both:
# 1. Wave your hand near proximity sensor
# 2. Say "Hey SARAS" 
# Both should start conversation
```

## Recommendation

**Start with Option 2 (Enhanced System)** because:
- Keeps your existing handshake functionality
- Adds wake word as bonus feature  
- Users can choose their preferred activation method
- Easy to disable wake word if needed
- Best of both worlds

The enhanced system gives you:
- 🤝 **Handshake detection** (proximity sensor)
- 🎯 **Wake word detection** (voice activation) 
- 🎤 **Manual chat** (button activation)

This makes your assistant accessible in more situations while maintaining all existing functionality!