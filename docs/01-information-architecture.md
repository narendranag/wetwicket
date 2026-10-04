---
id: information-architecture
title: Information architecture
order: 1
summary: How Wet Wicket is organised — principles, sections, URLs, the Archive, the content model, the front page and the first series.
status: stable
updated: 2026-10-04
audience: [everyone]
depends_on: [index]
related: []
defines: [section, series, piece, the Archive]
answers:
  - Which section does a new piece go in?
  - What is a piece's permanent URL?
  - How are series, pieces and the Archive related?
---

# Wet Wicket: information architecture

A loving exploration of cricket, by cricket lovers, for cricket lovers: data explorations,
breakdowns of epic matches, browser games, essays and tools.

## Principles

1. **Series first.** The front page and navigation lead with series: a few deep, ongoing
   explorations of one subject (Rain Rules, The Ashes, …), each mixing essays, data, match
   breakdowns, games and tools.
2. **Pieces have permanent homes.** Every piece lives at a stable URL under its section. A series
   lists and orders pieces, so a piece can join a series, move between series, or stand alone
   without its link changing.
3. **Vernacular names, plain subtitles.** Sections use cricket's own language, each with a plain
   label underneath, so they charm regulars and stay clear to newcomers and search engines.
4. **A masthead with signed pieces.** "Wet Wicket" is the publication. Each piece has a byline
   and is written in its author's own first-person voice. Guest writers are welcome later.
5. **Every number traces to a match.** Data pieces link to the matches they draw on and to the
   code that produced them.

## Sections

| Section | Subtitle | URL | What lives here |
|---|---|---|---|
| Series | Deep dives | `/series/` | One hub per series, with an intro and its pieces in reading order |
| The Numbers | Data | `/numbers/` | Data explorations and analysis |
| Classics | Great matches | `/classics/` | Breakdowns of epic matches, told through their key moments |
| The Nets | Games | `/nets/` | Simple browser games |
| The Long Room | Essays | `/long-room/` | Long-form writing |
| Scorebook | Tools | `/scorebook/` | Things you use rather than read: explorers, calculators |
| The Archive | Matches & players | `/matches/` | Every match, player, competition and ground in Cricsheet, rendered from D1 |

Supporting pages: `/` (front page), `/tags/<tag>/`, `/authors/<author>/`, `/glossary/`,
`/about/`, `/rss.xml`.

## URLs

```
/                                         Front page: lead series, latest from each section
/series/                                  All series
/series/rain-rules/                       Series hub
/numbers/who-wins-when-it-rains/          Piece (series: rain-rules, part 2)
/scorebook/rain-hit-matches/              Piece (series: rain-rules, part 1)
/classics/<year>-<short-name>/            e.g. /classics/2005-edgbaston/
/nets/<game>/                             e.g. /nets/beat-the-par/
/archive-<matches|players|places>.xml     Archive sitemaps, listed in /sitemap-index.xml
/long-room/<slug>/
/tags/<tag>/  /authors/<slug>/  /glossary/#<term>

/matches/?fmt=&gender=&rain=&page=        The Archive: every match, newest first
/matches/<cricsheet-id>/                  Scorecard, worm, Manhattan, fall of wickets, partnerships
/players/?q=   /players/<register-id>/    Search; career numbers by format, links out via the Register
/competitions/<slug>/<season>/            e.g. /competitions/indian-premier-league/2023/ ("2023/24" -> "2023-24")
/grounds/<slug>/                          How the ground plays, by format
```

## The Archive

The Archive is data rather than editorial. Its pages are rendered on request from Cloudflare D1
(`export const prerender = false`), while everything else is prerendered. The data comes from
Cricsheet via `pipeline/ingest.py` and is refreshed nightly by `.github/workflows/nightly.yml`.
Editorial pieces link into the Archive for any match, player or ground they mention.

## Content model

**Piece** (`src/content/pieces/<section>/<slug>.mdx`)

| Field | Notes |
|---|---|
| `title`, `dek` | Name and one-sentence summary (used in cards, meta description, OG) |
| `section` | `numbers` · `classics` · `nets` · `long-room` · `scorebook` (taken from the folder) |
| `author` | Author slug |
| `published`, `updated` | Dates |
| `series`, `seriesOrder` | Optional; which series it belongs to and where |
| `tags` | Topic tags: laws, formats, teams, eras, players |
| `matches` | Optional Cricsheet match IDs the piece draws on |
| `presentation` | `article` (prose with the site header) or `app` (full-width interactive piece) |

**Series** (`src/content/series/<slug>.md`): `title`, `dek`, `status` (ongoing / complete),
an intro in the body, and a `featured` flag for the front page.

**Author** (`src/content/authors/<slug>.md`): name, short bio.

**Classics piece.** An `article` piece built from four components in `src/components/classics/`:
`MatchStrip` (scoreline and scorecard link), `ParChase` (the chase against the D/L par),
`ParSheet` (the par for each number of wickets down) and `Moments` (key moments, or any
timeline). Its match data is `src/data/classics/<match id>.json`, written by
`pipeline/build_pieces.py <match id>`, and the piece lists the id in `matches`.

## Front page

1. Lead series: its hub card, plus its latest piece.
2. Latest from each section, one card each.
3. All series.

## First series: Rain Rules

1. *Rain Stopped Play* (Scorebook). Every rain-hit match in the Cricsheet archive.
2. *Who Wins When It Rains* (The Numbers). Rain-free chases replayed under six rain rules.
3. *Someone, Somewhere* (The Long Room). How Duckworth–Lewis came to be.
4. *The D/L Calculator* (Scorebook). Revised targets and par sheets with the Standard Edition.
5. *Beat the Par* (The Nets). Guess the D/L par score for six real chases.
6. *The Wrong Number* (Classics). Durban 2003, and the misread par sheet.
7. Next: more classic rain-affected matches.
