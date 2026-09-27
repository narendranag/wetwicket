#!/usr/bin/env bash
# Deploy a new Worker version without touching routes or custom domains, which are set once
# with `wrangler deploy` and need zone permissions the CI token doesn't have.
set -euo pipefail
npm run build
out=$(npx wrangler versions upload --message "${1:-CI deploy}")
echo "$out"
vid=$(echo "$out" | grep -oE "Worker Version ID: [0-9a-f-]+" | awk '{print $4}')
npx wrangler versions deploy "$vid@100%" --yes
