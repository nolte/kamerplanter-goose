#!/usr/bin/env bash
# Work through the Kamerplanter diary-analysis queue, one Goose process per entry.
#
# This is the process-isolated counterpart to recipes/diary-analysis-queue-apply.yaml.
# That recipe loops inside a single run and shares one context across every entry;
# this script starts a fresh `goose run` per entry, so an entry that exhausts its
# context or crashes cannot affect the next one. It is the shape the process spec
# asks for ("exactly one entry per run"), at the cost of one process start each.
#
# Goose's own `sub_recipes:` mechanism would be the natural fit and does not work
# here: measured against Goose 1.45.0 with GOOSE_PROVIDER=claude-code, neither a
# `sub_recipes:` block nor `--sub-recipe` produces a callable tool in the run.
#
# Usage:  scripts/analyse-queue.sh [max_entries] [tenant]
# Needs:  KAMERPLANTER_URL, KAMERPLANTER_API_KEY, GOOSE_ADDITIONAL_CONFIG_FILES
#         (direnv loads all three from .envrc)

set -euo pipefail

MAX_ENTRIES="${1:-3}"
TENANT="${2:-}"

# Validated, not trusted. `[ "$n" -ge "$MAX_ENTRIES" ]` is the left arm of an
# && list, so set -e exempts it: a non-numeric value makes `test` fail, the
# break is never reached, and the cap vanishes entirely — this loop then runs
# a write-capable recipe against every one of up to 100 queued entries and
# still exits 0. The usage line reads `[max_entries] [tenant]`, and the tenant
# is the parameter a caller remembers, so `analyse-queue.sh my-garden` is the
# obvious way to arrive here.
case "$MAX_ENTRIES" in
  '' | *[!0-9]*)
    echo "max_entries must be a non-negative integer, got '$MAX_ENTRIES'." >&2
    echo "Usage: $(basename "$0") [max_entries] [tenant]" >&2
    exit 2
    ;;
esac
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ID="queue-$(date +%Y%m%d-%H%M%S)"

: "${KAMERPLANTER_URL:?set it, or run: direnv allow}"
: "${KAMERPLANTER_API_KEY:?set it, or run: direnv allow}"

# The recipes load project skills from .claude/skills/, and skill discovery is
# relative to the Goose process's working directory — so every run starts here.
cd "$REPO_ROOT"
export GOOSE_RECIPE_PATH="$REPO_ROOT/recipes"
export GOOSE_ADDITIONAL_CONFIG_FILES="${GOOSE_ADDITIONAL_CONFIG_FILES:-$REPO_ROOT/extensions.yaml}"

mcp_call() {
  # $1 = JSON-RPC body. Opens its own session; the queue read is cheap enough
  # that reusing one across calls is not worth the extra state.
  local sid headers status
  # Without capturing the status separately, a 401 from a revoked key makes the
  # grep below find no session header, `set -e` kills the script mid-pipeline,
  # and the operator is left with no code, no body, and nothing to act on.
  headers=$(curl -sS -m 15 -X POST "$KAMERPLANTER_URL/api/v1/mcp" \
    -H "X-API-Key: $KAMERPLANTER_API_KEY" -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"analyse-queue","version":"1.0"}}}' \
    -D - -o /dev/null -w '%{http_code}') || {
      echo "!! could not reach $KAMERPLANTER_URL/api/v1/mcp" >&2
      return 1
    }
  status=$(printf '%s' "$headers" | tail -n1)
  sid=$(printf '%s' "$headers" | grep -i '^mcp-session-id:' | tr -d '\r' | cut -d' ' -f2)

  if [ -z "$sid" ]; then
    echo "!! no mcp-session-id in the initialize response (HTTP $status)." >&2
    echo "   Check KAMERPLANTER_API_KEY and KAMERPLANTER_URL, or run:" >&2
    echo "     goose run --recipe connectivity-check" >&2
    return 1
  fi

  curl -sS -m 30 -X POST "$KAMERPLANTER_URL/api/v1/mcp" \
    -H "X-API-Key: $KAMERPLANTER_API_KEY" -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: $sid" \
    -d "$1"
}

