# IEEE-EPIC Tkinter UI quickstart

To launch the desktop UI:

```bash
python3 epic_tk_ui.py
```

- 🎤 **Listen**: Start speech recognition (STT)
- 🔊 **Speak**: Speak the text using TTS
- 🤖 **AI Respond**: Get an AI response to the text
- Input box: Type or edit text for TTS/AI
- AI response: Shown in a scrollable box

All features are wired to your IEEE-EPIC backend (STT, TTS, AI) and run as a native desktop app.

---

**Requirements:**
- Python 3.8+
- All IEEE-EPIC dependencies installed (see `requirements.txt`)
- Tkinter (included with most Python installations)

---

**To customize:**
- Edit `epic_tk_ui.py` to add more controls, status, or visualizations.
- See [Tkinter documentation](https://docs.python.org/3/library/tkinter.html) for more UI elements.
