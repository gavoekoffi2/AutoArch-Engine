# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - Commands                                                   *
# *   Copyright (c) 2026 Arxio AI                                           *
# ***************************************************************************

"""Arxio AI commands registered with FreeCADGui.

Each command class follows the FreeCAD workbench contract:

* ``GetResources()``: icon, menu label, tool-tip.
* ``IsActive()``: enable/disable state.
* ``Activated()``: main entry point.
"""

from __future__ import annotations

import math
import os
from typing import List

import FreeCAD
import FreeCADGui

import ArxioUtils as U


# ---------------------------------------------------------------------------
# Preset house - one-click architecture
# ---------------------------------------------------------------------------

class Arxio_PresetHouse:
    """Generate a full single-story house from a couple of parameters."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_PresetHouse"),
            "MenuText": "Preset House",
            "Accel": "A, H",
            "ToolTip": (
                "One-click small house: walls, door, windows, slab, roof. "
                "Ideal to sketch a project in seconds."
            ),
        }

    def IsActive(self):
        return FreeCADGui.getMainWindow() is not None

    def Activated(self):
        import ArxioTaskPanels as TP
        import ArxioHouseBuilder as HB

        dialog = TP.PresetHouseDialog(FreeCADGui.getMainWindow())
        if dialog.exec_() != dialog.Accepted:
            return
        params = dialog.values()
        try:
            HB.build_preset_house(params)
        except Exception as exc:
            U.error(f"Preset House failed: {exc}")


# ---------------------------------------------------------------------------
# Fast walls - from a 2D selection
# ---------------------------------------------------------------------------

class Arxio_FastWalls:
    """Create Arch walls from the selected wires / sketches."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_FastWalls"),
            "MenuText": "Fast Walls",
            "Accel": "A, W",
            "ToolTip": (
                "Turn every selected line, wire, rectangle or sketch into a "
                "3D wall with the chosen height and thickness."
            ),
        }

    def IsActive(self):
        return (
            FreeCAD.ActiveDocument is not None
            and bool(FreeCADGui.Selection.getSelection())
        )

    def Activated(self):
        import Arch
        import ArxioTaskPanels as TP

        wires = U.get_selected_wires(require_planar=True)
        if not wires:
            U.error(
                "No planar wire selected. Draw a line, rectangle or sketch "
                "on the XY plane and try again."
            )
            return

        dialog = TP.WallsDialog(FreeCADGui.getMainWindow())
        if dialog.exec_() != dialog.Accepted:
            return
        v = dialog.values()
        doc = U.ensure_document()

        created = []
        for wire in wires:
            try:
                wall = Arch.makeWall(wire,
                                     height=v["height"],
                                     width=v["width"],
                                     align=v["alignment"])
                wall.Label = f"Wall ({v['material']})"
                wall.IfcType = "Wall"
                if hasattr(wall, "Description"):
                    wall.Description = v["material"]
                created.append(wall)
            except Exception as exc:
                U.warn(f"Could not create wall on '{wire.Label}': {exc}")

        U.safe_recompute(doc)
        U.log(f"{len(created)} wall(s) generated.")


# ---------------------------------------------------------------------------
# Smart openings - doors & windows
# ---------------------------------------------------------------------------

