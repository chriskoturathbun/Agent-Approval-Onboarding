#!/usr/bin/env python3
"""
Universal Multi-Agent Approval Chat Daemon
-------------------------------------------
Supports multiple LLM providers (Anthropic, OpenAI, local models, etc.)
Reads model configuration from OpenClaw config or command-line args

Usage:
    python3 approval_chat_daemon_universal.py \\
        --workspace /path/to/workspace \\
        --credentials /path/to/credentials.md \\
        --model anthropic/claude-sonnet-4-5

Supported providers:
    - Anthropic (claude-*) via ANTHROPIC_API_KEY
    - OpenAI (gpt-*, o1-*) via OPENAI_API_KEY
    - OpenAI-compatible APIs (custom baseUrl)

Auto-detects:
    - Reads OpenClaw config from ~/.openclaw/openclaw.json
    - Uses agent's configured model if --model not specified
    - Falls back to environment-based detection
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

# Try to import LLM clients (optional dependencies)
LLM_CLIENTS = {}

try:
    import anthropic
    LLM_CLIENTS['anthropic'] = anthropic
except ImportError:
    pass

try:
    import openai
    LLM_CLIENTS['openai'] = openai
except ImportError:
    pass


class UniversalLLMClient:
    """Universal LLM client supporting multiple providers"""
    
    def __init__(self, model: str, openclaw_config: Optional[Dict] = None):
        self.model = model
        self.provider = self._detect_provider(model)
        self.client = None
        
        if self.provider == 'anthropic':
            self._init_anthropic()
        elif self.provider == 'openai':
            self._init_openai(openclaw_config)
        else:
            raise ValueError(f"Unsupported model: {model}")
    
    def _detect_provider(self, model: str) -> str:
        """Detect provider from model string"""
        model_lower = model.lower()
        
        if 'claude' in model_lower or model_lower.startswith('anthropic/'):
            return 'anthropic'
        elif any(x in model_lower for x in ['gpt-', 'o1-', 'openai/']):
            return 'openai'
        else:
            # Default to openai-compatible API
            return 'openai'
    
    def _init_anthropic(self):
        """Initialize Anthropic client"""
        if 'anthropic' not in LLM_CLIENTS:
            raise ImportError("anthropic package not installed (pip install anthropic)")
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = LLM_CLIENTS['anthropic'].Anthropic(api_key=api_key)
        # Clean model name (remove anthropic/ prefix if present)
        if self.model.startswith('anthropic/'):
            self.model = self.model.replace('anthropic/', '')
    
    def _init_openai(self, openclaw_config: Optional[Dict] = None):
        """Initialize OpenAI or OpenAI-compatible client"""
        if 'openai' not in LLM_CLIENTS:
            raise ImportError("openai package not installed (pip install openai)")
        
        api_key = os.environ.get('OPENAI_API_KEY')
        base_url = None
        
        # Check if this is a custom provider from OpenClaw config
        if openclaw_config and 'models' in openclaw_config:
            providers = openclaw_config.get('models', {}).get('providers', {})
            for provider_name, provider_config in providers.items():
                if provider_config.get('api') == 'openai-completions':
                    base_url = provider_config.get('baseUrl')
                    api_key_var = provider_config.get('apiKey', '')
                    if api_key_var.startswith('${') and api_key_var.endswith('}'):
                        env_var = api_key_var[2:-1]
                        api_key = os.environ.get(env_var) or api_key
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY (or custom API key) environment variable not set")
        
        if base_url:
            self.client = LLM_CLIENTS['openai'].OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = LLM_CLIENTS['openai'].OpenAI(api_key=api_key)
        
        # Clean model name
        if self.model.startswith('openai/'):
            self.model = self.model.replace('openai/', '')
    
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response using configured provider"""
        if self.provider == 'anthropic':
            return self._generate_anthropic(prompt, max_tokens)
        elif self.provider == 'openai':
            return self._generate_openai(prompt, max_tokens)
        else:
            raise ValueError(f"Provider {self.provider} not supported")
    
    def _generate_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Generate using Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def _generate_openai(self, prompt: str, max_tokens: int) -> str:
        """Generate using OpenAI or compatible API"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


class ApprovalChatDaemon:
    """Universal multi-agent approval chat daemon"""
    
    def __init__(self, workspace: str, api_base: str, bot_token: str, agent_id: str, 
                 model: str, openclaw_config: Optional[Dict] = None, poll_interval: int = 5):
        self.workspace = workspace
        self.api_base = api_base.rstrip('/')
        self.bot_token = bot_token
        self.agent_id = agent_id
        self.model = model
        self.poll_interval = poll_interval
        
        self.headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        self.state_file = os.path.join(workspace, 'memory/approval-chat-daemon-state.json')
        self.state = self._load_state()
        
        # Initialize LLM client
        try:
            self.llm = UniversalLLMClient(model, openclaw_config)
            provider_name = self.llm.provider.upper()
        except Exception as e:
            print(f"ERROR: Failed to initialize LLM client: {e}", file=sys.stderr)
            raise
        
        print(f"🦞 Universal Multi-Agent Approval Chat Daemon", file=sys.stderr)
        print(f"   Agent: {agent_id}", file=sys.stderr)
        print(f"   Workspace: {workspace}", file=sys.stderr)
        print(f"   API: {api_base}", file=sys.stderr)
        print(f"   Model: {self.llm.model} ({provider_name})", file=sys.stderr)
        print(f"   Polling: every {poll_interval}s", file=sys.stderr)
        print(f"", file=sys.stderr)
    
    def _load_state(self) -> Dict:
        """Load last check timestamps"""
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
        """Get all pending approval requests"""
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
        messages = [m for m in messages if m.get('sender') == 'user']
        
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
        
        for filename in ['SOUL.md', 'USER.md', 'MEMORY.md', 'AGENTS.md']:
            path = os.path.join(self.workspace, filename)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        context[filename] = f.read()
                except IOError:
                    context[filename] = ""
            else:
                context[filename] = ""
        
        return context
    
    def generate_response(self, approval: Dict, user_message: str) -> str:
        """Generate AI response using configured LLM"""
        context = self.load_context()
        
        vendor = approval.get('vendor', 'Unknown')
        amount = approval.get('spending_amount_cents', 0) / 100
        category = approval.get('category', 'unknown')
        reason = approval.get('reason', '')
        deal_slug = approval.get('deal_slug', '')
        
        prompt = f"""You are responding to a user question about a spending approval request.

