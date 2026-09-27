# Wet Wicket

A loving exploration of cricket, by a cricket lover for cricket lovers: data explorations,
breakdowns of epic matches, browser games, essays and tools. Built with [Astro](https://astro.build)
and deployed as a static site on Cloudflare Pages.

The site's structure (series, sections, URLs and content model) is described in
[docs/information-architecture.md](docs/information-architecture.md).

## Running the site

```sh
npm install
npm run dev        # http://localhost:4321
npm run build      # static output in dist/
```

Content lives in `src/content/`:

- `series/`: one Markdown file per series.
- `pieces/<section>/<slug>.mdx`: every piece, published at `/<section>/<slug>/`. Sections are
  `numbers`, `classics`, `nets`, `long-room` and `scorebook`.
- `authors/`: bylines.

Interactive pieces are Astro components in `src/components/apps/`, with their scripts in
`public/assets/` and their data in `public/data/`.

## The data pipeline

The Rain Rules series is built from [Cricsheet](https://cricsheet.org/)'s ball-by-ball archive.
The pipeline is Python and writes the JSON files the site reads.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
mkdir -p data/raw && curl -L -o data/raw/all_json.zip https://cricsheet.org/downloads/all_json.zip
unzip -q data/raw/all_json.zip -d data/raw/all_json

.venv/bin/python pipeline/flag_rain.py       # mark rain-affected matches
.venv/bin/python pipeline/extract_overs.py   # over-by-over innings states
.venv/bin/python pipeline/simulate.py        # replay chases under each rain rule
.venv/bin/python pipeline/analyze.py         # bias measures -> data/analysis.json
.venv/bin/python pipeline/build_site.py      # -> public/data/*.json
.venv/bin/python pipeline/test_rain_rules.py # ICC worked examples
```

| Rule | Source |
|---|---|
| Average Run Rate, Most Productive Overs | Historical playing conditions |
| D/L Standard Edition | ICC playing conditions, 2002 resource table (`data/reference/`) |
| D/L Professional Edition | Duckworth & Lewis (2004), as reconstructed by C. Baker (2011) |
| D/L refit | Duckworth & Lewis's model refitted to 2015–2026 Cricsheet first innings |

The current DLS (Stern) edition is available only in ICC software and is not reproduced here.
See `data/reference/SOURCES.md` for every source.

## Credits and licences

Match data © Cricsheet, used under the
[Open Data Commons Attribution License](https://opendatacommons.org/licenses/by/1-0/).
Wet Wicket is independent and not affiliated with the ICC or the authors of the DLS method.

Code is released under the MIT License.
