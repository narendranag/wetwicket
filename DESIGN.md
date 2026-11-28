# DESIGN.md: Wet Wicket

How wetwicket.com looks, recorded from the live code on 2026-11-28. This file replaces the fleet's
house design (`~/claude-computer/claude-global/DESIGN.md`) for everything on this site. For anything
it leaves out, the house file still applies. Sources: `src/styles/global.css` (tokens and site
chrome), `src/styles/data.css` (the Archive), `rain.css`, `replay.css`, `par.css`, `calc.css` (one
per interactive piece), the scoped `<style>` blocks in `src/pages/` and `src/components/`, and
`src/layouts/Base.astro`.

## The idea

A cricket broadsheet's sports pages. Tall condensed uppercase headlines, a plain readable body, and
small monospaced uppercase labels like the type on a scorecard. Cool blue-grey paper, white panels
with hairline borders and no shadows. One accent, a deep blue, for links, the active state and the
thing you pressed. Colour otherwise belongs to the data: the six rain rules, and Team 1 against
Team 2.

This differs from the house design throughout: three webfonts instead of system type, a cool
palette instead of a warm one, flat panels instead of shadowed cards, and blue instead of state
colours. Only the light and dark theme pair, the 2px focus ring with a 2px offset, and the rule
"colour carries meaning, not decoration" are shared.

## Tokens

All on `:root` in `src/styles/global.css`. Dark applies under `prefers-color-scheme: dark`, in one
block; the site follows the system setting and has no theme switch. Components use the variables,
never the hex values. `Base.astro` sets `theme-color` to `--surface` for each scheme (`#ffffff`,
`#172027`), so a phone's browser bar matches the nav bar.

### Surfaces and text

