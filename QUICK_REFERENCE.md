# Quick Reference Card - Kotubot

**Emergency? Start here:** `bash /data/.openclaw/workspace/new_agent_bootstrap.sh`

---

## 📁 Essential File Paths

```
Core Context:
/data/.openclaw/workspace/SOUL.md               # Who you are
/data/.openclaw/workspace/USER.md               # Who Christopher is
/data/.openclaw/workspace/MEMORY.md             # Long-term memory (main session only)
/data/.openclaw/workspace/AGENTS.md             # Operating protocols
/data/.openclaw/workspace/HEARTBEAT.md          # Periodic tasks

Today's Work:
/data/.openclaw/workspace/memory/2026-XX-XX.md  # Today's log (replace date)

Systems:
/data/.openclaw/workspace/approval_chat_daemon_v2.py   # Auto-responder
/tmp/approval-daemon-v2.log                            # Daemon logs
```

---

## 🚀 Critical Commands

**Check systems:**
```bash
# All systems health check
bash /data/.openclaw/workspace/new_agent_bootstrap.sh

# Approval daemon running?
ps aux | grep approval_chat_daemon_v2

# Backend healthy?
curl http://localhost:3001/health

# View daemon logs
tail -f /tmp/approval-daemon-v2.log
```

**Restart systems:**
```bash
# Restart approval daemon
pkill -f approval_chat_daemon_v2
cd /data/.openclaw/workspace && nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &
```

**Check approvals:**
```bash
# Load credentials (always use these variables, never hardcode)
BOT_TOKEN=$(grep '^token:'    /data/.openclaw/workspace/memory/approval-gateway-credentials.md | awk '{print $2}')
AGENT_ID=$(grep '^agent_id:' /data/.openclaw/workspace/memory/approval-gateway-credentials.md | awk '{print $2}')

# Get pending approvals
curl -H "Authorization: Bearer $BOT_TOKEN" \
  "http://localhost:3001/api/bot/pending-approvals?agent_id=$AGENT_ID" | jq

# Get chat messages for an approval
curl -H "Authorization: Bearer $BOT_TOKEN" \
  "http://localhost:3001/api/chat-messages/REQUEST_ID" | jq
```

**Verify daemon before running:**
```bash
bash /data/.openclaw/workspace/verify_daemon.sh
# Must exit 0 before daemon is trusted to run
```

---

## 🔐 Credentials

**Approval Gateway:**
- API: `http://localhost:3001`
- Bot token + Agent ID: Retrieve from the Clawback Approval app → **Settings → Bot Tokens**
- Save both to: `memory/approval-gateway-credentials.md`
- ⚠️ Agent ID is user-specific — never hardcode it

**ClawbackX:**
- See: `memory/clawbackx-credentials.md`

---

## 💬 Response Style (from SOUL.md)

- Direct, efficient, zero fluff
- Start with answer, then explanation
- Structured formatting (bullets/tables)
- No em dashes, no "Great question!"
- Founder-to-founder energy

---

## 🧠 Memory Protocol

**Write immediately:**
- Significant events → `memory/YYYY-MM-DD.md`
- Lessons learned → `MEMORY.md` (review daily logs first)
- State updates → Auto-saved by systems

**Never:**
- Rely on "mental notes" (files = memory)
- Load MEMORY.md in group chats (security)
- Forget to log important decisions

---

## 🚨 Common Issues

**Approval layer inactive (no credentials file):**
→ Ask user to download Clawback Approval app → Settings → Bot Tokens → copy token + agent ID

**Daemon not trusted / verify fails:**
→ `bash verify_daemon.sh` to see which check failed; re-clone repo if checksum mismatch

**Daemon responding multiple times:**
→ Check state saves after each response, not at end

**API authentication fails:**
→ Check `memory/approval-gateway-credentials.md` has valid `token:` and `agent_id:` lines

**Backend not responding:**
→ `curl http://localhost:3001/health`

**Missing context:**
→ Read onboarding: `AGENT_ONBOARDING.md`

---

## 📊 Heartbeat Checklist

Every 30 minutes, check:
1. Approval daemon running (auto-handled)
2. ClawbackX commitments (fulfillment/cancellation)
3. Approval Gateway (approved/denied requests)

See: `HEARTBEAT.md` for full details

---

## ✅ First Message Template

```
✅ Onboarded. Read SOUL, USER, MEMORY, AGENTS, today's log.

Status:
- Approval daemon: ✅ Running (PID XXXXX)
- Backend: ✅ http://localhost:3001/health
- ClawbackX: X commitments (status)
- Pending approvals: X requests

Ready. What needs attention?
```

---

**Full docs:** `AGENT_ONBOARDING.md` (9.5 KB, 5-minute read)
