#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
GOLDEN_FILE=${GOLDEN_FILE:-"$SCRIPT_DIR/../tests/data/golden_employee.json"}
BASE_URL=${BASE_URL:-"http://127.0.0.1:8000"}
UPDATED_LAST=${UPDATED_LAST:-"IntegrationTest"}

if [[ ! -f "$GOLDEN_FILE" ]]; then
  echo "Golden data file not found: $GOLDEN_FILE" >&2
  exit 1
fi

# Load golden configuration into environment variables.
while IFS= read -r line; do
  eval "$line"
done < <(python - <<'PY' "$GOLDEN_FILE"
import json
import shlex
import sys

def emit(key, value):
    print(f"{key}={shlex.quote(str(value))}")

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)

emit("EMP_NO", data["employee"]["emp_no"])
emit("GOLDEN_FIRST", data["employee"]["first_name"])
emit("GOLDEN_LAST", data["employee"]["last_name"])
emit("WR_USER", "admin")
emit("WR_PASS", data["users"]["admin"]["password"])
emit("RD_USER", "analyst")
emit("RD_PASS", data["users"]["analyst"]["password"])
PY
)

function curl_json() {
  local auth_user=$1
  local auth_pass=$2
  local method=$3
  local url=$4
  shift 4
  local result
  result=$(curl -sS -u "$auth_user:$auth_pass" -X "$method" "$url" "$@" -H 'accept: application/json' -w '\n%{http_code}')
  HTTP_STATUS=$(echo "$result" | tail -n1)
  RESPONSE_BODY=$(echo "$result" | sed '$d')
}

function require_status() {
  local expected=$1
  if [[ "$HTTP_STATUS" != "$expected" ]]; then
    echo "Expected HTTP $expected but received $HTTP_STATUS" >&2
    echo "Response: $RESPONSE_BODY" >&2
    exit 1
  fi
}

echo "Starting writer session for $WR_USER"
curl_json "$WR_USER" "$WR_PASS" POST "$BASE_URL/sessions/start"
require_status 200
SESSION_ID=$(RESPONSE="$RESPONSE_BODY" python - <<'PY'
import json
import os

print(json.loads(os.environ["RESPONSE"])["session_id"])
PY
)

echo "Verifying employee $EMP_NO matches golden data"
curl_json "$WR_USER" "$WR_PASS" GET "$BASE_URL/employees/$EMP_NO" -H "X-Session-Id: $SESSION_ID"
require_status 200
PY_ARGS_FIRST="$GOLDEN_FIRST" PY_ARGS_LAST="$GOLDEN_LAST" RESPONSE="$RESPONSE_BODY" python - <<'PY'
import json
import os

payload = json.loads(os.environ["RESPONSE"])
first = os.environ["PY_ARGS_FIRST"]
last = os.environ["PY_ARGS_LAST"]

if payload["first_name"] != first or payload["last_name"] != last:
    raise SystemExit(
        f"Golden mismatch: expected {first} {last}, got {payload['first_name']} {payload['last_name']}"
    )
PY

echo "Updating employee $EMP_NO last name to $UPDATED_LAST"
curl_json "$WR_USER" "$WR_PASS" PUT "$BASE_URL/employees/$EMP_NO/last-name" \
  -H "Content-Type: application/json" -H "X-Session-Id: $SESSION_ID" \
  -d "{\"last_name\": \"$UPDATED_LAST\"}"
require_status 200

curl_json "$WR_USER" "$WR_PASS" GET "$BASE_URL/employees/$EMP_NO" -H "X-Session-Id: $SESSION_ID"
require_status 200
EXPECTED_LAST="$UPDATED_LAST" RESPONSE="$RESPONSE_BODY" python - <<'PY'
import json
import os

payload = json.loads(os.environ["RESPONSE"])
expected = os.environ["EXPECTED_LAST"]

if payload["last_name"] != expected:
    raise SystemExit(
        f"Update failed: expected last name {expected}, received {payload['last_name']}"
    )
PY

echo "Ensuring read-only user cannot perform updates"
curl_json "$RD_USER" "$RD_PASS" POST "$BASE_URL/sessions/start"
require_status 200
RD_SESSION=$(RESPONSE="$RESPONSE_BODY" python - <<'PY'
import json
import os

print(json.loads(os.environ["RESPONSE"])["session_id"])
PY
)

curl_json "$RD_USER" "$RD_PASS" PUT "$BASE_URL/employees/$EMP_NO/last-name" \
  -H "Content-Type: application/json" -H "X-Session-Id: $RD_SESSION" \
  -d '{"last_name": "ShouldFail"}'
require_status 403

echo "Reverting employee $EMP_NO last name to $GOLDEN_LAST"
curl_json "$WR_USER" "$WR_PASS" PUT "$BASE_URL/employees/$EMP_NO/last-name" \
  -H "Content-Type: application/json" -H "X-Session-Id: $SESSION_ID" \
  -d "{\"last_name\": \"$GOLDEN_LAST\"}"
require_status 200

curl_json "$WR_USER" "$WR_PASS" POST "$BASE_URL/sessions/end" -H "X-Session-Id: $SESSION_ID"
require_status 200

curl_json "$RD_USER" "$RD_PASS" POST "$BASE_URL/sessions/end" -H "X-Session-Id: $RD_SESSION"
require_status 200

echo "Integration checks completed successfully."
