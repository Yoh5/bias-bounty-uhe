"""Nommer les tracts privés de la strate chaleur, et dire qui y vit.

Le critère *Evidence* du prix pèse **25 %** et demande que « les tracts ou zones
soient nommés, les comparaisons solides, et la taille de la disparité
quantifiée ». Un pourcentage ne le satisfait pas : il faut des identifiants que
les juges puissent rouvrir.

Ce module produit cette liste pour Eastern Oklahoma — la région Cherokee /
Muscogee / Choctaw, que le défi étiquette « Drought + **heat** » — en croisant
`uhe_covered` avec `aiannh_name`, le nom de l'aire tribale porté par la table de
strates fournie.

**Déterminisme.** Du dénombrement et une jointure, aucun tirage. Relancer rend
le même tableau.

Usage :
    python src/tracts_nommes.py
    python src/tracts_nommes.py --region eastern-ok --top 15
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"


def charger(region: str) -> pd.DataFrame:
    chemin = DONNEES / f"strata-{region}.parquet"
    if not chemin.exists():
        raise SystemExit(f"{chemin} absent — lancer d'abord src/couverture_strates.py")
    d = pd.read_parquet(chemin)
    # GEOID en texte : une lecture entière mange le zéro initial des États dont
    # le FIPS commence par 0 et casse toute jointure ultérieure.
    d["GEOID"] = d["GEOID"].astype(str)
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", default="eastern-ok")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--sortie", default=str(RACINE / "resultats" / "tracts-sans-uhe.csv"))
    args = ap.parse_args()

    d = charger(args.region)
    d["uhe_ok"] = d["uhe_covered"].astype(bool)
    d["tribal"] = d["tribal_any"].astype(bool)

    sans = d[~d.uhe_ok]
    print(f"=== {args.region} : {len(d)} tracts notes ===")
    print(f"  sans strate de chaleur urbaine : {len(sans)} ({len(sans)/len(d):.1%})")
    print(f"  dont tribaux                   : {int(sans.tribal.sum())} "
          f"({sans.tribal.mean():.1%} des non couverts, "
          f"contre {d[d.uhe_ok].tribal.mean():.1%} des couverts)")
    print(f"  population concernee           : {int(sans['pop_total'].sum()):,}".replace(",", " "))

    # Par aire tribale : c'est le niveau auquel un lecteur reconnait la
    # communaute, et celui auquel une decision de secours se prend.
    tribaux = sans[sans.tribal & sans["aiannh_name"].notna()]
    if len(tribaux):
        par_aire = (tribaux.groupby("aiannh_name")
                    .agg(tracts=("GEOID", "size"),
                         population=("pop_total", "sum"),
                         svi_median=("svi_overall", "median"))
                    .sort_values("population", ascending=False))
        print(f"\n=== Aires tribales dont des tracts n'ont aucune strate chaleur ===")
        print(f"   {'aire':46} {'tracts':>7} {'population':>12} {'SVI med':>8}")
        for nom, r in par_aire.head(args.top).iterrows():
            print(f"   {str(nom)[:46]:46} {int(r.tracts):7} "
                  f"{int(r.population):12,} {r.svi_median:8.3f}".replace(",", " "))
        print(f"\n   {len(par_aire)} aires au total, "
              f"{int(par_aire.population.sum()):,} habitants".replace(",", " "))

    # Les tracts eux-memes, pour que les juges rouvrent exactement les memes.
    cols = [c for c in ("GEOID", "aiannh_name", "aiannh_kind", "pop_total",
                        "ur_class", "svi_overall", "tribal_pct") if c in d.columns]
    nommes = tribaux[cols].sort_values("pop_total", ascending=False)
    print(f"\n=== Les {min(args.top, len(nommes))} plus peuples, nommes ===")
    print(f"   {'GEOID':13} {'aire tribale':34} {'pop':>7} {'SVI':>7}  classe")
    for _, r in nommes.head(args.top).iterrows():
        print(f"   {r['GEOID']:13} {str(r.get('aiannh_name'))[:34]:34} "
              f"{int(r['pop_total']):7} {r.get('svi_overall', float('nan')):7.3f}  "
              f"{r.get('ur_class')}")

    sortie = Path(args.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    nommes.to_csv(sortie, index=False)
    print(f"\necrit : {sortie}  ({len(nommes)} tracts tribaux sans strate chaleur)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
