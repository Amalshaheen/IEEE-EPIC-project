#!/usr/bin/env python3
"""
Debug script to test Gemini API and find working models
"""

import os
from google import genai
from google.genai import types

def test_gemini_api():
    """Test Gemini API connection and models."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        print("✅ Client created successfully")
        
        # Test different model names
        model_names = [
            "gemini-1.5-flash-001",
            "gemini-1.5-flash",
            "gemini-1.5-pro-001",
            "gemini-1.5-pro",
            "gemini-2.0-flash-001"
        ]
        
        for model_name in model_names:
            try:
                print(f"\n🔍 Testing model: {model_name}")
                
                config = types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=50,
                    system_instruction="You are a helpful assistant. Respond briefly."
                )
                
                response = client.models.generate_content(
                    model=model_name,
                    contents="Hello, can you hear me?",
                    config=config
                )
                
                if response and response.text:
                    print(f"✅ {model_name} works! Response: {response.text[:100]}...")
                    return model_name  # Return the first working model
                else:
                    print(f"❌ {model_name} - Empty response")
                    
            except Exception as e:
                print(f"❌ {model_name} failed: {str(e)[:100]}...")
        
        print("\n❌ No working models found")
        
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        
if __name__ == "__main__":
    test_gemini_api()