class Arxio_SmartOpenings:
    """Place doors and windows on the selected walls."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_SmartOpenings"),
            "MenuText": "Smart Openings",
            "Accel": "A, O",
            "ToolTip": (
                "Place a door or a window centred on every selected wall. "
                "Choose position, width, height and sill in one dialog."
            ),
        }

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        return any(
            getattr(o, "IfcType", None) == "Wall"
            for o in FreeCADGui.Selection.getSelection()
        )

    def Activated(self):
        import Arch
        import ArxioTaskPanels as TP

        walls = [o for o in FreeCADGui.Selection.getSelection()
                 if getattr(o, "IfcType", None) == "Wall"]
        if not walls:
            U.error("Select at least one wall before calling Smart Openings.")
            return

        dialog = TP.OpeningsDialog(FreeCADGui.getMainWindow())
        if dialog.exec_() != dialog.Accepted:
            return
        v = dialog.values()

        position_ratio = {"One third": 1 / 3,
                          "Middle": 1 / 2,
                          "Two thirds": 2 / 3}[v["position"]]

        for wall in walls:
            try:
                base = wall.Base
                if base is None or not getattr(base, "Shape", None):
                    U.warn(f"Wall '{wall.Label}' has no base edge - skipped.")
                    continue
                edges = base.Shape.Edges
                if not edges:
                    continue
                edge = edges[0]
                p1 = edge.Vertexes[0].Point
                p2 = edge.Vertexes[-1].Point
                direction = p2 - p1
                length = direction.Length
                if length <= v["width"]:
                    U.warn(
                        f"Wall '{wall.Label}' is too short for a "
                        f"{v['width']:.0f} mm opening."
                    )
                    continue
                along = length * position_ratio
                centre = p1 + FreeCAD.Vector(direction).normalize().multiply(along)
                centre.z = v["sill"] + v["height"] / 2

                hor = FreeCAD.Vector(direction).normalize()
                normal = FreeCAD.Vector(-hor.y, hor.x, 0.0)
                placement = FreeCAD.Placement()
                placement.Base = centre
                placement.Rotation = FreeCAD.Rotation(
                    hor, FreeCAD.Vector(0, 0, 1), normal, "XZY"
                )

                opening = Arch.makeWindow(
                    None, width=v["width"], height=v["height"],
                    name=v["kind"]
                )
                opening.Placement = placement
                opening.Label = f"{v['kind']} ({wall.Label})"
                try:
                    opening.Hosts = [wall]
                except Exception:
                    pass
            except Exception as exc:
                U.warn(f"Opening on '{wall.Label}' failed: {exc}")

        U.safe_recompute()
        U.log(f"{len(walls)} opening(s) placed.")


# ---------------------------------------------------------------------------
# Auto roof + slab
# ---------------------------------------------------------------------------

class Arxio_AutoRoof:
    """Generate a roof (and optional slab) from the selected walls."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_AutoRoof"),
            "MenuText": "Auto Roof & Slab",
            "Accel": "A, R",
            "ToolTip": (
                "Cap the selected walls with a pitched roof and drop a "
                "ground slab underneath."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        import Arch
        import Draft
        import ArxioTaskPanels as TP

        doc = FreeCAD.ActiveDocument
        walls = [o for o in FreeCADGui.Selection.getSelection()
                 if getattr(o, "IfcType", None) == "Wall"]
        if not walls:
            walls = U.get_walls(doc)
        if not walls:
            U.error(
                "No wall found. Create walls first (Fast Walls or Preset "
                "House), then try again."
            )
            return

        dialog = TP.RoofDialog(FreeCADGui.getMainWindow())
        if dialog.exec_() != dialog.Accepted:
            return
        v = dialog.values()

        # Compute bounding box of walls to size the slab
        bbox = None
        for w in walls:
            shape = getattr(w, "Shape", None)
            if shape is None:
                continue
            if bbox is None:
                bbox = shape.BoundBox
            else:
                bbox.add(shape.BoundBox)
        if bbox is None:
            U.error("Walls have no computed shape. Recompute the document.")
            return

        # Slab
        if v["slab"]:
            try:
                placement = FreeCAD.Placement()
                placement.Base = FreeCAD.Vector(bbox.XMin, bbox.YMin,
                                                -v["slab_thickness"])
                rect = Draft.makeRectangle(
                    length=bbox.XLength, height=bbox.YLength,
                    placement=placement, face=True,
                )
                rect.Label = "Arxio slab footprint"
                slab = Arch.makeStructure(rect, height=v["slab_thickness"])
                slab.Label = "Ground slab"
                slab.IfcType = "Slab"
            except Exception as exc:
                U.warn(f"Slab creation failed: {exc}")

        # Roof
        try:
            roof = Arch.makeRoof(walls[0])
            if hasattr(roof, "Angles"):
                roof.Angles = [float(v["pitch"])] * len(roof.Angles or [1])
            if hasattr(roof, "Thickness"):
                roof.Thickness = v["thickness"]
            if hasattr(roof, "Overhang"):
                roof.Overhang = [float(v["overhang"])] * len(roof.Overhang or [1])
            roof.Label = "Roof"
        except Exception as exc:
            U.error(f"Roof creation failed: {exc}")
            return

        U.safe_recompute(doc)
        U.log("Roof and slab generated.")


# ---------------------------------------------------------------------------
# Quantity takeoff & cost estimate
# ---------------------------------------------------------------------------

class Arxio_Estimate:
    """Compute volumes and a rough cost estimate for the building."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_Estimate"),
            "MenuText": "Estimate & Quantities",
            "Accel": "A, E",
            "ToolTip": (
                "Compute wall / slab / roof volumes and a first-pass cost "
                "estimate using standard European unit prices."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        try:
            from PySide2 import QtWidgets
        except ImportError:  # pragma: no cover
            from PySide6 import QtWidgets  # type: ignore

        doc = FreeCAD.ActiveDocument
        walls = U.get_walls(doc)
        roofs = [o for o in doc.Objects if getattr(o, "IfcType", None) == "Roof"]
        slabs = [o for o in doc.Objects if getattr(o, "IfcType", None) == "Slab"]
        windows = [o for o in doc.Objects
                   if getattr(o, "IfcType", None) in ("Window", "Door")]

        def volume(objs) -> float:
            total = 0.0
            for o in objs:
                shape = getattr(o, "Shape", None)
                if shape is None:
                    continue
                try:
                    total += shape.Volume
                except Exception:
                    continue
            return total / 1e9  # mm³ → m³

        def area(objs) -> float:
            total = 0.0
            for o in objs:
                shape = getattr(o, "Shape", None)
                if shape is None:
                    continue
                try:
                    total += shape.Area
                except Exception:
                    continue
            return total / 1e6  # mm² → m²

        wall_vol = volume(walls)
        slab_vol = volume(slabs)
        roof_area = area(roofs)

        wall_cost = U.material_cost("Concrete block", wall_vol)
        slab_cost = U.material_cost("Concrete slab", slab_vol)
        roof_cost = U.material_cost("Tile roofing", roof_area)
        total_cost = wall_cost + slab_cost + roof_cost

        message = (
            f"<h3 style='color:#1f6feb;margin:0 0 12px 0;'>Arxio AI - "
            f"Quantity Takeoff</h3>"
            f"<table cellspacing='6' cellpadding='4'>"
            f"<tr><td><b>Walls</b></td><td>{len(walls)}</td>"
            f"<td>{wall_vol:.2f} m³</td><td>{wall_cost:,.0f} €</td></tr>"
            f"<tr><td><b>Slabs</b></td><td>{len(slabs)}</td>"
            f"<td>{slab_vol:.2f} m³</td><td>{slab_cost:,.0f} €</td></tr>"
            f"<tr><td><b>Roofs</b></td><td>{len(roofs)}</td>"
            f"<td>{roof_area:.2f} m²</td><td>{roof_cost:,.0f} €</td></tr>"
            f"<tr><td><b>Openings</b></td><td>{len(windows)}</td>"
            f"<td>-</td><td>-</td></tr>"
            f"</table>"
            f"<hr>"
            f"<p style='font-size:14px'><b>Total estimate:&nbsp;</b>"
            f"<span style='color:#2ea043;'>{total_cost:,.0f} €</span></p>"
            f"<p style='color:#8b949e;font-size:11px;'>"
            f"Prices are indicative and can be tuned in ArxioUtils.MATERIALS."
            f"</p>"
        )

        U.log(
            f"Estimate: walls {wall_vol:.2f} m³, slabs {slab_vol:.2f} m³, "
            f"roof {roof_area:.2f} m², total {total_cost:,.0f} €."
        )

        box = QtWidgets.QMessageBox(FreeCADGui.getMainWindow())
        box.setWindowTitle("Arxio AI - Estimate")
        box.setTextFormat(QtCore_TextFormat_Rich())
        box.setText(message)
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.exec_()


def QtCore_TextFormat_Rich():  # helper isolated for Qt5/6 compatibility
    try:
        from PySide2 import QtCore
    except ImportError:  # pragma: no cover
        from PySide6 import QtCore  # type: ignore
    return QtCore.Qt.RichText


# ---------------------------------------------------------------------------
# Sun study
# ---------------------------------------------------------------------------

def _solar_vector(lat_deg: float, lon_deg: float, month: int, day: int,
                  hour: float) -> FreeCAD.Vector:
    """Return a unit vector pointing towards the sun.

    Uses a compact Spencer / Cooper approximation - good enough to orient a
    building and to visualise shadows. Not a substitute for a full BIM solar
    analysis.
    """
    # Day of year (month/day → 1..365)
    month_offset = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    doy = month_offset[min(max(month - 1, 0), 11)] + min(max(day, 1), 31)

    # Declination (radians)
    decl = math.radians(23.45 * math.sin(2 * math.pi * (284 + doy) / 365))
    # Hour angle (degrees, 0 at solar noon, 15° per hour)
    hour_angle = math.radians(15.0 * (hour - 12.0))
    lat = math.radians(lat_deg)

    altitude = math.asin(
        math.sin(lat) * math.sin(decl)
        + math.cos(lat) * math.cos(decl) * math.cos(hour_angle)
    )
    azimuth = math.atan2(
        -math.sin(hour_angle),
        math.tan(decl) * math.cos(lat) - math.sin(lat) * math.cos(hour_angle),
    )
    # Convert to a unit vector: +X = east, +Y = north, +Z = up
    cos_alt = math.cos(altitude)
    sun_x = cos_alt * math.sin(azimuth)
    sun_y = cos_alt * math.cos(azimuth)
    sun_z = math.sin(altitude)
    v = FreeCAD.Vector(sun_x, sun_y, sun_z)
    if v.Length < 1e-6:
        return FreeCAD.Vector(0, 0, 1)
    v.normalize()
    return v


class Arxio_SunStudy:
    """Apply a solar direction light to the scene."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_SunStudy"),
            "MenuText": "Sun Study",
            "Accel": "A, S",
            "ToolTip": (
                "Compute the sun direction for the given location and date, "
                "and align the scene light."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        import ArxioTaskPanels as TP

        dialog = TP.SunStudyDialog(FreeCADGui.getMainWindow())
        if dialog.exec_() != dialog.Accepted:
            return
        v = dialog.values()
        direction = _solar_vector(
            v["latitude"], v["longitude"],
            v["month"], v["day"], v["hour"],
        )

        # Store the vector on the document so the user can replay it later.
        doc = U.ensure_document()
        sun = doc.getObject("ArxioSun") or doc.addObject(
            "App::FeaturePython", "ArxioSun"
        )
        if not hasattr(sun, "SunDirection"):
            sun.addProperty("App::PropertyVector", "SunDirection", "Arxio",
                            "Computed solar direction (East, North, Up).")
            sun.addProperty("App::PropertyFloat", "Altitude", "Arxio",
                            "Sun altitude in degrees.")
            sun.addProperty("App::PropertyFloat", "Azimuth", "Arxio",
                            "Sun azimuth in degrees (from North).")
        sun.SunDirection = direction
        sun.Altitude = math.degrees(math.asin(direction.z))
        sun.Azimuth = math.degrees(math.atan2(direction.x, direction.y))
        sun.Label = f"Sun ({v['month']:02d}/{v['day']:02d} - {v['hour']:.1f}h)"

        # Try to align the 3D view camera to point along -direction
        try:
            view = FreeCADGui.ActiveDocument.ActiveView
            view.setCameraOrientation(
                FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), direction)
            )
        except Exception:
            pass

        U.log(
            f"Sun direction set. Altitude {sun.Altitude:.1f}°, "
            f"azimuth {sun.Azimuth:.1f}°."
        )


