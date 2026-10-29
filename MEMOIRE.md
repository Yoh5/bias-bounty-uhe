# The stratum the scorecard cannot report as missing

**Bias Bounty Mapping Equity Challenge — submitted for *Best Bias Discovery*.**
Zindi username: **[TO FILL IN]**. No leaderboard submission is
associated with this writeup.

Every figure below is computed from the challenge package alone, by three scripts
published with this entry. No additional data source is used, nothing is
reconstructed from removed reference layers, and nothing is random: re-running
returns the same tables.

---

## 1. The discovery

**The only fine-grained urban-heat layer in the challenge package is absent for
30.8% to 62.4% of tracts in every study region, and its absence is concentrated
on tribal communities.**

The strata tables carry a NASA UHE-Daily urban-heat-exposure block
(`uhe_covered`, `uhe_city_name`, `uhe_wbgtmax28_days_per_yr`, and four more
columns). It is the only measure in the package that describes *urban* heat
exposure at tract level. It does not cover every tract:

| region | UHE absent | rural among absent vs covered | tribal among absent vs covered | population without the stratum |
|---|---|---|---|---|
| `eastern-wa` | **62.4%** (259/415) | 54.1% vs 0.6% | 6.2% vs 0.0% | **60.4%** |
| `eastern-ok` | **58.0%** (691/1192) | 58.2% vs 1.8% | **85.8% vs 42.3%** | **60.1%** |
| `northern-ca` | 48.6% (287/591) | 49.5% vs 1.6% | 4.5% vs 0.7% | 44.9% |
| `south-central-tx` | 35.6% (2138/6010) | 45.6% vs 0.4% | — | 34.9% |
| `maricopa-az` | 30.8% (490/1593) | 31.6% vs 0.7% | 6.3% vs 0.5% | 28.9% |

Five regions, one direction, rural concentration ratios of 31× to 114×.

### The mechanism, demonstrated rather than assumed

The layer is **keyed by city**. `uhe_city_name` is populated for **100%** of
covered tracts and **0%** of uncovered ones; `uhe_overlap_frac` has no non-null
value among the uncovered. In Eastern Oklahoma the layer knows **six cities** —
Tulsa, Oklahoma City, Norman, Edmond, Lawton, Fort Smith — and nothing outside
them.

This is not an error by NASA. It is what an urban dataset is. The finding is
that a package assembled **to measure equity** inherits a city-shaped blind
spot, and that nothing in the automated scorecard reveals it.

### Why the automated scorecard cannot surface this

The Bias Score computes five metrics **within** predefined strata. A tract with
no value for a stratum does not produce a "missing" count — it **drops silently
out of the breakdown**, and the metric returns a number for the tracts that
remain.

So the scorecard can report "the coverage gap is larger among rural tracts". It
cannot report "for 58% of this region, 85.8% of them tribal, this stratum does
not exist". The heat disparity it publishes is computed over a population that
systematically excludes the communities the challenge exists to protect.

### And the pattern does not fit the predefined strata

Most of the largest affected tracts are classified **`Urban`** by RUCA. A tract
can be urban and still fall outside the six city polygons the layer knows.

The absence therefore **does not follow rurality — it follows membership of one
of six named cities**. An urban/rural split cannot express this, because *both
sides* of that cut contain uncovered tracts. The stratum that explains the
pattern is one the API does not have: *is this tract inside a UHE city?*

---

## 2. The evidence

Eastern Oklahoma — the Cherokee / Muscogee / Choctaw region, which the challenge
itself labels "Drought + **heat**" — carries the finding.

| | |
|---|---|
| tracts scored | 1 192 |
| without the urban-heat stratum | **691 (58.0%)** |
| of those, tribal | **593** |
| population in uncovered tracts | **2 360 128** |
| tribal areas affected | **26**, totalling **2 013 570 residents** |

**By tribal area** (full list in `resultats/tracts-sans-uhe.csv`):

