"""Le résultat négatif : les tracts privés de la strate ne sont pas les plus chauds.

La trouvaille serait plus spectaculaire si les tracts sans couche de chaleur
urbaine étaient aussi les plus exposés à la chaleur : on aurait un argument
direct de sécurité des personnes. **Ce n'est pas le cas, et ce module le
mesure** plutôt que de passer la question sous silence.

Le contrôle croise deux couches fournies par le paquet :

- `uhe_covered` — la couche NASA UHE-Daily, fine mais indexée par ville, absente
  pour 30,8 % à 62,4 % des tracts selon la région ;
- `epht_heat_days_summer` — le nombre de jours de chaleur estivale CDC EPHT,
  complet partout sauf neuf tracts du Texas.

Et il demande : **parmi les tracts sans UHE, quelle part tombe dans le quart le
plus exposé au sens d'EPHT ?** Si cette part dépassait celle des tracts
couverts, l'absence frapperait les endroits les plus chauds. Mesuré : elle est
**plus basse**, et le module rend le rapport exact.

Le mécanisme est le même que celui qui produit la trouvaille — EPHT compte plus
de jours de chaleur en ville à cause de l'îlot de chaleur urbain, et UHE couvre
les villes. Les tracts non couverts sont, sur cette mesure, plus frais.

**Ce que ça ne retire pas à la trouvaille.** Ces communautés ne sont pas plus
chaudes ; elles sont **inévaluables** sur la chaleur urbaine. Un lieu qu'aucune
mesure ne décrit n'est pas un lieu sûr : c'est un lieu pour lequel aucun chiffre
ne plaide.

**Deux seuils, parce qu'ils ne disent pas la même chose, et que le second
contredit le premier dans deux régions.**

- *Seuil commun* : un quart supérieur calculé sur les cinq régions réunies.
  C'est le chiffre cité dans le mémoire — 19,6 % contre 31,0 %, rapport 0,63.
  Mais le Texas et Maricopa sont en valeur absolue plus chauds que
  l'Oklahoma, la Californie du Nord et Washington : trois régions sur cinq
  n'ont **aucun** tract au-dessus de ce seuil. Ce quart-là trie donc surtout
  des climats, pas des tracts.
- *Seuil local* : un quart supérieur calculé région par région, qui isole
  l'effet de l'absence de la différence de climat. Là, le sens **n'est pas
  uniforme** : trois régions sous 1 (Texas 0,37, Oklahoma 0,58, Maricopa 0,76)
  et deux au-dessus (Washington 1,97, Californie du Nord 6,48).

Les deux sont rendus. Ne publier que le premier reviendrait à donner pour
établi un résultat qu'un juge renverse en changeant une ligne.

**Déterminisme.** Un quantile et des dénombrements, aucun tirage. Relancer rend
les mêmes chiffres. Aucune source externe, aucune couche de référence retirée.

Usage :
    python src/quartile_chaleur.py
    python src/quartile_chaleur.py --mesure epht_heat_days_annual --quantile 0.9
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"

REGIONS = ["eastern-ok", "maricopa-az", "northern-ca",
           "south-central-tx", "eastern-wa"]


def charger(region: str) -> pd.DataFrame:
    chemin = DONNEES / f"strata-{region}.parquet"
    if not chemin.exists():
        raise SystemExit(f"{chemin} absent — lancer d'abord src/couverture_strates.py")
    d = pd.read_parquet(chemin)
    # GEOID en texte : une lecture entière mange le zéro initial des États dont
    # le FIPS commence par 0 et casse toute jointure ultérieure.
    d["GEOID"] = d["GEOID"].astype(str)
    d["region"] = region
    return d


def rassembler(regions: list[str], mesure: str) -> tuple[pd.DataFrame, int]:
    """Les tracts des régions demandées qui portent une valeur de chaleur.

    Rend aussi l'effectif avant filtrage : la différence est le nombre de
    tracts qu'aucun seuil ne peut classer, et il doit être dit.
    """
    tout = pd.concat([charger(r) for r in regions], ignore_index=True)
    avant = len(tout)
    gardes = tout[tout["epht_covered"].astype(bool) & tout[mesure].notna()].copy()
    return gardes, avant


def _rapport(r: dict) -> str:
    """Le rapport, ou « — » quand aucun tract couvert n'atteint le seuil.

    Rendre « nan » ici laisserait croire à une erreur de calcul : c'est au
    contraire l'information que cette région est entièrement sous le seuil.
    """
    v = r["rapport"]
    return f"{v:.2f}x" if v == v else "—"


def comparer(d: pd.DataFrame, mesure: str, seuil: float) -> dict[str, float | int]:
    """Part du quart supérieur chez les non couverts et chez les couverts."""
    haut = d[mesure] >= seuil
    sans = ~d["uhe_covered"].astype(bool)
    intersection = d[sans & haut]
    part_sans = float(haut[sans].mean()) if sans.any() else float("nan")
    part_avec = float(haut[~sans].mean()) if (~sans).any() else float("nan")
    return {
        "tracts": len(d),
        "sans_uhe": int(sans.sum()),
        "part_haut_sans_uhe": part_sans,
        "part_haut_avec_uhe": part_avec,
        "rapport": part_sans / part_avec if part_avec else float("nan"),
        "intersection": len(intersection),
        "intersection_tribale": int(intersection["tribal_any"].astype(bool).sum())
        if "tribal_any" in intersection else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--regions", nargs="*", default=REGIONS)
    ap.add_argument("--mesure", default="epht_heat_days_summer")
    ap.add_argument("--quantile", type=float, default=0.75)
    ap.add_argument("--sortie",
                    default=str(RACINE / "resultats" / "quartile-chaleur.csv"))
    args = ap.parse_args()

    d, avant = rassembler(args.regions, args.mesure)
    seuil = float(d[args.mesure].quantile(args.quantile))

    print(f"{avant} tracts notés, {len(d)} portant une valeur de "
          f"{args.mesure} ({avant - len(d)} sans)")
    print(f"seuil du quantile {args.quantile:.2f} : {seuil:.3f} jours\n")

    global_ = comparer(d, args.mesure, seuil)
    print(f"  sans strate UHE  : {global_['part_haut_sans_uhe']:6.1%} "
          f"dans le quart supérieur  (n={global_['sans_uhe']})")
    print(f"  avec strate UHE  : {global_['part_haut_avec_uhe']:6.1%}")
    print(f"  rapport          : {global_['rapport']:.2f}x "
          f"— {'plus' if global_['rapport'] > 1 else 'moins'} exposés")
    print(f"  intersection     : {global_['intersection']} tracts, dont "
          f"{global_['intersection_tribale']} tribaux\n")

    lignes = [{"perimetre": "toutes régions", "seuil_type": "commun",
               "seuil": seuil, **global_}]

    # D'abord chaque région sous le seuil commun : on voit alors que trois
    # régions n'ont aucun tract au-dessus, donc que ce seuil trie des climats.
    print("sous le seuil commun :")
    for region, part in d.groupby("region"):
        r = comparer(part, args.mesure, seuil)
        lignes.append({"perimetre": region, "seuil_type": "commun",
                       "seuil": seuil, **r})
        print(f"  {region:17} sans {r['part_haut_sans_uhe']:6.1%}  "
              f"avec {r['part_haut_avec_uhe']:6.1%}  "
              f"rapport {_rapport(r):>7}")

    # Puis chaque région contre elle-même, qui sépare l'absence du climat.
    # C'est là que deux régions sur cinq renversent le sens.
    print("\nsous un seuil local à chaque région :")
    for region, part in d.groupby("region"):
        local = float(part[args.mesure].quantile(args.quantile))
        r = comparer(part, args.mesure, local)
        lignes.append({"perimetre": region, "seuil_type": "local",
                       "seuil": local, **r})
        sens = "plus exposés" if r["rapport"] > 1 else "moins exposés"
        print(f"  {region:17} seuil {local:5.1f}  sans {r['part_haut_sans_uhe']:6.1%}  "
              f"avec {r['part_haut_avec_uhe']:6.1%}  "
              f"rapport {_rapport(r):>7}  {sens}")

    sortie = Path(args.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\necrit : {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
