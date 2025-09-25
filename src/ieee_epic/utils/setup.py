"""
Setup utilities for IEEE EPIC STT system.

This module handles model downloads, configuration setup,
and system verification.
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlretrieve

from loguru import logger

from ..core.config import Settings


class ModelDownloader:
    """Handle model downloads and setup."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def download_model(self, url: str, model_name: str, extract_path: Path) -> bool:
        """Download and extract a model."""
        logger.info(f"Downloading {model_name} model...")
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                # Download model
                def progress_hook(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = min(100, (block_num * block_size * 100) // total_size)
                        if percent % 10 == 0:  # Log every 10%
                            logger.info(f"Download progress: {percent}%")
                
                urlretrieve(url, tmp_file.name, reporthook=progress_hook)
                
                # Extract model
                logger.info(f"Extracting {model_name} model...")
                with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                    # Get the root directory name from the zip
                    names = zip_ref.namelist()
                    root_dir = names[0].split('/')[0] if names else model_name
                    
                    # Extract to temporary directory
                    temp_extract_dir = Path(tmp_file.name).parent / "extract"
                    zip_ref.extractall(temp_extract_dir)
                    
                    # Move to final location
                    extracted_model_dir = temp_extract_dir / root_dir
                    if extracted_model_dir.exists():
                        if extract_path.exists():
                            shutil.rmtree(extract_path)
                        shutil.move(str(extracted_model_dir), str(extract_path))
                        logger.success(f"✅ {model_name} model installed at {extract_path}")
                        return True
                    else:
                        logger.error(f"Could not find extracted model directory: {extracted_model_dir}")
                        return False
                
        except Exception as e:
            logger.error(f"Failed to download {model_name} model: {e}")
            return False
        finally:
            # Cleanup
            if 'tmp_file' in locals():
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
            if 'temp_extract_dir' in locals():
                try:
                    shutil.rmtree(temp_extract_dir)
                except:
                    pass
        
        return False
    
    def setup_english_model(self) -> bool:
        """Setup English Vosk model."""
        model_path = self.settings.models.english_model_path
        
        if model_path and model_path.exists():
            logger.info(f"English model already exists at {model_path}")
            return True
        
        url = self.settings.models.model_urls.get('en_small')
        if not url:
            logger.error("No URL configured for English model")
            return False
        
        return self.download_model(url, "English", model_path)
    
    def setup_malayalam_model(self) -> bool:
        """Setup Malayalam Vosk model."""
        model_path = self.settings.models.malayalam_model_path
        
        if model_path and model_path.exists():
            logger.info(f"Malayalam model already exists at {model_path}")
            return True
        
        url = self.settings.models.model_urls.get('ml_small')
        if not url:
            logger.warning("No URL configured for Malayalam model")
            return False
        
        logger.info("Attempting to download Malayalam model...")
        return self.download_model(url, "Malayalam", model_path)


class SystemChecker:
    """Check system requirements and configuration."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def check_audio_system(self) -> Dict[str, any]:
        """Check audio system availability."""
        result = {
            'available': False,
            'devices': [],
            'errors': []
        }
        
        try:
            import sounddevice as sd
            
            # List devices
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            result['available'] = len(input_devices) > 0
            result['devices'] = [
                {
                    'id': i,
                    'name': d['name'],
                    'channels': d['max_input_channels']
                }
                for i, d in enumerate(devices) if d['max_input_channels'] > 0
            ]
            
            if not input_devices:
                result['errors'].append("No audio input devices found")
            
        except ImportError:
            result['errors'].append("sounddevice package not available")
        except Exception as e:
            result['errors'].append(f"Audio system check failed: {e}")
        
        return result
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required dependencies are available."""
        dependencies = {
            'numpy': False,
            'sounddevice': False,
            'vosk': False,
            'openai': False,
            'whisper_cpp': False
        }
        
        for package in dependencies:
            try:
                if package == 'whisper_cpp':
                    import whisper_cpp_python
                else:
                    __import__(package)
                dependencies[package] = True
            except ImportError:
                dependencies[package] = False
        
        return dependencies
    
    def check_raspberry_pi(self) -> Dict[str, any]:
        """Check Raspberry Pi specific configuration."""
        result = {
            'is_rpi': False,
            'model': None,
            'audio_group': False,
            'memory': None
        }
        
        try:
            # Check if running on RPi
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    result['is_rpi'] = True
                    
                    # Extract model info
                    for line in cpuinfo.split('\n'):
                        if 'Model' in line:
                            result['model'] = line.split(':')[1].strip()
                            break
            
            # Check audio group membership
            try:
                import grp
                audio_group = grp.getgrnam('audio')
                current_user = os.getenv('USER')
                result['audio_group'] = current_user in audio_group.gr_mem
            except:
                pass
            
            # Check available memory
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal:' in line:
                            # Extract memory in KB and convert to MB
                            mem_kb = int(line.split()[1])
                            result['memory'] = mem_kb // 1024
                            break
            except:
                pass
                
        except FileNotFoundError:
            # Not on Linux/RPi
            pass
        
        return result


class SetupManager:
    """Main setup manager for IEEE EPIC STT system."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.downloader = ModelDownloader(settings)
        self.checker = SystemChecker(settings)
    
    def run_setup(self, force: bool = False) -> bool:
        """Run complete system setup."""
        logger.info("🔧 Starting IEEE EPIC STT setup...")
        
        success = True
        
        # Check system
        self._check_system()
        
        # Setup models
        if force or not self.settings.is_model_available('en'):
            if not self.downloader.setup_english_model():
                success = False
        
        if force or not self.settings.is_model_available('ml'):
            if not self.downloader.setup_malayalam_model():
                logger.warning("Malayalam model setup failed, but continuing...")
        
        # Create required directories
        self._setup_directories()
        
        # Setup configuration
        self._setup_configuration()
        
        # Final verification
        if success:
            success = self._verify_setup()
        
        if success:
            logger.success("🎉 Setup completed successfully!")
        else:
            logger.error("❌ Setup completed with errors")
        
        return success
    
    def _check_system(self):
        """Check system requirements."""
        logger.info("Checking system requirements...")
        
        # Check dependencies
        deps = self.checker.check_dependencies()
        for package, available in deps.items():
            status = "✅" if available else "❌"
            logger.info(f"  {package}: {status}")
        
        # Check audio
        audio_result = self.checker.check_audio_system()
        if audio_result['available']:
            logger.success(f"✅ Audio system: {len(audio_result['devices'])} input devices found")
        else:
            logger.error(f"❌ Audio system: {'; '.join(audio_result['errors'])}")
        
        # Check RPi specific
        rpi_result = self.checker.check_raspberry_pi()
        if rpi_result['is_rpi']:
            logger.info(f"🍓 Raspberry Pi detected: {rpi_result['model']}")
            if rpi_result['memory']:
                logger.info(f"  Memory: {rpi_result['memory']} MB")
            if not rpi_result['audio_group']:
                logger.warning("  User not in audio group - may need: sudo usermod -a -G audio $USER")
    
    def _setup_directories(self):
        """Create required directories."""
        logger.info("Setting up directories...")
        
        directories = [
            self.settings.paths.data_dir,
            self.settings.paths.models_dir,
            self.settings.paths.logs_dir,
            self.settings.paths.temp_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"  Created: {directory}")
            except Exception as e:
                logger.error(f"  Failed to create {directory}: {e}")
    
    def _setup_configuration(self):
        """Setup default configuration."""
        logger.info("Setting up configuration...")
        
        # Save current configuration
        config_file = Path("config.json")
        if self.settings.save_to_file(config_file):
            logger.info(f"  Configuration saved to {config_file}")
    
    def _verify_setup(self) -> bool:
        """Verify setup completion."""
        logger.info("Verifying setup...")
        
        # Check models
        en_available = self.settings.is_model_available('en')
        ml_available = self.settings.is_model_available('ml')
        
        logger.info(f"  English model: {'✅' if en_available else '❌'}")
        logger.info(f"  Malayalam model: {'✅' if ml_available else '❌'}")
        
        # At least English model should be available
        if not en_available:
            logger.error("English model is required but not available")
            return False
        
        # Test STT engine initialization
        try:
            from ..core.stt import STTEngine
            engine = STTEngine(self.settings)
            if engine.is_ready():
                logger.success("✅ STT engine initialization successful")
            else:
                logger.error("❌ STT engine failed to initialize")
                return False
        except Exception as e:
            logger.error(f"❌ STT engine test failed: {e}")
            return False
        
        return True