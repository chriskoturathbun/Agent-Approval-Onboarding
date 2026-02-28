#!/bin/bash
# Stop all multi-agent approval daemons

echo "🛑 Stopping Multi-Agent Approval Daemons"
echo "========================================"
echo ""

# Find all running daemons
PIDS=$(pgrep -f "approval_chat_daemon_multi_agent.py" || true)

if [ -z "$PIDS" ]; then
    echo "No approval daemons running"
    exit 0
fi

echo "Found running daemon(s):"
ps aux | grep "approval_chat_daemon_multi_agent.py" | grep -v grep

echo ""
echo "Stopping..."

# Kill all daemons
pkill -f "approval_chat_daemon_multi_agent.py"

sleep 2

# Check if any are still running
REMAINING=$(pgrep -f "approval_chat_daemon_multi_agent.py" || true)

if [ -z "$REMAINING" ]; then
    echo "✅ All daemons stopped"
else
    echo "⚠️  Some daemons still running, force killing..."
    pkill -9 -f "approval_chat_daemon_multi_agent.py"
    sleep 1
    echo "✅ Force stopped"
fi

echo ""
