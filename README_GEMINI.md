# IEEE EPIC STT with Gemini AI Integration

This project has been updated to use **Google Gemini** instead of offline AI responses. The system now provides intelligent, context-aware responses using Google's latest AI models.

## 🚀 What Changed

### Removed
- ❌ Offline pattern-based responses (`data/offline_responses.json`)
- ❌ OpenAI integration 
- ❌ Complex fallback logic between online/offline modes

### Added
- ✅ Google Gemini API integration
- ✅ Bilingual support (English + Malayalam) with AI understanding
- ✅ Streaming response support
- ✅ Context-aware conversations
- ✅ Graceful fallbacks when API is unavailable
- ✅ Modern Google GenAI SDK

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
# Install the updated project with Gemini dependencies
python3 -m pip install -e .

# Or install just the new dependency
pip install google-genai>=0.8.0
```

### 2. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set it as an environment variable:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export GOOGLE_API_KEY="your_gemini_api_key_here"

# Or set it temporarily
export GOOGLE_API_KEY="AIza..."
```

### 3. Test the System
```bash
# Check system status
ieee-epic status

# Test AI responses
ieee-epic demo

# Full conversation mode
ieee-epic conversation
```

## 🤖 Features

### Bilingual AI Support
The system now intelligently handles both English and Malayalam:

```python
# English input
"Hello, how are you?" 
# → "Hello! I'm doing well, thank you for asking. How can I assist you today?"

# Malayalam input  
"വണക്കം, എങ്ങനെയുണ്ട്?"
# → "വണക്കം! ഞാൻ നന്നായിരിക്കുന്നു. എങ്ങനെ സഹായിക്കാം?"
```

### Streaming Responses
Real-time response generation for better user experience:

```python
ai_system = AIResponseSystem()
for chunk in ai_system.generate_response_stream("Tell me about Kerala"):
    print(chunk, end="", flush=True)
```

### Context-Aware Conversations
The system maintains conversation history for meaningful interactions:

```python
ai_system.generate_response("My name is John")
# Later...
ai_system.generate_response("What's my name?")
# → "Your name is John, as you mentioned earlier."
```

## 📝 Configuration

### Environment Variables
```bash
# Required: Gemini API Key
export GOOGLE_API_KEY="your_api_key"

# Optional: Alternative name for API key
export GEMINI_API_KEY="your_api_key" 
```

### Settings (config.py)
```python
class AISettings(BaseModel):
    enabled: bool = True
    gemini_api_key: Optional[str] = None  # Auto-detected from env
    model: str = "gemini-2.0-flash-001"  # Latest model
    max_tokens: int = 150
    temperature: float = 0.7
    system_instruction: str = "Bilingual AI assistant..."
```

### Supported Models
- `gemini-2.0-flash-001` (default, latest)
- `gemini-2.0-flash-002`
- `gemini-1.5-flash-001`
- `gemini-1.5-pro-001`

## 🔍 API Status

### With Valid API Key
```bash
$ ieee-epic status
┌─────────────────┬───────────────────┬─────────────────────────┐
│ Component       │ Status            │ Details                 │ 
├─────────────────┼───────────────────┼─────────────────────────┤
│ AI Responses    │ ✅ Gemini Connected│ Model: gemini-2.0-flash-001│
└─────────────────┴───────────────────┴─────────────────────────┘
```

### Without API Key
```bash 
$ ieee-epic status
┌─────────────────┬───────────────────┬─────────────────────────┐
│ Component       │ Status            │ Details                 │
├─────────────────┼───────────────────┼─────────────────────────┤
│ AI Responses    │ ⚠️ API Key Missing │ Model: gemini-2.0-flash-001│
└─────────────────┴───────────────────┴─────────────────────────┘
```

## 🛠️ Development

### Testing Without API Key
The system includes intelligent fallback responses when Gemini API is unavailable:

```python
# English fallback
"I heard you, but I'm having trouble connecting to the AI service right now."

# Malayalam fallback  
"മനസ്സിലായി, പക്ഷേ ഇപ്പോൾ AI സേവനവുമായി ബന്ധപ്പെടാൻ കഴിയുന്നില്ല."
```

### Custom System Instructions
Modify the AI behavior by updating the system instruction:

```python
settings = Settings()
settings.ai.system_instruction = """
You are a technical assistant for Kerala engineering students.
Respond in Malayalam when asked technical questions.
Keep answers practical and implementation-focused.
"""
```

### Chat Sessions
For persistent conversations with memory:

```python
ai_system = AIResponseSystem()
chat = ai_system.create_chat_session()

if chat:
    response = chat.send_message("Hello!")
    print(response.text)
```

## 🔄 Migration from Old System

### Files Removed
- `data/offline_responses.json` - No longer needed
- OpenAI dependencies in `requirements.txt`
- `OfflineResponseGenerator` class

### Files Modified  
- `src/ieee_epic/core/ai_response.py` - Complete rewrite for Gemini
- `src/ieee_epic/core/config.py` - Updated AI settings
- `requirements.txt` & `pyproject.toml` - Gemini dependencies
- CLI commands - Updated status display

### Backward Compatibility
- All CLI commands work the same way
- Configuration file format unchanged (except AI section)
- STT engine integration unchanged
- Conversation flow identical to end users

## 🚨 Troubleshooting

### Common Issues

**"google.genai could not be resolved"**
```bash
pip install google-genai>=0.8.0
```

**"API Key Missing" in status**
```bash
export GOOGLE_API_KEY="your_key_here"
# Restart terminal or source ~/.bashrc
```

**"Gemini API request failed"**
- Check your API key is valid
- Ensure you have internet connectivity  
- Verify your Google Cloud billing is set up
- Check API quotas and limits

**Fallback responses only**
- Means Gemini API is not available
- Check environment variables
- Test with: `python3 -c "import os; print(os.getenv('GOOGLE_API_KEY'))"`

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your AI commands to see detailed logs
```

## 📊 Performance & Costs

### Gemini 2.0 Flash Pricing (as of 2024)
- **Input**: $0.075 per 1M tokens  
- **Output**: $0.30 per 1M tokens
- **Free tier**: 15 requests per minute

### Typical Usage
- Short responses (50-150 tokens): ~$0.00002 per query
- Medium responses (200-500 tokens): ~$0.00005 per query
- Long responses (500+ tokens): ~$0.0001+ per query

### Optimization Tips
- Use `max_tokens` setting to limit response length
- Enable conversation history for context without re-sending
- Consider using `temperature=0` for consistent, deterministic responses

## 🎯 Next Steps

1. **Set up your API key** - Get started immediately
2. **Test the system** - Run `ieee-epic demo` 
3. **Try conversation mode** - Test `ieee-epic conversation`
4. **Integrate with STT** - Full speech-to-text + AI pipeline
5. **Customize prompts** - Adapt system instructions for your use case

---

**Ready to experience AI-powered speech interaction? Set your API key and start talking to your computer in English or Malayalam! 🗣️🤖**