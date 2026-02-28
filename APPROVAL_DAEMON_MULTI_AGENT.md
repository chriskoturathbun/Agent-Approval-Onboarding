# Multi-Agent Approval Chat Daemon

## Overview

This system allows multiple AI agents to respond to approval chat messages independently using their own context and personality.

Each agent runs its own daemon instance that:
1. Polls the Approval Gateway for new messages
2. Loads agent-specific context files (SOUL.md, USER.md, MEMORY.md)
3. Generates AI responses using Anthropic API (Claude Sonnet 4.5)
4. Posts responses back to the Approval Gateway

## Architecture

```
User sends message in Approval Gateway app
    ↓
Daemon polls API every 5s (agent-specific)
    ↓
Detects new message
    ↓
Loads workspace context (SOUL.md, USER.md, MEMORY.md)
    ↓
Calls Anthropic API with full context
    ↓
Posts AI-generated response back to app
    ↓
User sees response (~5-10 seconds total)
```

## Setup

### Prerequisites

1. **Python 3** with `anthropic` package:
   ```bash
   pip install anthropic
   ```

2. **ANTHROPIC_API_KEY** environment variable (already set by OpenClaw)

3. **Credentials file** for each agent:
   ```
   {workspace}/memory/approval-gateway-credentials.md
   ```
   
   Format:
   ```
   token: appr_<bot_token_from_app>
   api_base: https://approvals.clawbackx.com
   agent_id: <agent_id_from_app>
   ```

### First-Time Setup

1. **Get credentials from the Approval Gateway app:**
   - Open app → Settings → Bot Tokens
   - Copy your Bot Token
   - Copy your Agent ID

2. **Create credentials file:**
   ```bash
   mkdir -p /data/.openclaw/workspace/memory
   cat > /data/.openclaw/workspace/memory/approval-gateway-credentials.md << EOF
   token: appr_<your_token_here>
   api_base: https://approvals.clawbackx.com
   agent_id: <your_agent_id_here>
   EOF
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x /data/.openclaw/workspace/*.sh
   ```

## Usage

### Start All Configured Daemons

```bash
bash /data/.openclaw/workspace/start_approval_daemons.sh
```

This starts a daemon for each agent configured in the script.

### Check Status

```bash
bash /data/.openclaw/workspace/check_approval_daemons.sh
```

Shows:
- Which agents have running daemons
- Process IDs
- Log file locations
- Last activity

### View Logs

```bash
# Real-time log for specific agent
tail -f /tmp/approval-daemon-kotubot.log

# Last 50 lines
tail -n 50 /tmp/approval-daemon-kotubot.log
```

### Stop All Daemons

```bash
bash /data/.openclaw/workspace/stop_approval_daemons.sh
```

### Manual Daemon Control

Start a single agent daemon:
```bash
python3 /data/.openclaw/workspace/approval_chat_daemon_multi_agent.py \
  --workspace /data/.openclaw/workspace

# Or in background
nohup python3 /data/.openclaw/workspace/approval_chat_daemon_multi_agent.py \
  --workspace /data/.openclaw/workspace \
  > /tmp/approval-daemon-kotubot.log 2>&1 &
```

Test with a single poll (no continuous loop):
```bash
python3 /data/.openclaw/workspace/approval_chat_daemon_multi_agent.py \
  --workspace /data/.openclaw/workspace \
  --once
```

## Multi-Agent Configuration

Edit `start_approval_daemons.sh` to add more agents:

```bash
AGENTS=(
    "kotubot:/data/.openclaw/workspace"
    "manus:/data/manus/workspace"
    "finance-bot:/data/finance-bot/workspace"
)
```

Each agent needs:
1. Its own workspace directory
2. Context files: SOUL.md, USER.md, MEMORY.md (optional), AGENTS.md (optional)
3. Credentials file: `{workspace}/memory/approval-gateway-credentials.md`
4. Unique bot token and agent ID from the Approval Gateway app

## How It Works

### State Management

Each daemon maintains its own state file:
```
{workspace}/memory/approval-chat-daemon-state.json
```

