"""Quelles strates manquent, où, et pour qui.

Le barème d'équité du défi décline cinq métriques **à l'intérieur** de strates
prédéfinies : urbain/rural, vulnérabilité sociale, vulnérabilité climatique,
tribal, exposition aux aléas. Il peut donc dire « le déficit de couverture est
plus fort chez les ruraux ». Il ne peut pas dire **« pour ce tract, cette strate
n'existe pas »** — un tract sans valeur de strate disparaît simplement de la
ventilation, et le barème continue de rendre un chiffre pour les autres.

Ce module mesure cette absence. Pour chaque région et chaque couche de strate,
il compte les tracts non couverts, puis demande **qui** ils sont : ruraux ou
urbains, tribaux ou non, et quelle population ils portent.

**Ce qui rend la question légitime ici.** Les tables de strates sont fournies, et
les colonnes `*_covered` y sont explicites — rien n'est reconstruit, aucune
couche de référence retirée n'est touchée, aucune donnée externe n'est
nécessaire. L'interdiction du défi porte sur la reconstruction des valeurs
cibles ; compter les trous d'une table fournie n'en approche aucune.

**Déterminisme.** Aucun tirage, aucun modèle : du dénombrement. Relancer rend
le même tableau, ce que le règlement exige (« Always set the seed » — ici il n'y
a pas de graine à poser, et c'est mieux).

Usage :
    python src/couverture_strates.py            # télécharge au besoin, puis mesure
    python src/couverture_strates.py --regions maricopa-az eastern-ok
"""

from __future__ import annotations

import argparse
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
DEPOT = ("https://data.source.coop/humane-intelligence/"
         "bias-bounty-mapping-equity-challenge/")

#: Les cinq régions que le README déclare notées, avec le nombre de tracts
#: qu'il annonce — contrôle d'intégrité du téléchargement.
REGIONS = {
    "eastern-ok": 1192,
    "maricopa-az": 1593,
    "northern-ca": 591,
    "south-central-tx": 6003,
    "eastern-wa": 415,
}


def telecharger(cle: str, nom: str, essais: int = 3) -> Path | None:
    """Récupère un fichier du dépôt public, en cache local.

    `User-Agent` explicite : le dépôt rend **403** à l'agent par défaut
    d'`urllib`, alors que le listage passe. Une heure perdue là-dessus.
    """
    DONNEES.mkdir(exist_ok=True)
    dest = DONNEES / nom
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    for i in range(essais):
        try:
            req = urllib.request.Request(DEPOT + cle, headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=120) as r:
                dest.write_bytes(r.read())
            return dest
        except Exception as e:  # noqa: BLE001
            if i == essais - 1:
                print(f"   echec {nom} : {type(e).__name__} {str(e)[:90]}")
                return None
            time.sleep(4)
    return None


def charger(region: str) -> pd.DataFrame | None:
    nom = f"strata-{region}.parquet"
    chemin = telecharger(
        f"strata/{region}/{region}-strata-tract-table.parquet", nom)
    if chemin is None:
        return None
    # GEOID en texte : Maricopa est en FIPS 04, et une lecture entière mange le
    # zéro initial puis casse toutes les jointures. Le défi le signale.
    d = pd.read_parquet(chemin)
    d["GEOID"] = d["GEOID"].astype(str)
    d["region"] = region
    return d


def colonnes_de_couverture(d: pd.DataFrame) -> list[str]:
    """Les colonnes booléennes qui disent si une couche couvre le tract."""
    out = []
    for c in d.columns:
        if not c.endswith("_covered"):
            continue
        valeurs = set(pd.unique(d[c].dropna()))
        if valeurs <= {True, False, 0, 1}:
            out.append(c)
    return out


def _part(serie: pd.Series) -> float:
    return float(serie.mean()) if len(serie) else float("nan")


def auditer(d: pd.DataFrame) -> pd.DataFrame:
    """Par couche : combien manquent, et chez qui.

    On rapporte la part de ruraux et de tribaux **parmi les non couverts** et
    **parmi les couverts**, plutôt qu'un seul pourcentage : un strate peut être
    rural à 30 % simplement parce que la région l'est. C'est l'écart entre les
    deux qui dit quelque chose.
    """
    rural = (d["ur_class"].astype(str).str.lower() == "rural") if "ur_class" in d else None
    tribal = d["tribal_any"].astype(bool) if "tribal_any" in d else None
    pop = d["pop_total"] if "pop_total" in d else None

    lignes = []
    for col in colonnes_de_couverture(d):
        ok = d[col].astype(bool)
        manquants = (~ok).sum()
        if manquants == 0:
            continue
        ligne = {
            "couche": col.removesuffix("_covered"),
            "tracts": len(d),
            "manquants": int(manquants),
            "part_manquante": manquants / len(d),
        }
        if rural is not None:
            ligne["rural_chez_manquants"] = _part(rural[~ok])
            ligne["rural_chez_couverts"] = _part(rural[ok])
        if tribal is not None:
            ligne["tribal_chez_manquants"] = _part(tribal[~ok])
            ligne["tribal_chez_couverts"] = _part(tribal[ok])
        if pop is not None and pop.sum() > 0:
            ligne["pop_manquante"] = int(pop[~ok].sum())
            ligne["part_pop_manquante"] = float(pop[~ok].sum() / pop.sum())
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--regions", nargs="*", default=list(REGIONS))
    ap.add_argument("--sortie", default=str(RACINE / "resultats" / "couverture-strates.csv"))
    args = ap.parse_args()

    morceaux = []
    for region in args.regions:
        print(f"=== {region} ===")
        d = charger(region)
        if d is None:
            continue
        attendu = REGIONS.get(region)
        etat = "conforme" if attendu == len(d) else f"ATTENDU {attendu}"
        print(f"   {len(d)} tracts, {len(d.columns)} colonnes  ({etat})")
        a = auditer(d)
        if a.empty:
            print("   toutes les couches couvrent tous les tracts")
            continue
        a.insert(0, "region", region)
        morceaux.append(a)
        for _, r in a.sort_values("part_manquante", ascending=False).iterrows():
            bout = (f"   {r['couche']:16} manque {r['manquants']:5} "
                    f"({r['part_manquante']:5.1%})")
            if "rural_chez_manquants" in r:
                bout += (f"  rural {r['rural_chez_manquants']:5.1%} vs "
                         f"{r['rural_chez_couverts']:5.1%}")
            if "tribal_chez_manquants" in r:
                bout += (f"  tribal {r['tribal_chez_manquants']:5.1%} vs "
                         f"{r['tribal_chez_couverts']:5.1%}")
            if "part_pop_manquante" in r:
                bout += f"  pop {r['part_pop_manquante']:5.1%}"
            print(bout)
        print()

    if not morceaux:
        print("(rien a rapporter)")
        return 1
    tout = pd.concat(morceaux, ignore_index=True)
    sortie = Path(args.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    tout.to_csv(sortie, index=False)
    print(f"ecrit : {sortie}  ({len(tout)} lignes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
