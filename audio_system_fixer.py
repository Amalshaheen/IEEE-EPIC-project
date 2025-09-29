#!/usr/bin/env python3
"""
Audio System Diagnostic and Fix Tool for IEEE EPIC Project
Diagnoses and attempts to fix audio-related issues
"""

import os
import sys
import subprocess
import time
from loguru import logger

class AudioSystemFixer:
    """Audio system diagnostic and fix tool"""
    
    def __init__(self):
        self.fixes_applied = []
        
    def check_audio_system(self):
        """Check the current audio system status"""
        logger.info("🔍 Checking audio system...")
        
        # Check ALSA devices
        self._check_alsa_devices()
        
        # Check PulseAudio
        self._check_pulseaudio()
        
        # Check Python audio libraries
        self._check_python_audio_libs()
        
        # Check microphone access
        self._check_microphone_access()
        
        return len(self.fixes_applied) == 0
    
    def _check_alsa_devices(self):
        """Check ALSA audio devices"""
        logger.info("Checking ALSA devices...")
        
        try:
            # List capture devices
            result = subprocess.run(['arecord', '-l'], 
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("ALSA capture devices:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"  {line}")
            else:
                logger.warning("No ALSA capture devices found or arecord not available")
                
        except Exception as e:
            logger.warning(f"Could not check ALSA devices: {e}")
    
    def _check_pulseaudio(self):
        """Check PulseAudio status"""
        logger.info("Checking PulseAudio...")
        
        try:
            # Check if PulseAudio is running
            result = subprocess.run(['pulseaudio', '--check'], 
                                    capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logger.info("✅ PulseAudio is running")
                
                # List sources
                try:
                    result = subprocess.run(['pactl', 'list', 'short', 'sources'], 
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.info("PulseAudio sources:")
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                logger.info(f"  {line}")
                except Exception as e:
                    logger.warning(f"Could not list PulseAudio sources: {e}")
            else:
                logger.warning("PulseAudio not running, attempting to start...")
                self._fix_pulseaudio()
                
        except Exception as e:
            logger.warning(f"Could not check PulseAudio: {e}")
    
    def _fix_pulseaudio(self):
        """Try to fix PulseAudio issues"""
        try:
            logger.info("Attempting to start PulseAudio...")
            
            # Kill existing PulseAudio processes
            subprocess.run(['pulseaudio', '--kill'], 
                          capture_output=True, timeout=5)
            
            # Wait a moment
            time.sleep(1)
            
            # Start PulseAudio
            result = subprocess.run(['pulseaudio', '--start'], 
                                   capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.success("✅ PulseAudio started successfully")
                self.fixes_applied.append("Started PulseAudio")
            else:
                logger.error(f"Failed to start PulseAudio: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error fixing PulseAudio: {e}")
    
    def _check_python_audio_libs(self):
        """Check Python audio libraries"""
        logger.info("Checking Python audio libraries...")
        
        required_libs = [
            'speech_recognition',
            'pyaudio', 
            'pygame',
            'pyttsx3'
        ]
        
        missing_libs = []
        
        for lib in required_libs:
            try:
                __import__(lib)
                logger.info(f"✅ {lib} available")
            except ImportError:
                logger.warning(f"❌ {lib} not available")
                missing_libs.append(lib)
        
        if missing_libs:
            logger.warning(f"Missing libraries: {missing_libs}")
            logger.info("Install with: pip install " + " ".join(missing_libs))
    
    def _check_microphone_access(self):
        """Check microphone access"""
        logger.info("Testing microphone access...")
        
        try:
            import speech_recognition as sr
            
            # Try to initialize recognizer and microphone
            recognizer = sr.Recognizer()
            
            # List microphones
            mics = sr.Microphone.list_microphone_names()
            logger.info(f"Available microphones: {len(mics)}")
            
            if len(mics) == 0:
                logger.warning("No microphones found")
                return
            
            # Try to use default microphone
            try:
                mic = sr.Microphone()
                with mic as source:
                    logger.info("Testing microphone access...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    logger.success("✅ Microphone accessible")
                    
            except Exception as mic_e:
                logger.error(f"❌ Microphone access failed: {mic_e}")
                self._fix_microphone_permissions()
                
        except Exception as e:
            logger.error(f"Error checking microphone: {e}")
    
    def _fix_microphone_permissions(self):
        """Try to fix microphone permission issues"""
        try:
            logger.info("Attempting to fix microphone permissions...")
            
            # Add user to audio group
            username = os.getenv('USER')
            if username:
                result = subprocess.run(['sudo', 'usermod', '-a', '-G', 'audio', username],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    logger.success("✅ Added user to audio group (restart required)")
                    self.fixes_applied.append("Added user to audio group")
                else:
                    logger.warning("Could not add user to audio group")
            
            # Set microphone permissions
            subprocess.run(['sudo', 'chmod', '666', '/dev/snd/*'], 
                          capture_output=True)
            
            logger.info("💡 You may need to restart for audio group changes to take effect")
            
        except Exception as e:
            logger.error(f"Error fixing microphone permissions: {e}")
    
    def apply_environment_fixes(self):
        """Apply environment variable fixes"""
        logger.info("Applying environment fixes...")
        
        # Set audio-related environment variables
        fixes = {
            'ALSA_CARD': '0',
            'PULSE_LATENCY_MSEC': '30',
            'ALSA_PCM_CARD': '0',
            'ALSA_PCM_DEVICE': '0'
        }
        
        for key, value in fixes.items():
            os.environ[key] = value
            logger.info(f"Set {key}={value}")
        
        self.fixes_applied.append("Applied environment variables")
    
    def create_audio_config(self):
        """Create audio configuration files"""
        logger.info("Creating audio configuration...")
        
        # Create ALSA configuration
        asound_content = """
pcm.!default {
    type pulse
    fallback "sysdefault"
    hint {
        show on
        description "Default ALSA Output (currently PulseAudio Sound Server)"
    }
}
ctl.!default {
    type pulse
    fallback "sysdefault"
}
"""
        
        try:
            home_dir = os.path.expanduser('~')
            asound_path = os.path.join(home_dir, '.asoundrc')
            
            if not os.path.exists(asound_path):
                with open(asound_path, 'w') as f:
                    f.write(asound_content)
                logger.success("✅ Created .asoundrc configuration")
                self.fixes_applied.append("Created ALSA config")
            else:
                logger.info(".asoundrc already exists")
                
        except Exception as e:
            logger.error(f"Error creating audio config: {e}")
    
    def run_full_diagnosis(self):
        """Run complete audio system diagnosis and fixes"""
        logger.info("🚀 Starting full audio system diagnosis...")
        
        # Apply environment fixes first
        self.apply_environment_fixes()
        
        # Create audio configs
        self.create_audio_config()
        
        # Check system
        system_ok = self.check_audio_system()
        
        # Summary
        logger.info("📋 Diagnosis Summary:")
        if self.fixes_applied:
            logger.info("Fixes applied:")
            for fix in self.fixes_applied:
                logger.info(f"  ✅ {fix}")
        
        if system_ok:
            logger.success("🎉 Audio system appears to be working correctly!")
        else:
            logger.warning("⚠️ Some audio issues detected. See above for details.")
            logger.info("💡 Try running the application now to see if issues are resolved.")
        
        return system_ok


def main():
    """Main function"""
    logger.info("🎵 Audio System Diagnostic Tool")
    logger.info("=" * 50)
    
    fixer = AudioSystemFixer()
    
    try:
        # Run diagnosis
        system_ok = fixer.run_full_diagnosis()
        
        if system_ok:
            return 0
        else:
            logger.info("\n💡 If issues persist, try:")
            logger.info("1. Restart your computer")
            logger.info("2. Check your microphone is properly connected")
            logger.info("3. Test microphone with: arecord -d 3 test.wav && aplay test.wav")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error running audio diagnosis: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())