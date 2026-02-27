#!/bin/bash
# verify_daemon.sh
# ─────────────────────────────────────────────────────────────
# Runs a 4-step trust chain on approval_chat_daemon_v2.py before
# the agent is allowed to copy or execute it.
#
# Usage:
#   bash verify_daemon.sh                    # verifies in same directory
#   bash verify_daemon.sh /path/to/daemon.py # verifies a specific file
#
# Exit codes:
#   0 = all checks passed — safe to copy and run
#   1 = one or more checks failed — do NOT run the daemon
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_FILE="${1:-$SCRIPT_DIR/approval_chat_daemon_v2.py}"
CHECKSUM_FILE="$SCRIPT_DIR/approval_chat_daemon_v2.sha256"

PASS=0
FAIL=0

pass() { echo "  ✅ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }
warn() { echo "  ⚠️  $1"; }

echo ""
echo "🔐 Daemon Trust Verification"
echo "════════════════════════════════════════════"
echo "  File: $DAEMON_FILE"
echo ""

# ─────────────────────────────────────────────
# LAYER 1 — File exists and is readable
# ─────────────────────────────────────────────
echo "1️⃣  Source check"

if [ ! -f "$DAEMON_FILE" ]; then
    fail "Daemon file not found: $DAEMON_FILE"
    echo ""
    echo "════════════════════════════════════════════"
    echo "🚫 VERIFICATION FAILED — do not run this daemon"
    exit 1
fi

pass "File exists"

# Check it came from the repo (same directory as this script)
DAEMON_DIR="$(cd "$(dirname "$DAEMON_FILE")" && pwd)"
if [ "$DAEMON_DIR" = "$SCRIPT_DIR" ]; then
    pass "Source is this repo (trusted origin)"
else
    warn "File is outside the repo directory — verify origin manually"
fi

echo ""

# ─────────────────────────────────────────────
# LAYER 2 — SHA256 checksum (tamper detection)
# ─────────────────────────────────────────────
echo "2️⃣  Cryptographic integrity (SHA256)"

if [ ! -f "$CHECKSUM_FILE" ]; then
    fail "Checksum file missing: $CHECKSUM_FILE"
    fail "Cannot verify integrity without a reference checksum"
else
    # Compute checksum of the daemon file
    if command -v shasum &>/dev/null; then
        ACTUAL=$(shasum -a 256 "$DAEMON_FILE" | awk '{print $1}')
    elif command -v sha256sum &>/dev/null; then
        ACTUAL=$(sha256sum "$DAEMON_FILE" | awk '{print $1}')
    else
        fail "No sha256 tool found (install shasum or sha256sum)"
        ACTUAL=""
    fi

    EXPECTED=$(awk '{print $1}' "$CHECKSUM_FILE")

    if [ -z "$ACTUAL" ]; then
        fail "Could not compute checksum"
    elif [ "$ACTUAL" = "$EXPECTED" ]; then
        pass "Checksum matches (${ACTUAL:0:16}...)"
    else
        fail "Checksum MISMATCH"
        echo "     Expected: $EXPECTED"
        echo "     Actual:   $ACTUAL"
        echo "     The file has been modified since it was committed."
        echo "     Do not run it. Re-clone the repo to get a clean copy."
    fi
fi

echo ""

# ─────────────────────────────────────────────
# LAYER 3 — Static policy scan (content audit)
# ─────────────────────────────────────────────
echo "3️⃣  Policy scan (dangerous pattern check)"

POLICY_FAIL=0

# Parallel arrays: patterns and their human-readable reasons
PATTERNS=(
    "os\.system\("
    "subprocess\.call\(.*shell=True"
    "eval\("
    "__import__"
    "import pickle"
    "curl http"
    "wget "
    "\bsudo\b"
    "rm -rf"
    "chmod 777"
)
REASONS=(
    "os.system() — use subprocess with args list instead"
    "shell=True in subprocess — allows shell injection"
    "eval() — executes arbitrary code"
    "__import__ — dynamic import, potential bypass"
    "pickle — can execute code on deserialization"
    "outbound curl call — unexpected network download"
    "outbound wget — unexpected network download"
    "sudo — daemon should not escalate privileges"
    "rm -rf — destructive file operation"
    "chmod 777 — insecure permission grant"
)

for i in "${!PATTERNS[@]}"; do
    if grep -qE "${PATTERNS[$i]}" "$DAEMON_FILE" 2>/dev/null; then
        fail "Forbidden pattern: ${REASONS[$i]}"
        POLICY_FAIL=$((POLICY_FAIL + 1))
    fi
done

if [ $POLICY_FAIL -eq 0 ]; then
    pass "No forbidden patterns detected"
fi

echo ""

# ─────────────────────────────────────────────
# LAYER 4 — Structure check (is it what we expect?)
# ─────────────────────────────────────────────
echo "4️⃣  Structure check"

# Must start with python shebang
if head -1 "$DAEMON_FILE" | grep -q "^#!/usr/bin/env python"; then
    pass "Valid Python shebang"
else
    fail "Missing or unexpected shebang (expected #!/usr/bin/env python3)"
fi

# Must contain expected function signatures (not arbitrary scripts)
REQUIRED_FUNCTIONS=("def load_credentials" "def poll_once" "def generate_response" "def run")
for FN in "${REQUIRED_FUNCTIONS[@]}"; do
    if grep -q "$FN" "$DAEMON_FILE"; then
        pass "Expected function present: $FN"
    else
        fail "Expected function MISSING: $FN — file may be wrong version or tampered"
    fi
done

# Must not contain credentials (belt-and-suspenders)
if grep -qE "appr_[a-z0-9]{10,}" "$DAEMON_FILE"; then
    fail "Hardcoded token detected — credentials should never be in source files"
else
    pass "No hardcoded credentials"
fi

echo ""

# ─────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────
echo "════════════════════════════════════════════"
echo "  Passed: $PASS    Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ VERIFICATION PASSED"
    echo "   The daemon is safe to copy and run."
    echo ""
    echo "   Suggested execution (restricted user, no root):"
    echo "   cp $DAEMON_FILE /data/.openclaw/workspace/"
    echo "   cd /data/.openclaw/workspace"
    echo "   nohup python3 approval_chat_daemon_v2.py > /tmp/approval-daemon-v2.log 2>&1 &"
    exit 0
else
    echo "🚫 VERIFICATION FAILED"
    echo "   Do not copy or run this daemon."
    echo "   Fix the issues above or re-clone the repo:"
    echo "   git clone https://github.com/chriskoturathbun/Agent-Approval-Onboarding.git"
    exit 1
fi
