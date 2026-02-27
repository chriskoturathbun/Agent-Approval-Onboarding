#!/usr/bin/env python3
"""
Kotubot Approval Gateway Client (Bot Token Authentication)
Handles approval requests and polling for agent spending decisions
"""

import json
import os
from typing import Optional, Dict, List
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class ApprovalGatewayClient:
    """Client for interacting with Approval Gateway API using bot token auth"""
    
    def __init__(self, api_base: str, bot_token: str, agent_id: str):
        self.api_base = api_base.rstrip('/')
        self.bot_token = bot_token
        self.agent_id = agent_id
        self.headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
    
    def request_approval(
        self,
        amount_cents: int,
        vendor: str,
        category: str,
        reason: str,
        deal_slug: Optional[str] = None
    ) -> Dict:
        """
        Request approval for a spending decision.
        
        Args:
            amount_cents: Amount in cents (e.g., 720 for $7.20)
            vendor: Vendor name (e.g., "Trade Coffee")
            category: Category (e.g., "food", "transportation")
            reason: Human-readable reason
            deal_slug: Optional deal identifier for ClawbackX
        
        Returns:
            {
                "approved": bool,  # True if auto-approved
                "status": "approved" | "pending",
                "request_id": str,
                "message": str,
                "reason": str
            }
        """
        payload = {
            'agent_id': self.agent_id,
            'agent_name': 'Kotubot',
            'spending_amount_cents': amount_cents,
            'vendor': vendor,
            'category': category,
            'reason': reason
        }
        
        if deal_slug:
            payload['deal_slug'] = deal_slug
        
        # Use bot API endpoint (no user_id needed - token identifies user)
        # BACKEND NOTE: The server should validate that payload['agent_id']
        # matches the agent_id registered for this bot token in the database.
        # This prevents a leaked token from being used to submit requests
        # under a different agent_id. See SECURITY.md for full details.
        url = f'{self.api_base}/api/bot/approval-requests'
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = Request(url, data=data, headers=self.headers, method='POST')
            with urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except (URLError, HTTPError) as e:
            return {
                'approved': False,
                'status': 'error',
                'message': f'Failed to request approval: {str(e)}'
            }
    
    def poll_approvals(self) -> List[Dict]:
        """
        Poll for all approval requests (pending, approved, denied, expired).
        
        Returns:
            List of approval requests with their current status.
            Each item includes:
            {
                "id": str,
                "status": "pending" | "approved" | "denied" | "expired",
                "vendor": str,
                "spending_amount_cents": int,
                "deal_slug": str | None,
                "decisions": [{"approved": bool, "reason": str}]
            }
        """
        # Use bot API endpoint with agent_id query param
        params = f'?agent_id={self.agent_id}'
        url = f'{self.api_base}/api/bot/pending-approvals{params}'
        
        try:
            req = Request(url, headers=self.headers, method='GET')
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('approvals', [])
        except (URLError, HTTPError) as e:
            print(f'⚠️  Failed to poll approvals: {e}')
            return []
    
    def get_approved_requests(self) -> List[Dict]:
        """Get only approved requests (ready to execute).
        
        Note: Results are already filtered by agent_id from poll_approvals,
        but this provides an additional safety filter.
        """
        all_requests = self.poll_approvals()
        # Double-check agent_id matches this client's agent
        return [
            req for req in all_requests 
            if req['status'] == 'approved' and req.get('agent_id') == self.agent_id
        ]
    
    def get_pending_requests(self) -> List[Dict]:
        """Get only pending requests (awaiting user decision).
        
        Note: Results are already filtered by agent_id from poll_approvals,
        but this provides an additional safety filter.
        """
        all_requests = self.poll_approvals()
        # Double-check agent_id matches this client's agent
        return [
            req for req in all_requests 
            if req['status'] == 'pending' and req.get('agent_id') == self.agent_id
        ]


# ============ KOTUBOT INTEGRATION HELPERS ============

