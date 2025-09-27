#!/bin/bash
# Configuration script for IEEE EPIC Voice Recognition with AI
# Run this script to set up your environment

echo "🔧 IEEE EPIC Voice Recognition Configuration"
echo "==========================================="
echo ""

# Check if Google API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY environment variable not set"
    echo ""
    echo "📝 To get a Google API key:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project or select existing project"
    echo "3. Enable the 'Generative Language API' (for Gemini)"
    echo "4. Go to 'Credentials' and create an API key"
    echo "5. Copy the API key"
    echo ""
    read -p "🔑 Enter your Google API key: " api_key
    
    if [ ! -z "$api_key" ]; then
        echo "export GOOGLE_API_KEY='$api_key'" >> ~/.bashrc
        echo "export GOOGLE_API_KEY='$api_key'" >> ~/.profile
        export GOOGLE_API_KEY="$api_key"
        echo "✅ API key saved to ~/.bashrc and ~/.profile"
        echo "🔄 Please run: source ~/.bashrc"
    else
        echo "⚠️ No API key entered. AI features will not work."
    fi
else
    echo "✅ GOOGLE_API_KEY is already set"
fi

echo ""
echo "📋 Checking system dependencies..."

# Check Python packages
echo "🐍 Checking Python packages..."
python3 -c "import speech_recognition" 2>/dev/null && echo "✅ SpeechRecognition installed" || echo "❌ SpeechRecognition missing: pip install SpeechRecognition"
python3 -c "import gtts" 2>/dev/null && echo "✅ gTTS installed" || echo "❌ gTTS missing: pip install gTTS"
python3 -c "from google import genai" 2>/dev/null && echo "✅ Google GenAI installed" || echo "❌ Google GenAI missing: pip install google-genai"

# Check audio tools
echo ""
echo "🔊 Checking audio tools..."
command -v arecord >/dev/null 2>&1 && echo "✅ arecord available" || echo "❌ arecord missing: sudo apt-get install alsa-utils"
command -v aplay >/dev/null 2>&1 && echo "✅ aplay available" || echo "❌ aplay missing: sudo apt-get install alsa-utils"
command -v mpg123 >/dev/null 2>&1 && echo "✅ mpg123 available" || echo "❌ mpg123 missing: sudo apt-get install mpg123"

# Test microphone
echo ""
echo "🎤 Testing microphone..."
if command -v arecord >/dev/null 2>&1; then
    echo "📊 Available recording devices:"
    arecord -l | grep -E "card|device" | head -5
    
    read -p "🧪 Test microphone recording? (y/n): " test_mic
    if [ "$test_mic" = "y" ] || [ "$test_mic" = "Y" ]; then
        echo "🔴 Recording 3 seconds... speak now!"
        arecord -d 3 -f cd test_config.wav 2>/dev/null
        
        if [ -f test_config.wav ]; then
            echo "✅ Recording completed"
            read -p "🔊 Play back recording? (y/n): " play_back
            if [ "$play_back" = "y" ] || [ "$play_back" = "Y" ]; then
                aplay test_config.wav 2>/dev/null
            fi
            rm -f test_config.wav
        else
            echo "❌ Recording failed - check microphone connection"
        fi
    fi
fi

echo ""
echo "🚀 Configuration complete!"
echo ""
echo "📝 Next steps:"
echo "1. If you set a new API key, run: source ~/.bashrc"
echo "2. Install any missing packages shown above"
echo "3. Test the voice recognition: python enhanced_voice_recognition.py"
echo ""
echo "💡 For technical questions, ask about:"
echo "   - Python programming"
echo "   - Web development (React, Next.js)"
echo "   - Data science (NumPy, Pandas)"
echo "   - Machine learning (TensorFlow, PyTorch)"
echo "   - And many more libraries!"
echo ""
echo "🎉 Enjoy your AI-powered voice assistant!"