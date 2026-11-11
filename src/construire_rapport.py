"""Assemble le compte rendu PDF a partir des preuves de chaque phase."""

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

from configuration import charger_configuration


INK = colors.HexColor("#172d3e")
TEAL = colors.HexColor("#14646b")
MUTED = colors.HexColor("#526572")
LINE = colors.HexColor("#d5e2e6")
PALE = colors.HexColor("#f1f7f7")


def polices():
    dossier = Path("C:/Windows/Fonts")
    noms = ("segoeui.ttf", "segoeuib.ttf", "consola.ttf")
    if not (dossier / noms[0]).exists():
        dossier = Path("/usr/share/fonts/truetype/dejavu")
        noms = ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSansMono.ttf")
    for nom, fichier in zip(("Rapport", "RapportBold", "RapportMono"), noms):
        pdfmetrics.registerFont(TTFont(nom, str(dossier / fichier)))
    pdfmetrics.registerFontFamily("Rapport", normal="Rapport", bold="RapportBold",
                                  italic="Rapport", boldItalic="RapportBold")


def styles():
    corps = ParagraphStyle("Corps", fontName="Rapport", fontSize=9.4, leading=14,
                           textColor=INK, spaceAfter=7, splitLongWords=True)
    return {
        "corps": corps,
        "h1": ParagraphStyle("Phase", parent=corps, fontName="RapportBold", fontSize=22,
                             leading=27, textColor=TEAL, spaceAfter=13, keepWithNext=True),
        "h2": ParagraphStyle("Question", parent=corps, fontName="RapportBold", fontSize=11.8,
                             leading=15, spaceBefore=7, spaceAfter=5, keepWithNext=True),
        "caption": ParagraphStyle("Figure", parent=corps, fontSize=8, leading=11,
                                  alignment=TA_CENTER, textColor=MUTED, spaceAfter=9),
        "table": ParagraphStyle("Cellule", parent=corps, fontSize=8.4, leading=11.6, spaceAfter=0),
        "th": ParagraphStyle("EnTete", parent=corps, fontName="RapportBold", fontSize=8.4,
                             leading=11.6, textColor=colors.white, spaceAfter=0),
        "mono": ParagraphStyle("Code", parent=corps, fontName="RapportMono", fontSize=8,
                               leading=11, backColor=PALE, spaceBefore=6, spaceAfter=9),
        "kicker": ParagraphStyle("Cours", parent=corps, fontName="RapportBold",
                                 fontSize=12, leading=18, textColor=TEAL),
        "cover": ParagraphStyle("Titre", parent=corps, fontName="RapportBold",
                                fontSize=35, leading=41, textColor=INK, spaceAfter=18),
        "subtitle": ParagraphStyle("SousTitre", parent=corps, fontSize=15, leading=22,
                                   textColor=MUTED, spaceAfter=15),
    }


INLINE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*")


def rendre_inline(texte):
    morceaux, debut = [], 0
    for m in INLINE.finditer(texte):
        morceaux.append(html.escape(texte[debut:m.start()]))
        libelle, lien, code, fort = m.groups()
        if libelle and lien.startswith(("https://", "http://")):
            morceaux.append(f'<link href="{html.escape(lien, quote=True)}" color="#14646b">{html.escape(libelle)}</link>')
        elif libelle:
            morceaux.append(f'{html.escape(libelle)} <font color="#526572" size="7.5">[{html.escape(lien)}]</font>')
        elif code:
            morceaux.append(f'<font name="RapportMono" size="8.2">{html.escape(code)}</font>')
        else:
            morceaux.append(f"<b>{html.escape(fort)}</b>")
        debut = m.end()
    morceaux.append(html.escape(texte[debut:]))
    return "".join(morceaux)


