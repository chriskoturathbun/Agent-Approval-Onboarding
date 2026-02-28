#!/usr/bin/env python3
"""
Universal Multi-Agent Approval Chat Daemon v2
----------------------------------------------
Production-hardened version with security and reliability improvements:
- Proper logging with levels
- User-Agent identification  
- Retry logic with exponential backoff
- Graceful error handling
- Passes security verification checks

Supports multiple LLM providers (Anthropic, OpenAI, local models, etc.)
Reads model configuration from OpenClaw config or command-line args

Usage:
    python3 approval_chat_daemon_universal_v2.py \\
        --workspace /path/to/workspace \\
        --model anthropic/claude-sonnet-4-5

Auto-detection:
    python3 approval_chat_daemon_universal_v2.py --workspace /path/to/workspace
    # Reads model from ~/.openclaw/openclaw.json automatically
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# LLM client imports (optional)
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


# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger('approval-daemon-universal')


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

USER_AGENT = 'ApprovalChatDaemon-Universal/2.0'
API_TIMEOUT = 10  # seconds
RETRY_DELAYS = [0, 1, 2]  # Exponential backoff delays (seconds)


# ─────────────────────────────────────────────
# Universal LLM Client
# ─────────────────────────────────────────────

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
        
        log.info(f"Initialized {self.provider.upper()} provider for model: {self.model}")
    
    def _detect_provider(self, model: str) -> str:
        """Detect provider from model string"""
        model_lower = model.lower()
        
        if 'claude' in model_lower or model_lower.startswith('anthropic/'):
            return 'anthropic'
        elif any(x in model_lower for x in ['gpt-', 'o1-', 'openai/']):
            return 'openai'
        else:
            return 'openai'  # Default to OpenAI-compatible
    
    def _init_anthropic(self):
        """Initialize Anthropic client"""
        if 'anthropic' not in LLM_CLIENTS:
            raise ImportError("anthropic package not installed (pip install anthropic)")
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = LLM_CLIENTS['anthropic'].Anthropic(api_key=api_key)
        
        # Clean model name
        if self.model.startswith('anthropic/'):
            self.model = self.model.replace('anthropic/', '')
    
    def _init_openai(self, openclaw_config: Optional[Dict] = None):
        """Initialize OpenAI or OpenAI-compatible client"""
        if 'openai' not in LLM_CLIENTS:
            raise ImportError("openai package not installed (pip install openai)")
        
        api_key = os.environ.get('OPENAI_API_KEY')
        base_url = None
        
        # Check for custom provider config
        if openclaw_config and 'models' in openclaw_config:
            providers = openclaw_config.get('models', {}).get('providers', {})
            for provider_config in providers.values():
                if provider_config.get('api') == 'openai-completions':
                    base_url = provider_config.get('baseUrl')
                    api_key_var = provider_config.get('apiKey', '')
                    if api_key_var.startswith('${') and api_key_var.endswith('}'):
                        env_var = api_key_var[2:-1]
                        api_key = os.environ.get(env_var) or api_key
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY (or custom API key) not set")
        
        if base_url:
            self.client = LLM_CLIENTS['openai'].OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = LLM_CLIENTS['openai'].OpenAI(api_key=api_key)
        
        # Clean model name
        if self.model.startswith('openai/'):
            self.model = self.model.replace('openai/', '')
    
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response with retry logic"""
        for attempt, delay in enumerate(RETRY_DELAYS, start=1):
            if delay > 0:
                time.sleep(delay)
            
            try:
                if self.provider == 'anthropic':
                    return self._generate_anthropic(prompt, max_tokens)
                elif self.provider == 'openai':
                    return self._generate_openai(prompt, max_tokens)
                else:
                    raise ValueError(f"Provider {self.provider} not supported")
            
            except Exception as e:
                log.warning(f"LLM generation attempt {attempt}/{len(RETRY_DELAYS)} failed: {e}")
                if attempt == len(RETRY_DELAYS):
                    raise
        
        raise Exception("All LLM generation attempts failed")
    
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


# ─────────────────────────────────────────────
# Approval Chat Daemon
# ─────────────────────────────────────────────

