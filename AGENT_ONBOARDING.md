# Agent Onboarding - Get Up to Speed in 5 Minutes

This document brings any new agent instance to full operational capability.

## 🚀 Quick Start (Read These First)

**Core Identity & Context (2 minutes):**
1. `/data/.openclaw/workspace/SOUL.md` - Who you are (personality, tone, behavior)
2. `/data/.openclaw/workspace/USER.md` - Who Christopher is (background, projects, preferences)
3. `/data/.openclaw/workspace/MEMORY.md` - Long-term memory (major events, decisions, lessons)
4. `/data/.openclaw/workspace/AGENTS.md` - Operating protocols (safety, workflows, conventions)

**Recent Context (1 minute):**
5. `/data/.openclaw/workspace/memory/YYYY-MM-DD.md` - Today's log (replace with current date)
6. `/data/.openclaw/workspace/memory/YYYY-MM-DD.md` - Yesterday's log (if exists)

**Tools & Systems (1 minute):**
7. `/data/.openclaw/workspace/TOOLS.md` - Tool-specific notes (camera names, SSH hosts, etc.)
8. `/data/.openclaw/workspace/HEARTBEAT.md` - Periodic tasks (what to check every 30 min)

---

## 🧠 Knowledge Base Structure

### Core Files (Workspace Root)
```
/data/.openclaw/workspace/
├── SOUL.md              # Who you are
├── USER.md              # Who Christopher is
├── MEMORY.md            # Long-term memory (ONLY in main session)
├── AGENTS.md            # Operating protocols
├── TOOLS.md             # Tool configurations
├── HEARTBEAT.md         # Periodic tasks checklist
├── IDENTITY.md          # Name, creature type, emoji, avatar
└── AGENT_ONBOARDING.md  # This file
```

### Memory Files (Daily Logs)
```
/data/.openclaw/workspace/memory/
├── 2026-02-26.md                          # Daily log
├── approval-chat-daemon-state.json        # Approval chat system state
├── clawbackx-state.json                   # ClawbackX commitments state
├── approval-gateway-state.json            # Approval gateway state
├── approval-gateway-credentials.md        # API credentials (secure)
└── clawbackx-credentials.md               # ClawbackX API key (secure)
```

### Active Skills
```
/data/.openclaw/workspace/
├── approval_chat_daemon_v2.py             # Auto-response daemon (running)
├── approval_chat_responder_simple.py      # Manual responder
├── kotubot_approval_client.py             # Approval Gateway API client
└── respond_to_approval_chats.py           # Legacy responder
```

---

## 🔧 Active Systems (Currently Running)

### 1. Approval Chat Auto-Responder
**Status:** ✅ Running (PID in `/tmp/approval-daemon-v2.log`)  
**Function:** Polls approval chat every 5 seconds, responds automatically with full context  
**Files:**
- Script: `/data/.openclaw/workspace/approval_chat_daemon_v2.py`
- State: `/data/.openclaw/workspace/memory/approval-chat-daemon-state.json`
- Logs: `/tmp/approval-daemon-v2.log`

**Check status:**
```bash
ps aux | grep approval_chat_daemon_v2
tail -20 /tmp/approval-daemon-v2.log
```

**Restart if needed:**
```bash
pkill -f approval_chat_daemon_v2
cd /data/.openclaw/workspace && nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &
```

### 2. Approval Gateway Backend
**Status:** ✅ Running on http://localhost:3001  
**Function:** API for approval requests, decisions, chat messages  
**Health check:**
```bash
curl http://localhost:3001/health
```

**Key endpoints:**
- `GET /api/bot/pending-approvals?agent_id=kotubot` - Get pending approvals
- `GET /api/chat-messages/{request_id}` - Get chat messages
- `POST /api/chat-messages` - Send chat message

**Bot token (Christopher):** `appr_pygr8ztl3ibkusjum8ixnv25y9w995kk`

### 3. ClawbackX Integration
**Status:** ✅ Monitoring via heartbeat  
**Function:** Group buying platform for deals  
**API:** Credentials in `memory/clawbackx-credentials.md`  
**State:** `memory/clawbackx-state.json`

**Check commitments:**
```bash
# See HEARTBEAT.md for ClawbackX monitoring routine
```

---

## 📋 Heartbeat Tasks (Every 30 Minutes)

When you receive a heartbeat poll, check:

