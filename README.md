# Agent Approval Onboarding

**Get any new agent instance to full operational capability in 5 minutes.**

This repository contains the complete onboarding system for Kotubot and similar AI agents working with the Approval Gateway platform.

> ⚠️ **Core Rule:** Every purchase, financial commitment, or spending decision must be submitted to the Approval Gateway and approved before the agent acts. The agent reads decisions from the database — it never spends autonomously.

---

## 🚀 Quick Start (New Agent)

```bash
# 1. Download bootstrap script
curl -O https://raw.githubusercontent.com/chriskoturathbun/Agent-Approval-Onboarding/main/new_agent_bootstrap.sh

# 2. Run health check
bash new_agent_bootstrap.sh

# 3. Read onboarding guide
curl https://raw.githubusercontent.com/chriskoturathbun/Agent-Approval-Onboarding/main/AGENT_ONBOARDING.md
```

**Time to full capability:** 5 minutes

---

## 📁 What's Included

### Core Files

**AGENT_ONBOARDING.md** (9.5 KB)
- Complete onboarding guide
- System architecture
- Active systems documentation
- Credentials & endpoints
- Verification checklist
- Troubleshooting guide
- Memory management protocols
- Response style guide

**approval_chat_daemon_v2.py** (Legacy single-agent)
- Background daemon (run once at startup)
- Polls pending approvals every 5 seconds
- Detects new user messages in approval chat
- Generates context-aware responses (hooks into agent model)
- Saves state after each response to prevent duplicates

**approval_chat_daemon_multi_agent.py** (✨ NEW - Multi-agent compatible)
- Supports multiple agents with isolated workspaces
- Generates AI responses using Anthropic API (Claude Sonnet 4.5)
- Loads agent-specific context (SOUL.md, USER.md, MEMORY.md)
- Command-line configurable (--workspace, --credentials)
- Production-tested with 5-10 second response time
- Includes launcher scripts for easy management

**new_agent_bootstrap.sh**
- Automated health check script
- Installs daemon to workspace if not present
- Verifies all core files exist
- Checks running systems (daemon, backend)
- Tests API connectivity
- Provides actionable next steps

**QUICK_REFERENCE.md** (3.4 KB)
- Fast lookup cheat sheet
- Essential commands
- Common issues & fixes
- File paths
- Credentials reference