def load_credentials() -> Dict[str, str]:
    """Load Approval Gateway credentials from memory file.

    Expects a file at the path below with at least a `token:` line.
    Retrieve your bot token from the Approval Gateway app under Settings → Bot Tokens.
    """
    creds_path = '/data/.openclaw/workspace/memory/approval-gateway-credentials.md'

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credentials file not found: {creds_path}\n"
            "Retrieve your bot token from the Approval Gateway app (Settings → Bot Tokens) "
            "and save it to that file with the line:\n  token: appr_<your_token_here>"
        )

    creds = {
        'api_base': 'http://localhost:3001',
        'bot_token': None,
        'agent_id': 'kotubot',
    }

    with open(creds_path, 'r') as f:
        for line in f:
            if ':' in line and not line.startswith('#'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(' ', '_')
                    value = parts[1].strip()
                    if key == 'token':
                        creds['bot_token'] = value
                    elif key == 'api_base':
                        creds['api_base'] = value
                    elif key == 'agent_id':
                        creds['agent_id'] = value

    if not creds['bot_token']:
        raise ValueError(
            f"No `token:` line found in {creds_path}\n"
            "Add a line like:  token: appr_<your_token_here>"
        )

    return creds


def create_client() -> ApprovalGatewayClient:
    """Create configured Approval Gateway client for Kotubot"""
    creds = load_credentials()
    return ApprovalGatewayClient(
        api_base=creds['api_base'],
        bot_token=creds['bot_token'],
        agent_id=creds['agent_id']
    )


# ============ CLAWBACKX INTEGRATION ============

def request_clawbackx_approval(
    deal_slug: str,
    amount_cents: int,
    vendor: str,
    discount_pct: float,
    cancel_window_hours: float
) -> Dict:
    """
    Request approval for a ClawbackX deal before committing.
    
    Args:
        deal_slug: ClawbackX deal identifier
        amount_cents: Final amount to be charged (in cents)
        vendor: Vendor name
        discount_pct: Discount percentage (e.g., 28 for 28%)
        cancel_window_hours: Hours remaining in cancel window
    
    Returns:
        {
            "approved": bool,
            "status": "approved" | "pending",
            "request_id": str,
            "message": str
        }
    """
    client = create_client()
    
    reason = f"{discount_pct:.0f}% discount (${amount_cents/100:.2f}), {cancel_window_hours:.1f}h cancel window"
    
    return client.request_approval(
        amount_cents=amount_cents,
        vendor=vendor,
        category='food',  # Most ClawbackX deals are food
        reason=reason,
        deal_slug=deal_slug
    )


def process_approved_deals() -> List[Dict]:
    """
    Check for approved ClawbackX deals and return list ready to commit.
    
    Only returns deals that belong to the authenticated bot (validated by agent_id).
    
    Returns:
        List of approved deals with deal_slug, ready for ClawbackX commit.
    """
    client = create_client()
    approved = client.get_approved_requests()
    
    # Filter for deals with deal_slug AND owned by this bot
    clawbackx_deals = [
        req for req in approved 
        if req.get('deal_slug') 
        and req['deal_slug'].startswith('trade-coffee')
        and validate_bot_ownership(client, req)
    ]
    
    return clawbackx_deals


# ============ HEARTBEAT INTEGRATION ============

def validate_bot_ownership(client: ApprovalGatewayClient, approval_request: Dict) -> bool:
    """
    Validate that an approval request belongs to the authenticated bot.
    
    Args:
        client: Authenticated client with bot token
        approval_request: Approval request from API
    
    Returns:
        True if approval belongs to this bot's agent_id, False otherwise
    """
    # Verify agent_id matches
    if approval_request.get('agent_id') != client.agent_id:
        print(f"⚠️  Approval {approval_request['id']} agent mismatch: "
              f"expected {client.agent_id}, got {approval_request.get('agent_id')}")
        return False
    
    return True


def heartbeat_check_approvals() -> Optional[str]:
    """
    Heartbeat routine: Check for approved deals and notify Christopher.
    
    Returns:
        Message to send to Christopher, or None if nothing needs attention.
    """
    client = create_client()
    
    # Check for newly approved deals
    all_approvals = client.poll_approvals()
    
    # Filter: only process approvals that belong to this bot
    approved = [
        req for req in all_approvals 
        if req['status'] == 'approved' and validate_bot_ownership(client, req)
    ]
    pending = [
        req for req in all_approvals 
        if req['status'] == 'pending' and validate_bot_ownership(client, req)
    ]
    
    messages = []
    
    # Notify about approved deals ready to execute
    for req in approved:
        if req.get('deal_slug'):
            decision = req['decisions'][0] if req['decisions'] else {}
            messages.append(
                f"✅ **Approved**: {req['vendor']} ${req['spending_amount_cents']/100:.2f}\n"
                f"   Deal: `{req['deal_slug']}`\n"
                f"   Reason: {decision.get('reason', 'No reason provided')}\n"
                f"   Ready to commit!"
            )
    
    # Notify about pending approvals (if >3, just count)
    if len(pending) > 0:
        if len(pending) <= 3:
            for req in pending:
                messages.append(
                    f"⏳ **Pending**: {req['vendor']} ${req['spending_amount_cents']/100:.2f}\n"
                    f"   Reason: {req['reason']}"
                )
        else:
            messages.append(f"⏳ **{len(pending)} approvals pending** (check mobile app)")
    
    if messages:
        return '\n\n'.join(messages)
    
    return None


# ============ TESTING ============

def test_integration():
    """Test the approval gateway integration"""
    print('🧪 Testing Kotubot Approval Gateway Integration\n')
    
    client = create_client()
    
    # Test 1: Request approval for a coffee deal
    print('1️⃣ Requesting approval for $7.20 coffee deal...')
    result = client.request_approval(
        amount_cents=720,
        vendor='Trade Coffee',
        category='food',
        reason='28% discount on coffee subscription',
        deal_slug='trade-coffee-test-deal'
    )
    print(f'   Result: {json.dumps(result, indent=2)}')
    print()
    
    # Test 2: Poll for approvals
    print('2️⃣ Polling for approvals...')
    approvals = client.poll_approvals()
    print(f'   Found {len(approvals)} approval requests')
    for req in approvals[:3]:  # Show first 3
        print(f'   - {req["vendor"]}: ${req["spending_amount_cents"]/100:.2f} ({req["status"]})')
    print()
    
    # Test 3: Get approved requests
    print('3️⃣ Checking approved requests...')
    approved = client.get_approved_requests()
    print(f'   Found {len(approved)} approved requests')
    for req in approved[:3]:
        decision = req['decisions'][0] if req['decisions'] else {}
        print(f'   ✅ {req["vendor"]}: ${req["spending_amount_cents"]/100:.2f}')
        print(f'      Reason: {decision.get("reason", "N/A")}')
    print()
    
    print('✅ Integration test complete!')


if __name__ == '__main__':
    test_integration()
