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

# 3. Check running systems
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

# 4. Check state files
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

# 5. Quick API test
echo "🔐 Testing Approval Gateway API..."
RESPONSE=$(curl -s -H "Authorization: Bearer appr_pygr8ztl3ibkusjum8ixnv25y9w995kk" \
    "http://localhost:3001/api/bot/pending-approvals?agent_id=kotubot" 2>&1)

if echo "$RESPONSE" | jq -e '.approvals' > /dev/null 2>&1; then
    APPROVAL_COUNT=$(echo "$RESPONSE" | jq '.approvals | length')
    echo "  ✅ API responding ($APPROVAL_COUNT pending approvals)"
else
    echo "  ❌ API not responding or credentials invalid"
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
