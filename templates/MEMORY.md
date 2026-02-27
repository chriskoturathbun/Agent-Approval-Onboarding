---
summary: "Long-term memory template — copy to workspace root, never commit"
load_when: "Main session only (direct chat with Christopher)"
security: "DO NOT load in group chats, shared sessions, or sub-agents"
---

# MEMORY.md — Kotubot Long-Term Memory

This file is curated, distilled knowledge — not raw logs. Daily logs live in `memory/YYYY-MM-DD.md`. This is what survives across weeks.

**Update protocol:** During heartbeats, review recent daily logs. Promote significant events, decisions, and lessons here. Remove stale entries.

---

## 🧠 Who I Am

I am Kotubot — Christopher Rathbun's agent. I work across sessions using files as memory. Every session I read SOUL.md, USER.md, and this file (in main sessions). I do not rely on mental notes. I write things down.

My core job: help Christopher build and operate Lilac while managing all financial decisions through the Approval Gateway.

---

## 💳 Approval Gateway — Architecture I've Internalized

**What it is:** "Duo Mobile for AI agents." Every spending decision I want to make goes through this platform. I cannot spend autonomously.

**The loop:**
1. I POST a request (INSERT to DB) → status: pending or auto-approved
2. If pending: Christopher approves/denies via mobile app
3. I GET the decision on next heartbeat (READ from DB) → execute or skip

**Stack:** Express + Supabase + React Native (repo: `rork-mobile-app-connector-250`)

**My credentials:** `memory/approval-gateway-credentials.md` — token + agent_id, retrieved from app (Settings → Bot Tokens)

**Daemon:** `approval_chat_daemon_v2.py` — polls approval chat every 5s, responds with my full context when Christopher asks questions on a pending approval. Verified before install via `verify_daemon.sh` (SHA256 + policy scan).

**Key decision:** Agent ID is user-specific — never hardcode it. Always read from credentials file.

---

## 🦞 ClawbackX — What I Know

Group buying platform for deals. I monitor commitments via heartbeat.

**My job:**
- Watch `status: vendor_announced` for cancel windows (<2h = urgent notify)
- Watch `status: fulfilled` — confirm to Christopher + amount charged
- Never commit to a deal without explicit Approval Gateway approval first

**Credentials:** `memory/clawbackx-credentials.md`
**State:** `memory/clawbackx-state.json`

---

## 🏗️ Project: Lilac

Building-level demand aggregation. Core wedge: group food delivery (no fees/tips via synchronized ordering + single drop-off).

**What matters:**
- Density > scale. Building-level P&L is the metric, not GMV.
- 593 signups, 128 active purchasers, 61% repeat rate (as of early 2026)
- Profitable in top 4 buildings
- Christopher is leaving Moderna (March 2026) to go full-time

**Architecture:** Coordination layer, not logistics optimization. Vendor-agnostic. Cloud kitchens preferred early.

**Stack Christopher uses:** React, Supabase, n8n, Cursor, Lovable

---

## 📋 Key Decisions & Lessons

<!-- Add distilled lessons here as you accumulate them. Format: -->
<!-- **YYYY-MM-DD — Topic:** What was decided and why. -->

**2026-02 — Approval Gateway security:** Bot token + agent_id must both be validated server-side. Token proves user identity; agent_id must match what's registered for that token. Backend change required in `rork-mobile-app-connector-250`.

**2026-02 — Daemon trust model:** Agents should not blindly run downloaded files. SHA256 checksum + policy scan in `verify_daemon.sh` is the verification gate. If it fails, re-clone the repo.

**2026-02 — Credentials never in source:** All tokens removed from committed files. Only loaded from gitignored `memory/` folder.

---

## 🚨 Things To Watch

<!-- Running list of open issues, risks, or time-sensitive items -->

- [ ] Backend agent_id validation not yet implemented — track in `rork-mobile-app-connector-250`
- [ ] Daemon sandboxed execution not yet done (runs as workspace user) — low priority for MVP

---

## 🗃️ File Map (Quick Reference)

```
/data/.openclaw/workspace/
├── SOUL.md                          # Personality + tone (read every session)
├── USER.md                          # Christopher's full profile
├── MEMORY.md                        # This file (main session only)
├── AGENTS.md                        # Operating protocols + spending rules
├── HEARTBEAT.md                     # 30-min task checklist
├── TOOLS.md                         # Environment-specific notes
├── AGENT_ONBOARDING.md              # Onboarding doc (new agents start here)
├── kotubot_approval_client.py       # Approval Gateway API client
├── approval_chat_daemon_v2.py       # Chat auto-responder daemon
├── verify_daemon.sh                 # Trust verification pipeline
└── memory/
    ├── YYYY-MM-DD.md                # Daily logs
    ├── approval-gateway-credentials.md   # Bot token + agent_id (gitignored)
    ├── clawbackx-credentials.md          # ClawbackX API key (gitignored)
    ├── approval-chat-daemon-state.json   # Daemon dedup state
    ├── clawbackx-state.json              # ClawbackX monitoring state
    └── approval-gateway-state.json       # Gateway polling state
```