Example:
```json
{
  "last_checks": {
    "request_abc123": "2026-02-27T20:00:00Z"
  },
  "last_poll": "2026-02-27T20:05:00Z"
}
```

This prevents duplicate responses to the same message.

### Context Loading

On each new message, the daemon:
1. Reads `SOUL.md` (agent personality/identity)
2. Reads `USER.md` (user context/preferences)
3. Reads `MEMORY.md` (long-term memory, first 2000 chars)
4. Reads `AGENTS.md` (operating protocols)

These are combined into a prompt for Claude.

### AI Response Generation

```python
# Simplified flow:
context = load_context_from_workspace()
prompt = f"""
You are responding to a user question about an approval request.

{context['soul']}
{context['user']}
{context['memory']}

Approval: {vendor} ${amount} - {reason}
User asked: {user_message}

Respond naturally as this agent would.
"""

response = anthropic.create(model="claude-sonnet-4-5", prompt=prompt)
post_to_approval_gateway(response)
```

## Troubleshooting

### Daemon not starting

1. Check `ANTHROPIC_API_KEY`:
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

2. Check credentials file exists:
   ```bash
   cat /data/.openclaw/workspace/memory/approval-gateway-credentials.md
   ```

3. Check anthropic package:
   ```bash
   python3 -c "import anthropic"
   ```

### No responses in app

1. Check daemon is running:
   ```bash
   bash check_approval_daemons.sh
   ```

2. Check logs for errors:
   ```bash
   tail -n 50 /tmp/approval-daemon-kotubot.log
   ```

3. Test API connectivity:
   ```bash
   python3 approval_chat_daemon_multi_agent.py \
     --workspace /data/.openclaw/workspace \
     --once
   ```

### Daemon responding multiple times

State file corruption. Stop daemon and reset:
```bash
bash stop_approval_daemons.sh
rm /data/.openclaw/workspace/memory/approval-chat-daemon-state.json
bash start_approval_daemons.sh
```

### Wrong agent responding

Each agent needs unique credentials (bot_token and agent_id) from the app.
Check credentials file has correct agent_id.

## Performance

- **Polling interval:** 5 seconds (configurable with `--poll-interval`)
- **Response time:** 5-10 seconds (from user message to AI response)
- **API calls:** Only when new messages detected
- **Cost:** Uses OpenClaw's ANTHROPIC_API_KEY (same billing as main agent)

## Comparison to Other Solutions

### vs. Cron Job
- ✅ Faster (5s vs 10-30s response time)
- ✅ More efficient (only acts when messages exist)
- ✅ Better state management

### vs. Heartbeat
- ✅ Much faster (5s vs 30 min)
- ✅ Purpose-built for approval chat
- ✅ Doesn't interrupt main agent session

### vs. Agent Session Integration
- ✅ Works without agent being active
- ✅ No dependency on session availability
- ✅ Cleaner separation of concerns

## Files

| File | Purpose |
|------|---------|
| `approval_chat_daemon_multi_agent.py` | Main daemon script |
| `start_approval_daemons.sh` | Launch all configured daemons |
| `stop_approval_daemons.sh` | Stop all running daemons |
| `check_approval_daemons.sh` | Check status of daemons |
| `APPROVAL_DAEMON_MULTI_AGENT.md` | This documentation |

## Integration with Onboarding Repo

This daemon system can be integrated with the [Agent-Approval-Onboarding](https://github.com/chriskoturathbun/Agent-Approval-Onboarding) repository by:

1. Replacing `approval_chat_daemon_v2.py` with `approval_chat_daemon_multi_agent.py`
2. Updating `new_agent_bootstrap.sh` to check for `anthropic` package
3. Adding multi-agent launcher scripts
4. Updating documentation to reference multi-agent setup

## License

Same as OpenClaw - MIT

## Support

Issues? Questions?
- Check logs first: `tail -f /tmp/approval-daemon-*.log`
- Test with `--once` flag for debugging
- Verify credentials file format
- Confirm ANTHROPIC_API_KEY is set