# A Kamerplanter garden slug is lowercase alphanumerics and hyphens. Checking
# that beats escaping it: interpolated raw, a slug carrying a quote or a
# backslash produces invalid JSON, and the server's parse error then arrives as
# an empty queue — which reads as "nothing to do" rather than as a typo.
tenant_arg=""
if [ -n "$TENANT" ]; then
  case "$TENANT" in
    *[!a-zA-Z0-9-_]*)
      echo "tenant must be a garden slug (letters, digits, - and _), got '$TENANT'." >&2
      exit 2
      ;;
  esac
  tenant_arg=",\"tenant\":\"$TENANT\""
fi

echo "Reading the analysis queue..."
queue_json=$(mcp_call "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"list_pending_diary_analyses\",\"arguments\":{\"limit\":100,\"include_stale\":true$tenant_arg}}}")

# Entries with no photos are not candidates for an image analysis; filtering them
# here keeps the per-entry runs from starting only to refuse.
#
# Captured into a variable rather than piped straight into `mapfile`: process
# substitution discards the exit status, `pipefail` does not cover it, and every
# failure path below — unparseable JSON, a JSON-RPC error, an envelope that
# changed shape — then produced an empty list, printed "Nothing pending" and
# exited 0. A cron job saw a clean, empty run while the queue backed up.
if ! entries_raw=$(printf '%s' "$queue_json" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit("could not parse the queue response")
if "error" in d:
    sys.exit("server error: " + json.dumps(d["error"]))
data = d.get("result", {}).get("structuredContent", {}).get("data", {})
for e in data.get("entries", []):
    if e.get("photo_count", 0) > 0:
        print(e["entry_key"])
'); then
  echo "!! could not read the analysis queue — see the message above." >&2
  echo "   The queue was NOT empty-checked; nothing was processed." >&2
  exit 1
fi

mapfile -t entries <<< "$entries_raw"
# `<<<` on an empty string yields one empty element, not zero.
[ "${#entries[@]}" -eq 1 ] && [ -z "${entries[0]}" ] && entries=()

total=${#entries[@]}
if [ "$total" -eq 0 ]; then
  echo "Nothing pending with photos. Done."
  exit 0
fi

echo "$total entry/entries pending with photos; processing up to $MAX_ENTRIES."
echo

completed=0; failed=0; skipped=0; n=0
for entry in "${entries[@]}"; do
  [ "$n" -ge "$MAX_ENTRIES" ] && break
  n=$((n + 1))
  echo "--- [$n/$MAX_ENTRIES] entry $entry ---"

  # One process per entry: a crash or context exhaustion here cannot reach the
  # next entry. The recipe still guarantees its own claim is submitted.
  # The final line decides, not the exit code. diary-photo-analysis-apply ends
  # normally with `NOT CLAIMED: <reason>` when another worker holds the lease —
  # exit 0, entry untouched. Counting that as processed reported
  # `PROCESSED: 3 ok / REMAINING: 0` for a queue that had not moved.
  # Captured, then echoed, rather than teed to /dev/stderr: teeing moved the
  # whole run's output onto stderr, changing what any caller redirecting the
  # streams sees, and its ordering was not reproducible here. The cost is that
  # a run's output appears when it ends instead of live.
  run_status=0
  run_output=$(goose run --no-session --max-turns 25 -q \
      --recipe diary-photo-analysis-apply \
      --params "entry_key=$entry" \
      --params "run_id=$RUN_ID-$entry" \
      ${TENANT:+--params "tenant=$TENANT"} 2>&1) || run_status=$?
  printf '%s\n' "$run_output"

  if [ "$run_status" -eq 0 ]; then
    if printf '%s' "$run_output" | grep -q '^NOT CLAIMED:'; then
      echo "!! $entry was not claimed; it stays in the queue"
      skipped=$((skipped + 1))
    else
      completed=$((completed + 1))
    fi
  else
    # A non-zero exit means the run itself died, so its claim may still be held.
    # The lease expires on its own; --include_stale picks the entry up next time.
    echo "!! run for $entry exited non-zero; its lease will expire and requeue it"
    failed=$((failed + 1))
  fi
  echo
done

echo "==============================="
echo "RUN ID:    $RUN_ID"
echo "PROCESSED: $completed ok, $failed failed, $skipped not claimed"
# Subtract what actually completed, not what was attempted. A failed run's lease
# expires and requeues the entry, and a `NOT CLAIMED` run never held it — both
# are still pending, so counting either as processed understates the backlog.
echo "REMAINING: $((total - completed)) still pending with photos"
