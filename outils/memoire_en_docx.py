# -*- coding: utf-8 -*-
"""Rendre MEMOIRE.md en .docx déposable, sans retaper le texte.

Le mémoire reste écrit en Markdown : c'est la source unique. Ce script en
fabrique le Word, donc corriger une faute ou remplir le pseudo Zindi se fait
dans le .md et se relance ici — jamais en retouchant le .docx à la main, qui
serait aussitôt périmé.

    python outils/memoire_en_docx.py            # MEMOIRE.md -> MEMOIRE.docx
    python outils/memoire_en_docx.py --sortie X.docx

Le sous-ensemble de Markdown reconnu est exactement celui du mémoire : titres,
paragraphes, tableaux à barres verticales, blocs de code encadrés, filets
horizontaux, et en ligne **gras**, *italique* et `code`. Tout le reste passe
tel quel plutôt que de disparaître silencieusement.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Inches, RGBColor

RACINE = Path(__file__).resolve().parent.parent

CORPS = "Cambria"
TITRES = "Calibri Light"
MONO = "Consolas"

#: Largeur utile : Letter 8,5 po moins deux marges de 1 po.
LARGEUR = Inches(6.5)

GRIS_ENTETE = "EDEDED"


# --------------------------------------------------------------- styles

def preparer(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = CORPS
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CORPS)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15

    for nom, taille, apres, avant in (("Title", 20, 4, 0),
                                      ("Heading 1", 14, 6, 16),
                                      ("Heading 2", 11.5, 4, 12),
                                      ("Heading 3", 10.5, 3, 10)):
        s = doc.styles[nom]
        s.font.name = TITRES
        s.font.size = Pt(taille)
        s.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
        s.font.bold = nom != "Title"
        s.element.rPr.rFonts.set(qn("w:eastAsia"), TITRES)
        s.paragraph_format.space_after = Pt(apres)
        s.paragraph_format.space_before = Pt(avant)
        s.paragraph_format.keep_with_next = True

    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    for cote in ("top", "bottom", "left", "right"):
        setattr(section, f"{cote}_margin", Inches(1))

    pied = section.footer.paragraphs[0]
    pied.alignment = WD_ALIGN_PARAGRAPH.CENTER
    champ = OxmlElement("w:fldSimple")
    champ.set(qn("w:instr"), "PAGE")
    pied._p.append(champ)
    for run in pied.runs:
        run.font.size = Pt(8.5)


def _ombrer(cellule, couleur: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), couleur)
    cellule._tc.get_or_add_tcPr().append(shd)


def _repeter_entete(ligne) -> None:
    trPr = ligne._tr.get_or_add_trPr()
    entete = OxmlElement("w:tblHeader")
    entete.set(qn("w:val"), "true")
    trPr.append(entete)


# ------------------------------------------------------- Markdown en ligne

JETON = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)", re.DOTALL)


def ecrire_en_ligne(paragraphe, texte: str, *, gras=False, italique=False,
                    taille=None) -> None:
    """Pose le texte en découpant **gras**, *italique* et `code`.

    Récursif, parce que le mémoire imbrique : `**\\`Urban\\`**` et
    `**submitted for *Best Bias Discovery*.**` sortaient avec leurs
    astérisques et leurs accents graves affichés.
    """
    for morceau in JETON.split(texte):
        if not morceau:
            continue
        if morceau.startswith("**") and morceau.endswith("**"):
            ecrire_en_ligne(paragraphe, morceau[2:-2], gras=True,
                            italique=italique, taille=taille)
            continue
        if morceau.startswith("*") and morceau.endswith("*"):
            ecrire_en_ligne(paragraphe, morceau[1:-1], gras=gras,
                            italique=True, taille=taille)
            continue
        if morceau.startswith("`") and morceau.endswith("`"):
            run = paragraphe.add_run(morceau[1:-1])
            run.font.name = MONO
            run.font.size = Pt((taille or 10.5) - 1)
        else:
            run = paragraphe.add_run(morceau)
            if taille:
                run.font.size = Pt(taille)
        run.bold = gras or None
        run.italic = italique or None


def _nu(texte: str) -> str:
    """Le texte sans son balisage, pour mesurer une colonne."""
    return re.sub(r"[*`]", "", texte)


# ------------------------------------------------------------- les blocs

def poser_tableau(doc: Document, lignes: list[list[str]]) -> None:
    entete, corps = lignes[0], lignes[1:]
    #: Le mémoire ouvre son tableau clé/valeur par « | | » : un en-tête vide
    #: rendu en gris se lit comme une ligne oubliée. On le retire.
    avec_entete = any(_nu(c).strip() for c in entete)
    if not avec_entete:
        corps = lignes[1:]

    table = doc.add_table(rows=len(lignes) if avec_entete else len(corps),
                          cols=len(entete))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Largeur proportionnelle au contenu, mais jamais inférieure au plus long
    # mot insécable de la colonne : un GEOID de onze chiffres coupé en deux
    # ligne se lit comme deux nombres.
    poids = []
    for i in range(len(entete)):
        cellules = [_nu(l[i]) for l in lignes if i < len(l)]
        mot = max((len(m) for c in cellules for m in c.split()), default=1)
        poids.append(max(mot + 3, min(40, max(len(c) for c in cellules))))
    total = sum(poids)
    largeurs = [int(LARGEUR.emu * p / total) for p in poids]

    if avec_entete:
        for i, (titre, cellule) in enumerate(zip(entete, table.rows[0].cells)):
            cellule.width = largeurs[i]
            _ombrer(cellule, GRIS_ENTETE)
            p = cellule.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            ecrire_en_ligne(p, titre, gras=True, taille=9)
        _repeter_entete(table.rows[0])

    for valeurs, ligne in zip(corps, table.rows[1:] if avec_entete else table.rows):
        for i, cellule in enumerate(ligne.cells):
            cellule.width = largeurs[i]
            p = cellule.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            ecrire_en_ligne(p, valeurs[i] if i < len(valeurs) else "", taille=9)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def poser_code(doc: Document, lignes: list[str]) -> None:
    for texte in lignes:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Inches(0.25)
        run = p.add_run(texte)
        run.font.name = MONO
        run.font.size = Pt(9)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def poser_filet(doc: Document) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    bordure = OxmlElement("w:pBdr")
    bas = OxmlElement("w:bottom")
    bas.set(qn("w:val"), "single")
    bas.set(qn("w:sz"), "6")
    bas.set(qn("w:color"), "BFBFBF")
    bordure.append(bas)
    p._p.get_or_add_pPr().append(bordure)


# ---------------------------------------------------------------- lecture

def _est_separateur(ligne: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|", ligne.strip()))


def _cellules(ligne: str) -> list[str]:
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def convertir(source: Path, sortie: Path) -> tuple[int, int]:
    doc = Document()
    preparer(doc)

    lignes = source.read_text(encoding="utf-8").splitlines()
    i, tableaux = 0, 0
    tampon: list[str] = []

    def vider() -> None:
        if tampon:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            ecrire_en_ligne(p, " ".join(tampon))
            tampon.clear()

    while i < len(lignes):
        ligne = lignes[i]
        nu = ligne.strip()

        if not nu:
            vider()
        elif nu.startswith("```"):
            vider()
            i += 1
            bloc = []
            while i < len(lignes) and not lignes[i].strip().startswith("```"):
                bloc.append(lignes[i])
                i += 1
            poser_code(doc, bloc)
        elif re.fullmatch(r"-{3,}", nu):
            vider()
            poser_filet(doc)
        elif nu.startswith("#"):
            vider()
            niveau = len(nu) - len(nu.lstrip("#"))
            titre = nu[niveau:].strip()
            style = "Title" if niveau == 1 else f"Heading {min(niveau - 1, 3)}"
            p = doc.add_paragraph(style=style)
            ecrire_en_ligne(p, titre)
        elif nu.startswith("|") and i + 1 < len(lignes) and _est_separateur(lignes[i + 1]):
            vider()
            bloc = [_cellules(nu)]
            i += 2
            while i < len(lignes) and lignes[i].strip().startswith("|"):
                bloc.append(_cellules(lignes[i]))
                i += 1
            poser_tableau(doc, bloc)
            tableaux += 1
            continue
        elif nu.startswith("- ") or nu.startswith("* ") or re.match(r"\d+\.\s", nu):
            vider()
            numerote = bool(re.match(r"\d+\.\s", nu))
            debut = re.sub(r"^\d+\.\s+", "", nu) if numerote else nu[2:]
            # Les lignes suivantes indentées appartiennent à la même puce.
            # Sans ça la moitié de chaque point partait en paragraphe à part,
            # désindentée, sous une puce tronquée.
            suite = [debut]
            while (i + 1 < len(lignes) and lignes[i + 1].strip()
                   and lignes[i + 1][:1] in " \t"
                   and not re.match(r"\s*([-*]\s|\d+\.\s)", lignes[i + 1])):
                i += 1
                suite.append(lignes[i].strip())
            p = doc.add_paragraph(
                style="List Number" if numerote else "List Bullet")
            p.paragraph_format.space_after = Pt(4)
            ecrire_en_ligne(p, " ".join(suite))
        elif nu.startswith(">"):
            vider()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.35)
            ecrire_en_ligne(p, nu.lstrip("> ").strip())
            for run in p.runs:
                run.italic = True
        else:
            tampon.append(nu)
        i += 1

    vider()
    sortie.parent.mkdir(parents=True, exist_ok=True)
    doc.save(sortie)

    mots = sum(len(p.text.split()) for p in doc.paragraphs)
    return mots, tableaux


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--source", default=str(RACINE / "MEMOIRE.md"))
    a.add_argument("--sortie", default=str(RACINE / "MEMOIRE.docx"))
    args = a.parse_args()

    source = Path(args.source)
    if not source.is_file():
        print(f"introuvable : {source}", file=sys.stderr)
        return 1

    mots, tableaux = convertir(source, Path(args.sortie))
    print(f"{args.sortie}\n{mots} mots hors tableaux, {tableaux} tableaux")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
