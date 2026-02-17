# 🤖 GenAI Integration Setup Guide

This guide will help you set up the OpenAI integration for your Smart CDN's GenAI Engine.

## 📋 Prerequisites

- OpenAI API account
- API key from OpenAI

## 🔑 Step 1: Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **"Create new secret key"**
5. Copy the generated API key (starts with `sk-...`)

⚠️ **Important:** Keep your API key secure and never commit it to version control!

## ⚙️ Step 2: Configure Environment Variables

### Option A: Using .env file (Recommended for Development)

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   GENAI_MODEL=gpt-3.5-turbo
   USE_GENAI_TTL=true
   USE_GENAI_PREFETCH=true
   USE_GENAI_EXPLAIN=true
   ```

### Option B: Export Environment Variables (Alternative)

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
$env:GENAI_MODEL="gpt-3.5-turbo"

# Linux/Mac
export OPENAI_API_KEY="sk-your-actual-api-key-here"
export GENAI_MODEL="gpt-3.5-turbo"
```

## 🚀 Step 3: Start the CDN with GenAI

```bash
# Build and start all services
docker-compose up --build

# Or start in detached mode
docker-compose up -d --build
```

## 🔍 Step 4: Verify GenAI Integration

Check the logs to confirm OpenAI is working:

```bash
docker logs genai-engine
```

You should see:
```
🤖 TTL Optimizer: OpenAI integration enabled
🤖 Prefetch Analyzer: OpenAI integration enabled
🤖 Explainability Engine: OpenAI integration enabled
```

If you see fallback messages:
```
📊 TTL Optimizer: Using rule-based optimization
```
This means the API key is missing or invalid.

## 🎯 What's Using GenAI?

### 1. **TTL Optimizer** 🕐
- **With GenAI:** GPT analyzes traffic patterns and recommends optimal cache durations
- **Fallback:** Rule-based heuristics
- **API Cost:** ~$0.0001 per recommendation

### 2. **Prefetch Analyzer** 🔮
- **With GenAI:** GPT detects complex request patterns and suggests prefetch rules
- **Fallback:** Simple pattern counting
- **API Cost:** ~$0.0002 per analysis batch

### 3. **Explainability Engine** 💬
- **With GenAI:** Natural language explanations for cache behavior
- **Fallback:** Template-based explanations
- **API Cost:** ~$0.0001 per request explanation

## 💰 Cost Estimation

With `gpt-3.5-turbo`:
- **Low traffic** (< 1000 requests/day): ~$0.05/day
- **Medium traffic** (< 10000 requests/day): ~$0.20/day
- **High traffic** (> 100000 requests/day): ~$1.00/day

With `gpt-4` (10x more expensive but more intelligent):
- Multiply above estimates by 10

## 🛠️ Configuration Options

### Model Selection

Edit `.env` to change the model:

```bash
# Faster and cheaper (recommended for most use cases)
GENAI_MODEL=gpt-3.5-turbo

# More intelligent but expensive
GENAI_MODEL=gpt-4

# Cheaper variant
GENAI_MODEL=gpt-3.5-turbo-16k
```

### Selective GenAI Features

Disable specific features to reduce costs:

```bash
# Disable GenAI for TTL optimization (use rule-based)
USE_GENAI_TTL=false

# Disable GenAI for prefetch analysis (use pattern counting)
USE_GENAI_PREFETCH=false

# Disable GenAI for explanations (use templates)
USE_GENAI_EXPLAIN=false
```

## 🧪 Testing GenAI Integration

1. **Generate some traffic:**
   ```bash
   # Windows PowerShell
   .\test-cdn.ps1
   
   # Linux/Mac
   ./test-cdn.sh
   ```

2. **Check TTL recommendations:**
   ```bash
   curl http://localhost:8888/genai/ttl/recommendations
   ```

3. **Check prefetch rules:**
   ```bash
   curl http://localhost:8888/genai/prefetch/recommendations
   ```

4. **Get AI explanations:**
   ```bash
   curl http://localhost:8888/genai/explain/recent
   ```

## 📊 Monitoring API Usage

Monitor your OpenAI API usage at:
https://platform.openai.com/usage

## 🚨 Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:** Ensure `OPENAI_API_KEY` is set in `.env` file or environment

### Issue: "Rate limit exceeded"

**Solution:** 
- Upgrade your OpenAI plan
- Reduce analysis frequency in `main.py`
- Disable some GenAI features

### Issue: "Invalid API key"

**Solution:**
- Verify your API key is correct
- Check if your OpenAI account has credits
- Ensure no extra spaces in `.env` file

### Issue: GenAI responses are slow

**Solution:**
- Use `gpt-3.5-turbo` instead of `gpt-4`
- Reduce `max_tokens` in engine files
- Consider caching recommendations

## 🔒 Security Best Practices

1. ✅ Never commit `.env` to git (it's already in `.gitignore`)
2. ✅ Use environment-specific API keys
3. ✅ Rotate API keys periodically
4. ✅ Monitor usage for unexpected spikes
5. ✅ Set spending limits in OpenAI dashboard

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Pricing](https://openai.com/pricing)
- [Smart CDN Architecture](./ARCHITECTURE.md)

## 💡 Tips

- Start with `gpt-3.5-turbo` to test functionality
- Monitor costs for a few days before scaling
- Use fallback mode (`USE_GENAI_*=false`) during development to save costs
- The system automatically falls back to rule-based if API calls fail

---

🎉 **You're all set!** Your Smart CDN now uses AI to optimize cache behavior, detect prefetch patterns, and explain decisions in natural language.

