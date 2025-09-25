import sounddevice as sd
import queue
import json
import os
from vosk import Model, KaldiRecognizer

def check_model_exists(model_path):
    """Check if model directory exists"""
    return os.path.exists(model_path) and os.path.isdir(model_path)

# Load models
print("🔄 Loading models...")

# Check for Malayalam model first
ml_model = None
ml_model_path = "vosk-ml"
if check_model_exists(ml_model_path):
    try:
        ml_model = Model(ml_model_path)
        print("✅ Malayalam model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load Malayalam model: {e}")
else:
    print("⚠️  Malayalam model not found at 'vosk-ml'. Continuing with English only.")

# Load English model
en_model = None
en_model_path = "vosk-en"
if check_model_exists(en_model_path):
    try:
        en_model = Model(en_model_path)
        print("✅ English model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load English model: {e}")
        exit(1)
else:
    print("❌ English model not found at 'vosk-en'. Please check model installation.")
    exit(1)

q = queue.Queue()

def callback(indata, frames, time, status):
    """Callback function for audio input"""
    if status:
        print(f"Audio status: {status}")
    q.put(bytes(indata))

def recognize(model, duration=5, language="Unknown"):
    """Recognize speech using the given model"""
    rec = KaldiRecognizer(model, 16000)
    
    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            print(f"🎤 Speak now in {language} (listening for {duration} seconds)...")
            
            # Clear the queue first
            while not q.empty():
                q.get()
            
            # Listen for the specified duration
            for _ in range(int(16000 / 8000 * duration)):
                try:
                    data = q.get(timeout=1.0)  # Add timeout to prevent hanging
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        if res.get("text"):
                            return res["text"]
                except queue.Empty:
                    continue
            
            # Get final result
            res = json.loads(rec.FinalResult())
            return res.get("text", "")
            
    except Exception as e:
        print(f"❌ Error during recognition: {e}")
        return ""

def main():
    """Main function to run speech recognition"""
    print("\n🚀 Starting Offline Speech Recognition Test")
    print("=" * 50)
    
    recognized_text = ""
    
    # Try Malayalam first if available
    if ml_model:
        print("\n📢 Trying Malayalam recognition...")
        recognized_text = recognize(ml_model, duration=6, language="Malayalam")
    
    # Fallback to English if Malayalam didn't work or isn't available
    if not recognized_text:
        print("\n📢 Fallback to English recognition...")
        recognized_text = recognize(en_model, duration=6, language="English")
    
    # Display result
    print("\n" + "=" * 50)
    if recognized_text:
        print(f"✅ You said: '{recognized_text}'")
    else:
        print("❌ No speech detected. Please try again.")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")