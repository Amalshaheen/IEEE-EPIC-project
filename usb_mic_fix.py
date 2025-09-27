#!/usr/bin/env python3
"""
USB Microphone Troubleshooting Script for Raspberry Pi
Specifically designed to fix USB microphone issues
"""

import subprocess
import os
import time
import sys
from loguru import logger

class USBMicrophoneFix:
    """Fix USB microphone issues on Raspberry Pi"""
    
    def __init__(self):
        self.usb_devices = []
        self.audio_cards = []
        self.working_device = None
    
    def check_usb_devices(self):
        """Check for USB audio devices"""
        logger.info("🔍 Checking USB devices...")
        
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if result.returncode == 0:
                usb_lines = result.stdout.split('\n')
                audio_devices = []
                
                for line in usb_lines:
                    if any(keyword in line.lower() for keyword in ['audio', 'microphone', 'webcam', 'headset', 'logitech', 'creative']):
                        audio_devices.append(line.strip())
                        logger.info(f"📱 Found USB audio device: {line.strip()}")
                
                if not audio_devices:
                    logger.warning("❌ No USB audio devices found!")
                    logger.info("💡 Try:")
                    logger.info("  - Reconnecting USB microphone")
                    logger.info("  - Using different USB port")
                    logger.info("  - Checking if device needs external power")
                    return False
                else:
                    logger.success(f"✅ Found {len(audio_devices)} USB audio device(s)")
                    self.usb_devices = audio_devices
                    return True
            else:
                logger.error("Failed to run lsusb")
                return False
                
        except Exception as e:
            logger.error(f"Error checking USB devices: {e}")
            return False
    
    def check_audio_cards(self):
        """Check ALSA audio cards"""
        logger.info("🎵 Checking ALSA audio cards...")
        
        try:
            # Check /proc/asound/cards
            if os.path.exists('/proc/asound/cards'):
                with open('/proc/asound/cards', 'r') as f:
                    cards_content = f.read()
                    logger.info("📋 Audio cards from /proc/asound/cards:")
                    for line in cards_content.split('\n'):
                        if line.strip():
                            logger.info(f"  {line}")
            
            # Check aplay -l
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("🔊 Playback devices:")
                for line in result.stdout.split('\n'):
                    if line.strip() and 'card' in line.lower():
                        logger.info(f"  {line}")
            
            # Check arecord -l  
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("🎤 Recording devices:")
                cards = []
                for line in result.stdout.split('\n'):
                    if line.strip() and 'card' in line.lower():
                        logger.info(f"  {line}")
                        cards.append(line)
                
                self.audio_cards = cards
                return len(cards) > 0
            else:
                logger.warning("❌ No recording devices found!")
                return False
                
        except Exception as e:
            logger.error(f"Error checking audio cards: {e}")
            return False
    
    def test_audio_recording(self, card_number=None, device_number=0):
        """Test audio recording with specific card"""
        logger.info(f"🎤 Testing audio recording (card {card_number}, device {device_number})...")
        
        try:
            # Build arecord command
            if card_number is not None:
                cmd = [
                    'arecord',
                    '-D', f'plughw:{card_number},{device_number}',
                    '-d', '3',
                    '-f', 'cd',
                    'usb_mic_test.wav'
                ]
            else:
                cmd = [
                    'arecord', 
                    '-d', '3',
                    '-f', 'cd', 
                    'usb_mic_test.wav'
                ]
            
            logger.info(f"🔴 Recording 3 seconds... SPEAK LOUDLY NOW!")
            logger.info(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, timeout=10)
            
            if result.returncode == 0:
                logger.success("✅ Recording completed!")
                
                # Check if file was created and has content
                if os.path.exists('usb_mic_test.wav'):
                    file_size = os.path.getsize('usb_mic_test.wav')
                    logger.info(f"📊 Recording file size: {file_size} bytes")
                    
                    if file_size > 1000:  # Should be much larger for 3 seconds
                        # Test playback
                        logger.info("🔊 Playing back recording...")
                        play_result = subprocess.run(['aplay', 'usb_mic_test.wav'], timeout=10)
                        
                        if play_result.returncode == 0:
                            logger.success("✅ Playback completed!")
                            
                            response = input("\n❓ Did you hear your voice? (y/n): ").lower().strip()
                            success = response.startswith('y')
                            
                            if success:
                                logger.success(f"🎉 USB microphone working with card {card_number}!")
                                self.working_device = (card_number, device_number)
                                return True
                            else:
                                logger.warning("⚠️ Recording worked but audio quality might be poor")
                                return False
                        else:
                            logger.error("❌ Playback failed")
                            return False
                    else:
                        logger.warning(f"⚠️ Recording file too small ({file_size} bytes) - microphone might be muted or broken")
                        return False
                else:
                    logger.error("❌ Recording file not created")
                    return False
            else:
                logger.error(f"❌ Recording failed with return code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Recording timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Recording test error: {e}")
            return False
        finally:
            # Clean up test file
            if os.path.exists('usb_mic_test.wav'):
                try:
                    os.remove('usb_mic_test.wav')
                except:
                    pass
    
    def fix_alsa_configuration(self):
        """Create/fix ALSA configuration for USB microphone"""
        logger.info("🔧 Setting up ALSA configuration...")
        
        asoundrc_content = """
# ALSA configuration for USB microphone
pcm.!default {
    type asym
    capture.pcm "mic"
    playback.pcm "speaker"
}

pcm.mic {
    type plug
    slave {
        pcm "hw:1,0"  # USB microphone (usually card 1)
    }
}

pcm.speaker {
    type plug
    slave {
        pcm "hw:0,0"  # Built-in audio (usually card 0)  
    }
}

ctl.!default {
    type hw
    card 0
}
"""
        
        try:
            home_dir = os.path.expanduser("~")
            asoundrc_path = os.path.join(home_dir, ".asoundrc")
            
            # Backup existing config
            if os.path.exists(asoundrc_path):
                backup_path = f"{asoundrc_path}.backup"
                subprocess.run(['cp', asoundrc_path, backup_path])
                logger.info(f"📁 Backed up existing .asoundrc to {backup_path}")
            
            # Write new config
            with open(asoundrc_path, 'w') as f:
                f.write(asoundrc_content)
            
            logger.success("✅ Created .asoundrc configuration")
            logger.info("🔄 Restarting ALSA...")
            
            # Restart ALSA
            subprocess.run(['sudo', 'alsa', 'force-reload'], capture_output=True)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create ALSA config: {e}")
            return False
    
    def show_mixer_instructions(self):
        """Show instructions for using alsamixer"""
        logger.info("🎛️ USB Microphone Volume Setup:")
        logger.info("")
        logger.info("1. Run: alsamixer")
        logger.info("2. Press F6 to select sound card")
        logger.info("3. Choose your USB device (usually card 1)")
        logger.info("4. Press F4 for capture devices")  
        logger.info("5. Use arrow keys to select microphone")
        logger.info("6. Press + to increase volume to 80-100%")
        logger.info("7. Press M to unmute if shows 'MM'")
        logger.info("8. Press Esc to exit")
        logger.info("")
    
    def test_all_cards(self):
        """Test all available audio cards"""
        logger.info("🧪 Testing all audio cards...")
        
        if not self.audio_cards:
            logger.error("No audio cards found")
            return False
        
        for card_info in self.audio_cards:
            # Extract card number from output like "card 1: Device [USB Audio Device]"
            try:
                if 'card' in card_info.lower():
                    card_part = card_info.split(':')[0]
                    card_num = int(card_part.split()[-1])
                    
                    logger.info(f"🧪 Testing card {card_num}: {card_info}")
                    
                    if self.test_audio_recording(card_num):
                        logger.success(f"🎉 Found working card: {card_num}")
                        return True
                    else:
                        logger.warning(f"⚠️ Card {card_num} not working properly")
                        
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse card info: {card_info}")
                continue
        
        logger.error("❌ No working audio cards found")
        return False
    
    def run_full_diagnosis(self):
        """Run complete USB microphone diagnosis"""
        logger.info("🔧 USB Microphone Complete Diagnosis")
        logger.info("=" * 60)
        
        # Step 1: Check USB devices
        usb_ok = self.check_usb_devices()
        
        # Step 2: Check audio cards
        audio_ok = self.check_audio_cards()
        
        if not usb_ok:
            logger.error("❌ USB microphone not detected!")
            logger.info("💡 Troubleshooting steps:")
            logger.info("  1. Unplug and replug USB microphone")
            logger.info("  2. Try different USB port")
            logger.info("  3. Check if microphone needs external power")
            logger.info("  4. Test microphone on another computer")
            return False
        
        if not audio_ok:
            logger.error("❌ No audio recording devices found!")
            logger.info("💡 Run: sudo apt-get install alsa-utils")
            return False
        
        # Step 3: Test audio recording
        logger.info("-" * 40)
        success = self.test_all_cards()
        
        if success:
            logger.success("🎉 USB microphone is working!")
            if self.working_device:
                card, device = self.working_device
                logger.info(f"💡 Working device: Card {card}, Device {device}")
                logger.info(f"💡 Use this in Python: hw:{card},{device}")
        else:
            logger.error("❌ USB microphone not working")
            
            # Step 4: Try fixing ALSA config
            logger.info("-" * 40)
            logger.info("🔧 Attempting to fix ALSA configuration...")
            self.fix_alsa_configuration()
            
            # Show manual instructions
            self.show_mixer_instructions()
            
            logger.info("💡 After running alsamixer, test again with:")
            logger.info("  arecord -d 3 test.wav && aplay test.wav")
        
        return success


def main():
    """Main function"""
    fixer = USBMicrophoneFix()
    success = fixer.run_full_diagnosis()
    
    if not success:
        logger.info("\n" + "=" * 60)
        logger.info("🆘 USB Microphone Troubleshooting Summary:")
        logger.info("")
        logger.info("1. Check USB connection:")
        logger.info("   lsusb | grep -i audio")
        logger.info("")
        logger.info("2. Check audio cards:")
        logger.info("   arecord -l")
        logger.info("")
        logger.info("3. Test recording:")
        logger.info("   arecord -D plughw:1,0 -d 3 test.wav")
        logger.info("   aplay test.wav")
        logger.info("")
        logger.info("4. Adjust volume:")
        logger.info("   alsamixer")
        logger.info("   - Press F6, select USB device")
        logger.info("   - Press F4 for capture")
        logger.info("   - Increase microphone volume")
        logger.info("")
        logger.info("5. Add to audio group:")
        logger.info("   sudo usermod -a -G audio $USER")
        logger.info("   sudo reboot")


if __name__ == "__main__":
    main()