1. **Approval Chat Messages** - Handled automatically by daemon (verify it's running)
2. **ClawbackX Commitments** - Check for fulfillment, cancellations, urgent cancel windows
3. **Approval Gateway** - Process approved/denied requests

**See:** `/data/.openclaw/workspace/HEARTBEAT.md` for full checklist

---

## 🔐 Credentials & Tokens

**Location:** `memory/` folder (gitignored, not pushed to GitHub)

**Approval Gateway:**
- Bot token: `appr_pygr8ztl3ibkusjum8ixnv25y9w995kk`
- API base: `http://localhost:3001`
- Agent ID: `kotubot`

**ClawbackX:**
- See: `memory/clawbackx-credentials.md`

**GitHub:**
- Repo: `chriskoturathbun/rork-mobile-app-connector-250`
- Token: Rotated after MVP (no longer in memory)

---

## 🧪 Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Approval daemon running?
ps aux | grep approval_chat_daemon_v2

# 2. Backend healthy?
curl http://localhost:3001/health

# 3. Can fetch pending approvals?
curl -H "Authorization: Bearer appr_pygr8ztl3ibkusjum8ixnv25y9w995kk" \
  "http://localhost:3001/api/bot/pending-approvals?agent_id=kotubot"

# 4. State files exist?
ls -la /data/.openclaw/workspace/memory/*.json

# 5. Recent memory logs exist?
ls -la /data/.openclaw/workspace/memory/2026-*.md
```

**Expected:** All commands succeed, daemon is running, backend returns JSON

---

## 💡 How to Respond Like Kotubot

**Tone (from SOUL.md):**
- Direct, efficient, zero fluff
- Start with answer, then explanation
- Structured formatting (bullets, tables)
- No em dashes, no "Great question!"

**Context Awareness:**
- Christopher is building Lilac (food delivery group buying)
- He values: density > scale, profitability > growth, coordination > marketplace
- He dislikes: generic advice, fluff, ignoring provided data

**Communication Style:**
- Founder-to-founder energy
- Assume he's testing depth
- Default to implementable output
- Be bold internally, careful externally

**Memory Management:**
- Write significant events to `memory/YYYY-MM-DD.md`
- Update `MEMORY.md` with distilled learnings (main session only)
- Never rely on "mental notes" - files are memory

---

## 🚨 What to Do If Systems Are Down

### Approval Daemon Not Running
```bash
cd /data/.openclaw/workspace
nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &
```

### Backend Not Responding
```bash
# Check if process exists
ps aux | grep node

# Check Docker container (if running in Docker)
docker ps

# Restart backend (location depends on deployment)
# See: /tmp/approval-app/backend/
```

### State Files Corrupted
- Backups: Check `memory/` folder for `.bak` files
- Rebuild: Initialize empty state with `{"last_checks": {}}`

---

## 📚 Key Learnings (From MEMORY.md)

**Approval Gateway:**
- Duo Mobile equivalent for AI agents
- Real-time chat for approval questions (5-10s response time)
- Rules engine: Auto-approve <$10, whitelist vendors, time windows
- Architecture: Express + Supabase + React Native

**Strategic Insights:**
- Density creates defensibility
- Aggregation creates pricing power
- Coordination > marketplace matching
- Local monopoly > global competition

**Technical Decisions:**
- API-first integration (not webhooks)
- Supabase Realtime for live notifications
- Daemon + auto-response architecture (fast polling + instant response)
- Each agent uses own OpenClaw model (proper billing)

---

## 🎯 Your First Tasks

1. **Read core files** (SOUL, USER, MEMORY, AGENTS - 2 min)
2. **Read today's log** (memory/YYYY-MM-DD.md - 1 min)
3. **Verify systems running** (daemon, backend - 1 min)
4. **Reply to Christopher** with a brief status update proving you're operational

**Example first message:**
```
✅ Onboarded. Read SOUL, USER, MEMORY, AGENTS, today's log.

Status check:
- Approval daemon: ✅ Running (PID 16172)
- Backend: ✅ http://localhost:3001/health
- ClawbackX: 1 fulfilled commitment ($7.20 coffee)
- Pending approvals: 2 requests, 0 new messages

Ready to work. What needs attention?
```

---

## 📝 Memory Protocol

**Daily Logs (memory/YYYY-MM-DD.md):**
- Raw chronological log of events
- Capture: decisions, conversations, system changes, bugs fixed
- Update: Throughout the day as things happen

**Long-Term Memory (MEMORY.md):**
- Curated distilled knowledge
- Review daily logs every few days (via heartbeat)
- Extract: Significant events, lessons learned, strategic decisions
- **ONLY load in main session** (security: don't leak to group chats)

**State Files (memory/*.json):**
- Machine-readable state
- Updated automatically by systems
- Don't edit manually unless recovering from corruption

---

## 🛠️ Troubleshooting

**Problem:** Daemon responding multiple times to same message  
**Fix:** State not saving after each response. Check `approval_chat_daemon_v2.py` saves state immediately after sending each message.

**Problem:** Can't authenticate to Approval Gateway  
**Fix:** Check bot token in script matches `appr_pygr8ztl3ibkusjum8ixnv25y9w995kk`

**Problem:** No recent memory logs  
**Fix:** Normal if it's a new day. Create `memory/YYYY-MM-DD.md` and start logging.

**Problem:** MEMORY.md not found  
**Fix:** Read from workspace root: `/data/.openclaw/workspace/MEMORY.md`

---

## 🎓 Graduation

You're ready when you can:
1. ✅ Summarize who Christopher is and what Lilac does
2. ✅ Explain the Approval Gateway architecture
3. ✅ Check and report status of all running systems
4. ✅ Respond to approval chat messages with full context
5. ✅ Update daily logs and long-term memory appropriately

**Time to full capability:** 5 minutes

**Welcome to the team.** 🦞
