"""
Advanced Wake Word Detection using Pocketsphinx
More accurate and efficient than continuous Google Speech Recognition
"""

import threading
import time
from typing import Callable, List, Optional
from loguru import logger

try:
    import speech_recognition as sr
    from pocketsphinx import pocketsphinx, Jsgf, FsgModel
    POCKETSPHINX_AVAILABLE = True
except ImportError:
    POCKETSPHINX_AVAILABLE = False
    logger.warning("Pocketsphinx not available, falling back to Google Speech Recognition")


class AdvancedWakeWordDetector:
    """Advanced wake word detector using Pocketsphinx for offline detection"""
    
    def __init__(self, wake_words: List[str] = None, confidence_threshold: float = 0.7):
        """
        Initialize advanced wake word detector
        
        Args:
            wake_words: List of wake words/phrases
            confidence_threshold: Minimum confidence score (0.0-1.0)
        """
        self.wake_words = wake_words or ["hey saras", "hello saras", "wake up saras"]
        self.confidence_threshold = confidence_threshold
        self.is_listening = False
        self.callback = None
        
        # Initialize recognizer and microphone
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        if POCKETSPHINX_AVAILABLE:
            self._setup_pocketsphinx()
        else:
            self._setup_fallback()
    
    def _setup_pocketsphinx(self):
        """Setup Pocketsphinx for offline wake word detection"""
        try:
            # Initialize microphone
            self.microphone = sr.Microphone()
            
            # Create grammar for wake words
            grammar_content = self._create_wake_word_grammar()
            
            # Setup Pocketsphinx with custom grammar
            config = pocketsphinx.Decoder.default_config()
            config.set_string('-hmm', pocketsphinx.get_model_path() + '/en-us')
            config.set_string('-dict', pocketsphinx.get_model_path() + '/cmudict-en-us.dict')
            config.set_float('-kws_threshold', 1e-20)  # Lower threshold for better detection
            config.set_string('-logfn', '/dev/null')  # Disable verbose logging
            
            self.decoder = pocketsphinx.Decoder(config)
            
            # Add wake word keywords
            self._add_wake_word_keywords()
            
            logger.info("✅ Pocketsphinx wake word detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup Pocketsphinx: {e}")
            logger.info("Falling back to Google Speech Recognition")
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback wake word detection using Google Speech Recognition"""
        try:
            self.microphone = sr.Microphone()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.5
            
            with self.microphone as source:
                logger.info("Calibrating microphone for fallback wake word detection...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            self.use_pocketsphinx = False
            logger.info("✅ Fallback wake word detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup fallback wake word detector: {e}")
            self.microphone = None
    
    def _create_wake_word_grammar(self) -> str:
        """Create JSGF grammar for wake words"""
        grammar_rules = []
        for i, wake_word in enumerate(self.wake_words):
            rule_name = f"wakeword{i}"
            words = wake_word.upper().replace(" ", " ")
            grammar_rules.append(f"<{rule_name}> = {words};")
        
        main_rule = " | ".join([f"<wakeword{i}>" for i in range(len(self.wake_words))])
        
        grammar = f"""
