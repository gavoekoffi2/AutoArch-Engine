# SPDX-License-Identifier: LGPL-2.1-or-later
"""Project bootstrap helpers — Site / Building / Floor."""

import FreeCAD


def _get_or_make(doc, maker, label, **kwargs):
    """Return an existing object with `label` or create one via `maker`."""
    for obj in doc.Objects:
        if obj.Label == label:
            return obj
    obj = maker(**kwargs) if kwargs else maker()
    obj.Label = label
    return obj


def setup_project(doc):
    """Create a Site → Building → Floor hierarchy if missing.

    Returns
    -------
    (site, building, floor) tuple of FreeCAD objects.
    """
    import Arch

    site = _get_or_make(doc, Arch.makeSite, "Arxio_Site")
    building = _get_or_make(doc, Arch.makeBuilding, "Arxio_Bâtiment")
    floor = _get_or_make(doc, Arch.makeFloor, "Arxio_RDC")

    if building not in getattr(site, "Group", []):
        try:
            site.Group = list(getattr(site, "Group", [])) + [building]
        except Exception:
            pass
    if floor not in getattr(building, "Group", []):
        try:
            building.Group = list(getattr(building, "Group", [])) + [floor]
        except Exception:
            pass

    doc.recompute()
    FreeCAD.Console.PrintLog(
        f"Arxio AI: project scaffold ready (site={site.Name}, "
        f"building={building.Name}, floor={floor.Name})\n"
    )
    return site, building, floor
