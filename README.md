# The stratum the scorecard cannot report as missing

Entry for **Best Bias Discovery** — Bias Bounty Mapping Equity Challenge
(Humane Intelligence × Radiant Earth). No leaderboard submission is associated
with this entry.

**The finding.** The only fine-grained urban-heat layer in the challenge package
— NASA UHE-Daily — is absent for **30.8% to 62.4% of tracts in every study
region**, and its absence is concentrated on rural and tribal communities. The
layer is keyed by city: `uhe_city_name` is populated for 100% of covered tracts
and 0% of uncovered ones. In Eastern Oklahoma it knows six cities and nothing
outside them, leaving **691 of 1 192 tracts (58.0%) with no value at all, 85.8%
of them tribal** — 2.36 million residents across 26 tribal statistical areas.

A tract with no value for a stratum does not produce a "missing" count in the
Bias Score: it drops silently out of the breakdown, and the metric returns a
number for the tracts that remain. The scorecard can report that a gap is larger
among rural tracts. It cannot report that for 58% of a region the stratum does
not exist.

The full write-up is **[`MEMOIRE.md`](MEMOIRE.md)** (also provided as
`MEMOIRE.docx`).

## Reproducing it

Python 3.10+ with `pandas` and `pyarrow`. No other dependency, no external data
source, no API key, no randomness — re-running returns the same tables.

```bash
python src/couverture_strates.py   # coverage of every stratum, all 5 regions
python src/tracts_nommes.py        # the named tracts and the tribal areas
python src/quartile_chaleur.py     # the negative result of section 3
```

The first script downloads `strata/<region>/<region>-strata-tract-table.parquet`
for the five regions from the public Source Cooperative repository and caches
them under `donnees/`; the other two read that cache. Results are written to
`resultats/` and the copies produced on our machine are committed, so the
outputs can be compared without re-downloading.

Nothing here touches a removed reference layer, and nothing reconstructs,
approximates or calibrates a leaderboard target. Every figure is a count or a
quantile over the strata tables as delivered.

| file | what it holds |
|---|---|
| `MEMOIRE.md` / `.docx` | the write-up |
| `src/couverture_strates.py` | per region and per stratum: who is missing, and who they are |
| `src/tracts_nommes.py` | the named tracts and tribal areas of Eastern Oklahoma |
| `src/quartile_chaleur.py` | the EPHT heat-quartile check, under both a common and a per-region threshold |
| `resultats/*.csv` | the outputs of the three scripts |
| `outils/memoire_en_docx.py` | renders the write-up to Word; the Markdown is the source |

## Two things worth knowing before you run it

- **Read `GEOID` as text.** Maricopa is FIPS 04 and an integer read eats the
  leading zero, breaking every join. The failure is silent.
- **The data repository returns HTTP 403 to `urllib`'s default user agent**
  while the S3 listing endpoint does not. The download helper sends an explicit
  `User-Agent`.

The source files carry their commentary in French; the write-up, the code
identifiers and this page are in English.
