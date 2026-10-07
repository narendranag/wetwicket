# Decisions — Wet Wicket

Append-only. Format: `- [<host>] [YYYY-MM-DD] <decision> — <why>`.

## Carried over from TASKS.md (2026-10-04)

These were recorded before this file existed, without dates or hosts. Don't re-ask them.

- **Name and domain:** Wet Wicket, bought via Cloudflare Registrar.
- **Structure:** series-first magazine, with vernacular section names and plain subtitles.
- **Stack:** Astro on Cloudflare Workers, with D1. R2 is not needed yet.
- **Nightly:** GitHub Actions cron, covering everything Cricsheet has.
- **Voice:** masthead plus signed first-person pieces.
- **Prose pieces** are drafted by Claude in Narendra's first person and published on his say-so.
- **Rain Rules:** the D/L Standard Edition is exact (all six ICC examples pass). The Professional Edition is a labelled reconstruction.
- **Licensing (2026-10-01):** Wet Wicket is a product, not open source — see CLAUDE.md, "Conventions".

## Since

- [air] [2026-10-04] Marketing analytics is GA4 through Google Tag Manager (container GTM-NJSJFFP6), defined in `analytics.yaml`; the direct `gtag.js` snippet goes when the container goes live — the fleet standard (DEV-GUIDELINES, "Analytics"), and one place to define events
- [air] [2026-10-04] The one GA event is `use_interactive` (key event, parameter `piece`) — for an editorial site, using an interactive piece is the conversion; page views, scrolls and outbound clicks are GA's automatic measurement
- [air] [2026-10-04] This brain follows the claude-computer standard: Now/Next/Later/Done tasks, this file, a justfile, docs in the documentation standard — so fleet sessions and tools (tasks-sync, docs-build) work here
- [air] [2026-10-07] Cloudflare "Always Use HTTPS" is on for the wetwicket.com zone (set via API with the zone token) — http:// served every page with a 200, and Search Console counted 268 http copies as alternates of the https pages, plus rss.xml as a duplicate
