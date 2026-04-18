# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - Preset house generator                                     *
# *   Copyright (c) 2026 Arxio AI                                           *
# ***************************************************************************

"""One-click house generation.

``build_preset_house`` creates a rectangular single-story building complete
with walls, a door, windows, a ground slab and a pitched roof. It is the
entry point used by the ``Arxio_PresetHouse`` command and is intentionally
decoupled from the task-panel layer so it can be driven from scripts or
tests.
"""

from __future__ import annotations

from typing import Dict, List

import FreeCAD

import ArxioUtils as U


def _make_rectangle(doc, length: float, width: float, origin=None):
    """Create a Draft rectangle at the origin."""
    import Draft

    placement = FreeCAD.Placement()
    if origin is not None:
        placement.Base = origin
    rect = Draft.makeRectangle(length=length, height=width, placement=placement,
                               face=False, support=None)
    rect.Label = "Arxio Footprint"
    return rect


def _make_wall_segment(doc, p1: FreeCAD.Vector, p2: FreeCAD.Vector,
                       height: float, width: float):
    """Create a wall along a straight edge between two points."""
    import Arch
    import Draft

    line = Draft.makeLine(p1, p2)
    wall = Arch.makeWall(line, height=height, width=width, align="Center")
    wall.Label = "Wall"
    return wall


def _place_opening(doc, wall, along: float, width: float, height: float,
                   sill: float, kind: str, direction: FreeCAD.Vector,
                   origin: FreeCAD.Vector, wall_height: float):
    """Place a door/window opening onto ``wall`` at the given distance."""
    import Arch

    # Compute opening position in world coordinates
    centre = origin + direction.multiply(along)
    centre.z = sill + height / 2.0

    length_vec = direction.normalize()
    # Compute a horizontal normal to the wall direction in the XY plane
    normal = FreeCAD.Vector(-length_vec.y, length_vec.x, 0.0)

    placement = FreeCAD.Placement()
    placement.Base = centre
    # Orient the opening host sketch in the wall plane
    rotation = FreeCAD.Rotation(length_vec, FreeCAD.Vector(0, 0, 1), normal, "XZY")
    placement.Rotation = rotation

    if kind == "Door":
        opening = Arch.makeWindow(None, width=width, height=height,
                                  name="Arxio Door")
        opening.WindowParts = [
            "Default", "Frame", "Wire0", "50", "0"
        ]
    else:
        opening = Arch.makeWindow(None, width=width, height=height,
                                  name="Arxio Window")
        opening.WindowParts = [
            "Default", "Frame", "Wire0", "50", "0"
        ]
    opening.Placement = placement
    try:
        opening.Hosts = [wall]
    except Exception:
        pass
    return opening


def _make_slab(doc, length: float, width: float, thickness: float):
    """Create a ground slab as an Arch::Structure from an extruded rectangle."""
    import Arch
    import Draft

    placement = FreeCAD.Placement()
    placement.Base = FreeCAD.Vector(0, 0, -thickness)
    rect = Draft.makeRectangle(length=length, height=width, placement=placement,
                               face=True)
    rect.Label = "Slab footprint"
    slab = Arch.makeStructure(rect, height=thickness)
    slab.Label = "Ground slab"
    slab.IfcType = "Slab"
    return slab


def _make_roof(doc, walls: List, pitch: float, thickness: float):
    """Create a pitched roof from the combined wall footprint."""
    import Arch

    try:
        roof = Arch.makeRoof(walls[0], angles=[pitch], run=[0.0],
                             idrel=[-1], thickness=[thickness],
                             overhang=[400.0])
    except TypeError:
        # Older Arch API fallback
        roof = Arch.makeRoof(walls[0])
        if hasattr(roof, "Angles"):
            roof.Angles = [pitch] * len(getattr(roof, "Angles", [pitch]))
        if hasattr(roof, "Thickness"):
            roof.Thickness = thickness
    roof.Label = "Roof"
    return roof


def build_preset_house(params: Dict) -> Dict:
    """Generate a complete small house and return the created objects.

    ``params`` keys: length, width, height, doors, windows, pitch.
    """
    doc = U.ensure_document()

    length = float(params["length"])
    width = float(params["width"])
    height = float(params["height"])
    n_doors = int(params.get("doors", 1))
    n_windows = int(params.get("windows", 4))
    pitch = float(params.get("pitch", 30))
    thickness = 200.0

    # Four corner points (clockwise, starting bottom-left)
    p0 = FreeCAD.Vector(0, 0, 0)
    p1 = FreeCAD.Vector(length, 0, 0)
    p2 = FreeCAD.Vector(length, width, 0)
    p3 = FreeCAD.Vector(0, width, 0)

    walls = [
        _make_wall_segment(doc, p0, p1, height, thickness),  # south
        _make_wall_segment(doc, p1, p2, height, thickness),  # east
        _make_wall_segment(doc, p2, p3, height, thickness),  # north
        _make_wall_segment(doc, p3, p0, height, thickness),  # west
    ]
    for w in walls:
        w.IfcType = "Wall"

    doc.recompute()

    # Place doors and windows — doors on the south wall, windows distributed
    # evenly on every wall.
    created_openings = []

    south_wall = walls[0]
    south_dir = (p1 - p0)
    south_length = south_dir.Length
    for i in range(n_doors):
        along = south_length * (i + 1) / (n_doors + 1)
        op = _place_opening(doc, south_wall, along, 900, 2100, 0,
                            "Door", south_dir, p0, height)
        created_openings.append(op)

    wall_defs = [
        (walls[0], p0, p1 - p0),  # south
        (walls[1], p1, p2 - p1),  # east
        (walls[2], p2, p3 - p2),  # north
        (walls[3], p3, p0 - p3),  # west
    ]
    windows_per_wall = max(1, n_windows // 4)
    remainder = n_windows - windows_per_wall * 4
    for idx, (wall, origin, direction) in enumerate(wall_defs):
        segment_length = direction.Length
        count = windows_per_wall + (1 if idx < remainder else 0)
        for i in range(count):
            along = segment_length * (i + 1) / (count + 1)
            op = _place_opening(doc, wall, along, 1200, 1200, 900,
                                "Window", direction, origin, height)
            created_openings.append(op)

    doc.recompute()

    slab = _make_slab(doc, length, width, thickness)
    roof = _make_roof(doc, walls, pitch, thickness)

    doc.recompute()

    U.log(f"Preset house generated: {length/1000:.1f}m x {width/1000:.1f}m, "
          f"{len(created_openings)} openings, roof @ {pitch}°.")

    return {
        "walls": walls,
        "openings": created_openings,
        "slab": slab,
        "roof": roof,
    }
