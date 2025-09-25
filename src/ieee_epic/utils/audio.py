"""
Audio testing utilities for IEEE EPIC STT system.
"""

import time
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger

from ..core.config import Settings


class AudioTester:
    """Audio system testing and diagnostics."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
    
    def list_devices(self):
        """List all available audio devices."""
        try:
            import sounddevice as sd
            
            devices = sd.query_devices()
            logger.info("Available Audio Devices:")
            logger.info("=" * 50)
            
            for i, device in enumerate(devices):
                device_type = "🎤 INPUT " if device['max_input_channels'] > 0 else ""
                device_type += "🔊 OUTPUT" if device['max_output_channels'] > 0 else ""
                
                if not device_type:
                    device_type = "❓ UNKNOWN"
                
                logger.info(f"{i:2d}: {device_type} | {device['name']}")
                logger.info(f"     Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
                logger.info(f"     Sample Rate: {device['default_samplerate']} Hz")
                logger.info("")
            
            return devices
            
        except ImportError:
            logger.error("sounddevice not available. Please install: pip install sounddevice")
            return []
        except Exception as e:
            logger.error(f"Failed to list audio devices: {e}")
            return []
    
    def test_microphone(self, device_id: Optional[int] = None, duration: float = 3.0):
        """Test microphone input."""
        try:
            import sounddevice as sd
            
            device_id = device_id or self.settings.audio.device_id
            
            logger.info(f"🎤 Testing microphone (Device: {device_id}, Duration: {duration}s)")
            logger.info("Speak into your microphone...")
            
            # Record audio
            audio_data = sd.rec(
                int(duration * self.settings.audio.sample_rate),
                samplerate=self.settings.audio.sample_rate,
                channels=self.settings.audio.channels,
                device=device_id,
                dtype=np.float32
            )
            
            sd.wait()  # Wait for recording to complete
            
            # Analyze audio
            audio_flat = audio_data.flatten()
            
            # Calculate statistics
            max_amplitude = np.max(np.abs(audio_flat))
            rms = np.sqrt(np.mean(audio_flat ** 2))
            
            logger.info("🔍 Audio Analysis:")
            logger.info(f"  Max Amplitude: {max_amplitude:.4f}")
            logger.info(f"  RMS Level: {rms:.4f}")
            
            if max_amplitude < 0.001:
                logger.warning("⚠️  Very low audio level - check microphone connection")
            elif max_amplitude > 0.95:
                logger.warning("⚠️  Audio may be clipping - reduce input volume")
            else:
                logger.success("✅ Audio levels look good!")
            
            # Check for silence
            silence_threshold = 0.001
            silent_samples = np.sum(np.abs(audio_flat) < silence_threshold)
            silence_ratio = silent_samples / len(audio_flat)
            
            if silence_ratio > 0.8:
                logger.warning(f"⚠️  {silence_ratio*100:.1f}% silence - speak louder or check microphone")
            else:
                logger.info(f"📊 Silence ratio: {silence_ratio*100:.1f}%")
            
            return {
                'success': True,
                'max_amplitude': float(max_amplitude),
                'rms': float(rms),
                'silence_ratio': float(silence_ratio)
            }
            
        except ImportError:
            logger.error("sounddevice not available")
            return {'success': False, 'error': 'sounddevice not available'}
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_stt_with_audio(self, duration: float = 5.0):
        """Test STT with live audio input."""
        try:
            from ..core.stt import STTEngine
            
            logger.info(f"🧪 Testing STT with live audio ({duration}s)")
            
            engine = STTEngine(self.settings)
            
            if not engine.is_ready():
                logger.error("STT engine not ready")
                return {'success': False, 'error': 'STT engine not ready'}
            
            # Record and recognize
            results = engine.recognize_speech(duration=duration, language="auto")
            
            if results:
                logger.success("✅ STT Test Results:")
                for key, text in results.items():
                    logger.info(f"  {key}: {text}")
                
                best_result = engine.get_best_result(results)
                if best_result:
                    logger.success(f"📝 Best Result: {best_result}")
                
                return {
                    'success': True,
                    'results': results,
                    'best_result': best_result
                }
            else:
                logger.warning("❌ No speech recognized")
                return {'success': False, 'error': 'No speech recognized'}
                
        except Exception as e:
            logger.error(f"STT test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_comprehensive_test(self):
        """Run comprehensive audio and STT testing."""
        logger.info("🔍 Running Comprehensive Audio Test")
        logger.info("=" * 50)
        
        # 1. List devices
        devices = self.list_devices()
        
        if not devices:
            logger.error("❌ No audio devices found")
            return False
        
        # 2. Find input devices
        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        
        if not input_devices:
            logger.error("❌ No input devices found")
            return False
        
        logger.info(f"✅ Found {len(input_devices)} input device(s)")
        
        # 3. Test microphone
        logger.info("\n🎤 Microphone Test")
        logger.info("-" * 20)
        
        # Use first input device or configured device
        test_device = self.settings.audio.device_id or input_devices[0]
        mic_result = self.test_microphone(test_device, duration=3.0)
        
        if not mic_result['success']:
            logger.error("❌ Microphone test failed")
            return False
        
        # 4. Test STT
        logger.info("\n🧠 STT Integration Test")
        logger.info("-" * 25)
        logger.info("Please speak clearly when prompted...")
        
        time.sleep(2)  # Give user time to prepare
        
        stt_result = self.test_stt_with_audio(duration=5.0)
        
        if stt_result['success']:
            logger.success("✅ All tests passed!")
            return True
        else:
            logger.warning("⚠️  STT test failed, but audio system is working")
            return False
    
    def interactive_test(self):
        """Run interactive testing mode."""
        logger.info("🧪 Interactive Audio Testing Mode")
        logger.info("Commands: 'devices', 'mic', 'stt', 'full', 'quit'")
        
        while True:
            try:
                command = input("\n📝 Test command: ").strip().lower()
                
                if command == 'quit':
                    logger.info("👋 Goodbye!")
                    break
                elif command == 'devices':
                    self.list_devices()
                elif command == 'mic':
                    duration = float(input("Recording duration (seconds, default 3): ") or 3.0)
                    device_input = input("Device ID (press enter for default): ").strip()
                    device_id = int(device_input) if device_input else None
                    self.test_microphone(device_id, duration)
                elif command == 'stt':
                    duration = float(input("Recording duration (seconds, default 5): ") or 5.0)
                    self.test_stt_with_audio(duration)
                elif command == 'full':
                    self.run_comprehensive_test()
                else:
                    logger.warning("❌ Unknown command")
                    
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")