AGENT IDENTITY:
{context.get('SOUL.md', '')}

USER CONTEXT:
{context.get('USER.md', '')}

RECENT MEMORY:
{context.get('MEMORY.md', '')[:2000]}

APPROVAL REQUEST:
- Vendor: {vendor}
- Amount: ${amount:.2f}
- Category: {category}
- Reason: {reason}
- Deal: {deal_slug}

USER QUESTION:
{user_message}

INSTRUCTIONS:
- Respond naturally as this agent based on the identity and context
- Be helpful and concise
- Provide clear options if the user is asking what to do
- Stay in character

Your response:"""
        
        try:
            return self.llm.generate(prompt, max_tokens=1024)
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}", file=sys.stderr)
            return f"I received your question about the {vendor} approval (${amount:.2f}). Having trouble generating a response right now. Approve, deny, or wait?"
    
    def process_approval(self, approval: Dict) -> int:
        """Process new messages for an approval"""
        request_id = approval['id']
        last_check = self.state['last_checks'].get(request_id, '2000-01-01T00:00:00Z')
        
        messages = self.get_messages(request_id, since=last_check)
        if not messages:
            return 0
        
        response_count = 0
        
        for msg in messages:
            user_message = msg.get('message', '').strip()
            if not user_message:
                continue
            
            created_at = msg.get('created_at', '')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📩 {user_message[:50]}...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Generating response...")
            
            response = self.generate_response(approval, user_message)
            
            if self.send_message(request_id, response):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sent")
                response_count += 1
                self.state['last_checks'][request_id] = created_at
                self._save_state()
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed")
        
        return response_count
    
    def poll_once(self) -> Dict:
        """Run one polling cycle"""
        now = datetime.now(timezone.utc).isoformat()
        
        results = {
            'timestamp': now,
            'pending_approvals': 0,
            'responses_sent': 0
        }
        
        pending = self.get_pending_approvals()
        results['pending_approvals'] = len(pending)
        
        if not pending:
            self.state['last_poll'] = now
            self._save_state()
            return results
        
        for approval in pending:
            if approval.get('id'):
                results['responses_sent'] += self.process_approval(approval)
        
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
                          f"Sent {results['responses_sent']} response(s)", file=sys.stderr)
                
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            print("\n✋ Stopping daemon...", file=sys.stderr)
            self._save_state()


def load_openclaw_config() -> Optional[Dict]:
    """Load OpenClaw configuration"""
    config_path = os.path.expanduser('~/.openclaw/openclaw.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def get_agent_model(openclaw_config: Optional[Dict], agent_id: str) -> Optional[str]:
    """Get configured model for agent from OpenClaw config"""
    if not openclaw_config:
        return None
    
    agents = openclaw_config.get('agents', {})
    
    # Check specific agent configuration
    agent_list = agents.get('list', [])
    for agent in agent_list:
        if agent.get('id') == agent_id or agent.get('name') == agent_id:
            return agent.get('model')
    
    # Fall back to default agent model
    defaults = agents.get('defaults', {})
    model_config = defaults.get('model', {})
    return model_config.get('primary')


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


def resolve_default_credentials_file(workspace: str) -> str:
    """Resolve default credentials file path with backwards compatibility."""
    preferred = os.path.join(workspace, 'memory/approval-gateway-credentials.md')
    legacy = os.path.join(workspace, 'memory/approval-gateway-credentials-simple.md')
    if os.path.exists(preferred):
        return preferred
    if os.path.exists(legacy):
        return legacy
    return preferred


def main():
    parser = argparse.ArgumentParser(
        description='Universal multi-agent approval chat daemon'
    )
    
    parser.add_argument('--workspace', default='/data/.openclaw/workspace')
    parser.add_argument('--credentials')
    parser.add_argument('--api-base')
    parser.add_argument('--bot-token')
    parser.add_argument('--agent-id')
    parser.add_argument('--model', help='Model to use (e.g., anthropic/claude-sonnet-4-5, gpt-4)')
    parser.add_argument('--poll-interval', type=int, default=5)
    parser.add_argument('--once', action='store_true')
    
    args = parser.parse_args()
    
    # Load OpenClaw config
    openclaw_config = load_openclaw_config()
    
    # Load credentials
    creds_file = args.credentials or resolve_default_credentials_file(args.workspace)
    try:
        creds = load_credentials(creds_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    
    # Get configuration
    api_base = args.api_base or creds['api_base']
    bot_token = args.bot_token or creds['bot_token']
    agent_id = args.agent_id or creds['agent_id']
    
    # Determine model
    model = args.model
    if not model:
        # Try to get from OpenClaw config
        model = get_agent_model(openclaw_config, agent_id)
    if not model:
        # Default fallback
        if os.environ.get('ANTHROPIC_API_KEY'):
            model = 'claude-sonnet-4-5'
        elif os.environ.get('OPENAI_API_KEY'):
            model = 'gpt-4'
        else:
            print("ERROR: No model specified and could not auto-detect", file=sys.stderr)
            print("Use --model or set API key environment variable", file=sys.stderr)
            return 1
    
    # Create daemon
    try:
        daemon = ApprovalChatDaemon(
            workspace=args.workspace,
            api_base=api_base,
            bot_token=bot_token,
            agent_id=agent_id,
            model=model,
            openclaw_config=openclaw_config,
            poll_interval=args.poll_interval
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    
    # Run
    if args.once:
        results = daemon.poll_once()
        print(json.dumps(results, indent=2))
        return 0
    else:
        daemon.run_continuous()
        return 0


if __name__ == '__main__':
    sys.exit(main())
