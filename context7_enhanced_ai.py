"""
Context7 Enhanced AI Response System
Integrates Context7 library documentation with AI responses
"""

import os
import asyncio
from typing import Optional, Dict, Any
from loguru import logger

# Try to import Context7 tools
try:
    from ieee_epic.core.ai_response import AIResponseSystem
    from ieee_epic.core.config import Settings
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class Context7EnhancedAI:
    """AI Response System enhanced with Context7 library documentation"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        
        # Initialize base AI system
        if AI_AVAILABLE:
            self.ai_system = AIResponseSystem(self.settings)
            self.context7_available = True
        else:
            self.ai_system = None
            self.context7_available = False
            logger.warning("AI system not available")
        
        # Context7 library cache
        self.library_cache = {}
        
        # Common programming/technical keywords that might benefit from Context7
        self.technical_keywords = [
            'python', 'javascript', 'react', 'nodejs', 'flask', 'django', 
            'tensorflow', 'pytorch', 'opencv', 'numpy', 'pandas', 'matplotlib',
            'api', 'rest', 'graphql', 'database', 'sql', 'mongodb', 'redis',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'github',
            'machine learning', 'ai', 'deep learning', 'neural network',
            'programming', 'code', 'development', 'software', 'algorithm',
            'data structure', 'function', 'class', 'variable', 'loop', 'array'
        ]
    
    def _contains_technical_content(self, text: str) -> bool:
        """Check if text contains technical/programming content"""
        text_lower = text.lower()
        
        # Check for technical keywords
        for keyword in self.technical_keywords:
            if keyword in text_lower:
                return True
        
        # Check for code-like patterns
        code_patterns = ['()', '{}', '[]', '.py', '.js', '.html', '.css', 'import ', 'from ', 'def ', 'class ']
        for pattern in code_patterns:
            if pattern in text_lower:
                return True
        
        return False
    
    def _extract_library_name(self, text: str) -> Optional[str]:
        """Extract potential library name from user query"""
        text_lower = text.lower()
        
        # Common library mappings
        library_mappings = {
            'react': 'react',
            'nextjs': 'next.js',
            'next js': 'next.js',
            'flask': 'flask',
            'django': 'django',
            'tensorflow': 'tensorflow',
            'pytorch': 'pytorch',
            'opencv': 'opencv',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'fastapi': 'fastapi',
            'express': 'express',
            'mongodb': 'mongodb',
            'postgresql': 'postgresql',
            'mysql': 'mysql',
            'redis': 'redis',
            'docker': 'docker',
            'kubernetes': 'kubernetes'
        }
        
        for keyword, library in library_mappings.items():
            if keyword in text_lower:
                return library
        
        return None
    
    async def get_context7_docs(self, library_name: str, topic: Optional[str] = None) -> Optional[str]:
        """Get documentation from Context7 for a specific library"""
        if not self.context7_available:
            return None
        
        try:
            # This would be replaced with actual Context7 MCP calls
            # For now, we'll simulate with a placeholder
            logger.info(f"Fetching Context7 docs for {library_name}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Return placeholder documentation
            docs = f"""
# {library_name.title()} Documentation Summary

## Overview
{library_name.title()} is a powerful library for software development.

## Key Features
- Feature 1: High performance and reliability
- Feature 2: Easy to use API
- Feature 3: Extensive documentation
- Feature 4: Active community support

## Common Usage Patterns
```python
# Basic usage example for {library_name}
import {library_name}

# Initialize
{library_name}_instance = {library_name}.create()

# Use the library
result = {library_name}_instance.process()
```

## Best Practices
1. Always handle errors appropriately
2. Follow the official documentation
3. Use type hints for better code quality
4. Write unit tests for your code

For more detailed information, check the official {library_name} documentation.
"""
            
            # Cache the documentation
            self.library_cache[library_name] = docs
            return docs
            
        except Exception as e:
            logger.error(f"Failed to fetch Context7 docs for {library_name}: {e}")
            return None
    
    async def generate_enhanced_response(self, user_input: str, language: str = "en") -> str:
        """Generate AI response enhanced with Context7 documentation"""
        if not self.ai_system:
            return self._get_fallback_response(user_input, language)
        
        try:
            # Check if this is a technical query
            is_technical = self._contains_technical_content(user_input)
            enhanced_prompt = user_input
            
            if is_technical:
                logger.info("Technical query detected, checking for library documentation")
                
                # Try to extract library name
                library_name = self._extract_library_name(user_input)
                
                if library_name:
                    # Get Context7 documentation
                    docs = await self.get_context7_docs(library_name)
                    
                    if docs:
                        # Enhance the prompt with documentation
                        enhanced_prompt = f"""
User Query: {user_input}

Relevant Documentation:
{docs}

Please answer the user's query using the provided documentation context. 
Be concise but informative. If the documentation doesn't fully answer the query, 
provide general guidance and suggest checking official documentation.
"""
                        logger.info(f"Enhanced prompt with {library_name} documentation")
            
            # Generate AI response with enhanced context
            response = self.ai_system.generate_response(enhanced_prompt, use_context=True)
            
            # Add a note about Context7 enhancement if docs were used
            if is_technical and library_name and library_name in self.library_cache:
                if language == "ml":
                    response += f"\n\n📚 {library_name} ഡോക്യുമെന്റേഷൻ സഹായത്തോടെ മറുപടി നൽകി."
                else:
                    response += f"\n\n📚 Response enhanced with {library_name} documentation."
            
            return response
            
        except Exception as e:
            logger.error(f"Enhanced response generation failed: {e}")
            return self._get_fallback_response(user_input, language)
    
    def _get_fallback_response(self, user_input: str, language: str) -> str:
        """Get fallback response when AI is not available"""
        if language == "ml":
            return f"AI സിസ്റ്റം ലഭ്യമല്ല. നിങ്ങൾ പറഞ്ഞത്: {user_input}"
        else:
            return f"AI system not available. You said: {user_input}"
    
    def clear_cache(self):
        """Clear the Context7 documentation cache"""
        self.library_cache.clear()
        logger.info("Context7 documentation cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached documentation"""
        return {
            'cached_libraries': list(self.library_cache.keys()),
            'cache_size': len(self.library_cache),
            'context7_available': self.context7_available
        }
    
    def is_available(self) -> bool:
        """Check if the enhanced AI system is available"""
        return self.ai_system is not None
    
    async def interactive_demo(self):
        """Run interactive demo of Context7 enhanced AI"""
        print("🚀 Context7 Enhanced AI Demo")
        print("Ask technical questions to see Context7 documentation integration!")
        print("Type 'quit' to exit, 'cache' to see cache info, 'clear' to clear cache")
        print()
        
        while True:
            try:
                user_input = input("🎤 You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'cache':
                    cache_info = self.get_cache_info()
                    print(f"📊 Cache Info: {cache_info}")
                    continue
                elif user_input.lower() == 'clear':
                    self.clear_cache()
                    print("🗑️ Cache cleared!")
                    continue
                
                if not user_input:
                    continue
                
                print("🤖 AI: Thinking...", end="", flush=True)
                response = await self.generate_enhanced_response(user_input)
                print(f"\r🤖 AI: {response}")
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """Main function for testing Context7 enhanced AI"""
    try:
        enhanced_ai = Context7EnhancedAI()
        
        if not enhanced_ai.is_available():
            print("❌ AI system not available. Please check your configuration.")
            return
        
        await enhanced_ai.interactive_demo()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())