#!/bin/bash
# scripts/pre_commit_check.sh - Run before committing

set -e

echo "🔍 Running pre-commit security checks..."

# Check for secrets
python scripts/security_check.py

# Check that .env files are not being committed
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "❌ ERROR: .env file is being tracked by Git!"
    echo "Run: git rm --cached .env"
    exit 1
fi

if git ls-files --error-unmatch "*service-account*.json" 2>/dev/null; then
    echo "❌ ERROR: Service account file is being tracked by Git!"
    echo "Run: git rm --cached *service-account*.json"
    exit 1
fi

echo "✅ Security checks passed!"