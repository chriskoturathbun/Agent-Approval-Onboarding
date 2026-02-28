#!/usr/bin/env python3
"""
Approval Chat Daemon v2
-----------------------
Pure relay daemon. Polls the Approval Gateway for new user chat messages on
pending approval requests, then forwards them to the live agent via notify_url.

The agent generates its own responses using its full live context and posts
them back directly via POST /api/chat-messages with its bot token.

If no notify_url is configured, messages are written to the inbox file so the
agent can pick them up on its next turn.

Usage:
    cd /data/.openclaw/workspace
    nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &

Stop:
    pkill -f approval_chat_daemon_v2

Logs:
    tail -f /tmp/approval-daemon-v2.log

Credentials file (memory/approval-gateway-credentials.md):
    token:      appr_<your_token>
    agent_id:   kotubot
    api_base:   https://approvals.clawbackx.com
    notify_url: http://localhost:8080/api/sessions/kotubot/notify   ← optional

State:
    memory/approval-chat-daemon-state.json

Inbox fallback (when no notify_url):
    memory/approval_chat_inbox.json
"""

import hashlib
import hmac
import json
import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

WORKSPACE     = '/data/.openclaw/workspace'
CREDS_FILE    = os.path.join(WORKSPACE, 'memory/approval-gateway-credentials.md')
STATE_FILE    = os.path.join(WORKSPACE, 'memory/approval-chat-daemon-state.json')
INBOX_FILE    = os.path.join(WORKSPACE, 'memory/approval_chat_inbox.json')
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
    if not os.path.exists(CREDS_FILE):
        raise FileNotFoundError(
            f"Credentials file not found: {CREDS_FILE}\n"
            "Retrieve your bot token from the Approval Gateway app "
            "(Settings → Bot Tokens) and save it with:  token: appr_<your_token>"
        )

    creds = {
        'api_base':   'https://approvals.clawbackx.com',
        'bot_token':  None,
        'agent_id':   'kotubot',
        'notify_url': None,
    }
    with open(CREDS_FILE) as f:
        for line in f:
            if ':' in line and not line.startswith('#'):
                key, _, value = line.partition(':')
                key   = key.strip().lower().replace(' ', '_')
                value = value.strip()
                if key == 'token':
                    creds['bot_token'] = value
                elif key == 'api_base':
                    creds['api_base'] = value
                elif key == 'agent_id':
                    creds['agent_id'] = value
                elif key == 'notify_url':
                    creds['notify_url'] = value

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

def _base_headers(token: str) -> Dict:
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type':  'application/json',
        'User-Agent':    'ApprovalChatDaemon/2.0',
    }


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
        req  = Request(url, data=data, headers=headers, method='POST')
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError) as e:
        log.warning(f"POST {url} failed: {e}")
        return None


# ─────────────────────────────────────────────
# Notification helpers
# ─────────────────────────────────────────────