# ---------------------------------------------------------------------------
# Auto plan - TechDraw page
# ---------------------------------------------------------------------------

class Arxio_AutoPlan:
    """Create a permit-ready TechDraw page with plan + elevations."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_AutoPlan"),
            "MenuText": "Auto Plan 2D",
            "Accel": "A, P",
            "ToolTip": (
                "Create a permit-ready TechDraw page with plan and two "
                "elevations at 1/50 scale."
            ),
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        import ArxioExporters as EX

        doc = FreeCAD.ActiveDocument
        if doc is None:
            U.error("Open or create a document first.")
            return
        try:
            page = EX.create_permit_page(doc)
            U.log(f"Permit page '{page.Label}' created.")
        except Exception as exc:
            U.error(f"Auto Plan failed: {exc}")


# ---------------------------------------------------------------------------
# Export PDF
# ---------------------------------------------------------------------------

class Arxio_ExportPDF:
    """Export the active TechDraw page to a PDF file."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_ExportPDF"),
            "MenuText": "Export PDF",
            "Accel": "A, X",
            "ToolTip": (
                "Export the active TechDraw page to a PDF file the client "
                "can print for the permit."
            ),
        }

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        return any(
            obj.TypeId == "TechDraw::DrawPage"
            for obj in FreeCAD.ActiveDocument.Objects
        )

    def Activated(self):
        try:
            from PySide2 import QtWidgets
        except ImportError:  # pragma: no cover
            from PySide6 import QtWidgets  # type: ignore

        import ArxioExporters as EX

        doc = FreeCAD.ActiveDocument
        pages = [obj for obj in doc.Objects
                 if obj.TypeId == "TechDraw::DrawPage"]
        if not pages:
            U.error(
                "No TechDraw page found. Run 'Auto Plan 2D' first to "
                "generate one."
            )
            return
        page = pages[0]

        default_name = (doc.Label or "Arxio_Plan") + ".pdf"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            FreeCADGui.getMainWindow(),
            "Arxio AI - Export permit plan",
            os.path.join(os.path.expanduser("~"), default_name),
            "PDF files (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        ok = EX.export_page_to_pdf(page, path)
        if ok:
            U.log(f"Plan exported: {path}")


