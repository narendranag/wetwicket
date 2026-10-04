# Wet Wicket

A loving exploration of cricket, by cricket lovers, for cricket lovers. Live at https://wetwicket.com.
Co-created by Narendra Nag and Avirook Sen. Repo: github.com/narendranag/wetwicket (public).

Read `TASKS.md` for current status and what's next, and `docs/information-architecture.md`
before adding content or pages.

## Architecture

- **Site:** Astro 7 with the `@astrojs/cloudflare` adapter, deployed as a Cloudflare Worker
  (`wrangler.jsonc`). Editorial pages are prerendered. Archive pages set
  `export const prerender = false` and read from D1 at request time.
- **Database:** Cloudflare D1 `wetwicket` (binding `DB`), about 230 MB. The schema is in
  `db/schema.sql`. Ball-by-ball detail is pre-aggregated into JSON columns (`overs_json`,
  `fow_json`, `partnerships_json`), so no raw deliveries are stored.
- **Data:** Cricsheet match JSON and the Cricsheet Register. `pipeline/ingest.py` loads them into
  `data/wetwicket.sqlite`, and `pipeline/export_d1.py` writes SQL for D1, either a full seed or a
  nightly delta.
- **Nightly:** `.github/workflows/nightly.yml` runs at 00:30 UTC.
  1. `pipeline/update.py` makes conditional downloads of the 7-day zip and the Register.
  2. It ingests them into the cached SQLite and writes `data/d1/delta.sql`.
  3. The workflow applies the delta to D1 and redeploys.
  4. It commits `public/data/rain.json`.
- **Deploy:** `.github/workflows/deploy.yml` runs on push to main.
- **Rain Rules analysis:** `pipeline/rain_rules.py`, `simulate.py`, `analyze.py` and
  `build_site.py` produce `public/data/replay.json`. It is rebuilt by hand, not nightly.
- **Piece data:** `pipeline/build_pieces.py [match id …]` writes the D/L table
  (`public/data/dl-se.json`), the Beat the Par chases (`public/data/par-game.json`) and one
  `src/data/classics/<id>.json` per match id. Rebuilt by hand.
- **D/L in the browser:** `public/assets/dl.js` is a port of the Standard Edition functions in
  `rain_rules.py`. Keep the two in step.
- **Search:** `@astrojs/sitemap` covers prerendered pages. `src/pages/archive-[kind].xml.ts`
  serves the Archive's sitemaps from D1, and `astro.config.mjs` lists them in `sitemap-index.xml`.
  wetwicket.com is a verified Domain property in Google Search Console.

## Layout

```
src/content/{pieces/<section>/<slug>.mdx, series/, authors/}   editorial content (content.config.ts)
src/pages/[section]/…, series/, tags/, authors/                 editorial routes
src/pages/{matches,players,competitions,grounds}/               the Archive (D1, on-demand)
src/components/apps/                                            interactive pieces (JS in public/assets/)
src/components/classics/                                        Classics pieces: MatchStrip, ParChase, ParSheet, Moments
src/data/classics/<match id>.json                               match data for a Classics piece (build_pieces.py)
src/components/data/                                            Archive components (Worm, Manhattan, MatchRow…)
src/lib/{sections,db,cricket,career}.ts                         helpers
pipeline/                                                       Python: ingest, update, export, rain-rule analysis
db/schema.sql · data/reference/ (D/L 2002 table + SOURCES.md) · scripts/deploy-ci.sh
```

## Commands

