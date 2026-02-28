#!/bin/bash
# Check status of multi-agent approval daemons

DAEMON_PATTERN="${DAEMON_PATTERN:-approval_chat_daemon_.*\\.py}"

extract_workspace() {
    echo "$1" | awk '{for (i = 1; i <= NF; i++) if ($i == "--workspace") {print $(i+1); exit}}'
}

echo "📊 Multi-Agent Approval Daemon Status"
echo "========================================"
echo ""

# Check if any daemons are running
PIDS=$(pgrep -f "$DAEMON_PATTERN" || true)

if [ -z "$PIDS" ]; then
    echo "❌ No approval daemons running"
    echo ""
    echo "Start with: bash start_approval_daemons.sh"
    exit 1
fi

echo "✅ Running daemon(s):"
echo ""

# Show process details
ps aux | grep -E "$DAEMON_PATTERN" | grep -v grep | while read -r line; do
    PID=$(echo "$line" | awk '{print $2}')
    
    # Extract workspace from command line
    WORKSPACE=$(extract_workspace "$line")
    [ -z "$WORKSPACE" ] && WORKSPACE="unknown"
    
    # Find agent name from workspace
    if [[ "$WORKSPACE" == *"/workspace" ]]; then
        AGENT_NAME=$(basename "$(dirname "$WORKSPACE")")
    else
        AGENT_NAME=$(basename "$WORKSPACE")
    fi
    
    # Check log file
    LOG_FILE="/tmp/approval-daemon-$AGENT_NAME.log"
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
        LAST_LINE=$(tail -n 1 "$LOG_FILE" 2>/dev/null || echo "")
    else
        LOG_SIZE="N/A"
        LAST_LINE=""
    fi
    
    echo "  Agent: $AGENT_NAME"
    echo "  PID: $PID"
    echo "  Workspace: $WORKSPACE"
    echo "  Log: $LOG_FILE ($LOG_SIZE)"
    if [ -n "$LAST_LINE" ]; then
        echo "  Last: $LAST_LINE"
    fi
    echo ""
done

echo "========================================"
echo ""
echo "View logs:"
for PID in $PIDS; do
    WORKSPACE=$(extract_workspace "$(ps -p "$PID" -o args=)")
    [ -z "$WORKSPACE" ] && WORKSPACE="unknown"
    if [[ "$WORKSPACE" == *"/workspace" ]]; then
        AGENT_NAME=$(basename "$(dirname "$WORKSPACE")")
    else
        AGENT_NAME=$(basename "$WORKSPACE")
    fi
    echo "  tail -f /tmp/approval-daemon-$AGENT_NAME.log"
done
echo ""
echo "Stop all:"
echo "  bash stop_approval_daemons.sh"
echo ""
