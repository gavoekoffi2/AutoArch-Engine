# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fast wall creation helpers.

Accepts any selection of 2D-ish objects (Sketch, Draft Line/Wire, Part wire/edge)
and produces Arch Wall objects with sensible, user-configurable defaults.
"""

import FreeCAD


PREF_GROUP = "User parameter:BaseApp/Preferences/Mod/ArxioAI"

DEFAULTS = {
    "WallHeight": 2800.0,   # mm
    "WallWidth": 200.0,     # mm
    "WallAlign": "Center",  # Left / Center / Right
}


def _params():
    return FreeCAD.ParamGet(PREF_GROUP)


def read_defaults():
    p = _params()
    return {
        "height": p.GetFloat("WallHeight", DEFAULTS["WallHeight"]),
        "width": p.GetFloat("WallWidth", DEFAULTS["WallWidth"]),
        "align": p.GetString("WallAlign", DEFAULTS["WallAlign"]) or DEFAULTS["WallAlign"],
    }


def write_defaults(height=None, width=None, align=None):
    p = _params()
    if height is not None:
        p.SetFloat("WallHeight", float(height))
    if width is not None:
        p.SetFloat("WallWidth", float(width))
    if align is not None:
        p.SetString("WallAlign", str(align))


def _is_acceptable_base(obj):
    """Accept sketches, draft lines/wires, and any Part feature with a Shape
    that contains edges."""
    if obj is None:
        return False
    if not hasattr(obj, "Shape"):
        # Sketches expose Shape too, but guard anyway.
        return hasattr(obj, "Geometry")
    shape = obj.Shape
    if shape is None:
        return False
    try:
        return bool(shape.Edges)
    except Exception:
        return False


def make_walls_from_selection(selection, params):
    """Create an Arch Wall for each valid base object in `selection`.

    Returns the list of walls actually created (may be empty).
    """
    import Arch

    height = float(params.get("height", DEFAULTS["WallHeight"]))
    width = float(params.get("width", DEFAULTS["WallWidth"]))
    align = params.get("align", DEFAULTS["WallAlign"])

    created = []
    for obj in selection:
        if not _is_acceptable_base(obj):
            continue
        try:
            wall = Arch.makeWall(obj, height=height, width=width, align=align)
        except TypeError:
            # Older API signatures — fall back to positional.
            wall = Arch.makeWall(obj)
            if hasattr(wall, "Height"):
                wall.Height = height
            if hasattr(wall, "Width"):
                wall.Width = width
            if hasattr(wall, "Align"):
                wall.Align = align
        if wall is not None:
            created.append(wall)
    return created