```sh
npm run dev                         # local site; Archive pages need the local D1 (below)
npm run build

# Local database (Python venv at .venv; install with: .venv/bin/pip install -r requirements.txt)
.venv/bin/python pipeline/ingest.py --register data/raw/register --matches data/raw/all_json
.venv/bin/python pipeline/export_d1.py --full && npm run db:local
.venv/bin/python pipeline/update.py              # what the nightly job does
.venv/bin/python pipeline/test_rain_rules.py     # ICC worked examples; must pass
node scripts/test-dl.mjs                         # the same examples against public/assets/dl.js
.venv/bin/python pipeline/build_pieces.py 65272  # data for the calculator, the game and a classic

# Cloudflare (always use the site token)
eval "$(secrets env --only WETWICKET_CLOUDFLARE_API_TOKEN)"; export CLOUDFLARE_API_TOKEN="$WETWICKET_CLOUDFLARE_API_TOKEN"
scripts/deploy-ci.sh "message"                   # deploy a new version without touching routes
npx wrangler d1 execute wetwicket --remote --file data/d1/delta.sql --yes
```

## Conventions

- **Licensing (2026-10-01): Wet Wicket is a product, not open source.** The repo is public so the
  data can be picked up. `LICENSE` reserves all rights in the code, pipeline, design, charts and
  writing; `LICENSE-DATA.md` puts Cricsheet's data and the datasets derived from it under ODC-By
  1.0. `data/reference/` is third-party and excluded. Never describe the code as MIT or open
  source, and keep README, `/data` and both licence files in agreement.
- **Credit Cricsheet** (Stephen Rushe, ODC Attribution License 1.0) on every page that uses its
  data: use `<DataCredit />`. Cricsheet has no per-match pages, so link matches to our own
  `/matches/<id>/`.
- **Voice:** "Wet Wicket" is the masthead. Pieces are signed and written in the author's first
  person. Section names are vernacular with plain subtitles: The Numbers (Data), Classics,
  The Nets (Games), The Long Room (Essays), Scorebook (Tools), The Archive.
- **Permanent URLs:** a piece keeps its URL under its section. Series only order pieces.
- **Styling:** shared tokens are in `src/styles/global.css`, with light and dark themes.
  - The chart palette is fixed: `--r-se`, `--r-arr`, `--r-refit`, `--r-mpo`, `--r-pro`, `--r-proavg`.
  - Team 1 is blue and Team 2 is orange on match charts.
- **Formats:** Test, ODI, T20I, First-class, One-day (other), T20 league and The Hundred, which
  has five-ball sets and is kept separate.
- **Commits:** end with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Gotchas

- **MDX frontmatter:** `layout:` is reserved by MDX, so pieces use `presentation: app | article`.
- **Season URLs:** seasons like "2023/24" appear as `2023-24` (`seasonSlug` / `seasonFromSlug`).
- **Deploying:** plain `wrangler deploy` needs zone permissions for the custom-domain routes,
  which the site token lacks. Use `scripts/deploy-ci.sh`.
  - The original `CLOUDFLARE_API_TOKEN` has zone and Registrar access. It created the `www` →
    apex redirect rule and bought the domain.
- **Env vars:** use `eval "$(secrets env --only NAME,…)"` (exports them) or `secrets exec --only NAME,… -- <cmd>`, or Python won't see the vars.
- **zsh:** in shell loops, never name a variable `path` (it wipes `PATH`), and quote paths
  containing `[...]`.
- **The Professional Edition** in the replay analysis is Chris Baker's 2011 reconstruction, not
  the official ICC version. Say so wherever it's shown. The current DLS is not public.
- **Deploy triggers:** `deploy.yml` only runs for changes under `src/`, `public/` and a few config
  files. A push that touches only `.github/`, `pipeline/` or docs deploys nothing.
- **Local D1** starts empty. Archive pages and the Archive sitemaps return 500 in `npm run dev`
  until it is seeded (see Commands).
- **Dev server:** `astro dev` runs in the background (`npx astro dev stop | status | logs`). After
  a change to `astro.config.mjs` it can fail to restart; stop it, delete `node_modules/.vite`, and
  start it again.
- **Drafts:** `draft: true` pieces show in dev and are left out of production builds.
- **DNS:** the apex TXT record `google-site-verification=…` keeps the Search Console property
  verified. Don't remove it.
- **Be polite to Cricsheet:** conditional requests, an identifying User-Agent, and no bulk HEAD scans.
