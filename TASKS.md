# Tasks

Last updated: 2026-10-01

## Status

**Live** at https://wetwicket.com. `www` redirects to the apex with a 301.

- **Home and series:** front page, `/series/`, and the Rain Rules series hub.
- **Rain Rules part 1:** *Rain Stopped Play* (`/scorebook/rain-hit-matches/`). 2,282 rain-hit
  matches, filterable by format, country, year and gender. Refreshed nightly.
- **Rain Rules part 2:** *Who Wins When It Rains* (`/numbers/who-wins-when-it-rains/`). 15,781
  rain-free chases replayed under ARR, MPO, D/L 2002, the D/L Professional Edition (ICC average
  and real average) and a modern refit. Rebuilt by hand.
- **The Archive:** `/matches/`, `/players/`, `/competitions/` and `/grounds/`, covering all
  22,983 Cricsheet matches and 18,554 Register people, served from D1.
- **Rain Rules parts 3 to 5** (published 2026-10-01): the D/L calculator
  (`/scorebook/dl-calculator/`), *Beat the Par* (`/nets/beat-the-par/`) and the Durban 2003
  classic *The Wrong Number* (`/classics/2003-durban/`). Data from `pipeline/build_pieces.py`.
- **Supporting pages:** `/data/` (Cricsheet credit and licence), `/about/`, author pages for
  Narendra Nag and Avirook Sen, RSS and sitemap.
- **Nightly job** at 00:30 UTC, with secrets set. Verified: a cold-cache rebuild with a D1 update,
  and a warm-cache no-op. The "new matches arrive" path (D1 delta, deploy, commit of rain.json)
  has not yet run for real. Check the first run after Cricsheet next publishes.
- **Deploy on push:** verified working.

## Next up

- [ ] **Watch the first real nightly run with new matches.** Check D1 counts, the
      `latest_match` meta value, that the redeploy succeeded, and the `rain.json` commit.
- [ ] **Confirm the bumped GitHub Actions run cleanly.** checkout v7, setup-node v7,
      setup-python v7 and cache v6 were pushed on 2026-10-01 but have not run yet: the deploy
      workflow ignores `.github/` changes. The next nightly run and the next deploy will show it.
- [ ] **Show Avirook his bio** (`src/content/authors/avirook-sen.md`) and get his approval.
- [ ] **Decide on domain auto-renew.** It is OFF, and wetwicket.com expires on 2027-09-27. The
      user decides: it's a recurring charge.

## Backlog: Rain Rules series

- [ ] Essay in The Long Room on how D/L came to be (ARR, then the 1992 MPO semi-final, then D/L,
      then DLS).
- [ ] Classics: more rain-affected matches, using the components in `src/components/classics/`
      and `pipeline/build_pieces.py <match id>`. Candidates in Cricsheet: the 2015 World Cup
      semi-final (656491), the 2007 World Cup final (247507).
- [ ] *Beat the Par*: a daily over that is the same for everyone; penalty runs and minimum-overs
      rules in the calculator.
- [ ] Link rain-hit matches and replay examples to Archive match pages. Done for the scorecard
      links; consider adding the replay's par scores to each match page.

## Backlog: The Archive

- [ ] Match pages: win-probability swings and "key moments", computed in the pipeline and stored
      as JSON.
- [ ] Player pages: season-by-season charts; a batting-position view; head-to-head bowler v batter.
- [ ] Competition pages: points using each competition's real rules (currently wins, then NRR);
      the knockout bracket.
- [ ] Ground pages: rain history by month; average scores over time.
- [ ] Team pages (`/teams/<slug>/`): results, head-to-heads.
- [ ] Search across matches, players and grounds from the nav.
- [ ] Edge caching for D1 pages (Cache API in middleware). Pages set Cache-Control, but Workers
      responses aren't cached at the CDN by default.
- [ ] Glossary (`/glossary/`), which the IA describes but doesn't yet exist.

## Decisions made (don't re-ask)

- **Name and domain:** Wet Wicket, bought via Cloudflare Registrar.
- **Structure:** series-first magazine, with vernacular section names and plain subtitles.
- **Stack:** Astro on Cloudflare Workers, with D1. R2 is not needed yet.
- **Nightly:** GitHub Actions cron, covering everything Cricsheet has.
- **Voice:** masthead plus signed first-person pieces.
- **Rain Rules:** the D/L Standard Edition is exact (all six ICC examples pass). The Professional
  Edition is a labelled reconstruction.