# ---------------------------------------------------------------------------
# Welcome dialog
# ---------------------------------------------------------------------------

class Arxio_Welcome:
    """Show a friendly welcome screen."""

    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_Welcome"),
            "MenuText": "Welcome",
            "ToolTip": "Open the Arxio AI welcome screen.",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            from PySide2 import QtCore, QtWidgets
        except ImportError:  # pragma: no cover
            from PySide6 import QtCore, QtWidgets  # type: ignore

        text = (
            "<h2 style='color:#1f6feb;margin:0 0 8px 0;'>Welcome to Arxio AI</h2>"
            "<p style='color:#8b949e;margin:0 0 16px 0;'>Smart automation for"
            " architects.</p>"
            "<p><b>1. Preset House</b> - generate a full small house in one"
            " click.</p>"
            "<p><b>2. Fast Walls</b> - draw lines, turn them into 3D walls.</p>"
            "<p><b>3. Smart Openings</b> - add doors and windows on"
            " selected walls.</p>"
            "<p><b>4. Auto Roof &amp; Slab</b> - cap the building with a"
            " pitched roof and a ground slab.</p>"
            "<p><b>5. Estimate</b> - quantity takeoff and first-pass cost.</p>"
            "<p><b>6. Auto Plan &amp; Export PDF</b> - permit-ready plan"
            " at 1/50.</p>"
            "<p><b>7. Sun Study</b> - align the scene to a real-world sun"
            " direction.</p>"
            "<hr>"
            "<p style='color:#8b949e;font-size:11px;'>"
            "Arxio AI v" + U.BRAND_VERSION + " - built on the FreeCAD"
            " open-source platform."
            "</p>"
        )
        box = QtWidgets.QMessageBox(FreeCADGui.getMainWindow())
        box.setWindowTitle("Arxio AI")
        box.setTextFormat(QtCore.Qt.RichText)
        box.setText(text)
        icon = QtWidgets.QApplication.windowIcon()
        if icon is not None:
            box.setIconPixmap(icon.pixmap(64, 64))
        box.exec_()


