# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - Export helpers                                             *
# *   Copyright (c) 2026 Arxio AI                                           *
# ***************************************************************************

"""PDF / TechDraw export helpers for Arxio AI.

Creating a permit-grade PDF in FreeCAD requires several coordinated steps:

1. Create a TechDraw page from a shipped SVG template (A3 landscape by
   default).
2. Add top / front / side views of the selected building objects.
3. Export the page to PDF using TechDraw's Gui command when running with a
   GUI, falling back to the Python API otherwise.

The helpers are defensive: missing templates, missing objects, or a
command-line context will not crash the workbench — they degrade gracefully
with a warning.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Optional

import FreeCAD

import ArxioUtils as U


def _visible_objects(doc) -> List:
    """Return the building objects we want to project on the drawing."""
    keepers = []
    for obj in doc.Objects:
        ifc = getattr(obj, "IfcType", None)
        if ifc in ("Wall", "Slab", "Roof", "Window", "Door"):
            keepers.append(obj)
    return keepers


def create_permit_page(doc, template_name: str = "A3_Landscape_ISO7200.svg"):
    """Create a TechDraw page populated with top / front / side views."""
    template_path = U.best_template_path(template_name)
    if not template_path:
        U.warn(
            "TechDraw template not found. Make sure the TechDraw module is "
            "installed. Creating a blank page instead."
        )

    page = doc.addObject("TechDraw::DrawPage", "ArxioPermitPage")
    template = doc.addObject("TechDraw::DrawSVGTemplate", "ArxioTemplate")
    if template_path:
        template.Template = template_path
    page.Template = template
    page.Label = "Arxio AI - Permit plan"

    sources = _visible_objects(doc)
    if not sources:
        U.warn("No Arxio objects found - the permit page will be empty.")
        return page

    # Top view (plan)
    top = doc.addObject("TechDraw::DrawViewPart", "Plan")
    top.Source = sources
    top.Direction = FreeCAD.Vector(0, 0, 1)
    top.Scale = 0.05
    top.X = 150
    top.Y = 210
    page.addView(top)

    # Front elevation
    front = doc.addObject("TechDraw::DrawViewPart", "Front")
    front.Source = sources
    front.Direction = FreeCAD.Vector(0, -1, 0)
    front.Scale = 0.05
    front.X = 150
    front.Y = 80
    page.addView(front)

    # Side elevation
    side = doc.addObject("TechDraw::DrawViewPart", "Side")
    side.Source = sources
    side.Direction = FreeCAD.Vector(1, 0, 0)
    side.Scale = 0.05
    side.X = 280
    side.Y = 80
    page.addView(side)

    doc.recompute()
    return page


def export_page_to_pdf(page, destination: str) -> bool:
    """Export the given TechDraw page to a PDF file.

    Returns ``True`` on success. The operation requires the TechDraw Gui
    module; when run headless the function logs a warning and returns
    ``False``.
    """
    destination = os.path.abspath(os.path.expanduser(destination))
    try:
        import TechDrawGui  # type: ignore
    except ImportError:
        U.warn("TechDrawGui is not available - cannot export PDF headless.")
        return False

    try:
        TechDrawGui.exportPageAsPdf(page, destination)
        U.log(f"PDF exported to {destination}")
        return True
    except Exception as exc:
        U.error(f"PDF export failed: {exc}")
        return False