#JSGF V1.0;
grammar wakewords;
{chr(10).join(grammar_rules)}
public <wake> = {main_rule};
        """
        return grammar.strip()
    
    def _add_wake_word_keywords(self):
        """Add wake words as keywords to Pocketsphinx"""
        if hasattr(self, 'decoder'):
            for wake_word in self.wake_words:
                # Convert to format expected by Pocketsphinx
                keyword = wake_word.lower().replace(" ", "_")
                self.decoder.set_kws("wake_words", {keyword: 1e-20})
    
    def set_callback(self, callback: Callable):
        """Set callback for wake word detection"""
        self.callback = callback
    
    def start_listening(self) -> bool:
        """Start wake word detection"""
        if not self.microphone:
            logger.error("Cannot start wake word detection - microphone not available")
            return False
        
        self.is_listening = True
        
        if POCKETSPHINX_AVAILABLE and hasattr(self, 'decoder'):
            listening_thread = threading.Thread(target=self._pocketsphinx_listen_loop, daemon=True)
        else:
            listening_thread = threading.Thread(target=self._fallback_listen_loop, daemon=True)
        
        listening_thread.start()
        logger.info(f"🎤 Advanced wake word detection started for: {', '.join(self.wake_words)}")
        return True
    
    def stop_listening(self):
        """Stop wake word detection"""
        self.is_listening = False
        logger.info("🎤 Advanced wake word detection stopped")
    
    def _pocketsphinx_listen_loop(self):
        """Pocketsphinx listening loop for offline detection"""
        logger.info("Using Pocketsphinx for offline wake word detection")
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                # Convert to format for Pocketsphinx
                audio_data = audio.get_wav_data()
                
                # Process with Pocketsphinx
                self.decoder.start_utt()
                self.decoder.process_raw(audio_data, False, False)
                self.decoder.end_utt()
                
                # Check for wake word detection
                if self.decoder.hyp():
                    hypothesis = self.decoder.hyp()
                    confidence = self.decoder.get_prob()
                    detected_phrase = hypothesis.hypstr
                    
                    logger.debug(f"Detected: '{detected_phrase}' (confidence: {confidence})")
                    
                    if confidence >= self.confidence_threshold:
                        # Check if detected phrase matches any wake word
                        for wake_word in self.wake_words:
                            wake_word_normalized = wake_word.lower().replace(" ", "")
                            detected_normalized = detected_phrase.lower().replace(" ", "")
                            
                            if wake_word_normalized in detected_normalized or detected_normalized in wake_word_normalized:
                                logger.success(f"🎯 Wake word detected: '{detected_phrase}' (confidence: {confidence})")
                                if self.callback:
                                    self.callback()
                                break
            
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Pocketsphinx detection error: {e}")
                time.sleep(1)
    
    def _fallback_listen_loop(self):
        """Fallback listening loop using Google Speech Recognition"""
        logger.info("Using Google Speech Recognition for wake word detection")
        consecutive_failures = 0
        max_failures = 3
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
                
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    text_lower = text.lower().strip()
                    
                    logger.debug(f"Heard: '{text_lower}'")
                    
                    # Check for wake word matches
                    for wake_word in self.wake_words:
                        if wake_word.lower() in text_lower:
                            logger.success(f"🎯 Wake word detected: '{wake_word}' in '{text}'")
                            consecutive_failures = 0
                            if self.callback:
                                self.callback()
                            break
                    
                    consecutive_failures = 0
                    
                except sr.UnknownValueError:
                    consecutive_failures = 0
                    continue
                except sr.RequestError as e:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        logger.warning(f"Multiple recognition failures, taking a break...")
                        time.sleep(5)
                        consecutive_failures = 0
            
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Fallback detection error: {e}")
                time.sleep(1)
    
    def is_available(self) -> bool:
        """Check if wake word detection is available"""
        return self.microphone is not None
    
    def get_detection_method(self) -> str:
        """Get current detection method"""
        if POCKETSPHINX_AVAILABLE and hasattr(self, 'decoder'):
            return "Pocketsphinx (Offline)"
        else:
            return "Google Speech Recognition (Online)"


# Installation instructions for Pocketsphinx
POCKETSPHINX_INSTALL_INSTRUCTIONS = """
To install Pocketsphinx for better wake word detection:

1. Install system dependencies:
   sudo apt-get install swig libpulse-dev

2. Install Python packages:
   pip install pocketsphinx
   pip install pyaudio

3. For Raspberry Pi, you might also need:
   sudo apt-get install python3-dev
   sudo apt-get install portaudio19-dev

If installation fails, the system will automatically fall back to 
Google Speech Recognition for wake word detection.
"""

if __name__ == "__main__":
    # Test the advanced wake word detector
    def on_wake_word():
        print("Wake word detected!")
    
    if not POCKETSPHINX_AVAILABLE:
        print(POCKETSPHINX_INSTALL_INSTRUCTIONS)
    
    detector = AdvancedWakeWordDetector()
    detector.set_callback(on_wake_word)
    
    print(f"Detection method: {detector.get_detection_method()}")
    print(f"Wake words: {detector.wake_words}")
    
    if detector.start_listening():
        try:
            print("Listening for wake words... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...")
            detector.stop_listening()
    else:
        print("Failed to start wake word detection")