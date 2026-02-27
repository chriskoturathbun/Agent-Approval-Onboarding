#!/usr/bin/env python3
"""
Approval Chat Daemon v2
-----------------------
Polls the Approval Gateway every 5 seconds for new chat messages on pending
approval requests. When a new message is found, it generates a response using
the agent's full context (SOUL.md, USER.md, MEMORY.md) and posts it back.

Usage:
    cd /data/.openclaw/workspace
    nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &

Stop:
    pkill -f approval_chat_daemon_v2

Logs:
    tail -f /tmp/approval-daemon-v2.log

State:
    memory/approval-chat-daemon-state.json
    {
        "last_checks": {"request_id": "2026-02-26T19:00:00Z"},
        "last_poll": "2026-02-26T19:00:05Z"
    }
"""

import json
import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

WORKSPACE = '/data/.openclaw/workspace'
CREDS_FILE = os.path.join(WORKSPACE, 'memory/approval-gateway-credentials.md')
STATE_FILE = os.path.join(WORKSPACE, 'memory/approval-chat-daemon-state.json')
POLL_INTERVAL = 5  # seconds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger('approval-daemon')


# ─────────────────────────────────────────────
# Credentials
# ─────────────────────────────────────────────

def load_credentials() -> Dict[str, str]:
    """Load bot token and API base from credentials file."""
    if not os.path.exists(CREDS_FILE):
        raise FileNotFoundError(
            f"Credentials file not found: {CREDS_FILE}\n"
            "Retrieve your bot token from the Approval Gateway app (Settings → Bot Tokens) "
            "and save it with the line:  token: appr_<your_token_here>"
        )

    creds = {'api_base': 'http://localhost:3001', 'bot_token': None, 'agent_id': 'kotubot'}
    with open(CREDS_FILE) as f:
        for line in f:
            if ':' in line and not line.startswith('#'):
                key, _, value = line.partition(':')
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                if key == 'token':
                    creds['bot_token'] = value
                elif key == 'api_base':
                    creds['api_base'] = value
                elif key == 'agent_id':
                    creds['agent_id'] = value

    if not creds['bot_token']:
        raise ValueError(f"No `token:` line in {CREDS_FILE}")

    return creds


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

def load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'last_checks': {}, 'last_poll': None}


def save_state(state: Dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────

def api_get(url: str, headers: Dict) -> Optional[Dict]:
    try:
        req = Request(url, headers=headers, method='GET')
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError) as e:
        log.warning(f"GET {url} failed: {e}")
        return None


def api_post(url: str, headers: Dict, payload: Dict) -> Optional[Dict]:
    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request(url, data=data, headers=headers, method='POST')
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError) as e:
        log.warning(f"POST {url} failed: {e}")
        return None


# ─────────────────────────────────────────────
# Context loading
# ─────────────────────────────────────────────

def load_context_file(filename: str) -> str:
    """Load a context file from the workspace, return empty string if missing."""
    path = os.path.join(WORKSPACE, filename)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ''


def load_agent_context() -> Dict[str, str]:
    """Load all context files the agent uses to respond intelligently."""
    return {
        'soul': load_context_file('SOUL.md'),
        'user': load_context_file('USER.md'),
        'memory': load_context_file('MEMORY.md'),
        'agents': load_context_file('AGENTS.md'),
    }


# ─────────────────────────────────────────────
# Response generation
# ─────────────────────────────────────────────

def generate_response(
    context: Dict[str, str],
    approval_request: Dict,
    new_message: Dict
) -> str:
    """
    Generate a response to a user's approval chat message.

    ┌─────────────────────────────────────────────────────────────────┐
    │  AGENT MODEL HOOK                                               │
    │                                                                 │
    │  This function is where your agent model (OpenClaw, Claude,    │
    │  etc.) should generate a response. It receives:                │
    │    - context: full SOUL/USER/MEMORY/AGENTS file contents       │
    │    - approval_request: the pending spend request details       │
    │    - new_message: the user's chat message to respond to        │
    │                                                                 │
    │  Replace the template below with a call to your model API.     │
    │  Example stub for OpenClaw:                                    │
    │                                                                 │
    │    from openclaw import complete                                │
    │    prompt = build_prompt(context, approval_request, new_message)│
    │    return complete(prompt)                                      │
    └─────────────────────────────────────────────────────────────────┘
    """
    vendor = approval_request.get('vendor', 'Unknown vendor')
    amount = approval_request.get('spending_amount_cents', 0) / 100
    reason = approval_request.get('reason', '')
    user_msg = new_message.get('content', '')

    # Default template response — replace this with your model call
    return (
        f"On the ${amount:.2f} {vendor} request: {reason}\n\n"
        f"Re: \"{user_msg}\" — I can clarify further if needed. "
        f"Approve or deny in the app when ready."
    )


# ─────────────────────────────────────────────
# Core poll loop
# ─────────────────────────────────────────────

def poll_once(creds: Dict, state: Dict) -> Dict:
    """
    Single poll cycle:
    1. Fetch pending approvals from DB
    2. For each: fetch chat messages
    3. If new messages: generate + post response
    4. Update and return state
    """
    api_base = creds['api_base']
    agent_id = creds['agent_id']
    headers = {
        'Authorization': f"Bearer {creds['bot_token']}",
        'Content-Type': 'application/json'
    }

    now = datetime.now(timezone.utc).isoformat()

    # 1. Fetch pending approvals (READ from DB)
    data = api_get(
        f"{api_base}/api/bot/pending-approvals?agent_id={agent_id}",
        headers
    )
    if data is None:
        return state

    pending = [r for r in data.get('approvals', []) if r['status'] == 'pending']
    state['last_poll'] = now

    if not pending:
        return state

    context = load_agent_context()

    for req in pending:
        request_id = req['id']
        last_check = state['last_checks'].get(request_id)

        # 2. Fetch chat messages for this approval (READ from DB)
        messages_data = api_get(f"{api_base}/api/chat-messages/{request_id}", headers)
        if not messages_data:
            continue

        messages = messages_data.get('messages', [])

        # 3. Find messages we haven't responded to yet
        new_messages = []
        for msg in messages:
            # Only respond to user messages (not our own)
            if msg.get('sender') == 'agent':
                continue
            msg_time = msg.get('created_at', '')
            if last_check is None or msg_time > last_check:
                new_messages.append(msg)

        if not new_messages:
            continue

        log.info(f"[{request_id}] {len(new_messages)} new message(s) from user")

        for msg in new_messages:
            # 4. Generate response using agent model + context
            response_text = generate_response(context, req, msg)

            # 5. POST response back (INSERT to DB)
            result = api_post(
                f"{api_base}/api/chat-messages",
                headers,
                {
                    'request_id': request_id,
                    'sender': 'agent',
                    'content': response_text
                }
            )

            if result:
                log.info(f"[{request_id}] Response posted")
            else:
                log.warning(f"[{request_id}] Failed to post response")

        # 6. Save state immediately after responding (prevents duplicates)
        state['last_checks'][request_id] = now
        save_state(state)

    return state


def run():
    log.info("🦞 Approval Chat Daemon v2 starting...")

    try:
        creds = load_credentials()
    except (FileNotFoundError, ValueError) as e:
        log.error(str(e))
        return

    log.info(f"API: {creds['api_base']} | Agent: {creds['agent_id']}")
    log.info(f"Polling every {POLL_INTERVAL}s — Ctrl+C to stop")

    state = load_state()

    while True:
        try:
            state = poll_once(creds, state)
        except KeyboardInterrupt:
            log.info("Daemon stopped.")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    run()
