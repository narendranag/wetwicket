# Hand-off — take GA4 + Tag Manager live on wetwicket.com

From the fleet session on 2026-10-04 (claude-computer). Read this, then `analytics.yaml`, then the "Analytics" section of `~/claude-computer/docs/DEV-GUIDELINES.md`.

## Where things stand

- **GA4:** the existing property `properties/556072136`, web stream `G-H14P5LK5VK` (the one the site already loads). New on 2026-10-04: custom dimension `piece` and key event `use_interactive`.
- **Tag Manager:** new web container **`GTM-NJSJFFP6`** ("Wet Wicket", account NarendraNag). It holds the Google tag (`G-H14P5LK5VK`, all pages), a data-layer variable `piece`, a trigger on the `use_interactive` event and a GA4 event tag for it. **Version 2 is saved and NOT published.**
- **`analytics.yaml`** (repo root) is the source of truth and holds every ID. `analytics sync` is idempotent: a second run changed nothing.
- **The site still loads GA directly:** `src/layouts/Base.astro` lines 25–31 have the `gtag.js` snippet for `G-H14P5LK5VK`. Nothing on the site uses GTM yet.

## What to do, in order

1. **Consent first — decide before going live.** wetwicket.com has readers in the UK and EU. The guidelines say GTM's consent mode and a cookie banner come before GA goes live there. Ask Narendra: banner (and which), or accept the current state (GA already runs without one today). Don't skip this question.
2. **Swap the snippet** in `src/layouts/Base.astro`: remove the `gtag.js` block (lines 25–31) and add the GTM container. `analytics snippet` prints both GTM parts (the `<head>` script and the `<noscript>` iframe after `<body>`). Remove the old block in the same change — with both, every page view counts twice.
3. **Send `use_interactive`** from the four interactive pieces (`src/components/apps/`, JS in `public/assets/`): once per page view, on the first real interaction (a calculation run, a game started, a filter changed, a replay played — not on load):
   `window.dataLayer = window.dataLayer || []; window.dataLayer.push({event: 'use_interactive', piece: '<id>'})`
   with `piece` one of `dl-calculator`, `beat-the-par`, `rain-explorer`, `replay`.
4. **Test locally, then in GTM Preview:** `npm run dev`, open GTM → Preview → connect to the local site, use each piece, check the GA4 event tag fires with `piece`. Then GA → Admin → DebugView.
5. **Deploy** (push to `main`; `src/` changes deploy).
6. **Publish the container — ask Narendra first, every time:** `analytics publish`. An unpublished container sends nothing, so once step 2 is deployed GA receives **no data at all** until this runs. Get his yes before the deploy, then publish straight after it.
7. **Reports:** the Google Analytics **Data API** must be enabled in the Cloud project `claude-computer-acccess` (Narendra's step: APIs & Services → Library). Then `analytics report acquisition`, `analytics report landing-pages`, `analytics report interactives`, `analytics funnel interactive`.

## Rules

- `analytics publish` changes what the live site sends to Google: ask every time.
- GA gets marketing events only. Anything about how people use a piece in detail (which inputs, how long) is product analytics — not GA.
- Change events in `analytics.yaml` first, then `analytics sync`, then the site code.
