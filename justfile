# justfile — setup / test / lint / run are the contract every repo keeps (~/claude-computer/docs/DEV-GUIDELINES.md).

setup:
    npm ci
    python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt

dev:
    npm run dev

run: dev

build:
    npm run build

# The ICC worked examples, in Python (pipeline) and in the site's JavaScript (public/assets/dl.js).
test:
    .venv/bin/python pipeline/test_rain_rules.py
    node scripts/test-dl.mjs

# Docs in the documentation standard, and analytics.yaml well formed (offline: no Google call).
lint:
    docs-build --check docs
    ANALYTICS_OFFLINE=1 analytics sync --dry-run > /dev/null