def tableau(lignes, s, largeur):
    corps = []
    for i, ligne in enumerate(lignes):
        cellules = [x.strip() for x in ligne.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cellules):
            continue
        corps.append([Paragraph(rendre_inline(c), s["th" if i == 0 else "table"]) for c in cellules])
    n = len(corps[0])
    proportion = [1.5] + [1] * (n - 1)
    t = Table(corps, repeatRows=1, colWidths=[largeur * x / sum(proportion) for x in proportion], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def page_phase(chemin, s, largeur):
    lignes = chemin.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        if not ligne.strip():
            i += 1
            continue
        if ligne.startswith("|"):
            j = i + 1
            while j < len(lignes) and lignes[j].startswith("|"):
                j += 1
            yield KeepTogether([tableau(lignes[i:j], s, largeur)])
            yield Spacer(1, 8)
            i = j
            continue
        if ligne.startswith("```"):
            j = i + 1
            while j < len(lignes) and not lignes[j].startswith("```"):
                j += 1
            yield Preformatted("\n".join(lignes[i + 1:j]), s["mono"])
            i = j + 1
            continue
        figure = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", ligne)
        if figure:
            img = Image(str(chemin.parent / figure[2]))
            facteur = min(largeur / img.imageWidth, 300 / img.imageHeight)
            img.drawWidth, img.drawHeight = img.imageWidth * facteur, img.imageHeight * facteur
            yield KeepTogether([img, Paragraph(html.escape(figure[1]), s["caption"])])
        elif ligne.startswith("# "):
            yield Paragraph(rendre_inline(ligne[2:]), s["h1"])
        elif ligne.startswith("##"):
            yield Paragraph(rendre_inline(ligne.lstrip("# ")), s["h2"])
        else:
            paragraphe = Paragraph(rendre_inline(ligne), s["corps"])
            suivante = next((l for l in lignes[i + 1:] if l.strip()), "")
            if suivante.startswith("|"):
                paragraphe.keepWithNext = True
            yield paragraphe
        i += 1


def main(nom, matricule, destination):
    polices()
    s = styles()
    graine = charger_configuration()["donnees"]["graine"]
    doc = SimpleDocTemplate(str(destination), pagesize=A4, title="TP de synthèse 2 — Remboursement",
                            author=nom, leftMargin=53, rightMargin=53, topMargin=58, bottomMargin=56)
    story = [
        Spacer(1, 95), Paragraph("DÉPLOIEMENT D’APPLICATIONS INTELLIGENTES · MLOPS", s["kicker"]),
        Spacer(1, 25), Paragraph("TP de synthèse 2<br/>Projet « Remboursement »", s["cover"]),
        Paragraph("De la donnée versionnée au modèle expliqué", s["subtitle"]), Spacer(1, 26),
        tableau(["| Étudiant | Matricule | Graine G |",
                 f"| {nom} | {matricule} | {graine} |"], s, doc.width),
        Spacer(1, 23),
        Paragraph("Ce compte rendu suit les questions A1 à F13. Les noms de fichiers entre crochets renvoient aux preuves du projet livré. Les données brutes et préparées sont suivies par DVC.", s["corps"]),
    ]
    for phase in "abcdef":
        story.append(PageBreak())
        story.extend(page_phase(Path("reports") / f"phase-{phase}.md", s, doc.width))

    def marges(canvas, document):
        largeur, hauteur = A4
        canvas.setFont("Rapport", 8)
        canvas.setFillColor(MUTED)
        if document.page > 1:
            canvas.drawString(53, hauteur - 34, "SYNTHÈSE 2  /  REMBOURSEMENT")
            canvas.drawRightString(largeur - 53, hauteur - 34, matricule)
            canvas.setStrokeColor(LINE)
            canvas.line(53, hauteur - 43, largeur - 53, hauteur - 43)
        canvas.setStrokeColor(LINE)
        canvas.line(53, 42, largeur - 53, 42)
        canvas.drawString(53, 27, "CNOPS · projet de cours")
        canvas.drawRightString(largeur - 53, 27, str(document.page))

    doc.build(story, onFirstPage=marges, onLaterPages=marges)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--nom", required=True)
    cli.add_argument("--matricule", required=True)
    cli.add_argument("--sortie", type=Path, default=Path("compte-rendu.pdf"))
    args = cli.parse_args()
    main(args.nom, args.matricule, args.sortie)
