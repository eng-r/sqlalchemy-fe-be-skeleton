#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

if ! command -v pytest >/dev/null 2>&1; then
  echo "pytest is required to run the test suite." >&2
  exit 1
fi

exec pytest --cov=app --cov-report=term-missing "$@"
