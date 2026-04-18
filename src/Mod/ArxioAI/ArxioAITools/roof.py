# SPDX-License-Identifier: LGPL-2.1-or-later
"""Roof + slab generation from a set of walls.

`Arch.makeRoof` expects a closed profile, not a wall. So we build an
envelope wire from the bounding box of the selected walls, extrude a
slab from it, and create a roof from the same outline.
"""

import FreeCAD


def _walls_only(selection):
    out = []
    for obj in selection:
        if hasattr(obj, "Proxy") and obj.Proxy.__class__.__name__ in (
            "_Wall",
            "ArchWall",
        ):
            out.append(obj)
        elif hasattr(obj, "IfcType") and getattr(obj, "IfcType", "") == "Wall":
            out.append(obj)
    return out


def _bounding_outline(walls):
    """Return a closed rectangular wire circumscribing the wall footprint
    at z = min(z). Used as a fallback base for slab + roof."""
    import Draft
    import Part

    xs, ys, zs = [], [], []
    for w in walls:
        shape = getattr(w, "Shape", None)
        if shape is None:
            continue
        bb = shape.BoundBox
        xs.extend([bb.XMin, bb.XMax])
        ys.extend([bb.YMin, bb.YMax])
        zs.append(bb.ZMin)

    if not xs or not ys:
        return None

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    z = min(zs) if zs else 0.0

    p1 = FreeCAD.Vector(xmin, ymin, z)
    p2 = FreeCAD.Vector(xmax, ymin, z)
    p3 = FreeCAD.Vector(xmax, ymax, z)
    p4 = FreeCAD.Vector(xmin, ymax, z)

    wire = Draft.makeWire([p1, p2, p3, p4], closed=True, face=False)
    wire.Label = "Arxio_Footprint"
    return wire


def make_slab_and_roof(selection, slab_thickness=200.0, roof_pitch=30.0, roof_thickness=200.0):
    """Build a slab at floor level and a roof at wall top.

    Returns (slab, roof). Either may be None on partial failure.
    """
    import Arch

    walls = _walls_only(selection)
    if not walls:
        return None, None

    outline = _bounding_outline(walls)
    if outline is None:
        return None, None

    slab = None
    try:
        slab = Arch.makeStructure(outline, height=float(slab_thickness))
        slab.Label = "Arxio_Dalle"
        slab.IfcType = "Slab"
    except Exception as exc:
        FreeCAD.Console.PrintWarning(f"Arxio AI: slab creation failed — {exc}\n")

    # Roof height: top of tallest wall
    top_z = 0.0
    for w in walls:
        shape = getattr(w, "Shape", None)
        if shape is not None:
            top_z = max(top_z, shape.BoundBox.ZMax)

    roof = None
    try:
        # Duplicate the outline at the top so the roof sits on the walls.
        import Draft

        roof_base = Draft.clone(outline)
        roof_base.Label = "Arxio_RoofBase"
        roof_base.Placement.Base = FreeCAD.Vector(0, 0, top_z)
        roof = Arch.makeRoof(
            roof_base,
            angles=[float(roof_pitch)],
            run=[250.0],
            idrel=[-1],
            thickness=[float(roof_thickness)],
            overhang=[300.0],
        )
        roof.Label = "Arxio_Toiture"
    except Exception as exc:
        FreeCAD.Console.PrintWarning(f"Arxio AI: roof creation failed — {exc}\n")

    return slab, roof
