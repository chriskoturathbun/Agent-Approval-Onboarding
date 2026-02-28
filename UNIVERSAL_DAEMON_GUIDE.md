# Universal Multi-Agent Approval Daemon

## Overview

The **universal daemon** supports any LLM provider that your agent has access to, not just Anthropic.

### Key Differences

| Feature | Anthropic-Only Daemon | Universal Daemon |
|---------|----------------------|------------------|
| **Models** | Anthropic Claude only | Any LLM (Anthropic, OpenAI, local, etc.) |
| **API Keys** | ANTHROPIC_API_KEY | Auto-detects from environment |
| **Configuration** | Hardcoded model | Reads from OpenClaw config or --model arg |
| **Providers** | 1 (Anthropic) | Multiple (extensible) |

## Supported Providers

✅ **Anthropic** (Claude models)
- claude-sonnet-4-5
- claude-haiku-4-5
- claude-opus-4-6
- Requires: `ANTHROPIC_API_KEY`

✅ **OpenAI**
- gpt-4, gpt-4-turbo
- gpt-3.5-turbo
- o1-preview, o1-mini
- Requires: `OPENAI_API_KEY`

✅ **OpenAI-Compatible APIs**
- Local models (Ollama, LM Studio, etc.)
- Moonshot (Kimi K2.5)
- Any API using OpenAI format
- Configure in `~/.openclaw/openclaw.json`

## Auto-Configuration

The universal daemon automatically:

1. **Reads OpenClaw config** (`~/.openclaw/openclaw.json`)
2. **Detects agent's model** from config
3. **Uses appropriate API** based on model name
4. **Falls back** to environment-based detection

### Example: Auto-Detection

```bash
# Your openclaw.json has:
# "agents": {
#   "defaults": {
#     "model": {
#       "primary": "anthropic/claude-haiku-4-5"
#     }
#   }
# }

# Daemon automatically uses claude-haiku-4-5:
python3 approval_chat_daemon_universal.py --workspace /data/.openclaw/workspace
# → 🦞 Model: claude-haiku-4-5 (ANTHROPIC)
```

## Manual Model Override

Specify a different model:

```bash
# Use GPT-4
python3 approval_chat_daemon_universal.py \
  --workspace /data/.openclaw/workspace \
  --model gpt-4

# Use Claude Sonnet
python3 approval_chat_daemon_universal.py \
  --workspace /data/.openclaw/workspace \
  --model claude-sonnet-4-5

# Use custom model
python3 approval_chat_daemon_universal.py \
  --workspace /data/.openclaw/workspace \
  --model moonshot/kimi-k2.5
```

## Environment Variables

The daemon checks for API keys in this order:

1. **Provider-specific key** (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)
2. **Custom keys from OpenClaw config** (e.g., `MOONSHOT_API_KEY`)

### Required Keys by Provider

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Moonshot (or other custom provider)
export MOONSHOT_API_KEY="sk-..."
```

## OpenClaw Config Integration

### Reading Agent's Model

The daemon reads your agent's configured model:

```json
// ~/.openclaw/openclaw.json
{
  "agents": {
    "list": [
      {
        "id": "kotubot",
        "model": "anthropic/claude-sonnet-4-5"
      },
      {
        "id": "manus",
        "model": "gpt-4"
      }
    ],
    "defaults": {
      "model": {
        "primary": "anthropic/claude-haiku-4-5"
      }
    }
  }
}
```

Daemon behavior:
- **Specific agent config** (e.g., kotubot → claude-sonnet-4-5)
- Falls back to **default primary model** (claude-haiku-4-5)
- Falls back to **environment detection** (ANTHROPIC_API_KEY → claude models)

### Custom Provider Setup

Add custom OpenAI-compatible providers:

```json
{
  "models": {
    "providers": {
      "moonshot": {
        "baseUrl": "https://api.moonshot.ai/v1",
        "apiKey": "${MOONSHOT_API_KEY}",
        "api": "openai-completions",
        "models": [
          {
            "id": "kimi-k2.5",
            "name": "Kimi K2.5"
          }
        ]
      }
    }
  }
}
```

The daemon automatically uses the custom baseUrl and API key.

## Usage

### Basic (Auto-Detect Everything)

```bash
python3 approval_chat_daemon_universal.py \
  --workspace /data/.openclaw/workspace
```

Automatically:
- Reads credentials from `{workspace}/memory/approval-gateway-credentials.md` (falls back to `...-credentials-simple.md`)
- Detects model from OpenClaw config
- Uses appropriate API key from environment

### Specify Model

```bash
python3 approval_chat_daemon_universal.py \
  --workspace /data/.openclaw/workspace \
  --model gpt-4
```

### Test Run

```bash
python3 approval_chat_daemon_universal.py \
  --workspace /data/.openclaw/workspace \
  --once
