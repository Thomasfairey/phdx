#!/usr/bin/env bash
#
# PHDx Quality Gates Script
# Run all quality checks before deployment
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "           PHDx Quality Gates"
echo "=============================================="
echo ""

FAILED=0

# Helper function
run_check() {
    local name="$1"
    local cmd="$2"
    echo -n "[$name] "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        return 1
    fi
}

# =============================================================================
# BACKEND CHECKS
# =============================================================================
echo "--- Backend Checks ---"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Python lint
if ! run_check "Python Lint (ruff)" "ruff check core/ api/ ui/ tests/"; then
    FAILED=1
fi

# Python format
if ! run_check "Python Format" "ruff format --check core/ api/ ui/ tests/"; then
    FAILED=1
fi

# Python tests
if ! run_check "Python Tests (pytest)" "python -m pytest tests/ -q"; then
    FAILED=1
fi

echo ""

# =============================================================================
# FRONTEND CHECKS
# =============================================================================
echo "--- Frontend Checks ---"

cd web_client

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "[npm install] Installing dependencies..."
    npm ci > /dev/null 2>&1
fi

# TypeScript typecheck
if ! run_check "TypeScript" "npm run typecheck"; then
    FAILED=1
fi

# ESLint
if ! run_check "ESLint" "npm run lint"; then
    FAILED=1
fi

# Vitest unit tests
if ! run_check "Unit Tests (vitest)" "npm run test"; then
    FAILED=1
fi

# Build
if ! run_check "Next.js Build" "npm run build"; then
    FAILED=1
fi

cd ..

echo ""
echo "=============================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All quality gates passed!${NC}"
    echo "=============================================="
    exit 0
else
    echo -e "${RED}Some quality gates failed.${NC}"
    echo "=============================================="
    exit 1
fi
