# AGENTS.md

## Project Overview
IEEE EPIC Speech-to-Text system with Google Gemini AI-powered responses and advanced online STT capabilities. Python package with CLI interface supporting Malayalam and English languages. Designed for both desktop and Raspberry Pi deployment with intelligent bilingual AI interactions and real-time streaming recognition.

## Key Features
- **Hybrid STT Architecture**: Offline (Vosk, Whisper) and Online (Google Cloud Speech-to-Text) backends
- **Real-time Streaming**: Continuous speech recognition with live transcription  
- **Intelligent Fallback**: Automatic fallback from online to offline backends
- **Bilingual Support**: Optimized English and Malayalam recognition
- **Google Gemini Integration**: AI-powered conversational responses
- **Cross-platform**: Desktop and Raspberry Pi optimized

## Setup Commands
```bash
# Install in development mode (recommended)
python3 -m pip install -e .

# Install with optional dev dependencies  
python3 -m pip install -e ".[dev]"

# Install dependencies only
python3 -m pip install -r requirements.txt

# Install Google Cloud Speech for online STT
python3 -m pip install google-cloud-speech

# Setup system components (models, audio)
ieee-epic setup

# Check system status
ieee-epic status

# Test online STT configuration
python3 test_online_stt.py
```

## Development Environment
- Python 3.8+ required
- Virtual environment recommended: `python3 -m venv .venv && source .venv/bin/activate`
- Package uses `pyproject.toml` with Hatchling build backend
- Installed as editable package provides `ieee-epic` CLI command

## Project Structure
```
src/ieee_epic/          # Main package
├── main.py             # CLI entry point (Typer + Rich)
├── core/               # Core business logic
│   ├── config.py       # Pydantic configuration models
│   ├── stt.py          # STT engine (Vosk + Whisper backends)
│   └── ai_response.py  # AI response system (online + offline)
├── utils/              # Utilities
│   ├── setup.py        # System setup automation
│   └── audio.py        # Audio testing utilities
└── cli/                # CLI modules (expandable)

tests/                  # Pytest test suite
data/                   # AI response patterns/database
models/                 # STT model storage
vosk-en/               # English Vosk model (downloaded)
```

## Code Style Guidelines
- Use type hints throughout (mypy compatible)
- Follow PEP 8 with Black formatting
- Pydantic models for configuration and data validation  
- Rich library for CLI output formatting
- Loguru for structured logging
- Error handling with graceful fallbacks

## Key Classes and Components
- `Settings` (config.py): Enhanced Pydantic configuration with online STT settings and Google Cloud credentials
- `STTEngine` (stt.py): Multi-backend speech recognition with streaming support and intelligent fallback
- `GoogleCloudSTTBackend` (stt.py): Cloud-based STT with real-time streaming capabilities
- `VoskSTTBackend` (stt.py): Offline STT backend (Enhanced)
- `WhisperSTTBackend` (stt.py): Offline STT backend (Enhanced)
- `AIResponseSystem` (ai_response.py): Google Gemini-powered bilingual response generation
- `GeminiResponseGenerator` (ai_response.py): Direct Gemini API integration with streaming support
- `AudioRecorder` (stt.py): Enhanced audio capture with streaming support for real-time recognition
- Main CLI app uses Typer with Rich console output and new streaming commands

## Testing Instructions
```bash
# Run all tests
python3 -m pytest tests/

# Run with coverage
python3 -m pytest tests/ --cov=src/ieee_epic

# Test specific module
python3 -m pytest tests/test_config.py

# Test CLI commands (integration)
ieee-epic status
ieee-epic demo

# Alternative: use virtual environment directly
.venv/bin/python -m pytest tests/
.venv/bin/pytest tests/ --cov=src/ieee_epic
```

## Build and Run Commands  
```bash
# CLI commands available after installation
ieee-epic status        # System status and backend information
ieee-epic stt          # Speech-to-text recognition (offline/online)
ieee-epic stream       # Real-time streaming STT (Google Cloud)
ieee-epic interactive  # Interactive STT mode with streaming support
ieee-epic conversation # Full conversational AI
ieee-epic demo         # AI response testing
ieee-epic setup        # System setup and model downloads

# Development mode
python3 -m ieee_epic.main status

# Build package (requires build tool)
python3 -m pip install build
python3 -m build

# Create source distribution
python3 -m build --sdist

# Create wheel distribution  
python3 -m build --wheel

# Run tests
python3 -m pytest tests/
python3 -m pytest --cov=src/ieee_epic

# Test online STT specifically
python3 test_online_stt.py

# Code quality checks
python3 -m black src/ tests/
python3 -m isort src/ tests/
python3 -m flake8 src/ tests/
python3 -m mypy src/

# Legacy compatibility
python main.py         # Shows help and status
```

## Configuration
- Settings managed via Pydantic models in `core/config.py`
- Environment variables: `IEEE_EPIC__SECTION__KEY=value` format
- Config files: JSON/TOML supported
- Platform detection: Auto-optimizes for Raspberry Pi vs Desktop
- Default config created on first run

## Dependencies and Backends
- **STT Backends**: Vosk (offline primary), Whisper (offline fallback), Google Cloud Speech (online primary)
- **AI Responses**: Google Gemini API (online), intelligent fallbacks (offline)
- **Audio**: sounddevice, pyaudio for capture and streaming
- **CLI**: Typer, Rich for modern interface
- **Config**: Pydantic v2 for validation
- **Logging**: loguru with rotation
- **AI Integration**: google-genai SDK for Gemini API
- **Online STT**: google-cloud-speech for streaming recognition

## Error Handling Patterns
- All engines implement graceful fallback (STT: Vosk → Whisper, AI: Gemini → Fallback responses)
- Configuration validation with helpful error messages
- Audio device auto-detection with fallbacks
- Platform-specific optimizations (memory, CPU usage)
- Intelligent language detection for bilingual fallbacks

## Performance Considerations
- Lazy loading of STT models (memory efficiency)
- Platform detection for Raspberry Pi optimizations
- Configurable audio buffer sizes
- Model caching and reuse
- Background processing for long-running tasks

## Security Notes
- Gemini API key via environment variable only
- No API keys stored in config files
- Audio data processed locally (offline capable)
- No network requirements for basic STT functionality
- Fallback responses when API unavailable

## Raspberry Pi Specific Instructions
- See `README_RPi.md` for detailed Pi setup
- Memory optimizations automatically applied
- Audio group permissions handled by setup
- Service mode configuration available
- Performance monitoring built-in

## File Naming Conventions
- Python modules: lowercase with underscores
- Classes: PascalCase
- Functions/methods: snake_case
- CLI commands: kebab-case with descriptive names
- Config sections: lowercase with underscores

## Commit and PR Guidelines
- Test all CLI commands before committing
- Run `python3 -m pytest` to ensure tests pass
- Type check with `python3 -m mypy src/` (when available)
- Format code with `python3 -m black src/ tests/`
- Sort imports with `python3 -m isort src/ tests/`
- Ensure backward compatibility for CLI interface
- Update AGENTS.md for new features or significant changes