#!/usr/bin/env python3
"""
Multi-Agent Approval Chat Daemon
---------------------------------
Polls Approval Gateway, detects new messages, and responds using Anthropic API
with workspace-specific context files.

Each agent runs its own daemon instance with isolated state and context.

Usage:
    python3 approval_chat_daemon_multi_agent.py \\
        --workspace /path/to/workspace \\
        --api-base https://approvals.clawbackx.com \\
        --credentials /path/to/workspace/memory/approval-gateway-credentials.md

Credentials file format (memory/approval-gateway-credentials.md):
    token: appr_<bot_token_from_app>
    api_base: https://approvals.clawbackx.com
    agent_id: <agent_id_from_app>

Environment:
    ANTHROPIC_API_KEY - Required for Claude API calls (inherited from OpenClaw)

State:
    {workspace}/memory/approval-chat-daemon-state.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Try to import anthropic
try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed", file=sys.stderr)
    print("Install with: pip install anthropic", file=sys.stderr)
    sys.exit(1)


class ApprovalChatDaemon:
    """Multi-agent approval chat daemon with AI response generation"""
    
    def __init__(self, workspace: str, api_base: str, bot_token: str, agent_id: str, poll_interval: int = 5):
        self.workspace = workspace
        self.api_base = api_base.rstrip('/')
        self.bot_token = bot_token
        self.agent_id = agent_id
        self.poll_interval = poll_interval
        
        self.headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        self.state_file = os.path.join(workspace, 'memory/approval-chat-daemon-state.json')
        self.state = self._load_state()
        
        # Initialize Anthropic client
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        
        print(f"🦞 Multi-Agent Approval Chat Daemon", file=sys.stderr)
        print(f"   Agent: {agent_id}", file=sys.stderr)
        print(f"   Workspace: {workspace}", file=sys.stderr)
        print(f"   API: {api_base}", file=sys.stderr)
        print(f"   Polling: every {poll_interval}s", file=sys.stderr)
        print(f"   Model: claude-sonnet-4-5 (via ANTHROPIC_API_KEY)", file=sys.stderr)
        print(f"", file=sys.stderr)
    
    def _load_state(self) -> Dict:
        """Load last check timestamps per approval request"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'last_checks': {}, 'last_poll': None}
    
    def _save_state(self):
        """Save state to disk"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _api_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API call to approval gateway"""
        url = f'{self.api_base}{endpoint}'
        
        try:
            if data:
                data_bytes = json.dumps(data).encode('utf-8')
                req = Request(url, data=data_bytes, headers=self.headers, method=method)
            else:
                req = Request(url, headers=self.headers, method=method)
            
            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except (URLError, HTTPError) as e:
            print(f"[ERROR] API call failed: {method} {endpoint} - {e}", file=sys.stderr)
            return None
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests for this agent"""
        result = self._api_call('GET', f'/api/bot/pending-approvals?agent_id={self.agent_id}')
        if result:
            return [r for r in result.get('approvals', []) if r.get('status') == 'pending']
        return []
    
    def get_messages(self, request_id: str, since: Optional[str] = None) -> List[Dict]:
        """Get chat messages for an approval request"""
        result = self._api_call('GET', f'/api/chat-messages/{request_id}')
        if not result:
            return []
        
        messages = result.get('messages', [])
        
        # Filter: only user messages
        messages = [m for m in messages if m.get('sender') == 'user']
        
        # Filter: only messages newer than 'since' timestamp
        if since:
            messages = [m for m in messages if m.get('created_at', '') > since]
        
        return messages
    
    def send_message(self, request_id: str, message: str) -> bool:
        """Send a message to the approval chat"""
        payload = {
            'approval_request_id': request_id,
            'sender': 'agent',
            'message': message
        }
        result = self._api_call('POST', '/api/chat-messages', payload)
        return result and result.get('success', False)
    
    def load_context(self) -> Dict[str, str]:
        """Load agent context files from workspace"""
        context = {}
        
        context_files = {
            'soul': 'SOUL.md',
            'user': 'USER.md',
            'memory': 'MEMORY.md',
            'agents': 'AGENTS.md'
        }
        
        for key, filename in context_files.items():
            path = os.path.join(self.workspace, filename)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        context[key] = f.read()
                except IOError:
                    context[key] = ""
            else:
                context[key] = ""
        
        return context
    
    def generate_response(self, approval: Dict, user_message: str) -> str:
        """Generate AI response using Anthropic API with full workspace context"""
        context = self.load_context()
        
        vendor = approval.get('vendor', 'Unknown')
        amount = approval.get('spending_amount_cents', 0) / 100
        category = approval.get('category', 'unknown')
        reason = approval.get('reason', '')
        deal_slug = approval.get('deal_slug', '')
        
        # Build prompt with full context
        prompt = f"""You are responding to a user question about a spending approval request.

AGENT IDENTITY:
{context.get('soul', '')}

USER CONTEXT:
{context.get('user', '')}

RECENT MEMORY:
{context.get('memory', '')[:2000]}

APPROVAL REQUEST DETAILS:
- Vendor: {vendor}
- Amount: ${amount:.2f}
- Category: {category}
- Reason: {reason}
- Deal Slug: {deal_slug}

USER QUESTION:
{user_message}

INSTRUCTIONS:
- Respond naturally as this agent would based on the identity and context above
- Be helpful and concise
- If the user is asking what to do, provide clear options
- If asking about the deal, explain what you know from the approval details
- Stay in character based on SOUL.md and USER.md

