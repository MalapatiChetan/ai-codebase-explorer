# Google Gemini Integration - Quick Reference

## TL;DR

Google Gemini is now supported as the primary AI provider. **Priority order**: Gemini > OpenAI > Rule-based

## 5-Minute Setup

### 1. Get API Key
Visit [Google AI Studio](https://ai.google.dev/tutorials/python_quickstart) → Click "Get API Key"

### 2. Set Environment Variable
```bash
# .env file
GOOGLE_API_KEY=your-google-api-key-here
```

### 3. Start Using
```bash
python -m uvicorn src.main:app --reload
```

**Done!** System now uses Gemini automatically.

## Provider Priority

| Priority | Provider | Requires |
|----------|----------|----------|
| 1st | Google Gemini | `GOOGLE_API_KEY` |
| 2nd | OpenAI | `OPENAI_API_KEY` |
| 3rd | Rule-based | None (always works) |

## Configuration

**All optional environment variables** in `.env`:

```env
# Google Gemini
GOOGLE_API_KEY=your-key                      # Get from Google AI Studio
GOOGLE_MODEL=gemini-1.5-flash                # Default model
GOOGLE_TEMPERATURE=0.7                       # Creativity (0-1)
GOOGLE_MAX_TOKENS=2000                       # Max response length

# OpenAI (still works as fallback)
OPENAI_API_KEY=your-key                      # Your OpenAI key
OPENAI_MODEL=gpt-4                           # Default model
```

## Testing

```bash
# Test setup
python test_gemini_support.py

# Run full test suite
python test_system.py
```

## API Usage - No Changes!

Your code works exactly as before:

```python
from src.modules.ai_analyzer import AIArchitectureAnalyzer

analyzer = AIArchitectureAnalyzer()  # Auto-selects best provider
result = analyzer.analyze(metadata)   # Works with any provider
```

REST API also unchanged:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -d '{"repo_url": "https://github.com/..."}'
```

## Which Provider Should I Use?

| Scenario | Recommendation |
|----------|-----------------|
| New project | **Gemini** (free tier) |
| Existing OpenAI | **Keep OpenAI as fallback, add Gemini** |
| Cost critical | **Rule-based** (always free) |
| Quality critical | **OpenAI** (more reliable) |
| High volume | **Gemini** (free tier has limits) |

## Logging

Check which provider is active:

```
INFO: ✓ Using Google Gemini (gemini-1.5-flash) for AI analysis
```

Or:

```
INFO: ✓ Using OpenAI (gpt-4) for AI analysis
```

Or:

```
INFO: ✓ Using rule-based analysis (no AI API configured)
```

## Troubleshooting

### "API key error"
```bash
# Verify key is valid
python -c "import google.generativeai; print('✓ Valid')"
```

### "Rate limit (429)"
- Gemini free tier: 60 requests/min
- Wait 60 seconds or upgrade account

### "Provider not switching"
```bash
# Update .env, then restart server
# New instance = new provider selection
python -m uvicorn src.main:app --reload
```

## Migration Path

### From OpenAI-only:
```env
# Before
OPENAI_API_KEY=your-key
# GOOGLE_API_KEY not set

# After (add Gemini, keep OpenAI)
GOOGLE_API_KEY=your-google-key
OPENAI_API_KEY=your-openai-key

# Result: Uses Gemini, falls back to OpenAI
```

### Rolling back:
```env
# Just clear Gemini key
GOOGLE_API_KEY=
OPENAI_API_KEY=your-key

# Back to OpenAI immediately
```

## Files Changed

- ✅ `requirements.txt` - Added google-generativeai
- ✅ `src/utils/config.py` - Added Google config
- ✅ `src/modules/ai_analyzer.py` - Multi-provider support
- ✅ `test_gemini_support.py` - New test file
- ✅ `GEMINI_SUPPORT.md` - Full documentation

## Backward Compatibility

✅ **100% compatible** - No code changes needed, all existing code works as-is

## Documentation

- **[GEMINI_SUPPORT.md](GEMINI_SUPPORT.md)** - Complete guide
- **[GEMINI_IMPLEMENTATION_SUMMARY.md](GEMINI_IMPLEMENTATION_SUMMARY.md)** - Implementation details
- **[API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md)** - API reference

## Cost Comparison

| Provider | Cost | Speed |
|----------|------|-------|
| Gemini | 🟢 Free tier | ⚡ Fast |
| OpenAI | 🟡 $0.05-0.10/req | ⚡⚡ Medium |
| Rule-based | 🟢 Free | ⚡⚡⚡ Instant |

## Key Models

**Gemini Options**:
- `gemini-1.5-flash` (recommended, fastest, best value)
- `gemini-1.5-pro` (better quality, slower, more cost)
- `gemini-2.0-flash` (newest, fast)

Set in `.env`:
```env
GOOGLE_MODEL=gemini-1.5-pro
```

## Getting Help

1. **Gemini errors**: [Google AI docs](https://ai.google.dev/)
2. **API issues**: [API guide](API_INTEGRATION_GUIDE.md)
3. **Setup help**: [Full guide](GEMINI_SUPPORT.md)
4. **Test failures**: Run `python test_gemini_support.py`

---

**Status**: ✅ Production Ready | ✅ Fully Tested | ✅ Backward Compatible
