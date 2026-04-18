# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Arxio AI — Command definitions for the FreeCAD workbench.
#
# Built on FreeCAD (https://www.freecad.org), LGPL-2.1-or-later.
# Copyright (c) 2026 Arxio AI contributors

import os

import FreeCAD
import FreeCADGui

from ArxioAITools import walls as aa_walls
from ArxioAITools import roof as aa_roof
from ArxioAITools import openings as aa_openings
from ArxioAITools import plan as aa_plan
from ArxioAITools import estimate as aa_estimate
from ArxioAITools import project as aa_project
from ArxioAITools import ai_generate as aa_ai_generate
from ArxioAITools import ai_review as aa_ai_review
from ArxioAITools import ai_assistant as aa_ai_assistant
from ArxioAITools import ai_config as aa_ai_config
from ArxioAITools import solar as aa_solar


def _icon(name):
    """Return absolute path to an icon if it exists, else empty string."""
    here = os.path.dirname(__file__)
    for base in (
        os.path.join(FreeCAD.getResourceDir(), "Mod", "ArxioAI", "Resources", "icons"),
        os.path.join(here, "Resources", "icons"),
    ):
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate):
            return candidate
    return ""


def _active_doc_or_new(name="ArxioAI_Project"):
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument(name)
    return doc


def _print_err(msg):
    FreeCAD.Console.PrintError(f"Arxio AI — {msg}\n")


def _print_ok(msg):
    FreeCAD.Console.PrintMessage(f"Arxio AI — {msg}\n")


