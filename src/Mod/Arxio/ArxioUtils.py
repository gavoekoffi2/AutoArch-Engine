# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - Utility helpers                                            *
# *   Copyright (c) 2026 Arxio AI                                           *
# ***************************************************************************

"""Shared utilities for the Arxio AI workbench.

Kept dependency-free (no hard requirement on Arch/Draft/Gui) so that the
helpers can be unit-tested in a headless environment.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Optional, Sequence

import FreeCAD


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------

BRAND_NAME = "Arxio AI"
BRAND_TAGLINE = "Smart automation for architects"
BRAND_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Resource discovery
# ---------------------------------------------------------------------------

def module_dir() -> str:
    """Return the absolute path to the Arxio module directory."""
    return os.path.dirname(os.path.abspath(__file__))


def resource_dir() -> str:
    """Return the absolute path to the Arxio Resources directory.

    In installed builds FreeCAD copies the icon payload to
    ``<ResourceDir>/Mod/Arxio/Resources``; in developer builds the files live
    alongside this module.
    """
    installed = os.path.join(
        FreeCAD.getResourceDir(), "Mod", "Arxio", "Resources"
    )
    if os.path.isdir(installed):
        return installed
    return os.path.join(module_dir(), "Resources")


def icon_path(name: str) -> str:
    """Resolve an SVG icon path by short name (without extension)."""
    return os.path.join(resource_dir(), "icons", f"{name}.svg")


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------

def ensure_document():
    """Return the active document, creating one if needed."""
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("ArxioProject")
    return doc


def get_walls(doc=None) -> List[object]:
    """Return all Arch wall objects in the given (or active) document."""
    doc = doc or FreeCAD.ActiveDocument
    if doc is None:
        return []
    walls = []
    for obj in doc.Objects:
        # Arch walls expose ``IfcType == 'Wall'`` and have a proxy
        if getattr(obj, "IfcType", None) == "Wall":
            walls.append(obj)
            continue
        proxy = getattr(getattr(obj, "Proxy", None), "Type", None)
        if proxy == "Wall":
            walls.append(obj)
    return walls


def get_selected_wires(require_planar: bool = True) -> List[object]:
    """Return the selected objects that are usable as wall baselines.

    A valid baseline is an object with a ``Shape`` containing at least one
    edge (wire, line, sketch).  When ``require_planar`` is true, only wires
    laying on the XY plane are returned, avoiding surprising wall heights.
    """
    try:
        import FreeCADGui
    except ImportError:
        return []
    wires: List[object] = []
    for obj in FreeCADGui.Selection.getSelection():
        shape = getattr(obj, "Shape", None)
        if shape is None or not shape.Edges:
            continue
        if require_planar:
            z_values = {round(v.Z, 3) for e in shape.Edges for v in e.Vertexes}
            if len(z_values) > 1:
                # Skip non-planar wires (e.g., 3D polylines) — they would
                # generate non-vertical walls.
                continue
        wires.append(obj)
    return wires


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def mm(value: float) -> float:
    """Identity helper - FreeCAD internal length unit is already millimetre."""
    return float(value)


def quantity(value: float, unit: str = "mm"):
    """Return a ``FreeCAD.Units.Quantity`` for the given value/unit."""
    try:
        return FreeCAD.Units.Quantity(float(value), unit)
    except Exception:
        return FreeCAD.Units.Quantity(f"{value} {unit}")


# ---------------------------------------------------------------------------
# Material database (simple, extendable)
# ---------------------------------------------------------------------------

# Unit costs expressed in EUR per cubic metre / square metre. These are sane
# European averages (2024-2026) used for quick quantity-takeoff estimates. Users
# can override them from the Estimate dialog; see ``ArxioTaskPanels``.
MATERIALS = {
    "Concrete block": {"cost_m3": 185.0, "density": 2100, "unit": "m3"},
    "Brick (hollow)": {"cost_m3": 220.0, "density": 1400, "unit": "m3"},
    "Reinforced concrete": {"cost_m3": 320.0, "density": 2400, "unit": "m3"},
    "Timber frame":  {"cost_m3": 480.0, "density":  500, "unit": "m3"},
    "Tile roofing":  {"cost_m2":  85.0, "density":    0, "unit": "m2"},
    "Metal roofing": {"cost_m2":  65.0, "density":    0, "unit": "m2"},
    "Concrete slab": {"cost_m3": 280.0, "density": 2400, "unit": "m3"},
}


def material_names() -> List[str]:
    return list(MATERIALS.keys())


def material_cost(name: str, quantity_value: float) -> float:
    """Return the estimated cost for ``quantity_value`` of the given material.

    The quantity is interpreted in the material's native unit (m3 or m2).
    Unknown materials return 0.
    """
    m = MATERIALS.get(name)
    if not m:
        return 0.0
    if m["unit"] == "m3":
        return m["cost_m3"] * quantity_value
    if m["unit"] == "m2":
        return m["cost_m2"] * quantity_value
    return 0.0


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def safe_recompute(doc=None) -> None:
    """Recompute the document if non-null, swallowing geometry warnings."""
    doc = doc or FreeCAD.ActiveDocument
    if doc is None:
        return
    try:
        doc.recompute()
    except Exception as exc:  # pragma: no cover - defensive
        FreeCAD.Console.PrintWarning(f"Arxio AI: recompute warning: {exc}\n")


def log(message: str) -> None:
    FreeCAD.Console.PrintMessage(f"[Arxio AI] {message}\n")


def warn(message: str) -> None:
    FreeCAD.Console.PrintWarning(f"[Arxio AI] {message}\n")


def error(message: str) -> None:
    FreeCAD.Console.PrintError(f"[Arxio AI] {message}\n")


def uniq(seq: Iterable) -> List:
    """Stable deduplication preserving first occurrence."""
    seen = set()
    out = []
    for item in seq:
        key = id(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def group_by_z(vertices: Sequence) -> dict:
    """Group vertices by their Z coordinate (rounded to millimetre)."""
    buckets: dict = {}
    for v in vertices:
        buckets.setdefault(round(v.Z, 3), []).append(v)
    return buckets


def best_template_path(name: str = "A3_Landscape_ISO7200.svg") -> Optional[str]:
    """Find a TechDraw SVG template shipped with FreeCAD."""
    candidate = os.path.join(
        FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates", name
    )
    if os.path.isfile(candidate):
        return candidate
    # Some distributions ship templates under the user data dir; search both.
    candidate = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "TechDraw",
                             "Templates", name)
    if os.path.isfile(candidate):
        return candidate
    return None
