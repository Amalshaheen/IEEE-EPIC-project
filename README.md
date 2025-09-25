# IEEE EPIC Speech-to-Text System

## 🎯 Overview
A professional Speech-to-Text system with AI-powered responses, supporting Malayalam and English languages. Built with modern Python architecture and designed for both desktop and Raspberry Pi deployment.

## 🚀 **Quick Start**
```bash
# Show system status
ieee-epic status

# Interactive speech recognition
ieee-epic stt

# AI conversation mode  
ieee-epic conversation

# Test AI responses
ieee-epic demo

# Setup system
ieee-epic setup
```

## 📁 **Project Structure**
```
IEEE-EPIC-project/
├── 📦 src/ieee_epic/           # Main package
│   ├── 🎯 main.py              # Modern CLI with Typer & Rich
│   ├── ⚙️ core/                # Core business logic
│   │   ├── config.py           # Pydantic configuration
│   │   ├── stt.py             # Multi-backend STT engine
│   │   └── ai_response.py     # AI response system
│   └── 🛠️ utils/               # Utilities
│       ├── setup.py           # System setup
│       └── audio.py           # Audio testing
├── 🧪 tests/                  # Test suite
├── 📁 data/                   # AI response data
├── 📁 models/                 # STT models storage
├── 📁 vosk-en/                # English STT model
├── 📝 pyproject.toml          # Project configuration
├── 📋 requirements.txt        # Dependencies
├── 🤖 AGENTS.md               # AI agents documentation
├── 🍓 README_RPi.md           # Raspberry Pi setup
└── 🔄 main.py                 # Compatibility wrapper
```

## 🤖 **AI Agents**
This project features multiple intelligent agents working together:
- **STT Agent**: Multi-backend speech recognition with auto-fallback
- **AI Response Agent**: Context-aware bilingual conversation system
- **Configuration Agent**: Platform-adaptive system optimization
- **Audio Processing Agent**: Intelligent audio capture and enhancement

**📖 See [AGENTS.md](AGENTS.md) for complete AI agent documentation**

## 🚀 Usage

### **Modern CLI (Recommended)**
```bash
# Show comprehensive system status
ieee-epic status

# Speech-to-text with options
ieee-epic stt --lang auto --duration 5

# Interactive STT mode  
ieee-epic interactive

# Full conversational AI
ieee-epic conversation

# AI response testing
ieee-epic demo

# System setup
ieee-epic setup
```

### **Programmatic Usage**
```python
from ieee_epic import STTEngine, AIResponseSystem, Settings

# Custom configuration
settings = Settings()
settings.audio.duration = 10.0

# Use the engines
stt_engine = STTEngine(settings)
ai_system = AIResponseSystem(settings)

results = stt_engine.recognize_speech()
response = ai_system.generate_response(results)
```

### **Backwards Compatibility**
```bash
python main.py          # Shows help and status
```

## 🎤 **Features**
- **🔤 Multilingual STT**: Malayalam and English speech recognition
- **🤖 AI Responses**: Context-aware conversation system  
- **🔄 Multi-Backend**: Vosk + Whisper with intelligent fallback
- **📱 Modern CLI**: Rich terminal interface with beautiful output
- **⚙️ Smart Config**: Pydantic-based configuration with validation
- **🍓 Raspberry Pi**: Optimized for edge deployment
- **🌐 Dual Mode**: Online (OpenAI) + Offline pattern-based AI
- **🔍 Auto-Detection**: Language and platform detection
- **🧪 Type Safe**: Full type hints and validation throughout

## 📊 **Current Status**
- ✅ **English STT Model**: Available and ready
- ❌ **Malayalam STT Model**: Optional (auto-download available)
- ✅ **AI Response System**: Offline mode functional
- ✅ **Audio Processing**: Ready with device auto-detection
- ✅ **CLI Interface**: Full feature set available
- ✅ **Package Installation**: Professional Python package

## 🔧 **Installation**
```bash
# Clone and install
git clone <repository>
cd IEEE-EPIC-project
pip install -e .

# Setup system components
ieee-epic setup
```

## 🔄 **Next Steps**
- 🔄 TTS (Text-to-Speech) integration
- 🔄 Web API interface for remote access  
- 🔄 Home Assistant integration examples
- 🔄 Enhanced Malayalam model support

## 🤝 **Contributing**
This project is part of the IEEE EPIC initiative. Contributions welcome!

**📖 For AI agent architecture details, see [AGENTS.md](AGENTS.md)**

## 📄 **License**
Educational use under IEEE EPIC project guidelines.