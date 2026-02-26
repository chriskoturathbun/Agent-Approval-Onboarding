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
# Get pending approvals
curl -H "Authorization: Bearer appr_pygr8ztl3ibkusjum8ixnv25y9w995kk" \
  "http://localhost:3001/api/bot/pending-approvals?agent_id=kotubot" | jq

# Get chat messages for an approval
curl -H "Authorization: Bearer appr_pygr8ztl3ibkusjum8ixnv25y9w995kk" \
  "http://localhost:3001/api/chat-messages/REQUEST_ID" | jq
```

---

## 🔐 Credentials

**Approval Gateway:**
- API: `http://localhost:3001`
- Bot token: `appr_pygr8ztl3ibkusjum8ixnv25y9w995kk`
- Agent ID: `kotubot`

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

**Daemon responding multiple times:**
→ Check state saves after each response, not at end

**API authentication fails:**
→ Verify bot token: `appr_pygr8ztl3ibkusjum8ixnv25y9w995kk`

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
