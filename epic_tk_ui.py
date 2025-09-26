import tkinter as tk
from tkinter import messagebox, scrolledtext
from src.ieee_epic.core.stt import STTEngine
from src.ieee_epic.core.tts import TTSEngine
from src.ieee_epic.core.ai_response import AIResponseSystem
from src.ieee_epic.core.config import Settings

settings = Settings()
stt_engine = STTEngine(settings)
tts_engine = TTSEngine(settings)
ai_system = AIResponseSystem(settings)

class EpicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('IEEE-EPIC Interactive UI')
        self.geometry('600x400')
        self.configure(bg='#f5f5f5')
        self.user_text = tk.StringVar()
        self.ai_response = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text='IEEE-EPIC Control Panel', font=('Arial', 18, 'bold'), bg='#f5f5f5').pack(pady=10)
        
        frame = tk.Frame(self, bg='#f5f5f5')
        frame.pack(pady=5)
        tk.Button(frame, text='🎤 Listen', width=12, command=self.recognize_speech).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text='🔊 Speak', width=12, command=self.speak_text).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text='🤖 AI Respond', width=12, command=self.ai_respond).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self, text='Input:', font=('Arial', 12), bg='#f5f5f5').pack(anchor='w', padx=20, pady=(15,0))
        self.input_entry = tk.Entry(self, textvariable=self.user_text, font=('Arial', 12), width=60)
        self.input_entry.pack(padx=20, pady=5)
        
        tk.Label(self, text='AI Response:', font=('Arial', 12), bg='#f5f5f5').pack(anchor='w', padx=20, pady=(10,0))
        self.response_box = scrolledtext.ScrolledText(self, font=('Arial', 12), height=5, width=60, wrap=tk.WORD, state='disabled')
        self.response_box.pack(padx=20, pady=5)

    def recognize_speech(self):
        results = stt_engine.recognize_speech(language="auto")
        if results:
            text = stt_engine.get_best_result(results)
            self.user_text.set(text)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, text)
            messagebox.showinfo('Speech Recognized', f'Recognized: {text}')
        else:
            messagebox.showwarning('No Speech', 'No speech detected.')

    def speak_text(self):
        text = self.user_text.get()
        if text:
            tts_engine.speak(text)
            messagebox.showinfo('Speaking', 'Speaking...')
        else:
            messagebox.showwarning('No Text', 'No text to speak.')

    def ai_respond(self):
        text = self.user_text.get()
        if text:
            response = ai_system.generate_response(text)
            self.ai_response.set(response)
            self.response_box.config(state='normal')
            self.response_box.delete('1.0', tk.END)
            self.response_box.insert(tk.END, response)
            self.response_box.config(state='disabled')
        else:
            messagebox.showwarning('No Input', 'No input for AI.')

if __name__ == '__main__':
    app = EpicApp()
    app.mainloop()