| area | tracts | population | median SVI |
|---|---|---|---|
| Cherokee OTSA | 131 | 456 814 | 0.658 |
| Creek OTSA | 103 | 334 494 | 0.626 |
| Chickasaw OTSA | 93 | 304 578 | 0.635 |
| Choctaw OTSA | 65 | 216 800 | 0.743 |
| Cheyenne and Arapaho OTSA | 55 | 202 874 | 0.523 |
| Kiowa-Comanche-Apache-Fort Sill Apache OTSA | 37 | 118 594 | 0.589 |
| Citizen Potawatomi Nation-Absentee Shawnee OTSA | 30 | 113 753 | 0.532 |
| Kaw/Ponca joint-use OTSA | 6 | 24 095 | **0.823** |
| Seminole OTSA | 8 | 19 724 | **0.798** |

Across all 26 affected areas, **9 have a median SVI above 0.75** — the most
socially vulnerable quartile — and **25 of 26 above 0.5**. The heat stratum is
missing almost everywhere social vulnerability sits above the national median.

**Named tracts**, so judges reopen exactly these:

| GEOID | tribal area | population | SVI | RUCA class |
|---|---|---|---|---|
| 40143005809 | Cherokee OTSA | 8 362 | 0.296 | Urban |
| 40143006709 | Creek OTSA | 8 244 | 0.280 | Urban |
| 40131050404 | Cherokee OTSA | 7 678 | 0.258 | Urban |
| 40009966200 | Cheyenne and Arapaho OTSA | 7 078 | **0.880** | Urban |
| 40143005805 | Cherokee OTSA | 7 369 | **0.808** | Urban |
| 40027202405 | Citizen Potawatomi Nation-Absentee Shawnee | 6 617 | 0.707 | Rural |

---

## 3. Who is affected, and what it changes

Urban heat exposure is what decides **where cooling centres go**, **which
neighbourhoods get a heat alert first**, and **who is doorknocked before a
forecast event**. Those decisions are made at tract level, from exactly the kind
of layer that is missing here. In the terms this challenge uses: the absence
bears on **emergency dispatch** — which tracts a heat-illness surge is
anticipated in, and where crews are staged before it — and on **disaster
relief** — where a cooling centre, a water distribution point or a wellness
check is placed once an event is under way. It bears less on evacuation
routing, which heat rarely triggers, and we do not claim it does.

A tract with no UHE value cannot be ranked for heat risk by any analysis built
on this package. It is not ranked low — it is **absent from the ranking**, which
is worse, because an absent tract produces no number for anyone to question.

The consequence is specific to these places. Eastern Oklahoma's tribal
statistical areas are designated drought-prone and heat-exposed by the
challenge's own framing, and they are where the layer is most often missing:
**2.0 million people across 26 tribal areas**, including 456 814 in the Cherokee
OTSA alone. Tract `40009966200` (Cheyenne and Arapaho OTSA, 7 078 residents,
SVI 0.880) sits in the most vulnerable 12% nationally and has no urban-heat
value at all.

This is the challenge's own hypothesis, one layer further in: *"Where those gaps
overlap with wildfire corridors, extreme-heat cities, and drought-prone tribal
lands, the consequences can be life-threatening."* The gap we report is not in
the map — it is in the instrument used to decide who the map is failing.

### A negative result we checked, and report

We tested whether uncovered tracts are *also* the hottest, which would have
made a direct life-safety case. **Pooled across the five regions, they are
not.** Using EPHT summer heat-days over the 9 792 scored tracts that carry one
— of 9 801; nine tracts in South-Central Texas have no EPHT value — 19.6% of
tracts without the UHE stratum fall in the top exposure quartile, against 31.0%
of covered ones, a ratio of **0.63×**. The intersection of "no UHE stratum" and
"top heat quartile" is 754 tracts, of which only 3 are tribal.

**That pooled quartile mostly sorts climates rather than tracts, and we say
so.** South-Central Texas and Maricopa are hotter in absolute terms than
Oklahoma, Northern California and Eastern Washington: three of the five regions
have **no tract at all** above the common threshold. Recomputing the quartile
**within each region**, which separates the absence from the climate, the
direction is not uniform:

| region | local threshold (summer heat-days) | top quartile, no UHE | top quartile, with UHE | ratio |
|---|---|---|---|---|
| `south-central-tx` | 16.6 | 12.1% | 32.5% | 0.37× |
| `eastern-ok` | 11.8 | 19.8% | 34.3% | 0.58× |
| `maricopa-az` | 15.3 | 25.3% | 33.4% | 0.76× |
| `eastern-wa` | 11.9 | 32.8% | 16.7% | **1.97×** |
| `northern-ca` | 11.6 | 53.3% | 8.2% | **6.48×** |

