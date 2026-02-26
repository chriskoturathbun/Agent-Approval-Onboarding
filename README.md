# Agent Approval Onboarding

**Get any new agent instance to full operational capability in 5 minutes.**

This repository contains the complete onboarding system for Kotubot and similar AI agents working with the Approval Gateway platform.

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

**new_agent_bootstrap.sh** (3.5 KB)
- Automated health check script
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

### Active Systems

**Approval Chat Auto-Responder**
- Polls approval requests every 5 seconds
- Responds automatically with full context (MEMORY.md, USER.md, SOUL.md)
- Response time: 5-10 seconds
- Script: `approval_chat_daemon_v2.py`

**Approval Gateway Backend**
- REST API for approval requests, decisions, chat messages
- Running on: http://localhost:3001
- Authentication: Bot token-based

**ClawbackX Integration**
- Group buying platform monitoring
- Tracks commitments, fulfillments, cancel windows
- Alerts for urgent actions

**Heartbeat System**
- Runs every 30 minutes
- Checks approval chats, ClawbackX, approval gateway
- Proactive monitoring and alerts

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
2. Copy credentials to `memory/` folder (gitignored)
3. Create `USER.md`, `SOUL.md`, `MEMORY.md` locally
4. Run bootstrap script

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
**Last updated:** February 26, 2026