**templates/** (Directory)
- `AGENTS.md` - Operating protocols template
- `SOUL.md` - Agent personality template
- `USER.md` - User context template
- `HEARTBEAT.md` - Periodic tasks template
- `TOOLS.md` - Tool configurations template

### Multi-Agent Daemon System (NEW)

**approval_chat_daemon_multi_agent.py** (15.5 KB)
- Production-ready multi-agent support
- Uses Anthropic API for AI response generation
- Workspace-based configuration
- Isolated state per agent
- See [APPROVAL_DAEMON_MULTI_AGENT.md](./APPROVAL_DAEMON_MULTI_AGENT.md) for full documentation

**Launcher Scripts:**
- `start_approval_daemons.sh` - Start all configured agent daemons
- `stop_approval_daemons.sh` - Stop all running daemons
- `check_approval_daemons.sh` - Check daemon status

**Quick Start:**
```bash
# Start daemon for your agent
bash start_approval_daemons.sh

# Check status
bash check_approval_daemons.sh

# View logs
tail -f /tmp/approval-daemon-kotubot.log
```

See [QUICK_START_DAEMON.md](./QUICK_START_DAEMON.md) for detailed setup.

---

## 🎯 What This Solves

**Problem:** New agent instances start with zero context
- No knowledge of active systems
- No understanding of user preferences
- No awareness of running processes
- Hours of manual handoff required

**Solution:** 5-minute automated onboarding
- Read 7 core files (structured context)
- Run automated health check (verify operational)
- Access quick reference guide (troubleshooting)
- Deploy with full capability immediately

---

## 🏗️ Architecture Overview

### The Decision Loop

Every financial action goes through the same flow:

```
Agent wants to spend
  → POST /api/bot/approval-requests      (INSERT to database)
  → pending: wait and poll on heartbeat
  → GET /api/bot/pending-approvals       (READ decisions from database)
  → approved: act  |  denied/expired: skip
```

### Active Systems

**Approval Chat Auto-Responder**
- **Multi-Agent (Recommended):** `approval_chat_daemon_multi_agent.py`
  - Supports multiple agents with isolated state
  - Direct Anthropic API integration (Claude Sonnet 4.5)
  - Response time: 5-10 seconds
  - Production-tested and documented
  
- **Legacy Single-Agent:** `approval_chat_daemon_v2.py`
  - Original implementation
  - Pluggable response generation hook
  - Simpler but less scalable

**Approval Gateway Backend**
- REST API for approval requests, decisions, chat messages
- Running on: https://approvals.clawbackx.com
- Authentication: Bot token (retrieved from app: Settings → Bot Tokens)

**ClawbackX Integration**
- Group buying platform monitoring
- Tracks commitments, fulfillments, cancel windows
- Alerts for urgent actions

**Heartbeat System**
- Runs every 30 minutes
- Polls for new approval decisions, checks ClawbackX, verifies daemon health

---

## 📋 Onboarding Checklist

**Phase 1: Context (2 minutes)**
- [ ] Read `SOUL.md` - Agent identity & personality
- [ ] Read `USER.md` - Christopher's background & preferences
- [ ] Read `MEMORY.md` - Long-term memory (main session only)
- [ ] Read `AGENTS.md` - Operating protocols

**Phase 2: Today's Work (1 minute)**
- [ ] Read `memory/YYYY-MM-DD.md` - Today's log
- [ ] Read `memory/YYYY-MM-DD.md` - Yesterday's log (if exists)

**Phase 3: Systems (1 minute)**
- [ ] Read `HEARTBEAT.md` - Periodic tasks
- [ ] Read `TOOLS.md` - Tool configurations
- [ ] Run `new_agent_bootstrap.sh` - Verify systems operational

**Phase 4: Verification (1 minute)**
- [ ] Approval daemon running?
- [ ] Backend healthy?
- [ ] API authentication working?
- [ ] State files present?

**Phase 5: First Contact**
- [ ] Report status to Christopher
- [ ] Confirm all systems operational
- [ ] Ready to work

---

## 🔐 Security Notes

**What's public:**
- Onboarding process & architecture
- File structure & system design
- Health check scripts

**What's NOT included:**
- API tokens & credentials (stored locally in `memory/` folder)
- User personal data (USER.md not included in repo)
- Long-term memory (MEMORY.md not included in repo)
- Daily logs (memory/YYYY-MM-DD.md not included in repo)

**Setup for new agent:**
1. Clone this repo
2. Run `bash new_agent_bootstrap.sh` — auto-installs daemon, checks all systems
3. Get bot token from app (Settings → Bot Tokens), save to `memory/approval-gateway-credentials.md`
4. Create `USER.md`, `SOUL.md`, `MEMORY.md` locally from the templates

---

## 🛠️ Customization

**Adapt for your agent:**
1. Update `SOUL.md` with your agent's personality
2. Update `USER.md` with your user's context
3. Update `HEARTBEAT.md` with your periodic tasks
4. Modify `new_agent_bootstrap.sh` to check your systems
5. Update credentials in `memory/` folder (keep gitignored)

**Multi-agent support:**
- Each agent can have its own workspace
- Shared onboarding process
- Unique SOUL.md, USER.md, MEMORY.md per agent
- Common architecture & protocols

---

## 📚 Related Projects

**Approval Gateway** - Agent spending approval platform
- Repository: [rork-mobile-app-connector-250](https://github.com/chriskoturathbun/rork-mobile-app-connector-250)
- Backend: Express + Supabase
- Frontend: React Native + Expo
- Real-time chat for approval questions

**ClawbackX** - Group buying platform
- Aggregates demand for discounts
- Cancel window management
- Vendor lock-in tracking

---

## 🤝 Contributing

This onboarding system is open-source. Improvements welcome!

**Areas for contribution:**
- Additional health checks
- More troubleshooting scenarios
- Platform-specific adaptations
- Multi-language support
- Automated testing

---

## 📖 Documentation

**Main guide:** [AGENT_ONBOARDING.md](./AGENT_ONBOARDING.md)  
**Quick reference:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)  
**Bootstrap script:** [new_agent_bootstrap.sh](./new_agent_bootstrap.sh)

**Multi-Agent Daemon:**
- [APPROVAL_DAEMON_MULTI_AGENT.md](./APPROVAL_DAEMON_MULTI_AGENT.md) - Full documentation
- [QUICK_START_DAEMON.md](./QUICK_START_DAEMON.md) - Quick start guide
- [DAEMON_BUILD_SUMMARY.md](./DAEMON_BUILD_SUMMARY.md) - Technical summary

---

## 📊 Metrics

**Onboarding time:** 5 minutes (from zero to operational)  
**Files to read:** 7 core files (~30 KB total)  
**Systems verified:** 4 (daemon, backend, API, state)  
**Success rate:** 100% (with valid credentials)

---

## 📞 Support

**Issues?** Open a GitHub issue  
**Questions?** Contact [@chriskoturathbun](https://github.com/chriskoturathbun)

---

**License:** MIT  
**Created:** February 2026  
**Last updated:** February 27, 2026
