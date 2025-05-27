# AI Configuration Guide for Extraction v3

This guide explains how to configure and use AI providers with the Extraction v3 system for intelligent RPG PDF processing.

## Overview

Extraction v3 supports multiple AI providers for game detection and content categorization:

- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic/Claude** (Claude-3-sonnet, Claude-3-haiku)
- **Local LLM** (Ollama, LM Studio, etc.)
- **Mock AI** (Testing/fallback)

## Quick Start

### 1. Using Mock AI (Default)
No configuration needed - works immediately for testing:

```bash
# Uses mock AI (default)
python3 Extraction.py extract book.pdf

# Explicitly specify mock
python3 Extraction.py extract book.pdf --ai-provider mock
```

### 2. Using OpenAI
```bash
# Set API key
export OPENAI_API_KEY="your-api-key-here"

# Use OpenAI
python3 Extraction.py extract book.pdf --ai-provider openai

# Specify model
python3 Extraction.py extract book.pdf --ai-provider openai --ai-model gpt-4
```

### 3. Using Anthropic/Claude
```bash
# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Use Claude
python3 Extraction.py extract book.pdf --ai-provider claude

# Specify model
python3 Extraction.py extract book.pdf --ai-provider claude --ai-model claude-3-sonnet-20240229
```

### 4. Using Local LLM
```bash
# Set local LLM URL (Ollama default)
export LOCAL_LLM_URL="http://localhost:11434"
export LOCAL_LLM_MODEL="llama2"

# Use local LLM
python3 Extraction.py extract book.pdf --ai-provider local
```

## Environment Variables

### OpenAI Configuration
```bash
export OPENAI_API_KEY="sk-..."                    # Required: Your OpenAI API key
export OPENAI_BASE_URL="https://api.openai.com"   # Optional: Custom API endpoint
```

### Anthropic Configuration
```bash
export ANTHROPIC_API_KEY="sk-ant-..."             # Required: Your Anthropic API key
export CLAUDE_API_KEY="sk-ant-..."                # Alternative: Claude API key
```

### Local LLM Configuration
```bash
export LOCAL_LLM_URL="http://localhost:11434"     # Optional: Ollama/local LLM URL
export LOCAL_LLM_MODEL="llama2"                   # Optional: Model name
```

## Command Line Options

### AI Provider Selection
```bash
--ai-provider {openai,claude,anthropic,local,mock}
```

### API Configuration
```bash
--ai-api-key "your-key"           # Override environment variable
--ai-base-url "custom-url"        # Custom API endpoint
--ai-model "model-name"           # Specific model to use
```

### AI Behavior Control
```bash
--ai-max-tokens 4000              # Maximum response tokens (default: 4000)
--ai-temperature 0.1              # Creativity level (default: 0.1 for consistency)
--ai-timeout 30                   # Request timeout seconds (default: 30)
--ai-retries 3                    # Number of retries (default: 3)
```

### Debugging and Caching
```bash
--ai-debug                        # Enable detailed AI debugging
--ai-cache                        # Enable response caching (default: on)
--no-ai-cache                     # Disable response caching
--no-ai                           # Disable AI completely (fallback mode)
```

## Detailed Provider Setup

### OpenAI Setup

1. **Get API Key**
   - Visit https://platform.openai.com/api-keys
   - Create new API key
   - Copy the key (starts with `sk-`)

2. **Install Package**
   ```bash
   pip install openai>=1.0.0
   ```

3. **Set Environment Variable**
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   ```

4. **Test Configuration**
   ```bash
   python3 Extraction.py extract test.pdf --ai-provider openai --ai-debug
   ```

### Anthropic/Claude Setup

1. **Get API Key**
   - Visit https://console.anthropic.com/
   - Create API key
   - Copy the key (starts with `sk-ant-`)

2. **Install Package**
   ```bash
   pip install anthropic>=0.8.0
   ```

3. **Set Environment Variable**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

4. **Test Configuration**
   ```bash
   python3 Extraction.py extract test.pdf --ai-provider claude --ai-debug
   ```

### Local LLM Setup (Ollama)

1. **Install Ollama**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai/download
   ```

2. **Pull a Model**
   ```bash
   ollama pull llama2
   # or
   ollama pull mistral
   ollama pull codellama
   ```

3. **Start Ollama Server**
   ```bash
   ollama serve
   # Runs on http://localhost:11434 by default
   ```

4. **Test Configuration**
   ```bash
   python3 Extraction.py extract test.pdf --ai-provider local --ai-model llama2 --ai-debug
   ```

## Model Recommendations

