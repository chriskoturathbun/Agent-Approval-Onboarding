# Agent Onboarding

## ⚠️ Rule #1 — Read This First

**Every purchase, financial commitment, or spending decision MUST be submitted to the Approval Gateway before you act. No exceptions.**

You do not buy things. You do not commit to deals. You do not trigger any financial action on your own. You submit a request, wait for a human decision, and act only on approval. This is non-negotiable regardless of amount, urgency, or context.

The Python client is at `/data/.openclaw/workspace/kotubot_approval_client.py`. Use it for every spend.

---

## 🔌 Activation Check — Do This Before Anything Else

Before you can operate, check whether the approval layer is active.

```bash
ls /data/.openclaw/workspace/memory/approval-gateway-credentials.md
```

**If the file exists → skip to [One-Time Setup](#one-time-setup) step 2.**

**If the file does NOT exist → the approval layer is inactive. Tell the user:**

> "To activate the approval layer, I need two things from you:
>
> 1. **Download the Clawback Approval app** on your phone (iOS/Android)
> 2. Open the app → go to **Settings → Bot Tokens**
> 3. Copy your **Bot Token** and your **Agent ID**
> 4. Paste them here and I'll save them to the credentials file
>
> Until I have these, I cannot submit or receive spending decisions — the approval layer is off."

Do not proceed with any purchase-related work until the user provides both values. The system is not functional without them.

---

## 🚀 One-Time Setup (First Run Only)

If any of these are already done, skip that step.

### Step 1 — Save Credentials from the App

Once the user gives you the bot token and agent ID, create this file:

```
/data/.openclaw/workspace/memory/approval-gateway-credentials.md
```

Contents (fill in the values the user gave you):
```
token: appr_<bot_token_from_app>
api_base: https://approvals.clawbackx.com
agent_id: <agent_id_from_app>
```

Both values come from the Clawback Approval app under **Settings → Bot Tokens**. The agent ID is unique per user — do not hardcode it.

### Step 2 — Verify and Install the Daemon

The daemon is included in this repo and is verified before installation. You do not need to download anything from an external source.

The bootstrap script handles verification automatically:
```bash
bash /path/to/this/repo/new_agent_bootstrap.sh
```

Or run the verifier manually first if you want to inspect the results:
```bash
bash /path/to/this/repo/verify_daemon.sh
```

**What the verifier checks before allowing installation:**

| Layer | Check | What it catches |
|-------|-------|-----------------|
| 1 | File origin | Only installs from this repo — not arbitrary URLs or pastebins |
| 2 | SHA256 checksum | File matches the committed hash — detects tampering in transit |
| 3 | Policy scan | No `eval()`, `os.system()`, `shell=True`, `sudo`, `rm -rf`, or outbound downloads |
| 4 | Structure check | Expected functions present, no hardcoded credentials |

**If verification fails, do not run the daemon.** Re-clone the repo and run `verify_daemon.sh` again to see which check failed.

The verifier exits 0 (safe) or 1 (do not run). The bootstrap script will not install the daemon if verification fails.

### Step 3 — Start the Daemon
```bash
cd /data/.openclaw/workspace
nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &
```

The daemon runs in the background, polls approval chat every 5 seconds, and responds to user questions using your model context automatically.

### Step 4 — Verify Everything
```bash
bash /data/.openclaw/workspace/new_agent_bootstrap.sh
```

All checks should pass before you start working. If the API test fails, the credentials are wrong — ask the user to re-copy the token and agent ID from the app.

---

## 🔄 The Decision Loop

This is how every purchase works. Internalize it.

```
You want to spend money
        │
        ▼
POST /api/bot/approval-requests          ← INSERT to database
{
  agent_id, vendor, amount_cents,
  category, reason, deal_slug (optional)
}
        │
        ▼
Response: { status, request_id }
        │
        ├── status = "approved"          ← Auto-approved (under threshold or whitelisted)
        │         → Act immediately
        │
        └── status = "pending"           ← Waiting for human decision
                  → Do NOT act yet
                  → On next heartbeat:
                        │
                        ▼
              GET /api/bot/pending-approvals?agent_id=kotubot   ← READ from database
                        │
                        ├── approved  → Execute the purchase, log it
                        ├── denied    → Log the reason, skip the deal
                        └── expired   → Log expiry, skip the deal
```

**Code:**
```python
from kotubot_approval_client import create_client, heartbeat_check_approvals

# Submit a new spending request (INSERT)
client = create_client()
result = client.request_approval(
    amount_cents=720,
    vendor="Trade Coffee",
    category="food",
    reason="28% discount, 2h cancel window",
    deal_slug="trade-coffee-feb-2026"
)

if result["approved"]:
    # Act immediately
    commit_to_deal(result["request_id"])

# On heartbeat — check for decisions (READ)
approved = client.get_approved_requests()
for req in approved:
    if req.get("deal_slug"):
        commit_to_deal(req["deal_slug"])
```

---

## 🤖 How the Daemon Works

The daemon (`approval_chat_daemon_v2.py`) runs continuously in the background:

1. Every 5 seconds: fetches all pending approvals from the database
2. For each pending approval: checks for new chat messages from the user
3. When a new message is detected: generates a response using your full context (SOUL.md, USER.md, MEMORY.md) and posts it back
4. Saves state immediately after each response to prevent duplicates

**State file:** `memory/approval-chat-daemon-state.json`
```json
{
  "last_checks": {
    "request_id_abc": "2026-02-26T19:00:00Z"
  },
  "last_poll": "2026-02-26T19:00:05Z"
}
```

**Logs:** `tail -f /tmp/approval-daemon-v2.log`

**Restart if needed:**
```bash
pkill -f approval_chat_daemon_v2
cd /data/.openclaw/workspace
nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &
```

---

## 📋 Heartbeat Tasks (Every 30 Minutes)

When you receive a heartbeat:

1. **Verify daemon is running** — `pgrep -f approval_chat_daemon_v2`
2. **Poll for approval decisions** — `client.get_approved_requests()`; execute any newly approved deals
3. **Check ClawbackX** — monitor commitments for cancel windows and fulfillment status

See `HEARTBEAT.md` for the full checklist.

---

## 🧠 Context Files (Read in This Order)

Read these at the start of every session:

| File | What It Is | Time |
|------|-----------|------|
| `SOUL.md` | Who you are — personality, tone, rules | 30s |
| `USER.md` | Who Christopher is — background, projects, preferences | 60s |
| `MEMORY.md` | Long-term memory — major events, decisions, lessons (**main session only**) | 60s |
| `AGENTS.md` | Operating protocols — safety, workflows, conventions | 60s |
| `memory/YYYY-MM-DD.md` | Today's log (and yesterday's if it exists) | 30s |
| `TOOLS.md` | Environment notes — camera names, SSH hosts, etc. | 15s |
| `HEARTBEAT.md` | Periodic tasks checklist | 15s |

