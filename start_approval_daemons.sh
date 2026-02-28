#!/bin/bash
# Multi-Agent Approval Daemon Launcher
# Start approval chat daemons for multiple agents (defaults to universal v2)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_SCRIPT="${DAEMON_SCRIPT:-$SCRIPT_DIR/approval_chat_daemon_universal_v2.py}"
DAEMON_BASENAME="$(basename "$DAEMON_SCRIPT")"

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

# Agent configurations
# Format: "agent_name:workspace_path"
AGENTS=(
    "kotubot:/data/.openclaw/workspace"
    # Add more agents here:
    # "manus:/data/manus/workspace"
    # "finance-bot:/data/finance-bot/workspace"
)

echo "🚀 Starting Approval Daemons"
echo "========================================"
echo "Daemon: $DAEMON_BASENAME"
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
        CREDS_FILE="$WORKSPACE/memory/approval-gateway-credentials-simple.md"
    fi
    if [ ! -f "$CREDS_FILE" ]; then
        echo "⚠️  Skipping $AGENT_NAME: credentials not found in memory/"
        continue
    fi
    
    # Check if daemon is already running
    if pgrep -f "$DAEMON_BASENAME.*$WORKSPACE" > /dev/null; then
        PID=$(pgrep -f "$DAEMON_BASENAME.*$WORKSPACE")
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
        --credentials "$CREDS_FILE" \
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
echo "  DAEMON_PATTERN=$DAEMON_BASENAME bash stop_approval_daemons.sh"
echo ""