### For Game Detection
- **OpenAI**: `gpt-4` (best accuracy) or `gpt-3.5-turbo` (faster/cheaper)
- **Claude**: `claude-3-sonnet-20240229` (balanced) or `claude-3-haiku-20240307` (faster)
- **Local**: `llama2` (general), `mistral` (good reasoning), `codellama` (structured output)

### Configuration Examples

#### High Accuracy (Recommended)
```bash
python3 Extraction.py extract book.pdf \
  --ai-provider openai \
  --ai-model gpt-4 \
  --ai-temperature 0.1 \
  --ai-max-tokens 4000
```

#### Fast Processing
```bash
python3 Extraction.py extract book.pdf \
  --ai-provider openai \
  --ai-model gpt-3.5-turbo \
  --ai-temperature 0.0 \
  --ai-max-tokens 2000 \
  --ai-timeout 15
```

#### Cost-Effective Local
```bash
python3 Extraction.py extract book.pdf \
  --ai-provider local \
  --ai-model mistral \
  --ai-base-url http://localhost:11434
```

## Troubleshooting

### Common Issues

#### "API key not found"
```bash
# Check environment variable
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set if missing
export OPENAI_API_KEY="your-key"
```

#### "Package not installed"
```bash
# Install required packages
pip install openai anthropic

# Or install all AI dependencies
pip install -r requirements.txt
```

#### "Connection timeout"
```bash
# Increase timeout
python3 Extraction.py extract book.pdf --ai-timeout 60

# Check network/firewall
curl -I https://api.openai.com
```

#### "Local LLM not responding"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve

# Check model is available
ollama list
```

### Debug Mode

Enable detailed debugging to see AI interactions:

```bash
python3 Extraction.py extract book.pdf --ai-provider openai --ai-debug --debug
```

This shows:
- AI provider initialization
- Prompt content sent to AI
- Raw AI responses
- Error messages and fallbacks

### Fallback Behavior

The system gracefully handles AI failures:

1. **API Errors**: Falls back to mock AI
2. **Network Issues**: Retries with exponential backoff
3. **Invalid Responses**: Uses fallback categorization
4. **Missing Keys**: Warns and uses mock AI

## Performance Optimization

### Caching
- **Enabled by default** - AI responses cached to avoid repeated analysis
- **Disable**: `--no-ai-cache` for testing
- **Clear cache**: Delete cache files in temp directory

### Token Management
- **Content Truncation**: Long PDFs automatically truncated to fit token limits
- **Smart Sampling**: First 15 pages analyzed for game detection
- **Response Limits**: Configurable max tokens for responses

### Batch Processing
```bash
# Process multiple PDFs efficiently
python3 Extraction.py batch ./pdfs/ --ai-provider openai --ai-cache
```

## Security Considerations

### API Key Protection
- **Never commit** API keys to version control
- **Use environment variables** or secure key management
- **Rotate keys** regularly
- **Monitor usage** on provider dashboards

### Local LLM Benefits
- **No external API calls** - data stays local
- **No usage costs** - only local compute
- **Offline capable** - works without internet
- **Privacy preserved** - content never leaves your system

## Cost Estimation

### OpenAI Pricing (approximate)
- **GPT-4**: ~$0.03-0.06 per PDF (depending on size)
- **GPT-3.5-turbo**: ~$0.002-0.004 per PDF

### Anthropic Pricing (approximate)
- **Claude-3-sonnet**: ~$0.015-0.03 per PDF
- **Claude-3-haiku**: ~$0.0025-0.005 per PDF

### Local LLM
- **No per-use costs** - only initial setup and compute
- **Hardware requirements**: 8GB+ RAM for most models

---

## Quick Reference

### Essential Commands
```bash
# Mock AI (testing)
python3 Extraction.py extract book.pdf

# OpenAI with API key
OPENAI_API_KEY="sk-..." python3 Extraction.py extract book.pdf --ai-provider openai

# Claude with custom model
python3 Extraction.py extract book.pdf --ai-provider claude --ai-model claude-3-haiku-20240307

# Local LLM
python3 Extraction.py extract book.pdf --ai-provider local --ai-model mistral

# Disable AI completely
python3 Extraction.py extract book.pdf --no-ai
```

### Environment Setup Script
```bash
#!/bin/bash
# ai_setup.sh - Quick AI environment setup

# Set your API keys here
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# Install dependencies
pip install openai anthropic

echo "AI environment configured!"
echo "Test with: python3 Extraction.py extract test.pdf --ai-provider openai --ai-debug"
```

For more help, run: `python3 Extraction.py --help`
