import speech_recognition as sr
from gtts import gTTS
import os
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

# GUI Setup
root = tk.Tk()
root.title("Interactive Robo - Malayalam + English")
root.geometry("800x500")

conversation_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 14))
conversation_box.pack(expand=True, fill="both")

def listen_and_recognize():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        conversation_box.insert(tk.END, "\n? Listening...\n")
        conversation_box.see(tk.END)
        root.update()
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="ml-IN")
        conversation_box.insert(tk.END, f"\n? [Malayalam]: {text}\n")
        conversation_box.see(tk.END)
        return text, "ml"
    except:
        try:
            text = r.recognize_google(audio, language="en-IN")
            conversation_box.insert(tk.END, f"\n? [English]: {text}\n")
            conversation_box.see(tk.END)
            return text, "en"
        except Exception as e:
            conversation_box.insert(tk.END, f"\n? Could not understand: {e}\n")
            conversation_box.see(tk.END)
            return None, None

def speak_and_display(response, lang):
    conversation_box.insert(tk.END, f"? [{lang.upper()}]: {response}\n")
    conversation_box.see(tk.END)
    root.update()

    tts = gTTS(text=response, lang=lang)
    filename = f"response_{datetime.now().timestamp()}.mp3"
    tts.save(filename)
    os.system(f"mpg123 -q {filename}")
    os.remove(filename)

def run_assistant():
    query, lang = listen_and_recognize()
    if query:
        if lang == "ml":
            response = "You've said: " + query
        else:
            response = "You said: " + query
        speak_and_display(response, lang)

# Button to trigger listening
listen_button = tk.Button(root, text="? Ask a Question", font=("Arial", 16), command=run_assistant)
listen_button.pack(pady=10)

# Run GUI
root.mainloop()