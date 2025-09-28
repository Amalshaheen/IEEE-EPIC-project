"""
AI Response System for IEEE EPIC STT system using Google Gemini.

This module provides intelligent response generation for recognized speech
using Google's Gemini API with bilingual support for English and Malayalam,
and integrated Text-to-Speech capabilities.
"""

import asyncio
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

from loguru import logger

from .config import Settings

# Check if Google GenAI is available
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("Google GenAI not available. Install with: pip install google-genai")


class GeminiResponseGenerator:
    """Gemini-based AI response generation with bilingual support."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash", 
                 system_instruction: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.system_instruction = system_instruction
        self.client = None
        
        if not GENAI_AVAILABLE:
            logger.error("Google GenAI library is not installed. Please run: pip install google-genai")
            return
            
        if self.api_key:
            self._initialize_client()
        else:
            logger.warning("No Gemini API key provided. Set GOOGLE_API_KEY environment variable.")
    
    def _initialize_client(self):
        """Initialize Gemini client."""
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✅ Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
    
    def generate_response(self, text: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """Generate response using Gemini API."""
        if not self.client or not text.strip():
            return None
        
        try:
            # Create configuration with system instruction
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=self.system_instruction
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=text.strip(),
                config=config
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            return None
    
    def generate_response_stream(self, text: str, max_tokens: int = 150, temperature: float = 0.7):
        """Generate streaming response using Gemini API."""
        if not self.client or not text.strip():
            return None
        
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=self.system_instruction
            )
            
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=text.strip(),
                config=config
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini streaming API request failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Gemini response generation is available."""
        return GENAI_AVAILABLE and self.client is not None


