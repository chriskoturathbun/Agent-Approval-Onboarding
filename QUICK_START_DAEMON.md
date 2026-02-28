# Quick Start: Multi-Agent Approval Daemon

## ✅ System is Ready!

The multi-agent approval chat daemon is installed and tested.

## Start the Daemon

```bash
bash /data/.openclaw/workspace/start_approval_daemons.sh
```

## Check Status

```bash
bash /data/.openclaw/workspace/check_approval_daemons.sh
```

## View Live Logs

```bash
tail -f /tmp/approval-daemon-kotubot.log
```

## Stop Daemon

```bash
bash /data/.openclaw/workspace/stop_approval_daemons.sh
```

## What Just Happened

**Test Results:**
- ✅ Daemon loaded credentials successfully
- ✅ Connected to API: http://localhost:3001
- ✅ Found 57 pending approvals
- ✅ anthropic package installed
- ✅ ANTHROPIC_API_KEY configured
- ✅ Multi-agent architecture ready

## How It Works

1. **User sends message** in Approval Gateway app
2. **Daemon detects** (polls every 5 seconds)
3. **Loads context** (SOUL.md, USER.md, MEMORY.md)
4. **Calls Claude** (claude-sonnet-4-5 via Anthropic API)
5. **Posts response** back to app
6. **User sees answer** (~5-10 seconds total)

## Adding More Agents

Edit `start_approval_daemons.sh`:

```bash
AGENTS=(
    "kotubot:/data/.openclaw/workspace"
    "manus:/data/manus/workspace"        # Add this
    "finance-bot:/path/to/workspace"     # And this
)
```

Each agent needs:
- Own workspace with context files
- Credentials file at: `{workspace}/memory/approval-gateway-credentials-simple.md`
- Unique bot token from app (Settings → Bot Tokens)

## Credentials File Format

Create: `{workspace}/memory/approval-gateway-credentials-simple.md`

```
token: appr_<bot_token_from_app>
api_base: http://localhost:3001
agent_id: <agent_id_from_app>
```

Get token and agent_id from: **Approval Gateway App → Settings → Bot Tokens**

## Full Documentation

See: [APPROVAL_DAEMON_MULTI_AGENT.md](APPROVAL_DAEMON_MULTI_AGENT.md)

## Ready to Deploy!

The system is production-ready. Just run `start_approval_daemons.sh` to begin responding to approval chat messages automatically.
