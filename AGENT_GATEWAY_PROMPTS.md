# Agent Gateway Onboarding Prompts

Use this page when you want to onboard an agent to the Approval Gateway quickly.

## 1) Choose your agent mode first

- `openclaw_vps` or `generic_vps`: agent can run daemon/polling, uses in-app approval chat
- `non_vps` + `managed`: centrally managed bot (for example Manus-native), no Telegram relay setup
- `non_vps` + `own`: non-VPS agent with user-owned Telegram bot token/webhook

---

## 2) Copy-paste prompt for VPS agents

```text
You are onboarding to my Approval Gateway.

Rules:
1. Never execute a purchase before approval.
2. Submit every spend via POST /api/bot/approval-requests.
3. Poll decisions via GET /api/bot/pending-approvals.
4. If approved, execute. If denied/expired, skip.

My credentials:
- api_base: https://approvals.clawbackx.com
- bot_token: <PASTE_BOT_TOKEN>
- agent_id: <PASTE_AGENT_ID>
- bot_type: openclaw_vps

Setup tasks:
1. Save credentials to memory/approval-gateway-credentials.md
2. Start approval chat daemon
3. Verify /health, auth, and pending approvals endpoint
4. Confirm operational status with a short checklist
```

---

## 3) Copy-paste prompt for non-VPS managed bots (Manus-native style)

```text
You are onboarding to my Approval Gateway in non-VPS managed mode.

Rules:
1. Never execute a purchase before approval.
2. Submit every spend via POST /api/bot/approval-requests.
3. Do not set up Telegram relay (this bot is centrally managed).
4. For ask/details flow, use this external assistant link only.

My credentials:
- api_base: https://approvals.clawbackx.com
- bot_token: <PASTE_BOT_TOKEN>
- agent_id: <PASTE_AGENT_ID>
- bot_type: non_vps
- telegram_control: managed
- agent_link: <PASTE_ASSISTANT_LINK>

Setup tasks:
1. Save credentials
2. Confirm approval submission works
3. Confirm non-VPS behavior: ask/details should open agent_link
4. Return a short verification summary
```

---

## 4) Copy-paste prompt for non-VPS with owned Telegram relay

```text
You are onboarding to my Approval Gateway in non-VPS + owned Telegram mode.

Rules:
1. Never execute a purchase before approval.
2. Submit every spend via POST /api/bot/approval-requests.
3. Use non-VPS handoff (agent_link) for ask/details.
4. Telegram relay is allowed because I control the bot token/webhook.

My credentials:
- api_base: https://approvals.clawbackx.com
- bot_token: <PASTE_BOT_TOKEN>
- agent_id: <PASTE_AGENT_ID>
- bot_type: non_vps
- telegram_control: own
- agent_link: <PASTE_ASSISTANT_LINK>

Telegram relay setup flow:
1. Open app: Settings -> Telegram Relay
2. Enter Telegram bot token
3. Save relay
4. Send one message to bot in Telegram
5. Tap "refresh link status" to capture chat_id

Return:
- approval auth check result
- relay status (not linked / waiting / linked)
```

---

## 5) What success looks like

Agent should report:

1. Approval API reachable (`/health`)
2. Bot token auth valid
3. Correct runtime mode recognized (`bot_type`, `telegram_control`)
4. Ask/details route confirmed:
- VPS -> in-app approval chat
- non-VPS -> external `agent_link`
5. Purchase rule acknowledged:
- no purchase without prior approval
