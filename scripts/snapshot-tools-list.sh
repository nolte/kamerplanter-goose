#!/usr/bin/env bash
# Refresh tests/kamerplanter-tools-list.json from a live Kamerplanter MCP server.
#
# The snapshot keeps each tool's name and its inputSchema property keys only —
# no descriptions, no values — so a diff shows exactly what changed in the
# catalog. tests/validate_recipes.py derives STATE_CHANGING_TOOLS from it.
#
# Usage: scripts/snapshot-tools-list.sh
# Needs KAMERPLANTER_URL and KAMERPLANTER_API_KEY (set by .envrc).
set -euo pipefail

: "${KAMERPLANTER_URL:?KAMERPLANTER_URL is not set; run direnv allow}"
: "${KAMERPLANTER_API_KEY:?KAMERPLANTER_API_KEY is not set; run direnv allow}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$root/tests/kamerplanter-tools-list.json"
endpoint="$KAMERPLANTER_URL/api/v1/mcp"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

post() {
  # $1: JSON-RPC body, $2: extra header (may be empty). Fails on any non-2xx.
  curl --silent --show-error --fail-with-body --max-time 30 \
    -H "X-API-Key: $KAMERPLANTER_API_KEY" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    ${2:+-H "$2"} \
    -D "$work/headers" \
    -d "$1" "$endpoint"
}

post '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"snapshot-tools-list","version":"1"}}}' '' >"$work/init.json"
session="$(grep -i '^mcp-session-id:' "$work/headers" | cut -d' ' -f2 | tr -d '\r')"
post '{"jsonrpc":"2.0","method":"notifications/initialized"}' "${session:+Mcp-Session-Id: $session}" >/dev/null
post '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' "${session:+Mcp-Session-Id: $session}" >"$work/tools.json"

python3 -I - "$work/init.json" "$work/tools.json" "$KAMERPLANTER_URL" "$out" <<'EOF'
import datetime
import json
import sys

init_path, tools_path, instance, out = sys.argv[1:]
init = json.load(open(init_path))
response = json.load(open(tools_path))
if "error" in response or "nextCursor" in response.get("result", {}):
    sys.exit(f"tools/list: unexpected response {json.dumps(response)[:300]}")
tools = {
    tool["name"]: sorted(tool.get("inputSchema", {}).get("properties", {}))
    for tool in response["result"]["tools"]
}
snapshot = {
    "instance": instance,
    "server": init["result"]["serverInfo"],
    "measured": datetime.date.today().isoformat(),
    "tools": dict(sorted(tools.items())),
}
with open(out, "w") as handle:
    json.dump(snapshot, handle, indent=2)
    handle.write("\n")
print(f"{len(tools)} tools written to {out}")
EOF