# ---------------------------------------------------------------------------
# About dialog
# ---------------------------------------------------------------------------

class Arxio_About:
    def GetResources(self):
        return {
            "Pixmap": U.icon_path("Arxio_About"),
            "MenuText": "About Arxio AI",
            "ToolTip": "Open the About dialog.",
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            from PySide2 import QtCore, QtWidgets
        except ImportError:  # pragma: no cover
            from PySide6 import QtCore, QtWidgets  # type: ignore

        html = (
            f"<h2 style='color:#1f6feb;margin:0;'>Arxio AI</h2>"
            f"<p style='margin:0 0 12px 0;color:#8b949e;'>"
            f"{U.BRAND_TAGLINE}</p>"
            f"<p>Version <b>{U.BRAND_VERSION}</b></p>"
            f"<p>Automated toolkit for architects: generate walls, roofs,"
            f" openings, slabs, permit plans and cost estimates in"
            f" minutes.</p>"
            f"<hr>"
            f"<p style='color:#8b949e;font-size:11px;'>"
            f"Built on FreeCAD - licensed under the LGPL v2.1-or-later."
            f"</p>"
        )
        box = QtWidgets.QMessageBox(FreeCADGui.getMainWindow())
        box.setWindowTitle("About Arxio AI")
        box.setTextFormat(QtCore.Qt.RichText)
        box.setText(html)
        box.exec_()


# ---------------------------------------------------------------------------
# Command registration
# ---------------------------------------------------------------------------

_COMMANDS = {
    "Arxio_PresetHouse": Arxio_PresetHouse,
    "Arxio_FastWalls": Arxio_FastWalls,
    "Arxio_SmartOpenings": Arxio_SmartOpenings,
    "Arxio_AutoRoof": Arxio_AutoRoof,
    "Arxio_Estimate": Arxio_Estimate,
    "Arxio_SunStudy": Arxio_SunStudy,
    "Arxio_AutoPlan": Arxio_AutoPlan,
    "Arxio_ExportPDF": Arxio_ExportPDF,
    "Arxio_Welcome": Arxio_Welcome,
    "Arxio_About": Arxio_About,
}


for _name, _cls in _COMMANDS.items():
    FreeCADGui.addCommand(_name, _cls())
