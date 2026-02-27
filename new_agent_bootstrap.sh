#!/bin/bash
# New Agent Bootstrap - Quick health check and context verification
# Run this when a new agent instance starts up

echo "🦞 New Agent Bootstrap - Kotubot"
echo "================================="
echo ""

# 1. Check core files exist
echo "📋 Checking core context files..."
REQUIRED_FILES=(
    "/data/.openclaw/workspace/SOUL.md"
    "/data/.openclaw/workspace/USER.md"
    "/data/.openclaw/workspace/MEMORY.md"
    "/data/.openclaw/workspace/AGENTS.md"
    "/data/.openclaw/workspace/TOOLS.md"
    "/data/.openclaw/workspace/HEARTBEAT.md"
    "/data/.openclaw/workspace/AGENT_ONBOARDING.md"
)

MISSING_FILES=0
for FILE in "${REQUIRED_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "  ✅ $(basename $FILE)"
    else
        echo "  ❌ $(basename $FILE) - MISSING"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: $MISSING_FILES core file(s) missing!"
    echo "   This agent may not function correctly."
fi

echo ""

# 2. Check today's memory log
TODAY=$(date +%Y-%m-%d)
TODAY_LOG="/data/.openclaw/workspace/memory/${TODAY}.md"

echo "📅 Checking today's memory log..."
if [ -f "$TODAY_LOG" ]; then
    echo "  ✅ memory/${TODAY}.md exists"
    LINE_COUNT=$(wc -l < "$TODAY_LOG")
    echo "     ($LINE_COUNT lines)"
else
    echo "  ℹ️  memory/${TODAY}.md doesn't exist yet"
    echo "     (Normal if it's a new day - will be created when needed)"
fi

echo ""

# 3. Install daemon if not present
echo "🤖 Checking approval daemon installation..."
WORKSPACE="/data/.openclaw/workspace"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DAEMON="$WORKSPACE/approval_chat_daemon_v2.py"
REPO_DAEMON="$REPO_DIR/approval_chat_daemon_v2.py"

if [ -f "$WORKSPACE_DAEMON" ]; then
    echo "  ✅ Daemon already installed"
elif [ -f "$REPO_DAEMON" ]; then
    cp "$REPO_DAEMON" "$WORKSPACE_DAEMON"
    echo "  ✅ Daemon copied from repo to workspace"
else
    echo "  ❌ Daemon not found in repo or workspace"
    echo "     Expected: $REPO_DAEMON"
fi

echo ""

# 4. Check running systems
echo "🚀 Checking active systems..."

# Approval daemon
if pgrep -f approval_chat_daemon_v2 > /dev/null; then
    PID=$(pgrep -f approval_chat_daemon_v2)
    echo "  ✅ Approval daemon running (PID $PID)"
else
    echo "  ❌ Approval daemon NOT running"
    echo "     Start with: cd /data/.openclaw/workspace && nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &"
fi

# Backend health
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "  ✅ Backend healthy (http://localhost:3001)"
else
    echo "  ❌ Backend not responding"
    echo "     Check: curl http://localhost:3001/health"
fi

echo ""

# 5. Check state files
echo "💾 Checking state files..."
STATE_FILES=(
    "/data/.openclaw/workspace/memory/approval-chat-daemon-state.json"
    "/data/.openclaw/workspace/memory/clawbackx-state.json"
    "/data/.openclaw/workspace/memory/approval-gateway-state.json"
)

for STATE_FILE in "${STATE_FILES[@]}"; do
    if [ -f "$STATE_FILE" ]; then
        echo "  ✅ $(basename $STATE_FILE)"
    else
        echo "  ⚠️  $(basename $STATE_FILE) - doesn't exist (will be created on first use)"
    fi
done

echo ""

# 6. Activation check — credentials & API test
echo "🔐 Checking approval layer activation..."
CREDS_FILE="/data/.openclaw/workspace/memory/approval-gateway-credentials.md"

if [ ! -f "$CREDS_FILE" ]; then
    echo ""
    echo "  🔴 APPROVAL LAYER IS INACTIVE"
    echo "  ════════════════════════════════════════════"
    echo "  The credentials file is missing:"
    echo "  $CREDS_FILE"
    echo ""
    echo "  To activate, tell the user:"
    echo ""
    echo "  1. Download the Clawback Approval app (iOS/Android)"
    echo "  2. Open app → Settings → Bot Tokens"
    echo "  3. Copy their Bot Token and Agent ID"
    echo "  4. Provide both to this agent"
    echo ""
    echo "  Then create the credentials file:"
    echo "  token: appr_<bot_token_from_app>"
    echo "  api_base: http://localhost:3001"
    echo "  agent_id: <agent_id_from_app>"
    echo ""
    echo "  ⚠️  No purchases can be processed until this is done."
    echo "  ════════════════════════════════════════════"
    echo ""
    echo "================================="
    echo "⚠️  Bootstrap complete — approval layer INACTIVE"
    exit 1
fi

# Validate credentials file has required fields
BOT_TOKEN=$(grep '^token:' "$CREDS_FILE" | awk '{print $2}')
AGENT_ID=$(grep '^agent_id:' "$CREDS_FILE" | awk '{print $2}')

if [ -z "$BOT_TOKEN" ]; then
    echo "  ❌ Credentials file found but missing 'token:' line"
    echo "     Ask the user to re-copy their bot token from the app (Settings → Bot Tokens)"
    exit 1
fi

if [ -z "$AGENT_ID" ]; then
    echo "  ❌ Credentials file found but missing 'agent_id:' line"
    echo "     Ask the user to check their agent ID in the app (Settings → Bot Tokens)"
    exit 1
fi

echo "  ✅ Bot token present"
echo "  ✅ Agent ID: $AGENT_ID"

# Live API test
RESPONSE=$(curl -s -H "Authorization: Bearer $BOT_TOKEN" \
    "http://localhost:3001/api/bot/pending-approvals?agent_id=${AGENT_ID}" 2>&1)

if echo "$RESPONSE" | jq -e '.approvals' > /dev/null 2>&1; then
    APPROVAL_COUNT=$(echo "$RESPONSE" | jq '.approvals | length')
    echo "  ✅ Approval layer ACTIVE ($APPROVAL_COUNT pending approvals)"
else
    echo "  ❌ API not responding or credentials invalid"
    echo "     Ask the user to re-copy their bot token and agent ID from the app"
fi

echo ""
echo "================================="
echo "✅ Bootstrap check complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Read AGENT_ONBOARDING.md for full context"
echo "   2. Read SOUL.md, USER.md, MEMORY.md, AGENTS.md"
echo "   3. Check memory/${TODAY}.md for today's events"
echo "   4. Report status to Christopher"
echo ""
