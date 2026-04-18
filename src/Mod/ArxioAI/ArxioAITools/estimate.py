# SPDX-License-Identifier: LGPL-2.1-or-later
"""Quantity takeoff and cost estimation.

Iterates the active document for Arch objects (walls, slabs, roofs,
windows, doors), sums volumes / areas / counts, and multiplies by
configurable unit prices stored in the FreeCAD parameter store.
"""

import FreeCAD


PREF_GROUP = "User parameter:BaseApp/Preferences/Mod/ArxioAI"

# Default unit prices in CFA Francs per m³ or m² — tweak in Preferences.
DEFAULT_PRICES = {
    "WallPricePerM3": 85000.0,
    "SlabPricePerM3": 110000.0,
    "RoofPricePerM2": 25000.0,
    "WindowPricePerUnit": 75000.0,
    "DoorPricePerUnit": 120000.0,
    "Currency": "FCFA",
}


def _params():
    return FreeCAD.ParamGet(PREF_GROUP)


def _read_prices():
    p = _params()
    return {
        "wall_m3": p.GetFloat("WallPricePerM3", DEFAULT_PRICES["WallPricePerM3"]),
        "slab_m3": p.GetFloat("SlabPricePerM3", DEFAULT_PRICES["SlabPricePerM3"]),
        "roof_m2": p.GetFloat("RoofPricePerM2", DEFAULT_PRICES["RoofPricePerM2"]),
        "window": p.GetFloat("WindowPricePerUnit", DEFAULT_PRICES["WindowPricePerUnit"]),
        "door": p.GetFloat("DoorPricePerUnit", DEFAULT_PRICES["DoorPricePerUnit"]),
        "currency": p.GetString("Currency", DEFAULT_PRICES["Currency"])
        or DEFAULT_PRICES["Currency"],
    }


def _volume_m3(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None:
        return 0.0
    try:
        return float(shape.Volume) / 1.0e9  # mm³ → m³
    except Exception:
        return 0.0


def _area_m2(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None:
        return 0.0
    try:
        # Surface area divided by 2 approximates the "outer skin" for a slab/roof.
        return float(shape.Area) / 1.0e6 / 2.0
    except Exception:
        return 0.0


def _classify(obj):
    ifc = getattr(obj, "IfcType", "")
    proxy_name = getattr(getattr(obj, "Proxy", None), "__class__", type(None)).__name__
    if ifc == "Wall" or "Wall" in proxy_name:
        return "wall"
    if ifc in ("Slab", "Floor") or "Structure" in proxy_name:
        return "slab"
    if ifc == "Roof" or "Roof" in proxy_name:
        return "roof"
    if ifc == "Window" or "Window" in proxy_name:
        return "window"
    if ifc == "Door":
        return "door"
    return None


def run(doc):
    """Compute quantities and costs.

    Returns a dict with per-category quantities, unit prices, and totals.
    """
    prices = _read_prices()
    totals = {
        "wall_m3": 0.0,
        "slab_m3": 0.0,
        "roof_m2": 0.0,
        "windows": 0,
        "doors": 0,
    }

    for obj in doc.Objects:
        kind = _classify(obj)
        if kind == "wall":
            totals["wall_m3"] += _volume_m3(obj)
        elif kind == "slab":
            totals["slab_m3"] += _volume_m3(obj)
        elif kind == "roof":
            totals["roof_m2"] += _area_m2(obj)
        elif kind == "window":
            totals["windows"] += 1
        elif kind == "door":
            totals["doors"] += 1

    cost = (
        totals["wall_m3"] * prices["wall_m3"]
        + totals["slab_m3"] * prices["slab_m3"]
        + totals["roof_m2"] * prices["roof_m2"]
        + totals["windows"] * prices["window"]
        + totals["doors"] * prices["door"]
    )

    return {
        "quantities": totals,
        "prices": prices,
        "total_cost": cost,
    }


def _format_report(report):
    q = report["quantities"]
    p = report["prices"]
    currency = p["currency"]
    lines = [
        "┌──────────────────── Arxio AI — Métré & Devis ────────────────────┐",
        f"│ Murs        : {q['wall_m3']:>10.2f} m³  × {p['wall_m3']:>10.0f} {currency}/m³",
        f"│ Dalles      : {q['slab_m3']:>10.2f} m³  × {p['slab_m3']:>10.0f} {currency}/m³",
        f"│ Toiture     : {q['roof_m2']:>10.2f} m²  × {p['roof_m2']:>10.0f} {currency}/m²",
        f"│ Fenêtres    : {q['windows']:>10d} u   × {p['window']:>10.0f} {currency}/u",
        f"│ Portes      : {q['doors']:>10d} u   × {p['door']:>10.0f} {currency}/u",
        "├──────────────────────────────────────────────────────────────────",
        f"│ TOTAL ESTIMÉ: {report['total_cost']:>16.0f} {currency}",
        "└──────────────────────────────────────────────────────────────────",
    ]
    return "\n".join(lines)


def show_report(report):
    """Print the report in the FreeCAD console. If Qt is available,
    also surface it in a message box."""
    text = _format_report(report)
    FreeCAD.Console.PrintMessage("\n" + text + "\n")

    try:
        from PySide import QtWidgets

        box = QtWidgets.QMessageBox()
        box.setWindowTitle("Arxio AI — Métré & Devis")
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setText("<pre>" + text + "</pre>")
        box.exec_()
    except ImportError:  # pragma: no cover
        pass
