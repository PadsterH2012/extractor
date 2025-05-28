# AI Configuration Guide

## Overview
The AI-Powered Extraction v3 System supports multiple AI providers for intelligent game detection and content categorization. This guide covers configuration options and setup procedures for each supported provider.

## Supported AI Providers

### 1. Claude (Anthropic) - **Recommended**
- **Provider**: `claude` or `anthropic`
- **Models**: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`
- **Strengths**: Excellent book detection accuracy (95%+ confidence)
- **Cost**: Moderate ($0.003-0.015 per 1K tokens)

### 2. OpenAI
- **Provider**: `openai`
- **Models**: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- **Strengths**: Fast processing, good general knowledge
- **Cost**: Variable ($0.001-0.03 per 1K tokens)

### 3. OpenRouter (Multiple Models)
- **Provider**: `openrouter`
- **Models**: Access to 100+ models including Claude, GPT-4, Gemini
- **Strengths**: Model variety, competitive pricing
- **Cost**: Varies by model ($0.0001-0.1 per 1K tokens)

### 4. Local LLM (Ollama)
- **Provider**: `local`
- **Models**: `llama2`, `mistral`, `codellama`
- **Strengths**: No API costs, privacy, offline operation
- **Cost**: Free (requires local GPU/CPU resources)

### 5. Mock AI (Testing)
- **Provider**: `mock`
- **Models**: N/A (keyword-based detection)
- **Strengths**: No API keys required, instant testing
- **Cost**: Free

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Create a `.env` file in the project root:

```bash
# Claude/Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Default AI Provider
DEFAULT_AI_PROVIDER=claude
DEFAULT_AI_MODEL=claude-3-5-sonnet-20241022
```

### Method 2: Command Line Arguments

```bash
# Claude AI
python3 Extraction.py extract file.pdf --ai-provider claude --ai-model claude-3-5-sonnet-20241022

# OpenAI
python3 Extraction.py extract file.pdf --ai-provider openai --ai-model gpt-4 --ai-api-key your_key

# OpenRouter
python3 Extraction.py extract file.pdf --ai-provider openrouter --ai-model anthropic/claude-3.5-sonnet

# Local LLM
python3 Extraction.py extract file.pdf --ai-provider local --ai-model llama2
```

### Method 3: Web UI Configuration

1. Start the Web UI: `python3 ui/start_ui.py`
2. Navigate to Settings (gear icon)
3. Configure AI provider and API keys
4. Settings are saved to `.env` file automatically

## Provider-Specific Setup

### Claude (Anthropic) Setup

1. **Get API Key**:
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create account and generate API key
   - Add credits to your account

2. **Configuration**:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   DEFAULT_AI_PROVIDER=claude
   DEFAULT_AI_MODEL=claude-3-5-sonnet-20241022
   ```

3. **Test Configuration**:
   ```bash
   python3 Extraction.py extract sample.pdf --ai-provider claude
   ```

### OpenAI Setup

1. **Get API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Create account and generate API key
   - Add payment method

2. **Configuration**:
   ```bash
   OPENAI_API_KEY=sk-...
   DEFAULT_AI_PROVIDER=openai
   DEFAULT_AI_MODEL=gpt-4
   ```

### OpenRouter Setup

1. **Get API Key**:
   - Visit [OpenRouter](https://openrouter.ai/)
   - Create account and generate API key
   - Add credits

2. **Configuration**:
   ```bash
   OPENROUTER_API_KEY=sk-or-...
   DEFAULT_AI_PROVIDER=openrouter
   DEFAULT_AI_MODEL=anthropic/claude-3.5-sonnet
   ```

### Local LLM (Ollama) Setup

1. **Install Ollama**:
   ```bash
   # Linux/Mac
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai/
   ```

2. **Install Models**:
   ```bash
   ollama pull llama2
   ollama pull mistral
   ```

3. **Configuration**:
   ```bash
   DEFAULT_AI_PROVIDER=local
   DEFAULT_AI_MODEL=llama2
   OLLAMA_HOST=http://localhost:11434
   ```

## Advanced Configuration

### AI Behavior Settings

```bash
# Temperature (creativity): 0.0-1.0
AI_TEMPERATURE=0.3

# Max tokens per request
AI_MAX_TOKENS=4000

# Request timeout (seconds)
AI_TIMEOUT=30

# Retry attempts on failure
AI_RETRIES=3

# Enable debug logging
AI_DEBUG=true

# Enable response caching
AI_CACHE=true
```

### Model-Specific Settings

```bash
# Claude-specific
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.3

# OpenAI-specific  
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.3

# OpenRouter-specific
OPENROUTER_MAX_TOKENS=4000
OPENROUTER_TEMPERATURE=0.3
```

## Performance Comparison

| Provider | Speed | Accuracy | Cost | Setup Difficulty |
|----------|-------|----------|------|------------------|
| Claude | Fast | Excellent (95%) | Medium | Easy |
| OpenAI | Very Fast | Good (85%) | Medium-High | Easy |
| OpenRouter | Fast | Varies by Model | Low-Medium | Easy |
| Local LLM | Slow | Good (80%) | Free | Hard |
| Mock AI | Instant | Basic (70%) | Free | None |

## Troubleshooting

### Common Issues

1. **API Key Invalid**:
   - Verify API key format and validity
   - Check account credits/billing
   - Ensure proper environment variable names

2. **Rate Limiting**:
   - Reduce concurrent requests
   - Add delays between API calls
   - Upgrade to higher tier plan

3. **Model Not Found**:
   - Verify model name spelling
   - Check provider's available models
   - Use fallback models

4. **Network Errors**:
   - Check internet connectivity
   - Verify firewall settings
   - Try different provider

### Debug Mode

Enable debug mode for detailed logging:

```bash
python3 Extraction.py extract file.pdf --ai-debug
```

Or set environment variable:
```bash
AI_DEBUG=true
```

### Fallback Configuration

Configure automatic fallback providers:

```bash
# Primary provider
DEFAULT_AI_PROVIDER=claude

# Fallback chain
AI_FALLBACK_PROVIDERS=openai,openrouter,mock
```

## Best Practices

### Security
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Monitor API usage and costs

### Performance
- Use appropriate models for task complexity
- Cache responses when possible
- Implement retry logic with exponential backoff
- Monitor token usage and costs

### Cost Optimization
- Start with mock AI for development
- Use cheaper models for testing
- Monitor usage with provider dashboards
- Set up billing alerts

## Production Deployment

### Environment Setup
```bash
# Production environment variables
NODE_ENV=production
AI_CACHE=true
AI_RETRIES=5
AI_TIMEOUT=60
```

### Monitoring
- Set up API usage monitoring
- Configure cost alerts
- Monitor error rates and response times
- Log all AI interactions for debugging

### Scaling
- Use connection pooling for high volume
- Implement request queuing
- Consider multiple API keys for rate limiting
- Monitor and scale based on usage patterns

This configuration guide ensures optimal AI provider setup for reliable, cost-effective PDF extraction and analysis.