# ----------------------------------------------------------------------------
# 0. Setup project (Site + Building + ground floor)
# ----------------------------------------------------------------------------
class CmdSetupProject:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_SetupProject.svg"),
            "MenuText": "Initialiser le projet",
            "ToolTip": (
                "Crée Site + Bâtiment + Rez-de-chaussée prêts à recevoir "
                "les murs, dalles et toitures."
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            doc = _active_doc_or_new()
            site, building, floor = aa_project.setup_project(doc)
            _print_ok(
                f"Projet initialisé — Site: {site.Label}, "
                f"Bâtiment: {building.Label}, Étage: {floor.Label}"
            )
        except Exception as exc:  # pragma: no cover - GUI feedback path
            _print_err(f"Initialisation impossible : {exc}")


# ----------------------------------------------------------------------------
# 1. Fast walls from selection (sketches, lines, wires, or faces)
# ----------------------------------------------------------------------------
class CmdFastWalls:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_FastWalls.svg"),
            "MenuText": "Murs rapides (1 clic)",
            "ToolTip": (
                "Transforme les entités 2D sélectionnées (ligne, esquisse, polyligne) "
                "en murs 3D paramétriques. Hauteur/épaisseur configurables."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            sel = FreeCADGui.Selection.getSelection()
            params = aa_walls.read_defaults()
            created = aa_walls.make_walls_from_selection(sel, params)
            if not created:
                _print_err(
                    "Sélectionnez au moins une esquisse, ligne ou polyligne 2D avant "
                    "d'activer cette commande."
                )
                return
            FreeCAD.ActiveDocument.recompute()
            _print_ok(f"{len(created)} mur(s) généré(s).")
        except Exception as exc:
            _print_err(f"Échec création mur : {exc}")


# ----------------------------------------------------------------------------
# 2. Automatic roof + slab from selected walls
# ----------------------------------------------------------------------------
class CmdAutoRoof:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_AutoRoof.svg"),
            "MenuText": "Toiture & dalle auto",
            "ToolTip": (
                "Génère une dalle basse et une toiture (plate ou à pentes) calées "
                "sur l'enveloppe des murs sélectionnés."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            sel = FreeCADGui.Selection.getSelection()
            slab, roof = aa_roof.make_slab_and_roof(sel)
            FreeCAD.ActiveDocument.recompute()
            if slab is None and roof is None:
                _print_err(
                    "Sélectionnez au moins un mur Arch avant d'activer cette commande."
                )
                return
            parts = []
            if slab is not None:
                parts.append(f"dalle {slab.Label}")
            if roof is not None:
                parts.append(f"toiture {roof.Label}")
            _print_ok("Généré : " + ", ".join(parts))
        except Exception as exc:
            _print_err(f"Échec toiture/dalle : {exc}")


# ----------------------------------------------------------------------------
# 3. Place openings (doors/windows) along selected wall
# ----------------------------------------------------------------------------
class CmdPlaceOpenings:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Openings.svg"),
            "MenuText": "Placer portes & fenêtres",
            "ToolTip": (
                "Ajoute une porte (ou une fenêtre) paramétrique sur le mur sélectionné. "
                "Boîte de dialogue pour dimensions et position."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            sel = FreeCADGui.Selection.getSelection()
            if not sel:
                _print_err("Sélectionnez d'abord le mur dans lequel percer l'ouverture.")
                return
            wall = aa_openings.pick_wall(sel)
            if wall is None:
                _print_err("La sélection ne contient pas de mur Arch.")
                return
            created = aa_openings.open_dialog_and_place(wall)
            if created is not None:
                FreeCAD.ActiveDocument.recompute()
                _print_ok(f"Ouverture ajoutée : {created.Label}")
        except Exception as exc:
            _print_err(f"Échec ouverture : {exc}")


# ----------------------------------------------------------------------------
# 4. Auto plan: TechDraw page with top + elevations
# ----------------------------------------------------------------------------
class CmdAutoPlan:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_AutoPlan.svg"),
            "MenuText": "Plans 2D automatiques",
            "ToolTip": (
                "Crée une page TechDraw A3 paysage avec vues en plan et façades "
                "à partir des objets du document. Idéal pour permis de construire."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            page = aa_plan.create_permit_page(FreeCAD.ActiveDocument)
            FreeCAD.ActiveDocument.recompute()
            _print_ok(f"Page de plan générée : {page.Label}")
        except Exception as exc:
            _print_err(f"Échec génération plan : {exc}")


# ----------------------------------------------------------------------------
# 5. Quantity takeoff + cost estimate
# ----------------------------------------------------------------------------
class CmdEstimate:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Estimate.svg"),
            "MenuText": "Métré & devis",
            "ToolTip": (
                "Calcule volumes et surfaces des éléments BIM du document, "
                "puis estime un coût à partir des prix unitaires configurés."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            report = aa_estimate.run(FreeCAD.ActiveDocument)
            aa_estimate.show_report(report)
        except Exception as exc:
            _print_err(f"Échec métré : {exc}")


# ----------------------------------------------------------------------------
# 6. Solar / orientation analysis (no API required)
# ----------------------------------------------------------------------------
class CmdSolarAnalysis:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Solar.svg"),
            "MenuText": "Analyse solaire",
            "ToolTip": (
                "Calcule la position du soleil pour une date/heure/lieu donnés, "
                "puis évalue l'orientation de chaque mur du projet (exposition, "
                "cardinalité, ensoleillement)."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            aa_solar.open_dialog(FreeCAD.ActiveDocument)
        except Exception as exc:
            _print_err(f"Échec analyse solaire : {exc}")


# ----------------------------------------------------------------------------
# 7. AI assistant chat
# ----------------------------------------------------------------------------
class CmdAIAssistant:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Assistant.svg"),
            "MenuText": "Assistant IA",
            "ToolTip": (
                "Ouvre la fenêtre de chat avec Arxio AI. Le contexte du document "
                "actif (quantitatifs, objets) est joint automatiquement."
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            aa_ai_assistant.open_dialog()
        except Exception as exc:
            _print_err(f"Assistant indisponible : {exc}")


# ----------------------------------------------------------------------------
# 8. Generate a building from a natural-language brief
# ----------------------------------------------------------------------------
class CmdGenerateFromBrief:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Generate.svg"),
            "MenuText": "Générer depuis brief",
            "ToolTip": (
                "Décrivez le projet en langage naturel ; l'IA produit un plan "
                "de base (pièces, murs, ouvertures) prêt à être affiné."
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            brief = aa_ai_generate.prompt_brief()
            if not brief:
                return
            doc = _active_doc_or_new("Arxio_Brief")
            _print_ok("Génération en cours — interrogation du modèle IA…")
            FreeCADGui.updateGui() if hasattr(FreeCADGui, "updateGui") else None
            spec = aa_ai_generate.generate_spec(brief)
            summary = aa_ai_generate.apply_spec(doc, spec)
            _print_ok(
                f"Projet généré : {summary['project_name']} — "
                f"{len(summary['rooms'])} pièce(s), {summary['openings']} ouverture(s)."
            )
        except Exception as exc:
            _print_err(f"Génération impossible : {exc}")


# ----------------------------------------------------------------------------
# 9. AI design review
# ----------------------------------------------------------------------------
class CmdDesignReview:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Review.svg"),
            "MenuText": "Revue IA du projet",
            "ToolTip": (
                "Envoie un résumé du document actif à l'IA pour obtenir une "
                "relecture critique : alertes fonctionnelles, réglementaires, "
                "optimisations budgétaires."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            _print_ok("Revue en cours — analyse du document et appel IA…")
            FreeCADGui.updateGui() if hasattr(FreeCADGui, "updateGui") else None
            text = aa_ai_review.review(FreeCAD.ActiveDocument)
            aa_ai_review.show_review(text)
        except Exception as exc:
            _print_err(f"Revue IA impossible : {exc}")


# ----------------------------------------------------------------------------
# 10. Configure the LLM provider / API key
# ----------------------------------------------------------------------------
class CmdConfigureAI:
    def GetResources(self):
        return {
            "Pixmap": _icon("ArxioAI_Configure.svg"),
            "MenuText": "Configurer l'IA",
            "ToolTip": (
                "Sélectionne le fournisseur LLM (Anthropic, OpenAI, local Ollama…), "
                "le modèle, et enregistre votre clé API dans le paramètre FreeCAD."
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            aa_ai_config.open_dialog()
        except Exception as exc:
            _print_err(f"Configuration impossible : {exc}")


# ----------------------------------------------------------------------------
# Command registration
# ----------------------------------------------------------------------------
FreeCADGui.addCommand("ArxioAI_SetupProject", CmdSetupProject())
FreeCADGui.addCommand("ArxioAI_FastWalls", CmdFastWalls())
FreeCADGui.addCommand("ArxioAI_AutoRoof", CmdAutoRoof())
FreeCADGui.addCommand("ArxioAI_PlaceOpenings", CmdPlaceOpenings())
FreeCADGui.addCommand("ArxioAI_AutoPlan", CmdAutoPlan())
FreeCADGui.addCommand("ArxioAI_Estimate", CmdEstimate())
FreeCADGui.addCommand("ArxioAI_SolarAnalysis", CmdSolarAnalysis())
FreeCADGui.addCommand("ArxioAI_Assistant", CmdAIAssistant())
FreeCADGui.addCommand("ArxioAI_GenerateFromBrief", CmdGenerateFromBrief())
FreeCADGui.addCommand("ArxioAI_DesignReview", CmdDesignReview())
FreeCADGui.addCommand("ArxioAI_Configure", CmdConfigureAI())