def build_notification(approval_request: Dict, chat_message: Dict) -> Dict:
    """Build the structured notification payload for the agent."""
    return {
        'type':        'approval_chat_question',
        'request_id':  approval_request['id'],
        'message_id':  chat_message.get('id', ''),
        'vendor':      approval_request.get('vendor', ''),
        'amount_cents': approval_request.get('spending_amount_cents', 0),
        'category':    approval_request.get('category', ''),
        'reason':      approval_request.get('reason', ''),
        'message':     chat_message.get('message', ''),
        'full_request': approval_request,
        'reply_via': {
            'method': 'POST',
            'url':    'https://approvals.clawbackx.com/api/chat-messages',
            'requires_local_token': True,
            'body_template': {
                'approval_request_id': approval_request['id'],
                'sender':  'agent',
                'message': '{{your_response}}',
            },
        },
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


def sign_payload(body: bytes, secret: str) -> str:
    """HMAC-SHA256 sign a payload so the agent can verify it came from the daemon."""
    return 'sha256=' + hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()


def send_notification(notify_url: str, bot_token: str,
                      approval_request: Dict, chat_message: Dict) -> bool:
    """
    POST a signed notification to the agent's notify_url.
    Retries 3 times with exponential backoff (0s, 1s, 2s).
    Returns True on success.
    """
    payload = build_notification(approval_request, chat_message)
    body    = json.dumps(payload).encode('utf-8')
    sig     = sign_payload(body, bot_token)

    headers = {
        'Content-Type':          'application/json',
        'X-Approval-Signature':  sig,
        'User-Agent':            'ApprovalChatDaemon/2.0',
    }

    delays = [0, 1, 2]  # seconds before each retry
    for attempt, delay in enumerate(delays, start=1):
        if delay > 0:
            time.sleep(delay)
        try:
            req = Request(notify_url, data=body, headers=headers, method='POST')
            with urlopen(req, timeout=10) as resp:
                if resp.status < 300:
                    log.info(f"Notification delivered to {notify_url}")
                    return True
                log.warning(f"notify attempt {attempt}/3 → HTTP {resp.status}")
        except Exception as e:
            log.warning(f"notify attempt {attempt}/3 → {e}")

    log.error(f"All notification attempts failed for {notify_url}")
    return False


def write_to_inbox(approval_request: Dict, chat_message: Dict) -> bool:
    """
    Fallback: write the pending question to the inbox file.
    The agent picks this up on its next turn and responds via the API.
    """
    inbox = []
    if os.path.exists(INBOX_FILE):
        try:
            with open(INBOX_FILE) as f:
                inbox = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    entry = build_notification(approval_request, chat_message)
    inbox.append(entry)

    try:
        os.makedirs(os.path.dirname(INBOX_FILE), exist_ok=True)
        with open(INBOX_FILE, 'w') as f:
            json.dump(inbox, f, indent=2)
    except IOError as e:
        log.error(f"Failed to write inbox file: {e}")
        return False

    log.info(f"Message written to inbox fallback: {INBOX_FILE}")
    return True


# ─────────────────────────────────────────────
# Core poll loop
# ─────────────────────────────────────────────

def poll_once(creds: Dict, state: Dict) -> Dict:
    """
    Single poll cycle:
    1. Fetch pending approvals
    2. For each: check for new USER messages
    3. Forward each new message to the agent via notify_url (or inbox fallback)
    4. Update state
    """
    api_base  = creds['api_base']
    agent_id  = creds['agent_id']
    bot_token = creds['bot_token']
    notify_url = creds.get('notify_url')
    headers   = _base_headers(bot_token)

    now = datetime.now(timezone.utc).isoformat()

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

    for req in pending:
        request_id = req['id']
        last_check = state['last_checks'].get(request_id)

        messages_data = api_get(f"{api_base}/api/chat-messages/{request_id}", headers)
        if not messages_data:
            continue

        messages = messages_data.get('messages', [])

        # Only forward USER messages we haven't seen yet
        new_user_messages = [
            msg for msg in messages
            if msg.get('sender') == 'user'
            and (last_check is None or msg.get('created_at', '') > last_check)
        ]

        if not new_user_messages:
            continue

        log.info(f"[{request_id}] {len(new_user_messages)} new user message(s) — forwarding to agent")

        max_forwarded_created_at = None
        for msg in new_user_messages:
            forwarded = False
            if notify_url:
                forwarded = send_notification(notify_url, bot_token, req, msg)
                if not forwarded:
                    log.warning(f"[{request_id}] notify_url delivery failed, falling back to inbox")
                    forwarded = write_to_inbox(req, msg)
            else:
                forwarded = write_to_inbox(req, msg)

            created_at = msg.get('created_at', '')
            if forwarded and created_at and (
                max_forwarded_created_at is None or created_at > max_forwarded_created_at
            ):
                max_forwarded_created_at = created_at

        if max_forwarded_created_at:
            state['last_checks'][request_id] = max_forwarded_created_at
            save_state(state)

    return state


def run():
    log.info("🦞 Approval Chat Daemon v2 starting...")

    try:
        creds = load_credentials()
    except (FileNotFoundError, ValueError) as e:
        log.error(str(e))
        return

    notify_url = creds.get('notify_url')
    log.info(f"API:    {creds['api_base']} | Agent: {creds['agent_id']}")
    log.info(f"Relay:  {'→ ' + notify_url if notify_url else 'inbox fallback (no notify_url set)'}")
    log.info(f"Poll:   every {POLL_INTERVAL}s — Ctrl+C to stop")

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