Your response:"""
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        
        except Exception as e:
            print(f"[ERROR] Anthropic API call failed: {e}", file=sys.stderr)
            # Fallback response
            return f"I received your question about the {vendor} approval (${amount:.2f}). I'm having trouble generating a detailed response right now. Would you like to approve, deny, or wait on this request?"
    
    def process_approval(self, approval: Dict) -> int:
        """Check and respond to new messages for an approval request"""
        request_id = approval['id']
        last_check = self.state['last_checks'].get(request_id, '2000-01-01T00:00:00Z')
        
        # Get new messages since last check
        messages = self.get_messages(request_id, since=last_check)
        
        if not messages:
            return 0
        
        response_count = 0
        
        for msg in messages:
            user_message = msg.get('message', '').strip()
            if not user_message:
                continue
            
            message_id = msg.get('id', '')
            created_at = msg.get('created_at', '')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📩 New message: {user_message[:50]}...")
            
            # Generate AI response
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Generating response...")
            response = self.generate_response(approval, user_message)
            
            # Send response
            if self.send_message(request_id, response):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Response sent")
                response_count += 1
                
                # Update state IMMEDIATELY after each successful response
                self.state['last_checks'][request_id] = created_at
                self._save_state()
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed to send response")
        
        return response_count
    
    def poll_once(self) -> Dict:
        """Run one polling cycle"""
        now = datetime.now(timezone.utc).isoformat()
        
        results = {
            'timestamp': now,
            'pending_approvals': 0,
            'new_messages': 0,
            'responses_sent': 0
        }
        
        # Get pending approvals
        pending = self.get_pending_approvals()
        results['pending_approvals'] = len(pending)
        
        if not pending:
            self.state['last_poll'] = now
            self._save_state()
            return results
        
        # Process each approval
        for approval in pending:
            request_id = approval.get('id')
            if not request_id:
                continue
            
            responses = self.process_approval(approval)
            results['responses_sent'] += responses
        
        self.state['last_poll'] = now
        self._save_state()
        
        return results
    
    def run_continuous(self):
        """Run continuous polling loop"""
        print(f"🚀 Starting continuous polling (Ctrl+C to stop)\n", file=sys.stderr)
        
        try:
            while True:
                results = self.poll_once()
                
                if results['responses_sent'] > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Processed {results['responses_sent']} message(s)", 
                          file=sys.stderr)
                
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            print("\n\n✋ Stopping daemon...", file=sys.stderr)
            self._save_state()


def load_credentials(creds_file: str) -> Dict[str, str]:
    """Load credentials from file"""
    if not os.path.exists(creds_file):
        raise FileNotFoundError(f"Credentials file not found: {creds_file}")
    
    creds = {
        'api_base': 'https://approvals.clawbackx.com',
        'bot_token': None,
        'agent_id': None
    }
    
    with open(creds_file, 'r') as f:
        for line in f:
            if ':' not in line or line.startswith('#'):
                continue
            
            key, _, value = line.partition(':')
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'token':
                creds['bot_token'] = value
            elif key == 'api_base':
                creds['api_base'] = value
            elif key == 'agent_id':
                creds['agent_id'] = value
    
    if not creds['bot_token']:
        raise ValueError(f"No 'token:' line found in {creds_file}")
    if not creds['agent_id']:
        raise ValueError(f"No 'agent_id:' line found in {creds_file}")
    
    return creds


def main():
    parser = argparse.ArgumentParser(
        description='Multi-agent approval chat daemon with AI response generation'
    )
    
    parser.add_argument(
        '--workspace',
        default='/data/.openclaw/workspace',
        help='Path to agent workspace (contains SOUL.md, USER.md, etc.)'
    )
    
    parser.add_argument(
        '--credentials',
        help='Path to credentials file (default: {workspace}/memory/approval-gateway-credentials.md)'
    )
    
    parser.add_argument(
        '--api-base',
        help='Approval Gateway API base URL (overrides credentials file)'
    )
    
    parser.add_argument(
        '--bot-token',
        help='Bot token (overrides credentials file)'
    )
    
    parser.add_argument(
        '--agent-id',
        help='Agent ID (overrides credentials file)'
    )
    
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=5,
        help='Polling interval in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run one poll cycle and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    # Determine credentials file path
    creds_file = args.credentials or os.path.join(args.workspace, 'memory/approval-gateway-credentials.md')
    
    # Load credentials from file
    try:
        creds = load_credentials(creds_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"\nCreate credentials file at: {creds_file}", file=sys.stderr)
        print(f"Format:", file=sys.stderr)
        print(f"  token: appr_<your_token>", file=sys.stderr)
        print(f"  api_base: https://approvals.clawbackx.com", file=sys.stderr)
        print(f"  agent_id: <your_agent_id>", file=sys.stderr)
        return 1
    
    # Command-line args override credentials file
    api_base = args.api_base or creds['api_base']
    bot_token = args.bot_token or creds['bot_token']
    agent_id = args.agent_id or creds['agent_id']
    
    # Check ANTHROPIC_API_KEY
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("This daemon uses the same API key as OpenClaw", file=sys.stderr)
        return 1
    
    # Create daemon
    try:
        daemon = ApprovalChatDaemon(
            workspace=args.workspace,
            api_base=api_base,
            bot_token=bot_token,
            agent_id=agent_id,
            poll_interval=args.poll_interval
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize daemon: {e}", file=sys.stderr)
        return 1
    
    # Run
    if args.once:
        print("Running single poll cycle...", file=sys.stderr)
        results = daemon.poll_once()
        print(json.dumps(results, indent=2))
        return 0
    else:
        daemon.run_continuous()
        return 0


if __name__ == '__main__':
    sys.exit(main())
