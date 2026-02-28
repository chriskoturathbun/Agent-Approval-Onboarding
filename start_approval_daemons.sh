#!/bin/bash
# Multi-Agent Approval Daemon Launcher
# Start approval chat daemons for multiple agents

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/approval_chat_daemon_multi_agent.py"

# Check if daemon script exists
if [ ! -f "$DAEMON_SCRIPT" ]; then
    echo "ERROR: Daemon script not found: $DAEMON_SCRIPT"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Check if anthropic package is installed
if ! python3 -c "import anthropic" 2>/dev/null; then
    echo "ERROR: anthropic package not installed"
    echo "Install with: pip install anthropic"
    exit 1
fi

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set"
    exit 1
fi

# Agent configurations
# Format: "agent_name:workspace_path"
AGENTS=(
    "kotubot:/data/.openclaw/workspace"
    # Add more agents here:
    # "manus:/data/manus/workspace"
    # "finance-bot:/data/finance-bot/workspace"
)

echo "🚀 Starting Multi-Agent Approval Daemons"
echo "========================================"
echo ""

STARTED_COUNT=0

for AGENT_CONFIG in "${AGENTS[@]}"; do
    # Parse agent name and workspace
    AGENT_NAME="${AGENT_CONFIG%%:*}"
    WORKSPACE="${AGENT_CONFIG##*:}"
    
    # Check if workspace exists
    if [ ! -d "$WORKSPACE" ]; then
        echo "⚠️  Skipping $AGENT_NAME: workspace not found: $WORKSPACE"
        continue
    fi
    
    # Check if credentials file exists
    CREDS_FILE="$WORKSPACE/memory/approval-gateway-credentials.md"
    if [ ! -f "$CREDS_FILE" ]; then
        echo "⚠️  Skipping $AGENT_NAME: credentials not found: $CREDS_FILE"
        continue
    fi
    
    # Check if daemon is already running
    if pgrep -f "approval_chat_daemon_multi_agent.py.*$WORKSPACE" > /dev/null; then
        PID=$(pgrep -f "approval_chat_daemon_multi_agent.py.*$WORKSPACE")
        echo "⚠️  $AGENT_NAME daemon already running (PID $PID)"
        continue
    fi
    
    # Start daemon
    LOG_FILE="/tmp/approval-daemon-$AGENT_NAME.log"
    
    echo "Starting $AGENT_NAME daemon..."
    echo "  Workspace: $WORKSPACE"
    echo "  Log: $LOG_FILE"
    
    nohup python3 "$DAEMON_SCRIPT" \
        --workspace "$WORKSPACE" \
        > "$LOG_FILE" 2>&1 &
    
    DAEMON_PID=$!
    echo "  ✅ Started (PID $DAEMON_PID)"
    echo ""
    
    STARTED_COUNT=$((STARTED_COUNT + 1))
    
    # Brief pause between starts
    sleep 1
done

echo "========================================"
echo "✅ Started $STARTED_COUNT daemon(s)"
echo ""
echo "Monitor logs:"
for AGENT_CONFIG in "${AGENTS[@]}"; do
    AGENT_NAME="${AGENT_CONFIG%%:*}"
    echo "  tail -f /tmp/approval-daemon-$AGENT_NAME.log"
done
echo ""
echo "Stop all daemons:"
echo "  pkill -f approval_chat_daemon_multi_agent"
echo ""
