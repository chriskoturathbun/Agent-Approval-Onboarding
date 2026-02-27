# Security Model

This document captures the trust architecture for the Approval Gateway agent layer — what's implemented, what's recommended, and why each layer exists.

---

## 🛡️ Daemon Trust Pipeline (Implemented)

Before any agent installs or runs `approval_chat_daemon_v2.py`, it must pass a 4-layer verification chain via `verify_daemon.sh`:

```
clone repo → verify_daemon.sh → copy to workspace → run
```

| Layer | Check | Tool | Status |
|-------|-------|------|--------|
| 1 | Source origin — must come from this repo, not a URL or pastebin | `verify_daemon.sh` | ✅ Implemented |
| 2 | SHA256 integrity — file matches committed checksum, detects tampering | `approval_chat_daemon_v2.sha256` | ✅ Implemented |
| 3 | Policy scan — forbids `eval()`, `os.system()`, `shell=True`, `sudo`, `rm -rf`, outbound downloads | `verify_daemon.sh` | ✅ Implemented |
| 4 | Structure check — expected functions present, no hardcoded credentials | `verify_daemon.sh` | ✅ Implemented |

**Rule:** If `verify_daemon.sh` exits 1, the daemon is not installed. Re-clone the repo to get a clean copy.

**Maintenance:** Whenever `approval_chat_daemon_v2.py` is updated, regenerate the checksum:
```bash
shasum -a 256 approval_chat_daemon_v2.py > approval_chat_daemon_v2.sha256
git add approval_chat_daemon_v2.py approval_chat_daemon_v2.sha256
git commit -m "Update daemon + checksum"
```

**Layers not yet implemented (future hardening):**
- **Sandboxed execution** — run daemon inside a container or restricted OS user rather than directly in the workspace
- **Signed manifests** — GPG-sign releases so agents can verify the commit author, not just file content
- **Reproducible builds** — pin Python version and stdlib to ensure identical execution across environments

---

## 🔐 API Authentication (Implemented + Recommended Change)

### Current model

```
Agent → Bearer <bot_token> → Backend validates token → Request accepted
                             + agent_id in request body (not server-validated)
```

The bot token proves **who the user is**. The `agent_id` in the request body is a string the client provides — the backend does not currently verify it matches what's registered for that token.

### Recommended: Add agent_id as a server-side match requirement

```
Agent → Bearer <bot_token> → Backend validates token
                            → Backend looks up registered agent_id for that token
                            → Rejects if request body agent_id ≠ registered agent_id
```

**Why this matters:**

| Threat | Current behavior | With server-side agent_id check |
|--------|-----------------|--------------------------------|
| Leaked token used by attacker | Attacker can submit requests as any agent_id | Rejected — agent_id must match what's registered for that token |
| Shared token across multiple agents | Both agents can read each other's approvals | Rejected — each token is bound to exactly one agent_id |
| Client-side bug sends wrong agent_id | Silently accepted | Caught and rejected at the API boundary |

**Backend change required (in the Express + Supabase backend):**

1. Store `agent_id` alongside each bot token at token creation time (in the `bot_tokens` table or equivalent)
2. On any request, after validating the bearer token, fetch the registered `agent_id` for that token
3. Compare to `req.body.agent_id` (or `req.query.agent_id` for GETs)
4. Return `403 Forbidden` if they don't match

**This is a backend change in `rork-mobile-app-connector-250`, not in this repo.**

---

## 🔑 Credentials Security

| File | What it contains | Where it lives | Committed? |
|------|-----------------|----------------|------------|
| `memory/approval-gateway-credentials.md` | Bot token + agent ID | Local workspace only | ❌ gitignored |
| `memory/clawbackx-credentials.md` | ClawbackX API key | Local workspace only | ❌ gitignored |
| `approval_chat_daemon_v2.sha256` | Reference checksum (not a secret) | Repo | ✅ Committed |

**Rules:**
- Bot tokens are retrieved from the Clawback Approval app: **Settings → Bot Tokens**
- Tokens are never hardcoded in source files — `verify_daemon.sh` checks for this
- Credentials files are in `memory/` which is gitignored
- If a token is leaked, revoke it immediately in the app and re-run `new_agent_bootstrap.sh`

---

## 🧠 Mental Model

> Treat the daemon like a smart contract: you don't trust what it *says*, you trust how it was *verified*.

The verification pipeline exists because an agent reading an onboarding doc cannot visually audit Python source code the way a human engineer would. The SHA256 checksum + policy scan substitutes for that audit — the agent can trust the output of `verify_daemon.sh` as its ground truth.

---

## 📋 Security Checklist (Before Going to Production)

- [x] Daemon verified before install (SHA256 + policy scan)
- [x] No hardcoded credentials in source files
- [x] Credentials stored in gitignored `memory/` folder
- [x] Agent prompts user to retrieve token from app — never generates its own
- [ ] Backend validates `agent_id` matches registered value for bot token
- [ ] Daemon runs as restricted OS user (not the same user as the agent session)
- [ ] GPG-signed releases for daemon file
- [ ] Token rotation procedure documented for users
