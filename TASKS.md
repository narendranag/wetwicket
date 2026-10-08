# Tasks — Wet Wicket

<!-- Format (shared by every brain): one `- [ ]` per task; optional `📅 YYYY-MM-DD` due date and `#tags`.
     Now / Next / Later / Done. Current status is in CLAUDE.md ("Status"); decisions in DECISIONS.md. -->

## Now

- [ ] **Take GA4 + Tag Manager live** — follow `docs/HANDOFF-2026-10-04-analytics.md`: decide consent with Narendra, swap the `gtag.js` snippet for GTM-NJSJFFP6, send `use_interactive` from the four interactive pieces, check in GTM Preview, deploy, publish (ask first) #analytics
- [ ] **Watch the first real nightly run with new matches.** Check D1 counts, the `latest_match` meta value, that the redeploy succeeded, and the `rain.json` commit.
- [ ] **Confirm the nightly workflow runs cleanly on the bumped Actions** (checkout v7, setup-node v7, setup-python v7, cache v6; pushed 2026-10-01). The deploy workflow already has, with no Node 20 warnings. The nightly's Python and cache steps were due to run first on 2026-10-02 at 00:30 UTC.

## Next

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
- [ ] Glossary (`/glossary/`), which the information architecture describes but doesn't yet exist. #archive

## Done

- [x] GA4 + Tag Manager set up from `analytics.yaml` (2026-10-04): container GTM-NJSJFFP6, key event `use_interactive`, dimension `piece`; version 2 saved, not published
- [x] Brain brought to the claude-computer standard (2026-10-04): Now/Next/Later/Done tasks, DECISIONS.md, justfile, docs in the documentation standard, gitleaks pre-commit
