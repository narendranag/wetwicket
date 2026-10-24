# Tasks — Wet Wicket

<!-- Format (shared by every brain): one `- [ ]` per task; optional `📅 YYYY-MM-DD` due date and `#tags`.
     Now / Next / Later / Done. Current status is in CLAUDE.md ("Status"); decisions in DECISIONS.md. -->

## Now

- [ ] **Resume here:** branch `feat/consent-gtm` (b604953, not pushed) brings wetwicket.com to Consent Mode v2 Advanced, tested locally. It waits on Narendra's yes to two linked steps: merge to `main` (deploys) and `analytics publish` straight after. Then re-run the live check below.
- [ ] **Ship Consent Mode v2 Advanced on wetwicket.com** (follow-up to the stale "Take GA4 + Tag Manager live", 2026-10-24). The fleet record says GA4 + GTM with Advanced consent have been live on every site since 2026-10-04; on wetwicket.com that is not so. Checked live 2026-10-24 in headless Chromium: the site loads `gtag.js` directly, not GTM; no consent default (`gcd=13l3l3l3l1l1`, no `gcs`); `_ga` and `_ga_H14P5LK5VK` set on the first page load; no banner. GTM-NJSJFFP6 *is* published, but its live version 1 is empty (`"tags":[]`); the Google tag and the `use_interactive` tag are in version 2, saved and unpublished. Branch `feat/consent-gtm` fixes the site: GTM loader with consent default denied (ads always denied), banner with Allow / No thanks (answer in localStorage `ww-consent`; No thanks clears `_ga*`), footer "Cookie choice" to reopen it, `use_interactive` once per page view from all four pieces. Local test, with v2's Google tag stood in by `gtag.js` + `config` and every hit intercepted: before an answer `gcs=G100`, no cookies; after Allow `gcs=G101`, `_ga` set; after No thanks cookies gone; each piece sends `use_interactive` only on first use. To finish, all with Narendra's yes: (1) merge and deploy; (2) `analytics publish` at once — until it runs, the deployed site sends GA nothing; (3) live re-check: G100 before an answer, G101 after Allow, `use_interactive` in GA DebugView. Also his: the banner wording, and whether the site needs a privacy page for the banner to link to (it has none) #analytics

## Next

- [ ] **Watch the first nightly with new matches on Ubuntu 26.** GitHub moves `ubuntu-latest` to Ubuntu 26 from 2026-10-19; the runs up to 2026-10-20 were still on ubuntu-24.04. Assessed low risk on 2026-10-21: actions/python-versions ships 3.12.15 for 26.04, the deps are numpy/pandas/scipy wheels, Node and wrangler don't care, and the match-database cache is OS-independent (the pip cache misses once). Migration completes by 2026-11-19. If the Python or wrangler steps break, pin `runs-on: ubuntu-24.04` in `nightly.yml` and `deploy.yml`.
- [ ] Build: WetWicket content automation — write the workplan (from Google Tasks, 2026-10-08) #gtasks
- [ ] **Fact-check the unsourced details in the two prose pieces**, published 2026-10-01 as written. _Someone, Somewhere_: Duckworth's nuclear-industry career, the 2010 MBEs, McMillan and Richardson at the crease and the last-ball single, Pringle bowling England's two cheapest overs. _The Wrong Number_: the 1992 and 1999 references.
- [ ] **Check Search Console** (Indexing > Pages): how many Archive pages Google has picked up, and any crawl errors, about a week after 2026-10-01.
- [ ] **Show Avirook his bio** (`src/content/authors/avirook-sen.md`) and get his approval.
- [ ] **Decide on domain auto-renew.** It is OFF, and wetwicket.com expires on 2027-09-27. Narendra decides: it's a recurring charge.
- [ ] Enable the Google Analytics Data API in the Cloud project `claude-computer-acccess` (Narendra), so `analytics report` and `analytics funnel` work #analytics

## Later

- [ ] Classics: more rain-affected matches, using the components in `src/components/classics/` and `pipeline/build_pieces.py <match id>`. Candidates in Cricsheet: the 2015 World Cup semi-final (656491), the 2007 World Cup final (247507). The 1992 semi-final is not in Cricsheet (its ODIs start in 2002). #rain-rules
- [ ] Request indexing in Search Console for the four new pieces if they are slow to appear. #rain-rules
- [ ] _Beat the Par_: a daily over that is the same for everyone; penalty runs and minimum-overs rules in the calculator. #rain-rules
- [ ] Link rain-hit matches and replay examples to Archive match pages. Done for the scorecard links; consider adding the replay's par scores to each match page. #rain-rules
- [ ] Match pages: win-probability swings and "key moments", computed in the pipeline and stored as JSON. #archive
- [ ] Player pages: season-by-season charts; a batting-position view; head-to-head bowler v batter. #archive
- [ ] Competition pages: points using each competition's real rules (currently wins, then NRR); the knockout bracket. #archive
- [ ] Ground pages: rain history by month; average scores over time. #archive
- [ ] Team pages (`/teams/<slug>/`): results, head-to-heads. #archive
- [ ] Search across matches, players and grounds from the nav. #archive
- [ ] Seed the local D1 (`npm run db:local`) so Archive pages and the Archive sitemaps can be tested in dev; it is currently empty on this machine. #archive
- [ ] Edge caching for D1 pages (Cache API in middleware). Pages set Cache-Control, but Workers responses aren't cached at the CDN by default. #archive
- [ ] Motion on the site, if wanted: small CSS transitions behind `prefers-reduced-motion` (as in `rain.css`, `par.css`), not Motion-Primitives — see DECISIONS 2026-10-15. Haikei SVG backgrounds remain the explore note's suggestion for this site #design
- [ ] Glossary (`/glossary/`), which the information architecture describes but doesn't yet exist. #archive

## Done

- [x] GA Google signals off, declared as `ga.google_signals: false` in analytics.yaml (2026-10-21): the property already had it disabled, so sync changed nothing; no GTM change, nothing published (2052a5a)
- [x] Nightly verified on the bumped Actions and with new matches (checked 2026-10-20): all runs 2026-10-01 to 10-20 succeeded with no deprecation warnings. Two carried matches: 10-08 and 10-15 (53 matches, 40 D1 queries / 111k rows, worker version 8176ced8 deployed at 100%, rain.json committed as e79bd87). Live Archive: 23,060 matches, up to 14 Oct 2026 — matching Cricsheet's last publish (Last-Modified 2026-10-14 22:23 UTC), so the quiet nights since are expected
- [x] GA4 + Tag Manager set up from `analytics.yaml` (2026-10-04): container GTM-NJSJFFP6, key event `use_interactive`, dimension `piece`; version 2 saved, not published
- [x] Brain brought to the claude-computer standard (2026-10-04): Now/Next/Later/Done tasks, DECISIONS.md, justfile, docs in the documentation standard, gitleaks pre-commit