class ConversationHistory:
    """Manage conversation history and context."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
    
    def add_interaction(self, user_input: str, ai_response: str):
        """Add a user-AI interaction to history."""
        from datetime import datetime
        
        interaction = {
            "user": user_input,
            "ai": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        
        self.history.append(interaction)
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_context(self) -> str:
        """Get conversation context for AI."""
        if not self.history:
            return ""
        
        context_parts = []
        for interaction in self.history[-3:]:  # Last 3 interactions
            context_parts.append(f"User: {interaction['user']}")
            context_parts.append(f"AI: {interaction['ai']}")
        
        return "\n".join(context_parts)
    
    def get_formatted_history(self) -> List[types.Content]:
        """Get conversation history formatted for Gemini API."""
        if not self.history:
            return []
        
        formatted_history = []
        for interaction in self.history[-5:]:  # Last 5 interactions
            # Add user message
            formatted_history.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(interaction["user"])]
                )
            )
            # Add AI response
            formatted_history.append(
                types.Content(
                    role="model", 
                    parts=[types.Part.from_text(interaction["ai"])]
                )
            )
        
        return formatted_history
    
    def clear(self):
        """Clear conversation history."""
        self.history.clear()


class AIResponseSystem:
    """Main AI response system using Google Gemini with TTS integration."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        
        # Initialize Gemini generator
        self.gemini_generator = None
        if self.settings.ai.enabled:
            self.gemini_generator = GeminiResponseGenerator(
                api_key=self.settings.ai.gemini_api_key,
                model=self.settings.ai.model,
                system_instruction=self.settings.ai.system_instruction
            )
        
        # Initialize TTS engine
        self.tts_engine = None
        if self.settings.tts.enabled:
            try:
                from .tts import TTSEngine
                self.tts_engine = TTSEngine(self.settings)
                logger.info("✅ TTS engine initialized for AI responses")
            except ImportError as e:
                logger.error(f"Failed to import TTS engine: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize TTS engine: {e}")
        
        # Conversation history
        self.conversation = ConversationHistory()
        
        # Fallback responses for when Gemini is unavailable
        self.fallback_responses = {
            "en": [
                "I heard you, but I'm having trouble connecting to the AI service right now.",
                "Sorry, I'm temporarily unavailable. Please try again in a moment.",
                "I'm experiencing some technical difficulties. Could you repeat that?"
            ],
            "ml": [
                "മനസ്സിലായി, പക്ഷേ ഇപ്പോൾ AI സേവനവുമായി ബന്ധപ്പെടാൻ കഴിയുന്നില്ല.",
                "ക്ഷമിക്കുക, ഞാൻ താൽക്കാലികമായി ലഭ്യമല്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.",
                "എനിക്ക് ചില സാങ്കേതിക പ്രശ്നങ്ങൾ അനുഭവപ്പെടുന്നു. അത് വീണ്ടും പറയാമോ?"
            ]
        }
        
        logger.info("🤖 AI Response System initialized with Gemini")
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection for Malayalam vs English."""
        malayalam_chars = set("അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ")
        text_chars = set(text)
        
        if malayalam_chars.intersection(text_chars):
            return "ml"
        return "en"
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Get a fallback response when Gemini is unavailable."""
        import random
        
        language = self._detect_language(user_input)
        responses = self.fallback_responses.get(language, self.fallback_responses["en"])
        return random.choice(responses)
    
    def generate_response(self, user_input: str, use_context: bool = True) -> str:
        """Generate AI response for user input."""
        if not user_input.strip():
            return "I didn't hear anything. Could you please speak again?"
        
        logger.info(f"Generating response for: '{user_input}'")
        
        # Check if Gemini is available
        if not self.gemini_generator or not self.gemini_generator.is_available():
            logger.warning("Gemini API unavailable, using fallback response")
            response = self._get_fallback_response(user_input)
            self.conversation.add_interaction(user_input, response)
            return response
        
        try:
            # Prepare input with context if requested
            if use_context and self.conversation.history:
                context = self.conversation.get_context()
                enhanced_input = f"Previous conversation:\n{context}\n\nUser: {user_input}"
            else:
                enhanced_input = user_input
            
            # Generate response using Gemini
            response = self.gemini_generator.generate_response(
                enhanced_input,
                max_tokens=self.settings.ai.max_tokens,
                temperature=self.settings.ai.temperature
            )
            
            if response:
                logger.info("Generated Gemini AI response")
                self.conversation.add_interaction(user_input, response)
                return response
            else:
                logger.warning("Empty response from Gemini, using fallback")
                fallback = self._get_fallback_response(user_input)
                self.conversation.add_interaction(user_input, fallback)
                return fallback
                
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            fallback = self._get_fallback_response(user_input)
            self.conversation.add_interaction(user_input, fallback)
            return fallback
    
    def generate_response_stream(self, user_input: str, use_context: bool = True):
        """Generate streaming AI response for user input."""
        if not user_input.strip():
            yield "I didn't hear anything. Could you please speak again?"
            return
        
        logger.info(f"Generating streaming response for: '{user_input}'")
        
        # Check if Gemini is available
        if not self.gemini_generator or not self.gemini_generator.is_available():
            logger.warning("Gemini API unavailable, using fallback response")
            response = self._get_fallback_response(user_input)
            self.conversation.add_interaction(user_input, response)
            yield response
            return
        
        try:
            # Prepare input with context if requested
            if use_context and self.conversation.history:
                context = self.conversation.get_context()
                enhanced_input = f"Previous conversation:\n{context}\n\nUser: {user_input}"
            else:
                enhanced_input = user_input
            
            # Generate streaming response using Gemini
            stream = self.gemini_generator.generate_response_stream(
                enhanced_input,
                max_tokens=self.settings.ai.max_tokens,
                temperature=self.settings.ai.temperature
            )
            
            if stream:
                full_response = ""
                for chunk in stream:
                    if chunk.text:
                        full_response += chunk.text
                        yield chunk.text
                
                # Add complete response to conversation history
                if full_response:
                    self.conversation.add_interaction(user_input, full_response)
                    logger.info("Generated streaming Gemini AI response")
            else:
                logger.warning("No stream from Gemini, using fallback")
                fallback = self._get_fallback_response(user_input)
                self.conversation.add_interaction(user_input, fallback)
                yield fallback
                
        except Exception as e:
            logger.error(f"Error generating streaming Gemini response: {e}")
            fallback = self._get_fallback_response(user_input)
            self.conversation.add_interaction(user_input, fallback)
            yield fallback
    
    def create_chat_session(self):
        """Create a persistent chat session using Gemini's chat API."""
        if not self.gemini_generator or not self.gemini_generator.is_available():
            return None
        
        try:
            # Create chat with system instruction
            chat = self.gemini_generator.client.chats.create(
                model=self.gemini_generator.model,
                config=types.CreateChatConfig(
                    system_instruction=self.settings.ai.system_instruction
                )
            )
            return chat
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return None
    
    def interactive_demo(self):
        """Run interactive AI response demo."""
        logger.info("🤖 AI Response System Demo (Powered by Gemini)")
        logger.info("Type 'quit' to exit, 'clear' to clear history, 'stream' to toggle streaming")
        
        if self.gemini_generator and self.gemini_generator.is_available():
            logger.info("✅ Gemini API connected")
        else:
            logger.info("❌ Gemini API unavailable - using fallback responses only")
        
        use_streaming = False
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                elif user_input.lower() == 'quit':
                    logger.info("👋 Goodbye!")
                    break
                elif user_input.lower() == 'clear':
                    self.conversation.clear()
                    logger.info("🗑️ Conversation history cleared")
                    continue
                elif user_input.lower() == 'stream':
                    use_streaming = not use_streaming
                    logger.info(f"🔄 Streaming {'enabled' if use_streaming else 'disabled'}")
                    continue
                
                # Generate and display response
                if use_streaming:
                    print("🤖 AI: ", end="", flush=True)
                    for chunk in self.generate_response_stream(user_input):
                        print(chunk, end="", flush=True)
                    print()  # New line after streaming
                else:
                    response = self.generate_response(user_input)
                    logger.info(f"🤖 AI: {response}")
                
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    async def generate_and_speak_response(self, user_input: str, use_context: bool = True) -> str:
        """Generate AI response and speak it aloud."""
        response = self.generate_response(user_input, use_context)
        
        if self.tts_engine and response:
            try:
                # Detect language and speak
                language = self._detect_language(response)
                success = await self.tts_engine.speak(response, language)
                
                if success:
                    logger.success("✅ AI response spoken successfully")
                else:
                    logger.warning("⚠️ TTS playback failed, response generated only")
                    
            except Exception as e:
                logger.error(f"TTS error: {e}")
        
        return response
    
    async def generate_response_stream_with_tts(self, user_input: str, use_context: bool = True):
        """Generate streaming AI response with optional TTS."""
        full_response = ""
        
        # Collect streaming response
        for chunk in self.generate_response_stream(user_input, use_context):
            full_response += chunk
            yield chunk
        
        # Speak the complete response if TTS is enabled
        if self.tts_engine and full_response:
            try:
                language = self._detect_language(full_response)
                asyncio.create_task(self.tts_engine.speak(full_response, language))
                logger.info("🔊 Speaking AI response in background")
            except Exception as e:
                logger.error(f"Background TTS error: {e}")
    
    def speak_text(self, text: str, language: str = "auto") -> bool:
        """Speak given text using TTS engine."""
        if not self.tts_engine:
            logger.warning("TTS engine not available")
            return False
        
        try:
            # Run async speak method
            success = asyncio.run(self.tts_engine.speak(text, language))
            return success
        except Exception as e:
            logger.error(f"Failed to speak text: {e}")
            return False
    
    def is_tts_available(self) -> bool:
        """Check if TTS functionality is available."""
        return self.tts_engine is not None and self.tts_engine.is_ready()
    
    def get_status(self) -> Dict[str, any]:
        """Get AI system status."""
        gemini_available = (self.gemini_generator and 
                           self.gemini_generator.is_available())
        
        return {
            'gemini_available': gemini_available,
            'genai_library_available': GENAI_AVAILABLE,
            'conversation_length': len(self.conversation.history),
            'model': self.settings.ai.model,
            'api_key_configured': bool(self.settings.ai.gemini_api_key),
            'enabled': self.settings.ai.enabled,
            'tts_available': self.is_tts_available(),
            'tts_enabled': self.settings.tts.enabled
        }