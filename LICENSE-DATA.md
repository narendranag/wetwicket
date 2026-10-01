# Data licence

The cricket data in this repository is offered under the
[Open Data Commons Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/)
(ODC-By). You may copy, share, adapt and build on it, including commercially,
provided you attribute it as set out below and keep this notice with it.

This file covers the data only. The code, design and writing in the repository
are covered by [`LICENSE`](LICENSE) and are not open source.

## What it covers

- **Cricsheet's data.** The ball-by-ball match files and the Cricsheet Register
  are © [Cricsheet](https://cricsheet.org/) (Stephen Rushe) and are made
  available by Cricsheet under ODC-By 1.0. They are downloaded by the pipeline
  into `data/raw/` and are not altered.
- **Wet Wicket's derived datasets.** The files in `public/data/`, the tables
  the pipeline writes into `data/`, and the contents of the Archive database
  are produced from Cricsheet's data. They are offered under the same licence.

## What it does not cover

- `data/reference/`. These tables are transcribed from published playing
  conditions and papers by other authors. Their sources are listed in
  [`data/reference/SOURCES.md`](data/reference/SOURCES.md), and Wet Wicket
  grants no licence over them.
- Anything that is not data. See [`LICENSE`](LICENSE).

## How to attribute

If you use Cricsheet's data, credit Cricsheet:

> Match and player data from [Cricsheet](https://cricsheet.org/) by Stephen
> Rushe, used under the Open Data Commons Attribution License 1.0.

If you use a dataset that Wet Wicket derived, credit both:

> Derived by [Wet Wicket](https://wetwicket.com/) from data by
> [Cricsheet](https://cricsheet.org/) (Stephen Rushe), used under the Open Data
> Commons Attribution License 1.0.

Wet Wicket is independent and is not affiliated with Cricsheet, the ICC or the
authors of the DLS method.
