---
summary: "Template for individual skill files — one per capability"
usage: "Copy to workspace, rename to match the skill (e.g., SKILL-approval-gateway.md)"
---

# SKILL — [Skill Name]

> One skill = one file. Keep it focused. This is your reference, not a tutorial.

---

## What This Skill Does

<!-- One or two sentences. What problem does this solve? -->

---

## Setup (One-Time)

<!-- Steps to get this skill ready. Credentials, dependencies, file locations. -->

```bash
# Example
pip install somepackage
cp config.example.json memory/skill-config.json
```

**Credentials:** <!-- Where they live, how to get them -->

---

## Usage

<!-- The most common operations. Code-first. -->

### [Most common operation]

```python
# Example
from skill_client import do_thing
result = do_thing(param="value")
```

### [Second most common]

```bash
# Shell example if relevant
curl -H "Authorization: Bearer $TOKEN" "http://localhost:PORT/endpoint"
```

---

## State Files

<!-- If this skill tracks state, list the files and their structure -->

| File | Purpose |
|------|---------|
| `memory/skill-state.json` | Last check timestamps, cached values |

---

## Heartbeat Integration

<!-- What to check on each 30-min heartbeat, if anything -->

```python
# Paste into HEARTBEAT.md integration section
from skill_client import heartbeat_check
message = heartbeat_check()
if message:
    notify_christopher(message)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Auth fails | Check credentials file has correct token format |
| No results returned | Verify state file isn't filtering out everything |

---

## Notes

<!-- Anything that tripped you up, edge cases, quirks of this integration -->

---

# SKILL — Approval Gateway (Example / In Use)

## What This Skill Does

Handles all agent spending decisions. Every purchase request is submitted here and waits for human approval before the agent acts. Uses `kotubot_approval_client.py`.

---

## Setup (One-Time)

1. Get bot token from the Clawback Approval app: **Settings → Bot Tokens**
2. Create credentials file:

```
/data/.openclaw/workspace/memory/approval-gateway-credentials.md
---
token: appr_<your_token>
api_base: https://approvals.clawbackx.com
agent_id: <your_agent_id>
```

3. Verify and install daemon:
```bash
bash /data/.openclaw/workspace/verify_daemon.sh
# then bootstrap runs it automatically
bash /data/.openclaw/workspace/new_agent_bootstrap.sh
```

---

## Usage

### Submit a spending request (INSERT to DB)

```python
from kotubot_approval_client import create_client

client = create_client()
result = client.request_approval(
    amount_cents=720,
    vendor="Trade Coffee",
    category="food",
    reason="28% discount, 2h cancel window",
    deal_slug="trade-coffee-feb-2026"   # optional
)

if result["approved"]:
    act_immediately()          # auto-approved under threshold
else:
    # status = "pending" — wait for human decision
    save_request_id(result["request_id"])
```

### Check for decisions (READ from DB)

```python
approved = client.get_approved_requests()
for req in approved:
    execute_purchase(req["deal_slug"])

pending = client.get_pending_requests()
# Log count, check again next heartbeat
```

---

## State Files

| File | Purpose |
|------|---------|
| `memory/approval-gateway-credentials.md` | Bot token + agent_id (gitignored) |
| `memory/approval-gateway-state.json` | Last poll timestamp, processed request IDs |
| `memory/approval-chat-daemon-state.json` | Daemon dedup — last message seen per request |

---

## Heartbeat Integration

```python
from kotubot_approval_client import heartbeat_check_approvals

message = heartbeat_check_approvals()
if message:
    notify_christopher(message)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `FileNotFoundError` on credentials | Create `memory/approval-gateway-credentials.md` with token + agent_id from app |
| 401 Unauthorized | Token expired or revoked — get a new one from the app |
| Daemon not responding to chat | Check `pgrep -f approval_chat_daemon_v2` — restart if down |
| Daemon responding multiple times | State not saving — check `memory/approval-chat-daemon-state.json` is writable |

---

## Notes

- The token proves *who you are*. The agent_id proves *which agent you are*. Both are required.
- Never hardcode agent_id — always read from credentials file. It's user-specific.
- Daemon is verified before install via SHA256 + policy scan. See `SECURITY.md`.
