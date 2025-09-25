"""
AI Response System for IEEE EPIC STT system.

This module provides intelligent response generation for recognized speech,
with both online (OpenAI) and offline capabilities.
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from loguru import logger

from .config import Settings


class OfflineResponseGenerator:
    """Offline response generation using predefined patterns and responses."""
    
    def __init__(self, responses_file: Optional[Path] = None):
        self.responses_file = responses_file or Path("data/offline_responses.json")
        self.responses: Dict[str, List[str]] = {}
        self.patterns: Dict[str, str] = {}
        self._load_responses()
    
    def _load_responses(self):
        """Load offline responses from file."""
        try:
            if self.responses_file.exists():
                with open(self.responses_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.responses = data.get('responses', {})
                    self.patterns = data.get('patterns', {})
                logger.info(f"Loaded {len(self.responses)} response categories")
            else:
                self._create_default_responses()
        except Exception as e:
            logger.error(f"Failed to load offline responses: {e}")
            self._create_default_responses()
    
    def _create_default_responses(self):
        """Create default response patterns and save to file."""
        default_data = {
            "patterns": {
                "greeting": r"(hello|hi|hey|good morning|good evening|namaste)",
                "question": r"\b(what|who|when|where|why|how)\b",
                "weather": r"\b(weather|temperature|rain|sunny|cloud)\b",
                "time": r"\b(time|clock|hour|minute)\b",
                "goodbye": r"\b(bye|goodbye|see you|farewell)\b",
                "thanks": r"\b(thank|thanks|appreciate)\b",
                "malayalam_greeting": r"\b(വണക്കം|നമസ്കാരം|എങ്ങനെയുണ്ട്)\b",
                "malayalam_question": r"\b(എന്താണ്|എവിടെ|എപ്പോൾ|എങ്ങനെ)\b"
            },
            "responses": {
                "greeting": [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?",
                    "Good to see you! How may I assist?",
                    "വണക്കം! എന്തുസഹായം വേണം?"  # Malayalam greeting
                ],
                "question": [
                    "That's an interesting question. Let me think about it.",
                    "I understand you're asking about something. Could you be more specific?",
                    "That's a good question. I'd be happy to help if you can provide more details.",
                    "നല്ല ചോദ്യമാണ്. കൂടുതൽ വിവരങ്ങൾ പറഞ്ഞാൽ സഹായിക്കാം."  # Malayalam
                ],
                "weather": [
                    "I don't have access to current weather data, but you can check your local weather app.",
                    "For weather information, I'd recommend checking a reliable weather service.",
                    "കാലാവസ്ഥയെക്കുറിച്ച് അറിയാൻ കാലാവസ്ഥാ ആപ്പ് നോക്കൂ."  # Malayalam
                ],
                "time": [
                    "I don't have access to the current time. Please check your device's clock.",
                    "You can check the time on your computer or phone.",
                    "സമയം അറിയാൻ നിങ്ങളുടെ ഫോൺ നോക്കൂ."  # Malayalam
                ],
                "goodbye": [
                    "Goodbye! Have a great day!",
                    "See you later! Take care!",
                    "Farewell! It was nice talking to you!",
                    "വിടകൊള്ളട്ടെ! നല്ല ദിവസമാകട്ടെ!"  # Malayalam goodbye
                ],
                "thanks": [
                    "You're welcome! Happy to help!",
                    "No problem at all!",
                    "Glad I could assist!",
                    "സന്തോഷമായി! എപ്പോഴും സഹായിക്കാം!"  # Malayalam
                ],
                "malayalam_greeting": [
                    "വണക്കം! എന്തുസഹായം വേണം?",
                    "നമസ്കാരം! എന്തു ചെയ്യാൻ കഴിയും?",
                    "Hello! How can I help you in Malayalam?"
                ],
                "malayalam_question": [
                    "നല്ല ചോദ്യമാണ്. കൂടുതൽ വിവരങ്ങൾ പറയാമോ?",
                    "മനസ്സിലായി. കൂടുതൽ വിശദീകരിക്കാമോ?",
                    "That's a good question in Malayalam. Could you provide more details?"
                ],
                "default": [
                    "I heard you, but I'm not sure how to respond to that. Could you rephrase?",
                    "Interesting! Tell me more about that.",
                    "I understand you're saying something, but I need more context to help properly.",
                    "മനസ്സിലാകുന്നില്ല. വീണ്ടും പറയാമോ?"  # Malayalam default
                ]
            }
        }
        
        # Ensure directory exists
        self.responses_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save default responses
        with open(self.responses_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        self.responses = default_data['responses']
        self.patterns = default_data['patterns']
        logger.info("Created default offline responses")
    
    def generate_response(self, text: str) -> str:
        """Generate response based on input text patterns."""
        if not text.strip():
            return random.choice(self.responses.get('default', ['Hello!']))
        
        text_lower = text.lower()
        
        # Check each pattern
        for category, pattern in self.patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                responses = self.responses.get(category, self.responses.get('default', ['Hello!']))
                return random.choice(responses)
        
        # If no pattern matches, use default responses
        return random.choice(self.responses.get('default', ['I heard you!']))


class OnlineResponseGenerator:
    """Online response generation using OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if api_key:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI package not available. Please install: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def generate_response(self, text: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """Generate response using OpenAI API."""
        if not self.client or not text.strip():
            return None
        
        try:
            # Create system message for context
            system_message = """You are a helpful AI assistant for the IEEE EPIC project. 
            You can respond in both English and Malayalam. Keep responses concise and friendly.
            If the input is in Malayalam, try to respond in Malayalam when appropriate."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if online response generation is available."""
        return self.client is not None


class ConversationHistory:
    """Manage conversation history and context."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
    
    def add_interaction(self, user_input: str, ai_response: str):
        """Add a user-AI interaction to history."""
        interaction = {
            "user": user_input,
            "ai": ai_response,
            "timestamp": str(Path(__file__).stat().st_mtime)  # Simple timestamp
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
    
    def clear(self):
        """Clear conversation history."""
        self.history.clear()


class AIResponseSystem:
    """Main AI response system with multiple generation methods."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        
        # Initialize generators
        self.offline_generator = OfflineResponseGenerator(
            self.settings.ai.offline_responses_file
        )
        
        self.online_generator = None
        if self.settings.ai.openai_api_key and self.settings.ai.enabled:
            self.online_generator = OnlineResponseGenerator(
                api_key=self.settings.ai.openai_api_key,
                model=self.settings.ai.model
            )
        
        # Conversation history
        self.conversation = ConversationHistory()
        
        logger.info("🤖 AI Response System initialized")
    
    def generate_response(self, user_input: str) -> str:
        """Generate AI response for user input."""
        if not user_input.strip():
            return "I didn't hear anything. Could you please speak again?"
        
        logger.info(f"Generating response for: '{user_input}'")
        
        response = None
        
        # Try online generation first (if available and enabled)
        if (self.online_generator and 
            self.online_generator.is_available() and 
            not self.settings.ai.offline_mode):
            
            try:
                # Add conversation context for online generation
                context = self.conversation.get_context()
                enhanced_input = f"{context}\nUser: {user_input}" if context else user_input
                
                response = self.online_generator.generate_response(
                    enhanced_input,
                    max_tokens=self.settings.ai.max_tokens,
                    temperature=self.settings.ai.temperature
                )
                
                if response:
                    logger.info("Generated online AI response")
                
            except Exception as e:
                logger.warning(f"Online generation failed: {e}")
        
        # Fallback to offline generation
        if not response:
            response = self.offline_generator.generate_response(user_input)
            logger.info("Generated offline AI response")
        
        # Add to conversation history
        self.conversation.add_interaction(user_input, response)
        
        return response
    
    def interactive_demo(self):
        """Run interactive AI response demo."""
        logger.info("🤖 AI Response System Demo")
        logger.info("Type 'quit' to exit, 'clear' to clear history")
        
        online_status = "✅ Online" if (self.online_generator and self.online_generator.is_available()) else "❌ Offline only"
        logger.info(f"Status: {online_status}")
        
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
                
                # Generate and display response
                response = self.generate_response(user_input)
                logger.info(f"🤖 AI: {response}")
                
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def get_status(self) -> Dict[str, any]:
        """Get AI system status."""
        return {
            'offline_available': True,
            'online_available': self.online_generator.is_available() if self.online_generator else False,
            'conversation_length': len(self.conversation.history),
            'offline_mode': self.settings.ai.offline_mode,
            'model': self.settings.ai.model if self.online_generator else 'offline'
        }