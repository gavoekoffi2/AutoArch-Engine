# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - Automated architecture workbench                           *
# *   Copyright (c) 2026 Arxio AI                                           *
# *                                                                         *
# *   This file is part of the Arxio AI workbench, built on FreeCAD.        *
# *   Licensed under the LGPL-2.1-or-later.                                 *
# ***************************************************************************

"""Arxio AI workbench - GUI registration.

This file is executed by FreeCAD at GUI startup. It registers the Arxio AI
workbench with FreeCADGui. Heavy imports are deferred to ``Initialize`` so
that the startup impact is minimal.
"""

import os

import FreeCAD
import FreeCADGui


class ArxioWorkbench(FreeCADGui.Workbench):
    """Arxio AI - Smart architecture design workbench.

    Provides a curated, opinionated toolbox that turns 2D sketches into a
    permit-ready 3D building with a handful of clicks.
    """

    def __init__(self):
        icon_dir = os.path.join(
            FreeCAD.getResourceDir(), "Mod", "Arxio", "Resources", "icons"
        )
        # Fallback to the source tree in developer builds
        if not os.path.isdir(icon_dir):
            icon_dir = os.path.join(os.path.dirname(__file__), "Resources", "icons")

        self.__class__.MenuText = "Arxio AI"
        self.__class__.ToolTip = (
            "Arxio AI - Smart automation toolkit for architects. "
            "Turn 2D sketches into permit-ready plans in minutes."
        )
        self.__class__.Icon = os.path.join(icon_dir, "ArxioWorkbench.svg")

    def Initialize(self):
        """Called by FreeCAD the first time the workbench is activated."""
        # Import commands only when the workbench is activated
        import ArxioCommands  # noqa: F401 (registers commands)

        design_cmds = [
            "Arxio_PresetHouse",
            "Arxio_FastWalls",
            "Arxio_SmartOpenings",
            "Arxio_AutoRoof",
        ]
        analyze_cmds = [
            "Arxio_Estimate",
            "Arxio_SunStudy",
        ]
        deliver_cmds = [
            "Arxio_AutoPlan",
            "Arxio_ExportPDF",
        ]
        misc_cmds = [
            "Arxio_Welcome",
            "Arxio_About",
        ]

        self.appendToolbar("Arxio AI - Design", design_cmds)
        self.appendToolbar("Arxio AI - Analyze", analyze_cmds)
        self.appendToolbar("Arxio AI - Deliver", deliver_cmds)

        self.appendMenu(["&Arxio AI", "Design"], design_cmds)
        self.appendMenu(["&Arxio AI", "Analyze"], analyze_cmds)
        self.appendMenu(["&Arxio AI", "Deliver"], deliver_cmds)
        self.appendMenu(["&Arxio AI"], misc_cmds)

        FreeCAD.Console.PrintLog("Arxio AI workbench initialized.\n")

    def Activated(self):
        FreeCAD.Console.PrintMessage(
            "Arxio AI activated. Tip: start with 'Preset House' or 'Fast Walls'.\n"
        )

    def Deactivated(self):
        pass

    def ContextMenu(self, recipient):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(ArxioWorkbench())
