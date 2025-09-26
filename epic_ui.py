from nicegui import ui
from src.ieee_epic.core.stt import STTEngine
from src.ieee_epic.core.tts import TTSEngine
from src.ieee_epic.core.ai_response import AIResponseSystem
from src.ieee_epic.core.config import Settings

settings = Settings()
stt_engine = STTEngine(settings)
tts_engine = TTSEngine(settings)
ai_system = AIResponseSystem(settings)

user_text = ""
ai_response = ""

ui.label('IEEE-EPIC Interactive UI')
ui.separator()

with ui.row():
    ui.button('🎤 Listen', on_click=lambda: recognize_speech())
    ui.button('🔊 Speak', on_click=lambda: speak_text())
    ui.button('🤖 AI Respond', on_click=lambda: ai_respond())

user_input = ui.input('Type text to speak or send to AI', on_change=lambda e: set_user_text(e.value))
ui.label('AI Response:').bind_text(lambda: ai_response)

# --- Logic ---
def set_user_text(text):
    global user_text
    user_text = text

def recognize_speech():
    global user_text
    results = stt_engine.recognize_speech(language="auto")
    if results:
        user_text = stt_engine.get_best_result(results)
        user_input.value = user_text
        ui.notify(f"Recognized: {user_text}")
    else:
        ui.notify('No speech detected', color='negative')

def speak_text():
    if user_text:
        tts_engine.speak(user_text)
        ui.notify('Speaking...')
    else:
        ui.notify('No text to speak', color='warning')

def ai_respond():
    global ai_response
    if user_text:
        ai_response = ai_system.generate_response(user_text)
        ui.notify('AI responded!')
    else:
        ui.notify('No input for AI', color='warning')

ui.run(title='IEEE-EPIC Interactive UI')