In Eastern Washington and Northern California the missing stratum falls
**disproportionately on the locally hottest tracts**. We publish this because an
entry reporting only the pooled figure would be overturned by a judge changing
one line, and because it is the stronger reading of our own finding in two of
the five regions.

The pooled mechanism is nonetheless real: EPHT heat-days run higher in cities
because of the urban heat island, and the UHE layer covers cities. That is why
the two measures disagree — and why neither can stand in for the other.

**This narrows the claim, and we state it narrowed.** The finding is not that
these communities are hotter: pooled they are cooler, and within region it
depends on the region. It is that they **cannot be assessed on urban
heat at all** — any analysis reaching for the package's only urban-heat measure
silently drops 58% of Eastern Oklahoma, 85.8% of that tribal, and reports a
disparity computed on the remainder. An unmeasurable place is not a safe place;
it is a place no number argues for.

---

## 4. What the scorecard should add

Three changes, each a column or a count rather than a new dataset:

1. **Publish stratum coverage beside every metric.** Each of the five metrics
   should report the number of scored tracts it was computed over, and the
   number dropped for want of a stratum value. A metric that silently loses 58%
   of a region reads identically to one that loses none.

2. **Add an `is_uhe_city` boolean.** The pattern we report is invisible to the
   urban/rural split because *both sides* contain uncovered tracts. One boolean
   — is this tract inside a UHE city polygon — would expose it inside the
   existing hazard-exposure breakdown instead of hiding it.

3. **Flag city-keyed layers as such in the data dictionary.** UHE-Daily is
   indexed by city by construction; a user who does not unnest `uhe_city_name`
   has no way to know its coverage is a function of municipal boundaries rather
   than of data quality.

---

## 5. Reproducing this

Everything below is at **https://github.com/Yoh5/bias-bounty-uhe** — the
three scripts, the result tables they produce, and this write-up.

Three scripts, provided data only, no randomness:

```
python src/couverture_strates.py   # coverage of every stratum, all 5 regions
python src/tracts_nommes.py        # the named tracts and tribal areas
python src/quartile_chaleur.py     # the negative result of section 3, both thresholds
```

The first downloads `strata/<region>/<region>-strata-tract-table.parquet` from
the public Source Cooperative repository and caches it; the other two read that
cache. Outputs land in `resultats/couverture-strates.csv`,
`resultats/tracts-sans-uhe.csv` and `resultats/quartile-chaleur.csv`.

Three practical notes that cost us time:

- **Read `GEOID` as text.** Maricopa is FIPS 04 and an integer read eats the
  leading zero, breaking every join. The challenge warns of this; it is worth
  repeating because the failure is silent.
- **The repository returns 403 to urllib's default user agent** while the S3
  listing endpoint does not. An explicit `User-Agent` header fixes it.
- **South-Central Texas carries 6 010 tracts, not the 6 003 the README
  announces.** The 6 010 GEOIDs are distinct, so this is not duplication. Every
  figure here is computed over the tables as delivered, and our scripts print
  the discrepancy rather than silently adopting either count.

---

## 6. What we did not establish

**We could not confirm which heat layer the Bias Score API consumes.** The
challenge page names "NOAA/CDC HeatRisk"; the repository README documents CDC
EPHT and NASA GEHE / UHE-Daily, and does not specify the API's strata. If the
API's heat stratum is drawn from EPHT — which is complete across all five
regions except nine tracts in South-Central Texas — then the finding is that the *complete but
coarse* layer conceals a hole in the *fine-grained* one, rather than that the
API's own stratum is blind. That is a weaker claim than the strongest reading,
and we state it rather than assume the stronger one.

Either way the operative point survives: any analyst reaching for urban-heat
exposure in this package inherits a city-shaped absence that falls on tribal
and non-city communities, and no metric in the scorecard reports it.

**We did not cross this with Overture coverage.** Showing that the blind spot
falls where mapping is already weakest would strengthen the impact argument, and
it requires the 0.9 GB reference package for Eastern Oklahoma. We report what we
verified.

**Two pattern families were deliberately set aside** because the organisers
published them, and restating an organiser's own finding is not a discovery: the
cross-region incomparability of the transport component (Overture/TIGER ratio
0.71 to 1.59) and the exclusion of hospitals (Overture at roughly 12× the
reference).
