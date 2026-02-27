#!/usr/bin/env python3
"""
Approval Chat Daemon v2
-----------------------
Polls the Approval Gateway every 5 seconds for new chat messages on pending
approval requests. When a new message arrives, it uses the agent's own model
(via ANTHROPIC_API_KEY) with the full SOUL/USER/MEMORY/AGENTS context to
generate a response, then posts it back.

Usage:
    cd /data/.openclaw/workspace
    nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &

Stop:
    pkill -f approval_chat_daemon_v2

Logs:
    tail -f /tmp/approval-daemon-v2.log

State:
    memory/approval-chat-daemon-state.json
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

WORKSPACE     = '/data/.openclaw/workspace'
CREDS_FILE    = os.path.join(WORKSPACE, 'memory/approval-gateway-credentials.md')
STATE_FILE    = os.path.join(WORKSPACE, 'memory/approval-chat-daemon-state.json')
POLL_INTERVAL = 5   # seconds
MODEL         = 'claude-haiku-4-5-20251001'   # fast + cheap for chat replies
MAX_TOKENS    = 512

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
        'api_base':  'https://approvals.clawbackx.com',
        'bot_token': None,
        'agent_id':  'kotubot',
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
# Context loading
# ─────────────────────────────────────────────

def load_context_file(filename: str) -> str:
    path = os.path.join(WORKSPACE, filename)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ''


def load_agent_context() -> Dict[str, str]:
    return {
        'soul':   load_context_file('SOUL.md'),
        'user':   load_context_file('USER.md'),
        'memory': load_context_file('MEMORY.md'),
        'agents': load_context_file('AGENTS.md'),
        'skill':  load_context_file('SKILL.md'),
    }


# ─────────────────────────────────────────────
# Model call (Anthropic API)
# ─────────────────────────────────────────────

def call_model(system_prompt: str, user_message: str) -> Optional[str]:
    """
    Call the agent's Claude model with full context.
    Requires ANTHROPIC_API_KEY in the environment.
    Returns None on failure so the caller can fall back gracefully.
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        log.warning("ANTHROPIC_API_KEY not set — falling back to template response")
        return None

    payload = {
        'model':      MODEL,
        'max_tokens': MAX_TOKENS,
        'system':     system_prompt,
        'messages':   [{'role': 'user', 'content': user_message}],
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req  = Request(
            'https://api.anthropic.com/v1/messages',
            data=data,
            headers={
                'x-api-key':         api_key,
                'anthropic-version': '2023-06-01',
                'content-type':      'application/json',
                'User-Agent':        'ApprovalChatDaemon/2.0',
            },
            method='POST',
        )
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result['content'][0]['text']
    except Exception as e:
        log.warning(f"Model call failed: {e}")
        return None


def build_system_prompt(context: Dict[str, str]) -> str:
    """
    Build the system prompt from the agent's own context files.
    This gives the model the agent's identity, user knowledge, and memory.
    """
    parts = []

    if context.get('soul'):
        parts.append(f"# Who You Are\n{context['soul']}")

    if context.get('user'):
        parts.append(f"# Your User\n{context['user']}")

    if context.get('memory'):
        parts.append(f"# Your Memory\n{context['memory']}")

    if context.get('agents'):
        parts.append(f"# Agent Instructions\n{context['agents']}")

    if context.get('skill'):
        parts.append(f"# Skills\n{context['skill']}")

    parts.append("""# Your Current Task
You are responding to a message sent by your user through the Clawback Approval app.
The user is asking about a pending spending request that you submitted for their approval.

Guidelines:
- Answer as yourself using your full identity and context above
- Be concise (under 120 words) and direct
- Reference specific details from the request (vendor, amount, reason) where relevant
- Do NOT tell them to approve or deny — they do that in the app
- If they ask something you don't know, say so honestly""")

    return "\n\n".join(parts)


def build_user_prompt(approval_request: Dict, user_msg: str) -> str:
    vendor   = approval_request.get('vendor', 'Unknown vendor')
    amount   = approval_request.get('spending_amount_cents', 0) / 100
    reason   = approval_request.get('reason', '(no reason provided)')
    category = approval_request.get('category', '')

    lines = [
        "The user sent this message about a pending approval request:",
        f'"{user_msg}"',
        "",
        "Request details:",
        f"  Vendor:   {vendor}",
        f"  Amount:   ${amount:.2f}",
    ]
    if category:
        lines.append(f"  Category: {category}")
    lines.append(f"  Reason:   {reason}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Response generation
# ─────────────────────────────────────────────

def generate_response(
    context: Dict[str, str],
    approval_request: Dict,
    new_message: Dict,
) -> str:
    """
    Generate a response using the agent's own model + full context.
    Falls back to a structured template if the model is unavailable.
    """
    user_msg = new_message.get('message', '')

    # ── Primary: use the agent's model ───────────────────────────────
    system_prompt = build_system_prompt(context)
    user_prompt   = build_user_prompt(approval_request, user_msg)
    response      = call_model(system_prompt, user_prompt)

    if response:
        return response

    # ── Fallback: structured template (no model available) ───────────
    vendor   = approval_request.get('vendor', 'Unknown vendor')
    amount   = approval_request.get('spending_amount_cents', 0) / 100
    reason   = approval_request.get('reason', '(no reason provided)')
    category = approval_request.get('category', '')
    msg_low  = user_msg.lower().strip()

    if any(w in msg_low for w in ['why', 'reason', 'purpose', 'what for', 'explain']):
        return (
            f"The reason I submitted this ${amount:.2f} {vendor} request:\n\n"
            f"{reason}\n\nLet me know if you need anything else before deciding."
        )

    if any(w in msg_low for w in ['more info', 'details', 'tell me more',
                                   'elaborate', 'give me more', 'what is', "what's"]):
        lines = [f"Full details:\n", f"• Vendor:   {vendor}", f"• Amount:   ${amount:.2f}"]
        if category:
            lines.append(f"• Category: {category}")
        lines.append(f"• Reason:   {reason}")
        return "\n".join(lines)

    if any(w in msg_low for w in ['alternative', 'other option', 'different', 'instead']):
        return (
            f"I can explore alternatives to {vendor} if you prefer. "
            f"Deny this request and let me know your constraints."
        )

    return (
        f"You asked: \"{user_msg}\"\n\n"
        f"{vendor} · ${amount:.2f} — {reason}\n\n"
        f"Happy to answer any follow-up questions."
    )


# ─────────────────────────────────────────────
# Core poll loop
# ─────────────────────────────────────────────

def poll_once(creds: Dict, state: Dict) -> Dict:
    api_base = creds['api_base']
    agent_id = creds['agent_id']
    headers  = _base_headers(creds['bot_token'])

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

    context = load_agent_context()

    for req in pending:
        request_id = req['id']
        last_check = state['last_checks'].get(request_id)

        messages_data = api_get(f"{api_base}/api/chat-messages/{request_id}", headers)
        if not messages_data:
            continue

        messages = messages_data.get('messages', [])

        new_messages = [
            msg for msg in messages
            if msg.get('sender') != 'agent'
            and (last_check is None or msg.get('created_at', '') > last_check)
        ]

        if not new_messages:
            continue

        log.info(f"[{request_id}] {len(new_messages)} new message(s) from user")

        for msg in new_messages:
            response_text = generate_response(context, req, msg)

            result = api_post(
                f"{api_base}/api/chat-messages",
                headers,
                {
                    'approval_request_id': request_id,
                    'sender':              'agent',
                    'message':             response_text,
                }
            )

            if result:
                log.info(f"[{request_id}] Response posted")
            else:
                log.warning(f"[{request_id}] Failed to post response")

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

    has_key = bool(os.environ.get('ANTHROPIC_API_KEY'))
    log.info(f"API: {creds['api_base']} | Agent: {creds['agent_id']}")
    log.info(f"Model: {'claude (active)' if has_key else 'template fallback (no ANTHROPIC_API_KEY)'}")
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