| Token | Light | Dark | For |
| --- | --- | --- | --- |
| `--bg` | `#edf0f2` | `#0f1418` | the page; also insets inside a panel (a formula, an input's fill, a row hover) |
| `--surface` | `#ffffff` | `#172027` | nav bar, cards, panels, tables, the cookie banner |
| `--ink` | `#16202a` | `#e4e9ed` | text |
| `--muted` | `#5b6875` | `#93a1ad` | ledes, labels, meta, axis text |
| `--line` | `#d5dbe0` | `#2a3540` | borders, header rules |
| `--grid` | `#e6eaee` | `#222c35` | rules between table rows, chart gridlines, empty tracks |
| `--accent` | `#1f5f99` | `#6fa8dc` | links, active nav, pressed chips and segments, primary buttons, focus ring |
| `--accent-ink` | `#ffffff` | `#0f1418` | text on `--accent` |
| `--chip` | `#e2e8ed` | `#212c35` | resting fill of chips, segmented controls, step buttons, pills |
| `--likely` | `#8fb3d6` | `#3c5c7a` | "likely" rain-hit (hatched), next to `--accent` "confirmed" |

### Data colours

The rain-rule palette is fixed and in this order everywhere (validated for colour-vision deficiency
in both themes). Never reuse a rule's colour for something else, except the team pair below.

| Token | Light | Dark | Rule |
| --- | --- | --- | --- |
| `--r-se` | `#2a78d6` | `#3987e5` | D/L Standard Edition (2002) |
| `--r-arr` | `#eb6834` | `#d95926` | Average Run Rate |
| `--r-refit` | `#1baf7a` | `#199e70` | the modern refit |
| `--r-mpo` | `#eda100` | `#c98500` | Most Productive Overs |
| `--r-pro` | `#e87ba4` | `#d55181` | D/L Professional Edition (ICC average) |
| `--r-proavg` | `#008300` | `#008300` | D/L Professional Edition (real average) |

- **Teams:** Team 1 is `--r-se` (blue), Team 2 is `--r-arr` (orange), on every match chart, strip
  and swatch.
- **Diverging:** `--pos` (`#2a78d6` / `#3987e5`), `--neg` (`#e34948` / `#e66767`), `--mid`
  (`#f0efec` / `#383835`). `--neg` doubles as the error and wicket colour. `--mid` is the
  diverging scale's neutral, kept for a diverging heatmap.
- **Sequential blues:** `--w0` … `--w8` (light runs dark to pale, dark reverses it). Reserved for
  heatmaps and other sequential scales; nothing uses them yet, and they stay (owner, 2026-11-28).
  Use these rather than inventing a new ramp.

### Shape, space, depth

- **Radius:** 6px for cards, panels, tables, strips and score blocks; 4px for buttons, inputs, step
  buttons and tooltips; 3px for pills and swatches; 999px for chips and segmented controls; 50%
  for the ball markers in Beat the Par. The rule for a new control: a choice among options (a
  filter, a toggle, an example) is a 999px pill; an action or a field (a button, an input, a step
  button) is 4px.
- **Borders:** 1px `--line` on every surface. Stacked stat or score cells sit in a grid with a 1px
  gap over a `--line` background, so the borders read as hairlines (`.stats`, `.scoreline`,
  `.findings`, `.scores`).
- **Shadow:** none, except the cookie banner (`0 -4px 16px rgb(0 0 0 / .08)`). Depth comes from
  `--surface` on `--bg` and the hairline.
- **Spacing:** no fixed grid; the values in use are 4, 6, 8, 10, 12, 14, 16, 18, 22, 28 and 40px.
  Panel padding 16–18px (22–26px for a feature card), gaps 18–22px between panels, 28–44px between
  page blocks.
- **Width:** 1180px for the site chrome, editorial pages, the Archive, Rain Stopped Play and the
  calculator; 1040px for Who Wins When It Rains; 760px for Beat the Par. 20px side padding.
  Reading text at 68ch, ledes at 62–70ch.
- **Hit targets:** 44px for the game's step and submit buttons. On touch (`@media (pointer:
  coarse)`), chips, segment buttons, nav and Archive-nav links, the Archive search and the pieces'
  inputs and selects are at least 40px; with a mouse they keep their compact size (about 30px).

## Type

Three webfonts from Google Fonts, loaded in `Base.astro` with `display=swap` (a page may pass its own
`fonts` query, none does today):

| Token | Family | Weights loaded | Fallback |
| --- | --- | --- | --- |
| `--display` | Barlow Condensed | 500, 600, 700 | `"Arial Narrow", sans-serif` |
| `--body` | Source Sans 3 | 400, 400 italic, 600 | `"Segoe UI", system-ui, sans-serif` |
| `--mono` | IBM Plex Mono | 400, 500 | `ui-monospace, Menlo, monospace` |

- **Display** is always uppercase, with letter-spacing 0.01–0.04em, line-height 0.85–1.1, and
  `text-wrap: balance` on headlines.
- **Mono** is for labels (uppercase, 11–13px, letter-spacing 0.04–0.08em, weight 500 or 600), dates,
  and figures in tables and charts.
- **Figures** use `font-variant-numeric: tabular-nums` wherever they line up: scores, tables, stats.

| Role | Style |
| --- | --- |
| Home masthead | display 700, `clamp(56px, 12vw, 128px)` / 0.85, 3px `--ink` rule below |
| Page title (h1) | display 700, `clamp(40px, 7vw, 68px)` / 0.95 (pieces up to 76px; Archive 34–58px) |
| The one big figure (D/L target, the game's call) | display 700, `clamp(72px, 12vw, 112px)` / 0.85 |
| Score | display 700, 34–60px, tabular |
| Stat figure | display 700, 38px |
| Section head (h2) | display 700, 26–30px, letter-spacing 0.02em |
| Card / panel title | display 700, 22–24px |
| Sub-head (h3, legend) | display 600, 20–22px, letter-spacing 0.04em |
| Nav section name | display 600, 17px |
| Lede | body 400, 18–19px, `--muted` |
| Body | body 400, 16px / 1.6; prose 18px / 1.7 |
| Card text, table cells | body, 14–15px |
| Kicker, eyebrow, crumbs, table head, field label | mono 500, 11–12px, uppercase, `--muted` |
| Notes, captions, legends | body, 13–14px, `--muted` |
| Buttons, chips | body 600, 14–16px |

Bold is weight 600, never 700, in body text.

## Components

**Where styles live.** `global.css` holds the tokens, the site chrome and every shared component:
`.kicker`/`.eyebrow`, `.chip`/`.chips`, `.seg`, `.swatch`, `.t1`/`.t2`, `.legend`, `.panel`,
`.muted`, `.lede`, `.hint`, `.card`. A piece's own stylesheet (`rain.css`, `replay.css`, `par.css`,
`calc.css`) holds only what is unique to it, and every selector in it is scoped under the piece's
root class (`.app-rain`, `.app-replay`, `.app-par`, `.app-calc`), so nothing reaches the nav, the
footer or another piece. A new piece gets its own `.app-<name>` root and follows the same rule.
`data.css` holds the Archive's own components.

- **Site nav** (`Base.astro`): a `--surface` bar with a `--line` rule under it. The wordmark (a
  blue raindrop with a ball's stitched seam, then "WET WICKET" in display 700 22px), then each
  section as two lines: the vernacular name in display (The Nets) over its plain name in 10.5px
  mono (Games). The current section gets a 2px `--accent` underline. The list scrolls sideways on a
  phone.
- **Footer:** a `--line` rule, muted 13.5px text: what Wet Wicket is, links, the Cricsheet credit and
  licence, "not affiliated with the ICC", and the "Cookie choice" link-button.
- **Cookie banner:** fixed to the bottom, `--surface`, one question in plain words, "Allow" (primary)
  and "No thanks".
- **Page head:** kicker (mono, linking the section), h1, a muted lede, a byline ("By **Name** ·
  date") on pieces.
- **Series bar:** under the nav on a series piece: kicker, then the parts in order, the current
  one in `--ink` 600, the others as `--accent` links.
- **Card** (`.card`, `PieceCard`): `--surface`, 1px `--line`, radius 6, padding 18; mono meta
  line, display title, muted text. Hover turns the border `--accent`. Laid out in an auto-fill grid,
  280px minimum.
- **Lead story** (home): one wide card, copy on the left, the numbered parts on the right, each a
  `--bg` row with a big `--accent` display numeral.
- **Panel** (`.panel`, `.figure`, `fieldset`): the card's box with a display head and a legend; holds
  a chart, a table or form fields.
- **Stat strip / scoreline:** cells divided by hairlines; a mono uppercase label, a big display
  figure, a muted line under it.
- **Table:** mono uppercase 11px heads over a `--line` rule; rows divided by `--grid`; figures
  right-aligned and tabular; links in `--ink` with a `--line` underline that turns `--accent` on
  hover. Wide tables scroll inside their panel; long ones get a sticky head.
- **Match row** (`MatchRow`): a grid of a mono date, the teams in 600, the format in mono, the result
  muted on the next line; `--bg` on hover; one column under 560px.
- **Chip:** a 999px pill on `--chip` with a `--line` border, body 600 14px, padding 7px 12px.
  Hover turns the border `--accent`. Pressed or current: `--accent` fill, `--accent-ink` text. Used
  for filters and examples.
- **Kicker / eyebrow:** mono 500 12px, letter-spacing 0.08em, uppercase, `--muted`; the two class
  names are the same style.
- **Segmented control** (`.seg`): chips joined in one 999px track; the pressed segment `--accent`.
- **Buttons:** primary is `--accent` fill, radius 4, body 600 14–16px. Secondary is `--chip` with a
  `--line` border. Quiet actions ("Clear filters", "Add a stoppage") are underlined `--accent` text.
- **Inputs:** radius 4, 1px `--line`, `--bg` fill inside a panel; figures in mono (calculator) or
  display (the game).
- **Pill / badge:** mono 600 11px uppercase on `--chip`, radius 3; "Rain" and "Confirmed" on
  `--accent`; "Likely" hatched in `--likely`; "Provisional" on `--chip`.
- **Tooltip:** inverted (`--ink` fill, `--bg` text), radius 4, 12.5px.
- **Focus:** `outline: 2px solid var(--accent); outline-offset: 2px` on `:focus-visible`.
- **Data credit** (`DataCredit`): a bordered `--surface` note at the foot of every page that uses
  Cricsheet's data.
- **Classics pieces:** `MatchStrip` (venue line, two team blocks with swatches and big scores),
  `ParChase` (the chase against par as an SVG line chart), `ParSheet` (the par table, the hit cell in
  `--accent`), `Moments` (a timeline of over numbers and short display heads).

## Charts

Hand-drawn SVG in Astro components (`src/components/data/`, `classics/`) and in `public/assets/*.js`.
No chart library.

- Axis and tick labels: mono 11px, `--muted`. Direct labels: body 600 12–13px in `--ink` or the
  series colour. End values: display 700 20px.
- Gridlines in `--grid`, axes in `--line`. Charts scale to the panel's width (`width: 100%`).
- Series colours only from the data tokens above. Swatches are 10–12px squares, radius 2–3. A
  dashed line means "projected" or "par", a solid line "actual".
- Worm, Manhattan, rain by month and scores by year are the stock Archive charts.

## Motion

Almost none: background and colour transitions of .15s on chips, country rows, buttons and the
game's balls, only under `prefers-reduced-motion: no-preference`.

## Imagery

No photographs or illustrations. The only drawn mark is the wordmark's raindrop and seam
(`public/assets/favicon.svg`, `#1f5f99` with a white seam; inline in the nav it uses `--accent` and
`--surface`). The pictures are the charts and the numbers set large.

## Words

- **Voice:** a signed piece is in its author's first person, warm and exact, for people who already
  love the game. Cricket's own words are used without apology (par, DLS, the follow-on); the
  glossary explains them.
- **Section names** are vernacular with a plain subtitle: The Numbers (Data), Classics, The Nets
  (Games), The Long Room (Essays), Scorebook (Tools), The Archive (Matches & players), Series (Deep
  dives).
- **Interface text** is short and plain, in sentence case; the uppercase belongs to the type, not
  the words. Questions are asked as questions ("May Google Analytics set a cookie…?"), buttons are
  verbs or plain answers ("Allow", "No thanks", "Clear filters", "Add a stoppage").
- **Honesty about the data:** credit Cricsheet wherever its data appears, mark provisional matches as
  "Provisional", and say that the Professional Edition is Chris Baker's 2011 reconstruction wherever
  it is shown.

## Drift to decide

None open. The first audit's items were settled by the owner on 2026-11-28: the unused sequential
and diverging tokens are kept (see Data colours); the rest were fixed and are recorded above.

Still different between files, deliberately: table cell padding (each table is sized for its
content), and `MatchStrip.astro`'s own copy of the team swatches (a scoped style in a Classics
component).
