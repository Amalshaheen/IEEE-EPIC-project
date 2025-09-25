"""
Raspberry Pi Setup Script for Malayalam Voice Recognition
========================================================
This script sets up the environment and downloads necessary models
for offline Malayalam speech recognition on Raspberry Pi.
"""

import os
import sys
import subprocess
import zipfile
import requests
from pathlib import Path

class RPiSetup:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.models_dir = self.project_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
        
    def check_system_requirements(self):
        """Check if running on Raspberry Pi and system requirements"""
        print("🔍 Checking system requirements...")
        
        # Check if running on ARM (typical for RPi)
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'ARM' in cpuinfo or 'arm' in cpuinfo:
                    print("✅ ARM processor detected (Raspberry Pi compatible)")
                else:
                    print("⚠️  Non-ARM processor detected")
        except FileNotFoundError:
            print("⚠️  Could not detect processor type")
        
        # Check available memory
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if 'MemTotal' in line:
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / 1024 / 1024
                        print(f"💾 Total RAM: {mem_gb:.1f} GB")
                        if mem_gb < 1:
                            print("⚠️  Low RAM detected. Consider using smaller models.")
                        break
        except:
            print("⚠️  Could not detect memory info")
    
    def install_system_dependencies(self):
        """Install required system packages"""
        print("\n📦 Installing system dependencies...")
        
        packages = [
            'python3-pyaudio',
            'portaudio19-dev', 
            'alsa-utils',
            'pulseaudio',
            'ffmpeg',
            'wget',
            'unzip'
        ]
        
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            for package in packages:
                print(f"Installing {package}...")
                subprocess.run(['sudo', 'apt', 'install', '-y', package], check=True)
            print("✅ System dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing system dependencies: {e}")
            return False
        return True
    
    def download_file(self, url, filename):
        """Download file with progress bar"""
        print(f"📥 Downloading {filename}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📊 Progress: {percent:.1f}%", end='')
            
            print(f"\n✅ Downloaded {filename}")
            return True
        except Exception as e:
            print(f"\n❌ Error downloading {filename}: {e}")
            return False
    
    def setup_vosk_models(self):
        """Download and setup Vosk models for Malayalam and English"""
        print("\n🤖 Setting up Vosk models...")
        
        models_to_download = [
            {
                'name': 'English (Small - RPi optimized)',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
                'filename': 'vosk-model-small-en-us-0.15.zip',
                'extract_to': 'vosk-en'
            },
            # Note: Malayalam model URL might need verification
            {
                'name': 'Malayalam (if available)',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-ml-0.22.zip',
                'filename': 'vosk-model-ml-0.22.zip',
                'extract_to': 'vosk-ml'
            }
        ]
        
        for model in models_to_download:
            model_path = self.project_dir / model['extract_to']
            
            # Skip if already exists
            if model_path.exists():
                print(f"✅ {model['name']} already exists")
                continue
            
            zip_path = self.models_dir / model['filename']
            
            # Download if not exists
            if not zip_path.exists():
                if not self.download_file(model['url'], zip_path):
                    print(f"⚠️  Skipping {model['name']} - download failed")
                    continue
            
            # Extract
            try:
                print(f"📂 Extracting {model['name']}...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.project_dir)
                
                # Rename to expected directory name
                extracted_dirs = [d for d in self.project_dir.iterdir() 
                                if d.is_dir() and 'vosk-model' in d.name]
                
                if extracted_dirs:
                    extracted_dirs[0].rename(model_path)
                    print(f"✅ {model['name']} setup complete")
                else:
                    print(f"⚠️  Could not find extracted directory for {model['name']}")
                    
            except Exception as e:
                print(f"❌ Error extracting {model['name']}: {e}")
    
    def setup_whisper_cpp(self):
        """Setup Whisper.cpp for better performance on RPi"""
        print("\n🔧 Setting up Whisper.cpp (optional, for better performance)...")
        
        whisper_dir = self.project_dir / "whisper.cpp"
        
        if whisper_dir.exists():
            print("✅ Whisper.cpp already exists")
            return True
        
        try:
            print("📥 Cloning Whisper.cpp...")
            subprocess.run([
                'git', 'clone', 
                'https://github.com/ggml-org/whisper.cpp.git',
                str(whisper_dir)
            ], check=True)
            
            print("🔨 Building Whisper.cpp...")
            subprocess.run(['make', '-j', '2'], cwd=whisper_dir, check=True)
            
            print("📥 Downloading small multilingual model...")
            subprocess.run([
                './models/download-ggml-model.sh', 'small'
            ], cwd=whisper_dir, check=True)
            
            print("✅ Whisper.cpp setup complete")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Whisper.cpp setup failed: {e}")
            print("   Continuing with Vosk-only setup...")
            return False
    
    def create_audio_test(self):
        """Create audio test script"""
        print("\n🎵 Creating audio test script...")
        
        test_script = """#!/usr/bin/env python3
import sounddevice as sd
import numpy as np

def test_audio():
    '''Test audio input/output on Raspberry Pi'''
    print("🔊 Audio Device Test")
    print("=" * 30)
    
    # List audio devices
    print("Available audio devices:")
    print(sd.query_devices())
    
    # Test recording
    print("\\n🎤 Testing microphone (speak for 3 seconds)...")
    try:
        duration = 3
        sample_rate = 16000
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype='int16')
        sd.wait()
        
        # Check if we got audio
        max_amplitude = np.max(np.abs(recording))
        if max_amplitude > 100:
            print("✅ Microphone working - audio detected!")
        else:
            print("⚠️  Low audio level - check microphone connection")
            
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        print("   Try: sudo usermod -a -G audio $USER")
        print("   Then logout and login again")

if __name__ == "__main__":
    test_audio()
"""
        
        with open(self.project_dir / "test_audio.py", 'w') as f:
            f.write(test_script)
        
        # Make executable
        os.chmod(self.project_dir / "test_audio.py", 0o755)
        print("✅ Audio test script created")
    
    def create_rpi_optimized_stt(self):
        """Create RPi-optimized STT script"""
        print("\n🎯 Creating RPi-optimized STT script...")
        
        script_content = '''#!/usr/bin/env python3
"""
Raspberry Pi Optimized Malayalam Speech Recognition
==================================================
Optimized for Raspberry Pi with memory and CPU constraints.
"""

import os
import sys
import json
import queue
import threading
import time
import wave
import sounddevice as sd
from pathlib import Path

# Try to import Vosk
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    print("⚠️  Vosk not available. Install with: pip install vosk")
    VOSK_AVAILABLE = False

class RPiSpeechRecognizer:
    def __init__(self):
        self.models = {}
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.sample_rate = 16000
        self.block_size = 8000
        
        # Load models
        self.load_models()
    
    def load_models(self):
        """Load available speech recognition models"""
        print("🔄 Loading models...")
        
        model_paths = {
            'malayalam': 'vosk-ml',
            'english': 'vosk-en'
        }
        
        for lang, path in model_paths.items():
            if os.path.exists(path) and VOSK_AVAILABLE:
                try:
                    print(f"📚 Loading {lang} model...")
                    self.models[lang] = Model(path)
                    print(f"✅ {lang.capitalize()} model loaded")
                except Exception as e:
                    print(f"❌ Failed to load {lang} model: {e}")
        
        if not self.models:
            print("❌ No models loaded. Please run setup first.")
            sys.exit(1)
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        
        if self.is_listening:
            self.audio_queue.put(bytes(indata))
    
    def recognize_speech(self, language='english', duration=5):
        """Recognize speech in specified language"""
        if language not in self.models:
            print(f"❌ {language} model not available")
            return ""
        
        print(f"🎤 Listening in {language} for {duration} seconds...")
        
        recognizer = KaldiRecognizer(self.models[language], self.sample_rate)
        self.is_listening = True
        
        # Clear queue
        while not self.audio_queue.empty():
            self.audio_queue.get()
        
        result_text = ""
        start_time = time.time()
        
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            ):
                while time.time() - start_time < duration:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        
                        if recognizer.AcceptWaveform(data):
                            result = json.loads(recognizer.Result())
                            if result.get('text'):
                                result_text = result['text']
                                print(f"🗣️  Partial: {result_text}")
                        
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"❌ Recognition error: {e}")
                        break
                
                # Get final result
                if not result_text:
                    final_result = json.loads(recognizer.FinalResult())
                    result_text = final_result.get('text', '')
        
        finally:
            self.is_listening = False
        
        return result_text.strip()
    
    def auto_detect_language(self, duration=3):
        """Try to auto-detect language by testing both models"""
        results = {}
        
        for language in self.models.keys():
            print(f"\\n🔍 Testing {language}...")
            text = self.recognize_speech(language, duration)
            if text:
                results[language] = text
                print(f"✅ {language}: '{text}'")
            else:
                print(f"❌ {language}: No speech detected")
        
        return results
    
    def interactive_mode(self):
        """Interactive speech recognition mode"""
        print("\\n🚀 Interactive Speech Recognition Mode")
        print("=" * 50)
        print("Commands:")
        print("  'ml' or 'malayalam' - Malayalam recognition")
        print("  'en' or 'english' - English recognition")  
        print("  'auto' - Auto-detect language")
        print("  'quit' - Exit")
        print("=" * 50)
        
        while True:
            try:
                command = input("\\n📝 Enter command: ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    break
                elif command in ['ml', 'malayalam']:
                    if 'malayalam' in self.models:
                        result = self.recognize_speech('malayalam', 5)
                        if result:
                            print(f"\\n✅ Malayalam: '{result}'")
                        else:
                            print("\\n❌ No speech detected")
                    else:
                        print("\\n❌ Malayalam model not available")
                        
                elif command in ['en', 'english']:
                    if 'english' in self.models:
                        result = self.recognize_speech('english', 5)
                        if result:
                            print(f"\\n✅ English: '{result}'")
                        else:
                            print("\\n❌ No speech detected")
                    else:
                        print("\\n❌ English model not available")
                        
                elif command == 'auto':
                    results = self.auto_detect_language(4)
                    if results:
                        print("\\n🎯 Detection Results:")
                        for lang, text in results.items():
                            print(f"  {lang}: '{text}'")
                    else:
                        print("\\n❌ No speech detected in any language")
                        
                else:
                    print("\\n❓ Unknown command. Try 'ml', 'en', 'auto', or 'quit'")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\\n❌ Error: {e}")
        
        print("\\n👋 Goodbye!")

def main():
    """Main function"""
    recognizer = RPiSpeechRecognizer()
    recognizer.interactive_mode()

if __name__ == "__main__":
    main()
'''
        
        with open(self.project_dir / "rpi_stt.py", 'w') as f:
            f.write(script_content)
        
        os.chmod(self.project_dir / "rpi_stt.py", 0o755)
        print("✅ RPi-optimized STT script created")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Raspberry Pi Malayalam Voice Recognition Setup")
        print("=" * 60)
        
        self.check_system_requirements()
        
        if not self.install_system_dependencies():
            print("❌ Setup failed at system dependencies")
            return False
        
        self.setup_vosk_models()
        self.setup_whisper_cpp()  # Optional, continues if fails
        self.create_audio_test()
        self.create_rpi_optimized_stt()
        
        print("\n🎉 Setup Complete!")
        print("=" * 60)
        print("Next steps:")
        print("1. Test audio: python3 test_audio.py")
        print("2. Install Python dependencies: pip3 install -r requirements.txt")
        print("3. Run speech recognition: python3 rpi_stt.py")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    setup = RPiSetup()
    setup.run_setup()