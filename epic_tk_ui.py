import tkinter as tk
from tkinter import scrolledtext
import asyncio
import threading
import os
import sys

# Ensure the local 'src' directory is importable when running this script directly
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from ieee_epic.core.stt import STTEngine
from ieee_epic.core.tts import TTSEngine
from ieee_epic.core.ai_response import AIResponseSystem
from ieee_epic.core.config import Settings
from loguru import logger


class EpicConversationApp(tk.Tk):
    """Minimal conversational UI: Start -> listen -> Gemini -> speak -> repeat."""

    def __init__(self):
        super().__init__()
        self.title('IEEE-EPIC Conversational Assistant')
        self.geometry('700x480')
        self.configure(bg='#ffffff')

        # Core systems
        self.settings = Settings()
        self.stt = STTEngine(self.settings)
        self.tts = TTSEngine(self.settings)
        self.ai = AIResponseSystem(self.settings)

        # UI State
        self.running = False
        self.loop_thread: threading.Thread | None = None

        # Widgets
        self._build_ui()

    def _build_ui(self):
        header = tk.Label(self, text='IEEE-EPIC Conversational Assistant', font=('Arial', 18, 'bold'), bg='#ffffff')
        header.pack(pady=10)

        self.start_btn = tk.Button(self, text='▶️ Start', width=15, command=self.toggle)
        self.start_btn.pack(pady=5)

        self.status_lbl = tk.Label(self, text='Idle', font=('Arial', 11), bg='#ffffff', fg='#444')
        self.status_lbl.pack()

        tk.Label(self, text='Conversation', font=('Arial', 12, 'bold'), bg='#ffffff').pack(anchor='w', padx=16, pady=(12, 0))
        self.history = scrolledtext.ScrolledText(self, font=('Arial', 12), height=16, width=80, wrap=tk.WORD, state='disabled')
        self.history.pack(padx=16, pady=8)

    def toggle(self):
        if self.running:
            self.running = False
            self.start_btn.configure(text='▶️ Start')
            self._set_status('Stopped')
        else:
            self.running = True
            self.start_btn.configure(text='⏹ Stop')
            self._set_status('Listening…')
            self.loop_thread = threading.Thread(target=self._conversation_loop, daemon=True)
            self.loop_thread.start()

    def _append_history(self, role: str, text: str):
        self.history.config(state='normal')
        self.history.insert(tk.END, f"{role}: {text}\n")
        self.history.see(tk.END)
        self.history.config(state='disabled')

    def _set_status(self, text: str):
        self.status_lbl.configure(text=text)
        self.update_idletasks()

    def _conversation_loop(self):
        while self.running:
            try:
                # 1) Listen
                self._set_status('Listening…')
                results = self.stt.recognize_speech(language='auto')
                user_text = self.stt.get_best_result(results) if results else ''

                if not user_text:
                    self._set_status('Did not catch that. Listening again…')
                    continue

                self._append_history('You', user_text)

                # 2) Ask Gemini (lower-school style via system_instruction)
                self._set_status('Thinking…')
                ai_text = self.ai.generate_response(user_text)
                if not ai_text:
                    ai_text = "Sorry, I couldn't think of an answer. Can you try again?"
                self._append_history('Assistant', ai_text)

                # 3) Speak
                self._set_status('Speaking…')
                try:
                    asyncio.run(self.tts.speak(ai_text, 'auto'))
                except Exception as e:
                    logger.error(f'TTS error: {e}')

                # 4) Loop continues automatically
                self._set_status('Listening…')

            except Exception as e:
                logger.error(f'Loop error: {e}')
                self._set_status('Error occurred, continuing…')


if __name__ == '__main__':
    app = EpicConversationApp()
    app.mainloop()