```

Output:
```
🦞 Universal Multi-Agent Approval Chat Daemon
   Agent: kotubot
   Workspace: /data/.openclaw/workspace
   API: http://localhost:3001
   Model: claude-haiku-4-5 (ANTHROPIC)
   Polling: every 5s

{
  "timestamp": "2026-02-28T02:33:16Z",
  "pending_approvals": 57,
  "responses_sent": 0
}
```

## Multi-Agent with Different Models

Each agent can use a different model:

```bash
# Kotubot uses Claude Haiku (fast, cost-effective)
python3 approval_chat_daemon_universal.py \
  --workspace /data/kotubot/workspace \
  --agent-id kotubot \
  --model claude-haiku-4-5 &

# Manus uses GPT-4 (more capable, analytical)
python3 approval_chat_daemon_universal.py \
  --workspace /data/manus/workspace \
  --agent-id manus \
  --model gpt-4 &

# Finance-bot uses Claude Opus (maximum capability)
python3 approval_chat_daemon_universal.py \
  --workspace /data/finance-bot/workspace \
  --agent-id finance-bot \
  --model claude-opus-4-6 &
```

Each daemon:
- Uses its own API keys
- Loads its own context files
- Maintains separate state
- Responds with appropriate model

## Installation

### Required Packages

```bash
# For Anthropic models
pip install anthropic

# For OpenAI models
pip install openai

# Both (recommended)
pip install anthropic openai
```

The daemon checks which packages are available and enables corresponding providers.

## Troubleshooting

### "No model specified and could not auto-detect"

**Cause:** No model in OpenClaw config and no API keys found

**Solution:**
```bash
# Option 1: Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: Specify model explicitly
python3 approval_chat_daemon_universal.py --model claude-haiku-4-5
```

### "anthropic package not installed"

```bash
pip install anthropic
```

### "openai package not installed"

```bash
pip install openai
```

### "ANTHROPIC_API_KEY environment variable not set"

```bash
# Check current environment
echo $ANTHROPIC_API_KEY

# Set if missing
export ANTHROPIC_API_KEY="your-key-here"

# Or add to ~/.bashrc for persistence
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Migration from Anthropic-Only Daemon

The universal daemon is a **drop-in replacement**:

```bash
# Old (anthropic-only)
python3 approval_chat_daemon_multi_agent.py --workspace /data/.openclaw/workspace

# New (universal, auto-detects Anthropic)
python3 approval_chat_daemon_universal.py --workspace /data/.openclaw/workspace
```

No changes needed if you're using Anthropic - it auto-detects and works the same way.

## Benefits

✅ **Provider-agnostic** - Use any LLM your agent has access to  
✅ **Auto-configuration** - Reads from OpenClaw config  
✅ **Multi-model support** - Different agents can use different models  
✅ **Cost optimization** - Use cheaper models for simple responses  
✅ **Capability matching** - Use powerful models when needed  
✅ **Local model support** - Works with Ollama, LM Studio, etc.  
✅ **Future-proof** - Easy to add new providers

## Examples

### Cost-Optimized Setup

```bash
# Use Haiku for routine approval questions (cheapest)
--model claude-haiku-4-5

# Use Sonnet for complex reasoning (balanced)
--model claude-sonnet-4-5

# Use Opus only for critical decisions (most capable)
--model claude-opus-4-6
```

### Mixed Provider Setup

```bash
# Kotubot: Anthropic Claude (personality-focused)
--workspace /data/kotubot/workspace --model claude-sonnet-4-5

# TechBot: OpenAI GPT-4 (analytical, code-focused)
--workspace /data/techbot/workspace --model gpt-4

# BudgetBot: Local Ollama (privacy-focused, free)
--workspace /data/budgetbot/workspace --model ollama/llama2
```

## Architecture

```
User Question in App
        ↓
Universal Daemon (polls every 5s)
        ↓
Auto-detect provider from model name
        ↓
     ┌──────┴──────┐
     ↓             ↓
Anthropic API  OpenAI API  (or custom)
(Claude)       (GPT-4)
     ↓             ↓
     └──────┬──────┘
            ↓
    AI-generated response
            ↓
    Post to Approval Gateway
            ↓
    User sees answer (~5-10s)
```

## Performance

- **Response time:** 5-10 seconds (same as anthropic-only)
- **Provider detection:** < 1ms (cached)
- **API overhead:** Minimal (direct HTTP requests)
- **Cost:** Depends on chosen model

## Conclusion

The universal daemon gives you **full flexibility** to use any LLM provider while maintaining the same easy deployment and multi-agent architecture.

**Choose the right model for each agent** based on:
- Cost requirements
- Capability needs
- Response time preferences
- Privacy concerns
- Provider availability

**Recommended:** Start with auto-detection (reads from OpenClaw config), then optimize per-agent as needed.
