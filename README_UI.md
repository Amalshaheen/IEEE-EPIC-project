# IEEE-EPIC NiceGUI UI quickstart

To launch the interactive UI:

```bash
python3 epic_ui.py
```

- 🎤 **Listen**: Start speech recognition (STT)
- 🔊 **Speak**: Speak the text using TTS
- 🤖 **AI Respond**: Get an AI response to the text
- Input box: Type text to use with TTS or AI

All features are wired to your IEEE-EPIC backend (STT, TTS, AI) and run in your browser.

---

**Requirements:**
- Python 3.8+
- All IEEE-EPIC dependencies installed (see `requirements.txt`)
- `nicegui` installed (auto-installed)

---

**To customize:**
- Edit `epic_ui.py` to add more controls, status, or visualizations.
- See [NiceGUI documentation](https://nicegui.io/) for more UI elements.