class ApprovalChatDaemon:
    """Universal multi-agent approval chat daemon with production hardening"""
    
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
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT
        }
        
        self.state_file = os.path.join(workspace, 'memory/approval-chat-daemon-state.json')
        self.state = self._load_state()
        
        # Initialize LLM client
        try:
            self.llm = UniversalLLMClient(model, openclaw_config)
        except Exception as e:
            log.error(f"Failed to initialize LLM client: {e}")
            raise
        
        log.info(f"🦞 Universal Multi-Agent Approval Chat Daemon v2")
        log.info(f"   Agent: {agent_id}")
        log.info(f"   Workspace: {workspace}")
        log.info(f"   API: {api_base}")
        log.info(f"   Model: {self.llm.model} ({self.llm.provider.upper()})")
        log.info(f"   Polling: every {poll_interval}s")
        log.info(f"")
    
    def _load_state(self) -> Dict:
        """Load last check timestamps"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"Failed to load state file: {e}")
        return {'last_checks': {}, 'last_poll': None}
    
    def _save_state(self):
        """Save state to disk"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError as e:
            log.error(f"Failed to save state: {e}")
    
    def _api_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API call with retry logic"""
        url = f'{self.api_base}{endpoint}'
        
        for attempt, delay in enumerate(RETRY_DELAYS, start=1):
            if delay > 0:
                time.sleep(delay)
            
            try:
                if data:
                    data_bytes = json.dumps(data).encode('utf-8')
                    req = Request(url, data=data_bytes, headers=self.headers, method=method)
                else:
                    req = Request(url, headers=self.headers, method=method)
                
                with urlopen(req, timeout=API_TIMEOUT) as response:
                    return json.loads(response.read().decode('utf-8'))
            
            except (URLError, HTTPError) as e:
                log.warning(f"API call attempt {attempt}/{len(RETRY_DELAYS)} failed: {method} {endpoint} - {e}")
                if attempt == len(RETRY_DELAYS):
                    log.error(f"All API attempts failed for: {method} {endpoint}")
                    return None
        
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
                except IOError as e:
                    log.warning(f"Failed to load {filename}: {e}")
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
- Respond naturally as this agent based on identity and context
- Be helpful and concise
- Provide clear options if user is asking what to do
- Stay in character

Your response:"""
        
        try:
            return self.llm.generate(prompt, max_tokens=1024)
        except Exception as e:
            log.error(f"LLM generation failed: {e}")
            # Fallback response
            return f"I received your question about the {vendor} approval (${amount:.2f}). Having trouble generating a detailed response right now. Would you like to approve, deny, or wait on this request?"
    
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
            
            log.info(f"[{request_id[:8]}] New message: {user_message[:50]}...")
            log.info(f"[{request_id[:8]}] Generating response...")
            
            response = self.generate_response(approval, user_message)
            
            if self.send_message(request_id, response):
                log.info(f"[{request_id[:8]}] ✅ Response sent")
                response_count += 1
                self.state['last_checks'][request_id] = created_at
                self._save_state()
            else:
                log.error(f"[{request_id[:8]}] ❌ Failed to send response")
        
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
                try:
                    results['responses_sent'] += self.process_approval(approval)
                except Exception as e:
                    log.error(f"Error processing approval {approval.get('id', 'unknown')}: {e}")
        
        self.state['last_poll'] = now
        self._save_state()
        
        return results
    
    def run_continuous(self):
        """Run continuous polling loop with graceful error handling"""
        log.info("🚀 Starting continuous polling (Ctrl+C to stop)")
        log.info("")
        
        try:
            while True:
                try:
                    results = self.poll_once()
                    
                    if results['responses_sent'] > 0:
                        log.info(f"Sent {results['responses_sent']} response(s)")
                
                except Exception as e:
                    log.error(f"Unexpected error in poll cycle: {e}")
                    # Continue running despite errors
                
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            log.info("")
            log.info("✋ Stopping daemon...")
            self._save_state()


# ─────────────────────────────────────────────
# Configuration Helpers
# ─────────────────────────────────────────────

def load_openclaw_config() -> Optional[Dict]:
    """Load OpenClaw configuration"""
    config_path = os.path.expanduser('~/.openclaw/openclaw.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log.warning(f"Failed to load OpenClaw config: {e}")
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


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Universal multi-agent approval chat daemon v2'
    )
    
    parser.add_argument('--workspace', default='/data/.openclaw/workspace')
    parser.add_argument('--credentials')
    parser.add_argument('--api-base')
    parser.add_argument('--bot-token')
    parser.add_argument('--agent-id')
    parser.add_argument('--model', help='Model (e.g., claude-sonnet-4-5, gpt-4)')
    parser.add_argument('--poll-interval', type=int, default=5)
    parser.add_argument('--once', action='store_true', help='Run once and exit (for testing)')
    
    args = parser.parse_args()
    
    # Load OpenClaw config
    openclaw_config = load_openclaw_config()
    
    # Load credentials
    creds_file = args.credentials or resolve_default_credentials_file(args.workspace)
    
    try:
        creds = load_credentials(creds_file)
    except (FileNotFoundError, ValueError) as e:
        log.error(str(e))
        return 1
    
    # Get configuration
    api_base = args.api_base or creds['api_base']
    bot_token = args.bot_token or creds['bot_token']
    agent_id = args.agent_id or creds['agent_id']
    
    # Determine model
    model = args.model
    if not model:
        model = get_agent_model(openclaw_config, agent_id)
    if not model:
        # Default fallback
        if os.environ.get('ANTHROPIC_API_KEY'):
            model = 'claude-sonnet-4-5'
        elif os.environ.get('OPENAI_API_KEY'):
            model = 'gpt-4'
        else:
            log.error("No model specified and could not auto-detect")
            log.error("Use --model or set API key environment variable")
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
        log.error(f"Failed to initialize daemon: {e}")
        return 1
    
    # Run
    if args.once:
        log.info("Running single poll cycle...")
        results = daemon.poll_once()
        print(json.dumps(results, indent=2))
        return 0
    else:
        daemon.run_continuous()
        return 0


if __name__ == '__main__':
    sys.exit(main())
