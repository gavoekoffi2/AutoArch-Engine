# SPDX-License-Identifier: LGPL-2.1-or-later
"""AI-powered design review.

Serialises a compact summary of the active document (quantities,
opening ratios, orientation, spans) and asks the LLM to flag obvious
issues: missing natural light, overly narrow corridors, unsealed
rooms, code-relevant concerns, cost outliers.
"""

import FreeCAD

from ArxioAITools import ai
from ArxioAITools import estimate as aa_estimate


SYSTEM_PROMPT = """Tu es Arxio AI, architecte conseil expérimenté.

On te donne un RÉSUMÉ STRUCTURÉ d'un projet BIM. Tu dois faire une
RELECTURE CRITIQUE et CONCISE en français, organisée en sections :

1. Points forts (1 à 3 bullets)
2. Alertes fonctionnelles (ventilation, éclairage naturel, circulations,
   proportions des pièces, accessibilité PMR)
3. Alertes réglementaires potentielles (isolation, garde-corps,
   ouvertures de secours, RE2020 / thermique, normes locales)
4. Optimisations budgétaires (matériaux, ratios, surfaces à reconsidérer)
5. Prochaines étapes recommandées (3 actions concrètes)

Sois direct, factuel, actionable. Pas de blabla. Utilise le markdown
léger (gras, listes). Longueur totale : 250 à 400 mots.
"""


def _summarise_document(doc):
    """Return a compact text summary suitable to feed the LLM."""
    report = aa_estimate.run(doc)
    q = report["quantities"]
    prices = report["prices"]

    # Count BIM object kinds
    kinds = {}
    for obj in doc.Objects:
        ifc = getattr(obj, "IfcType", "")
        if ifc:
            kinds[ifc] = kinds.get(ifc, 0) + 1

    kind_lines = "\n".join(f"  - {k}: {v}" for k, v in sorted(kinds.items()))
    if not kind_lines:
        kind_lines = "  (aucun objet BIM détecté)"

    summary = (
        f"Projet FreeCAD — document: {doc.Label}\n"
        f"Objets BIM par type:\n{kind_lines}\n\n"
        f"Quantitatif:\n"
        f"  - Murs: {q['wall_m3']:.2f} m³\n"
        f"  - Dalles: {q['slab_m3']:.2f} m³\n"
        f"  - Toiture: {q['roof_m2']:.2f} m²\n"
        f"  - Fenêtres: {q['windows']}\n"
        f"  - Portes: {q['doors']}\n\n"
        f"Coût estimé: {report['total_cost']:.0f} {prices['currency']}\n"
        f"Nombre total d'objets dans le document: {len(doc.Objects)}\n"
    )
    return summary


def review(doc):
    """Ask the LLM to review the active document. Returns the text report."""
    summary = _summarise_document(doc)
    prompt = (
        "Voici le résumé du projet à relire. Applique ta grille d'analyse:\n\n"
        f"```\n{summary}\n```"
    )
    return ai.ask(prompt, system=SYSTEM_PROMPT)


def show_review(text):
    """Display the review in a scrollable Qt window, or the console."""
    FreeCAD.Console.PrintMessage(
        "\n======== Arxio AI — Revue de conception ========\n"
        f"{text}\n"
        "================================================\n\n"
    )
    try:
        from PySide import QtWidgets
    except ImportError:  # pragma: no cover
        return

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle("Arxio AI — Revue de conception")
    dlg.resize(640, 540)
    layout = QtWidgets.QVBoxLayout(dlg)
    browser = QtWidgets.QTextBrowser()
    browser.setOpenExternalLinks(True)
    browser.setMarkdown(text)
    layout.addWidget(browser)
    close = QtWidgets.QPushButton("Fermer")
    close.clicked.connect(dlg.accept)
    layout.addWidget(close, alignment=0)
    dlg.exec_()
