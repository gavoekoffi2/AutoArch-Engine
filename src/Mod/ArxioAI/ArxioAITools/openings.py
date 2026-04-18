# SPDX-License-Identifier: LGPL-2.1-or-later
"""Door / window placement on a selected wall."""

import FreeCAD


def pick_wall(selection):
    for obj in selection:
        proxy_name = getattr(getattr(obj, "Proxy", None), "__class__", type(None)).__name__
        if proxy_name in ("_Wall", "ArchWall"):
            return obj
        if getattr(obj, "IfcType", "") == "Wall":
            return obj
    return None


def _prompt_parameters():
    """Ask the user via Qt dialog for opening kind + dimensions.

    Falls back to console defaults if Qt is not available.
    """
    try:
        from PySide import QtWidgets
    except ImportError:  # pragma: no cover
        return {"kind": "Door", "width": 900.0, "height": 2100.0, "sill": 0.0, "offset": 500.0}

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle("Arxio AI — Placer une ouverture")
    form = QtWidgets.QFormLayout(dlg)

    kind = QtWidgets.QComboBox()
    kind.addItems(["Porte", "Fenêtre"])
    width = QtWidgets.QDoubleSpinBox()
    width.setRange(100.0, 10000.0)
    width.setValue(900.0)
    width.setSuffix(" mm")
    height = QtWidgets.QDoubleSpinBox()
    height.setRange(100.0, 10000.0)
    height.setValue(2100.0)
    height.setSuffix(" mm")
    sill = QtWidgets.QDoubleSpinBox()
    sill.setRange(0.0, 5000.0)
    sill.setValue(0.0)
    sill.setSuffix(" mm")
    offset = QtWidgets.QDoubleSpinBox()
    offset.setRange(0.0, 100000.0)
    offset.setValue(500.0)
    offset.setSuffix(" mm")

    form.addRow("Type", kind)
    form.addRow("Largeur", width)
    form.addRow("Hauteur", height)
    form.addRow("Allège", sill)
    form.addRow("Distance le long du mur", offset)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    form.addRow(buttons)

    if dlg.exec_() != QtWidgets.QDialog.Accepted:
        return None

    return {
        "kind": "Door" if kind.currentText() == "Porte" else "Window",
        "width": float(width.value()),
        "height": float(height.value()),
        "sill": float(sill.value()),
        "offset": float(offset.value()),
    }


def _build_rect_sketch(wall, params):
    """Create a rectangular sketch on the wall face, at the requested offset."""
    import Draft

    shape = wall.Shape
    bb = shape.BoundBox
    # Simplified placement: use the wall's base placement, offset along X,
    # rectangle in XZ plane with given width/height.
    origin = wall.Placement.Base
    x0 = origin.x + float(params["offset"])
    y0 = origin.y
    z0 = bb.ZMin + float(params["sill"])
    w = float(params["width"])
    h = float(params["height"])

    p1 = FreeCAD.Vector(x0, y0, z0)
    p2 = FreeCAD.Vector(x0 + w, y0, z0)
    p3 = FreeCAD.Vector(x0 + w, y0, z0 + h)
    p4 = FreeCAD.Vector(x0, y0, z0 + h)
    rect = Draft.makeWire([p1, p2, p3, p4], closed=True, face=True)
    rect.Label = f"Arxio_{params['kind']}Profile"
    return rect


def open_dialog_and_place(wall):
    """Ask user for parameters then place a door/window on `wall`.

    Returns the created Arch object or None on cancel / failure.
    """
    import Arch

    params = _prompt_parameters()
    if params is None:
        return None

    profile = _build_rect_sketch(wall, params)
    try:
        if params["kind"] == "Door":
            obj = Arch.makeWindow(profile, width=params["width"], height=params["height"])
            if hasattr(obj, "WindowParts"):
                obj.Label = "Arxio_Porte"
            try:
                Arch.addComponents(obj, wall)
            except Exception:
                pass
        else:
            obj = Arch.makeWindow(profile, width=params["width"], height=params["height"])
            obj.Label = "Arxio_Fenêtre"
            try:
                Arch.addComponents(obj, wall)
            except Exception:
                pass
        return obj
    except Exception as exc:
        FreeCAD.Console.PrintError(f"Arxio AI: opening placement failed — {exc}\n")
        return None