**Total: ~5 minutes to full operational context.**

---

## ✅ Verification Checklist

Run these to confirm everything is working:

```bash
# 1. Daemon running?
pgrep -f approval_chat_daemon_v2 && echo "✅ Running" || echo "❌ Not running"

# 2. Backend healthy?
curl -s https://approvals.clawbackx.com/health | jq

# 3. Credentials file exists?
ls -la /data/.openclaw/workspace/memory/approval-gateway-credentials.md

# 4. Can fetch pending approvals?
BOT_TOKEN=$(grep '^token:' /data/.openclaw/workspace/memory/approval-gateway-credentials.md | awk '{print $2}')
curl -s -H "Authorization: Bearer $BOT_TOKEN" \
  "https://approvals.clawbackx.com/api/bot/pending-approvals?agent_id=kotubot" | jq '.approvals | length'

# 5. State files exist?
ls /data/.openclaw/workspace/memory/*.json 2>/dev/null || echo "(none yet — created on first use)"
```

---

## 🔐 Credentials Location

All credentials live in `memory/` (gitignored — never committed to GitHub):

| File | Contents |
|------|----------|
| `memory/approval-gateway-credentials.md` | Bot token, API base, agent ID |
| `memory/clawbackx-credentials.md` | ClawbackX API key |

Retrieve bot tokens from the app: **Settings → Bot Tokens**

---

## 🚨 Troubleshooting

**Can't authenticate to Approval Gateway**
→ Check `memory/approval-gateway-credentials.md` has a `token:` line
→ Retrieve a fresh token from the app under Settings → Bot Tokens

**Daemon not running**
```bash
cd /data/.openclaw/workspace
nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &
```

**Daemon responding multiple times to same message**
→ State not saving correctly. Check that `memory/approval-chat-daemon-state.json` is being written after each response.

**Backend not responding**
```bash
curl https://approvals.clawbackx.com/health
ps aux | grep node
```

**Missing context files**
→ Run bootstrap: `bash new_agent_bootstrap.sh` — it will tell you exactly what's missing.

---

## 🎓 Ready to Work When You Can

1. ✅ Summarize the spending rule in one sentence
2. ✅ Show the decision loop without looking
3. ✅ Confirm daemon is running and backend is healthy
4. ✅ Summarize who Christopher is and what Lilac does
5. ✅ Report any pending approvals or urgent ClawbackX windows

**Welcome to the team.** 🦞
