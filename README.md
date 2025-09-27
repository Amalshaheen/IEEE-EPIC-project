# IEEE EPIC Conversational Assistant (EN + ML)

Minimal, online-only voice assistant: click Start, speak in English or Malayalam, it listens, asks Gemini, speaks a short child-friendly reply, and keeps listening.

## 🎤 Voice Recognition Features

This project includes multiple voice recognition implementations:
- **Simple Voice Recognition**: Standalone GUI with basic Malayalam & English support
- **Enhanced Voice Recognition**: Advanced GUI with improved error handling
- **Modular Components**: Reusable STT/TTS modules for integration

See [VOICE_RECOGNITION.md](./VOICE_RECOGNITION.md) for detailed documentation.

## Quick start

```bash
# Create/activate a venv (recommended)
python3 -m venv .venv
. .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Set credentials
export GOOGLE_API_KEY="<your-gemini-api-key>"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/gcloud-service-account.json"

# Run the UI
python epic_tk_ui.py
```

## What’s inside

```
src/ieee_epic/
	core/
		config.py     # Pydantic settings (audio, Google STT, TTS, Gemini)
		stt.py        # Google Cloud Speech (online-only)
		tts.py        # Edge TTS playback (en-IN/ml-IN voices)
		ai_response.py# Gemini responses (child-friendly)
epic_tk_ui.py     # Start/Stop loop: Listen → Gemini → Speak → repeat
```

## Behavior

- Speech-to-Text: Google Cloud Speech with automatic punctuation
	- Primary language en-IN, alternative ml-IN/en-US for bilingual detection
- AI: Google Gemini (gemini-2.0-flash-001) with a lower/primary-school “friendly teacher” style
- Text-to-Speech: Edge TTS with sensible default voices
	- English: en-IN-NeerjaNeural
	- Malayalam: ml-IN-SobhanaNeural
- UI: Single button Start/Stop; after speaking, it listens again automatically

## Notes

- Microphone: uses your default input (configure in `Settings().audio` if needed)
- Dependencies: see `requirements.txt` and `pyproject.toml`
- Logs: written to console via loguru
- Raspberry Pi: should work if audio/credentials are set; we no longer ship offline models

## Context7

This project uses Context7 to fetch up-to-date library usage (for example, confirming Edge TTS usage patterns). If you want runtime integration (like retrieval-augmented answers from docs), tell us what sources to connect and we’ll wire it in.

## License

MIT