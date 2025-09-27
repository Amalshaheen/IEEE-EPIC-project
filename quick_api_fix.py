#!/usr/bin/env python3
"""
Quick API Fix Script
Run this to test and fix your Google API key configuration
"""

import os
import sys

def main():
    print("🔧 Quick API Fix for IEEE EPIC Voice Recognition")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found!")
        print("\n💡 Quick fix:")
        print("1. Get your API key from: https://console.cloud.google.com/")
        print("2. Enable 'Generative Language API'")
        print("3. Run: export GOOGLE_API_KEY='your-api-key-here'")
        print("4. Run this script again")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test basic import
    try:
        from google import genai
        print("✅ google-genai library available")
    except ImportError:
        print("❌ google-genai not installed")
        print("💡 Fix: pip install google-genai")
        return False
    
    # Test API connection with fallback models
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-pro", 
        "gemini-pro",
        "gemini-1.0-pro"
    ]
    
    from google.genai import types
    
    for model in models_to_try:
        try:
            print(f"🧪 Testing {model}...")
            
            client = genai.Client(api_key=api_key)
            
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=30
            )
            
            response = client.models.generate_content(
                model=model,
                contents="Say 'API test successful' in one sentence.",
                config=config
            )
            
            if response and response.text:
                print(f"✅ SUCCESS with {model}!")
                print(f"📝 Response: {response.text.strip()}")
                print(f"\n🎉 Your API key works! Model '{model}' is working.")
                print(f"💡 You can now use the voice recognition with AI responses!")
                return model
                
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ {model} failed: {error_msg[:80]}...")
            
            if "API key not valid" in error_msg:
                print("❌ API key invalid!")
                print("💡 Check your API key and make sure 'Generative Language API' is enabled")
                return False
    
    print("❌ All models failed!")
    print("💡 Troubleshooting:")
    print("1. Check API key is correct")
    print("2. Enable 'Generative Language API' in Google Cloud Console")
    print("3. Make sure billing is enabled (free tier available)")
    print("4. Try a different API key")
    
    return False

if __name__ == "__main__":
    try:
        working_model = main()
        
        if working_model:
            print("\n" + "=" * 50)
            print("🚀 READY TO GO!")
            print("Run: python enhanced_voice_recognition.py")
            print("Ask: 'What is Python programming?'")
            print("Enjoy intelligent AI responses! 🤖")
        else:
            print("\n❌ API setup needs attention")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have: pip install google-genai")