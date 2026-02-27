# Heartbeat Checklist
# Runs on Haiku to minimize cost. Keep this lean.

## Approval Chat Messages (every heartbeat)
When heartbeat fires:
1. Fetch pending approvals from Approval Gateway API
2. For each pending approval, check for new user messages in chat
3. Respond to new messages with full Kotubot context (MEMORY.md, USER.md, SOUL.md)
4. Track last check time to avoid duplicate responses
5. Send replies back to approval chat

**Implementation:**
- Use bot token to fetch approvals: `GET /api/bot/pending-approvals?agent_id=kotubot`
- Check messages: `GET /api/chat-messages/{request_id}`
- Filter messages newer than last check
- Reply with full agent context (not keyword matching)
- Post reply: `POST /api/chat-messages` with sender=agent

**State tracking:**
- File: `memory/approval-chat-state.json`
- Structure: `{"last_checks": {"request_id": "2026-02-26T19:00:00Z"}, "last_poll": "..."}`

## ClawbackX (every 30 minutes)
When heartbeat fires:
1. Fetch `GET /api/commitments` with API key from memory/clawbackx-credentials.md
2. Check each commitment for:
   - `status: vendor_announced` + `cancel_window_hours_remaining > 0` → notify with cancel window countdown
   - `status: vendor_announced` + `cancel_window_hours_remaining < 2` → send URGENT message
   - `status: auto_cancelled` → confirm to Christopher
   - `status: fulfilled` → confirm to Christopher + amount charged
3. Update memory/clawbackx-state.json with lastCheck timestamp
4. Never commit without explicit approval from Christopher

## Approval Gateway (every heartbeat)
When heartbeat fires:
1. Run `python3 /data/.openclaw/workspace/kotubot_approval_client.py` to check approvals
   - Uses credentials from memory/approval-gateway-credentials.md
   - API base: https://approvals.clawbackx.com
2. For each approval:
   - If status=approved + deal_slug exists → Commit to ClawbackX deal
   - If status=denied → Log reason, skip deal
   - If status=pending → Wait, check again next heartbeat
   - If status=expired → Log expiry, skip deal
3. Update memory/approval-gateway-state.json with:
   - lastCheck timestamp
   - approvals processed
   - deals committed
4. If new approvals or denials → Notify Christopher

**INTEGRATION:**
```python
from kotubot_approval_client import heartbeat_check_approvals
message = heartbeat_check_approvals()
if message:
    notify_christopher(message)
```

**CREDENTIALS:**
- API Base: https://approvals.clawbackx.com
- Bot Token: Loaded from `memory/approval-gateway-credentials.md` (retrieve from app: Settings → Bot Tokens)
- Agent ID: kotubot
- Note: Bot token automatically identifies user (no user_id needed)
