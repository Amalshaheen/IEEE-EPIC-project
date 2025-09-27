#!/usr/bin/env python3
"""
Google API Key Tester for IEEE EPIC Project
Tests if your Google API key works with Gemini
"""

import os
import sys
from loguru import logger

def test_google_api_key():
    """Test if Google API key works with Gemini"""
    
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("❌ No API key found!")
        logger.info("💡 Set your API key:")
        logger.info("export GOOGLE_API_KEY='your-api-key-here'")
        return False
    
    logger.info(f"🔑 API key found: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
    
    try:
        # Test with google-genai library
        logger.info("🧪 Testing with google-genai library...")
        
        from google import genai
        from google.genai import types
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        logger.info("✅ Gemini client initialized")
        
        # Test simple generation
        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=50
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents="Say hello in one sentence.",
            config=config
        )
        
        if response and response.text:
            logger.success(f"✅ Gemini API working! Response: '{response.text.strip()}'")
            return True
        else:
            logger.error("❌ Empty response from Gemini")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("💡 Install: pip install google-genai")
        return False
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Gemini API test failed: {error_msg}")
        
        # Provide specific error guidance
        if "API key not valid" in error_msg:
            logger.info("💡 API Key Issues:")
            logger.info("1. Check if your API key is correct")
            logger.info("2. Make sure you enabled 'Generative Language API' in Google Cloud Console")
            logger.info("3. API key should be ~39 characters starting with 'AIza'")
            logger.info("4. Get key from: https://console.cloud.google.com/")
            
        elif "quota" in error_msg.lower():
            logger.info("💡 Quota exceeded - try again later or check billing")
            
        elif "permission" in error_msg.lower():
            logger.info("💡 Enable the 'Generative Language API' in Google Cloud Console")
            
        return False

def test_alternative_apis():
    """Test alternative API configurations"""
    logger.info("🔄 Testing alternative configurations...")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return False
    
    try:
        # Try different model names
        models_to_try = [
            "gemini-2.0-flash-001",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        for model in models_to_try:
            try:
                logger.info(f"🧪 Trying model: {model}")
                
                config = types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=30
                )
                
                response = client.models.generate_content(
                    model=model,
                    contents="Hi",
                    config=config
                )
                
                if response and response.text:
                    logger.success(f"✅ Model {model} works! Response: '{response.text.strip()}'")
                    
                    # Update the config file to use this model
                    logger.info(f"💡 Consider using model: {model}")
                    return model
                    
            except Exception as e:
                logger.warning(f"⚠️ Model {model} failed: {str(e)[:100]}")
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Alternative API test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🔧 Google API Key Tester for IEEE EPIC")
    logger.info("=" * 50)
    
    # Test main API
    success = test_google_api_key()
    
    if not success:
        logger.info("-" * 30)
        # Try alternatives
        working_model = test_alternative_apis()
        
        if working_model:
            logger.success(f"🎉 Found working model: {working_model}")
            success = True
    
    logger.info("=" * 50)
    
    if success:
        logger.success("🎉 API key is working! Your voice recognition will now have AI responses!")
        logger.info("💡 Run: python enhanced_voice_recognition.py")
    else:
        logger.error("❌ API key issues detected. Please check your configuration.")
        logger.info("🛠️ Troubleshooting steps:")
        logger.info("1. Get API key: https://console.cloud.google.com/")
        logger.info("2. Enable 'Generative Language API'")
        logger.info("3. Set: export GOOGLE_API_KEY='your-key'")
        logger.info("4. Install: pip install google-genai")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)