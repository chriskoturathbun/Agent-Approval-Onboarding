#!/bin/bash
# Stop all multi-agent approval daemons

DAEMON_PATTERN="${DAEMON_PATTERN:-approval_chat_daemon_.*\\.py}"

echo "🛑 Stopping Multi-Agent Approval Daemons"
echo "========================================"
echo ""

# Find all running daemons
PIDS=$(pgrep -f "$DAEMON_PATTERN" || true)

if [ -z "$PIDS" ]; then
    echo "No approval daemons running"
    exit 0
fi

echo "Found running daemon(s):"
ps aux | grep -E "$DAEMON_PATTERN" | grep -v grep

echo ""
echo "Stopping..."

# Kill all daemons
pkill -f "$DAEMON_PATTERN"

sleep 2

# Check if any are still running
REMAINING=$(pgrep -f "$DAEMON_PATTERN" || true)

if [ -z "$REMAINING" ]; then
    echo "✅ All daemons stopped"
else
    echo "⚠️  Some daemons still running, force killing..."
    pkill -9 -f "$DAEMON_PATTERN"
    sleep 1
    echo "✅ Force stopped"
fi

echo ""
