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
- [mini] [2026-10-15] Not adopting Motion-Primitives (explore note `ui-stack`) in Wet Wicket (Narendra agreed 2026-10-15) — the site is Astro + hand-written vanilla JS with its own CSS tokens: no React, no Tailwind, no shadcn `components.json`. Taking it means adding `@astrojs/react`, React, Tailwind v4 (whose preflight would restyle every page unless split out) and Motion (+57 KB gz measured in the note) to pages whose largest script is 4.7 KB gz, and rewriting the interactives as React islands. The note itself lists this brain only for Haikei backgrounds. Motion here stays CSS, behind `prefers-reduced-motion` as `rain.css` and `par.css` already do
- [mini] [2026-10-21] Keep `runs-on: ubuntu-latest` through GitHub's Ubuntu 26.04 migration rather than pinning 24.04 — every dependency of the nightly and deploy jobs has a 26.04 build or is OS-independent; pin only if a run breaks
- [mini] [2026-10-21] GA Google signals off for Wet Wicket, declared as `ga.google_signals: false` in analytics.yaml (Narendra, fleet-wide, 2026-10-21) — advertising features stay off; the property already had it disabled, so `analytics sync` changed nothing in GA and no GTM change was made or published
- [mini] [2026-10-24] wetwicket.com takes Consent Mode v2 Advanced as the fleet decided on 2026-10-20, through GTM-NJSJFFP6: consent default denied before the container loads, analytics_storage granted only on the banner's Allow, ad consent never; the answer lives in localStorage `ww-consent`, and "No thanks" clears `_ga*` — the live site was found on 2026-10-24 still on a bare gtag.js with no consent at all, contrary to the fleet record
