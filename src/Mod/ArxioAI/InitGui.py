# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Arxio AI module - GUI workbench initialisation
#
# Built on FreeCAD (https://www.freecad.org), LGPL-2.1-or-later.
# Copyright (c) 2026 Arxio AI contributors

import os

import FreeCAD
import FreeCADGui


def _resource_dir():
    return os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "ArxioAI", "Resources")


def _shipped_resource_dir():
    return os.path.join(FreeCAD.getResourceDir(), "Mod", "ArxioAI", "Resources")


def _find_resources():
    for candidate in (_shipped_resource_dir(), _resource_dir()):
        if os.path.isdir(candidate):
            return candidate
    # Fallback: source tree (development runs)
    here = os.path.dirname(__file__)
    return os.path.join(here, "Resources")


class ArxioAIWorkbench(FreeCADGui.Workbench):
    """Arxio AI — Outils automatisés pour architectes et BET."""

    MenuText = "Arxio AI"
    ToolTip = "Arxio AI — Conception architecturale accélérée (murs, toiture, plans, devis)"

    def __init__(self):
        res = _find_resources()
        icon = os.path.join(res, "icons", "ArxioAIWorkbench.svg")
        if os.path.isfile(icon):
            self.__class__.Icon = icon

    def Initialize(self):
        res = _find_resources()
        icon_dir = os.path.join(res, "icons")
        if os.path.isdir(icon_dir):
            FreeCADGui.addIconPath(icon_dir)

        # Import commands — this registers them with FreeCADGui
        import ArxioAICommands  # noqa: F401

        self.modeling_cmds = [
            "ArxioAI_SetupProject",
            "ArxioAI_FastWalls",
            "ArxioAI_AutoRoof",
            "ArxioAI_PlaceOpenings",
        ]
        self.doc_cmds = [
            "ArxioAI_AutoPlan",
            "ArxioAI_Estimate",
            "ArxioAI_SolarAnalysis",
        ]
        self.ai_cmds = [
            "ArxioAI_Assistant",
            "ArxioAI_GenerateFromBrief",
            "ArxioAI_DesignReview",
            "ArxioAI_Configure",
        ]

        self.appendToolbar("Arxio AI — Modélisation", self.modeling_cmds)
        self.appendToolbar("Arxio AI — Documents", self.doc_cmds)
        self.appendToolbar("Arxio AI — Intelligence", self.ai_cmds)
        self.appendMenu(
            "&Arxio AI",
            self.modeling_cmds
            + ["Separator"]
            + self.doc_cmds
            + ["Separator"]
            + self.ai_cmds,
        )

        FreeCAD.Console.PrintLog("Arxio AI: workbench initialised\n")

    def Activated(self):
        FreeCAD.Console.PrintMessage("Arxio AI activé.\n")

    def Deactivated(self):
        FreeCAD.Console.PrintLog("Arxio AI désactivé.\n")

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(ArxioAIWorkbench())
