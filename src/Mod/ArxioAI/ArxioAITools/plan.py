# SPDX-License-Identifier: LGPL-2.1-or-later
"""Automatic TechDraw page generation for permit drawings."""

import os

import FreeCAD


def _template_path():
    """Return a valid TechDraw template path, trying a few common names."""
    base = os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates")
    for name in (
        "A3_Landscape_ISO7200.svg",
        "A3_LandscapeTD.svg",
        "A3_LandscapeISO.svg",
        "A3_Landscape_blank.svg",
    ):
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate):
            return candidate
    # Last resort: return the first SVG in Templates dir, if any.
    if os.path.isdir(base):
        for fn in sorted(os.listdir(base)):
            if fn.lower().endswith(".svg"):
                return os.path.join(base, fn)
    return ""


def _collect_visible_bim_objects(doc):
    """Return BIM-ish objects worth drawing (walls, slabs, roofs, windows, doors)."""
    wanted = ("Wall", "Structure", "Roof", "Window", "Door", "Floor", "Building")
    out = []
    for obj in doc.Objects:
        ifc_type = getattr(obj, "IfcType", "")
        if ifc_type in wanted:
            out.append(obj)
        else:
            proxy_name = getattr(getattr(obj, "Proxy", None), "__class__", type(None)).__name__
            if any(k in proxy_name for k in ("Wall", "Roof", "Structure", "Window")):
                out.append(obj)
    return out


def create_permit_page(doc):
    """Create a TechDraw page with top + front + side views.

    Returns the TechDraw::DrawPage object.
    """
    template_file = _template_path()
    if not template_file:
        raise RuntimeError(
            "Aucun gabarit TechDraw trouvé. Vérifiez votre installation FreeCAD."
        )

    page = doc.addObject("TechDraw::DrawPage", "Arxio_PermisPage")
    template = doc.addObject("TechDraw::DrawSVGTemplate", "Arxio_Template")
    template.Template = template_file
    page.Template = template  # <-- the original bug was `doc.Template`

    objs = _collect_visible_bim_objects(doc)
    if not objs:
        FreeCAD.Console.PrintWarning(
            "Arxio AI: aucun objet BIM trouvé — la page reste vide.\n"
        )
        return page

    views = [
        ("Plan", (0.0, 0.0, 1.0), (100.0, 150.0)),
        ("Façade_Sud", (0.0, -1.0, 0.0), (100.0, 50.0)),
        ("Façade_Est", (1.0, 0.0, 0.0), (300.0, 150.0)),
    ]
    for name, direction, pos in views:
        view = doc.addObject("TechDraw::DrawViewPart", f"Arxio_{name}")
        view.Source = objs
        view.Direction = FreeCAD.Vector(*direction)
        view.X, view.Y = pos
        view.Scale = 0.02  # 1:50
        page.addView(view)

    return page
