"""
Quick test to verify Vosk models load correctly
"""
import os
from vosk import Model

def test_models():
    """Test if models can be loaded"""
    print("🔍 Testing model loading...")
    
    # Test English model
    if os.path.exists("vosk-en"):
        try:
            en_model = Model("vosk-en")
            print("✅ English model loaded successfully")
        except Exception as e:
            print(f"❌ English model failed: {e}")
    else:
        print("❌ English model directory not found")
    
    # Test Malayalam model (if exists)
    if os.path.exists("vosk-ml"):
        try:
            ml_model = Model("vosk-ml")
            print("✅ Malayalam model loaded successfully")
        except Exception as e:
            print(f"❌ Malayalam model failed: {e}")
    else:
        print("⚠️  Malayalam model directory not found")
    
    print("🎵 Testing audio device access...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print("✅ Audio devices detected:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"   📱 Input Device {i}: {device['name']}")
    except Exception as e:
        print(f"❌ Audio device test failed: {e}")

if __name__ == "__main__":
    test_models()