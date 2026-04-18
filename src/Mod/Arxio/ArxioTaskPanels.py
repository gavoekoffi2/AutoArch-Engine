# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - Parameter dialogs (task panels)                            *
# *   Copyright (c) 2026 Arxio AI                                           *
# ***************************************************************************

"""Qt task panels / dialogs used by the Arxio AI commands.

Each panel is self-contained and returns a plain dictionary of user inputs
through its ``values()`` method. That keeps the commands testable and avoids
tight coupling to the Qt event loop.
"""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - GUI-only imports
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:  # pragma: no cover - FreeCAD Qt6 fallback
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore


import ArxioUtils as U


# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------

_BRAND_QSS = """
QDialog {
    background: #0f1419;
    color: #e6edf3;
}
QLabel#arxioTitle {
    color: #7ee8fa;
    font-size: 18px;
    font-weight: 600;
    padding-bottom: 4px;
}
QLabel#arxioSubtitle {
    color: #9aa5b1;
    font-size: 11px;
}
QLabel {
    color: #e6edf3;
}
QPushButton {
    background: #1f6feb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 500;
}
QPushButton:hover { background: #388bfd; }
QPushButton:disabled { background: #30363d; color: #6e7681; }
QPushButton#secondary {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
}
QPushButton#secondary:hover { background: #30363d; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #1f6feb;
}
QGroupBox {
    color: #9aa5b1;
    font-weight: 500;
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
"""


def _style(dialog: QtWidgets.QDialog) -> None:
    dialog.setStyleSheet(_BRAND_QSS)


def _header(title: str, subtitle: str) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    v = QtWidgets.QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 8)
    v.setSpacing(2)
    t = QtWidgets.QLabel(title)
    t.setObjectName("arxioTitle")
    s = QtWidgets.QLabel(subtitle)
    s.setObjectName("arxioSubtitle")
    v.addWidget(t)
    v.addWidget(s)
    return w


def _buttons(dialog: QtWidgets.QDialog, ok_text: str = "Generate") -> QtWidgets.QDialogButtonBox:
    box = QtWidgets.QDialogButtonBox()
    cancel = box.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
    cancel.setObjectName("secondary")
    ok = box.addButton(ok_text, QtWidgets.QDialogButtonBox.AcceptRole)
    box.accepted.connect(dialog.accept)
    box.rejected.connect(dialog.reject)
    return box


# ---------------------------------------------------------------------------
# Walls parameters
# ---------------------------------------------------------------------------

class WallsDialog(QtWidgets.QDialog):
    """Collect wall generation parameters."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None,
                 defaults: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Arxio AI - Fast Walls")
        self.setMinimumWidth(420)
        _style(self)
        d = defaults or {}

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(_header("Fast Walls", "Turn 2D sketches into 3D walls."))

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        self.height = QtWidgets.QDoubleSpinBox()
        self.height.setRange(500, 20000)
        self.height.setSingleStep(100)
        self.height.setSuffix(" mm")
        self.height.setValue(d.get("height", 3000))

        self.width = QtWidgets.QDoubleSpinBox()
        self.width.setRange(50, 2000)
        self.width.setSingleStep(10)
        self.width.setSuffix(" mm")
        self.width.setValue(d.get("width", 200))

        self.alignment = QtWidgets.QComboBox()
        self.alignment.addItems(["Center", "Left", "Right"])
        self.alignment.setCurrentText(d.get("alignment", "Center"))

        self.material = QtWidgets.QComboBox()
        self.material.addItems(U.material_names())
        self.material.setCurrentText(d.get("material", "Concrete block"))

        form.addRow("Wall height:", self.height)
        form.addRow("Wall thickness:", self.width)
        form.addRow("Alignment:", self.alignment)
        form.addRow("Material:", self.material)
        root.addLayout(form)

        root.addStretch(1)
        root.addWidget(_buttons(self, "Generate walls"))

    def values(self) -> dict:
        return {
            "height": self.height.value(),
            "width": self.width.value(),
            "alignment": self.alignment.currentText(),
            "material": self.material.currentText(),
        }


# ---------------------------------------------------------------------------
# Roof parameters
# ---------------------------------------------------------------------------

class RoofDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None,
                 defaults: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Arxio AI - Auto Roof & Slab")
        self.setMinimumWidth(420)
        _style(self)
        d = defaults or {}

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(_header("Auto Roof & Slab",
                               "Cap the building with a roof and a ground slab."))

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        self.pitch = QtWidgets.QDoubleSpinBox()
        self.pitch.setRange(0, 75)
        self.pitch.setSingleStep(5)
        self.pitch.setSuffix(" °")
        self.pitch.setValue(d.get("pitch", 30))

        self.thickness = QtWidgets.QDoubleSpinBox()
        self.thickness.setRange(80, 600)
        self.thickness.setSingleStep(10)
        self.thickness.setSuffix(" mm")
        self.thickness.setValue(d.get("thickness", 200))

        self.overhang = QtWidgets.QDoubleSpinBox()
        self.overhang.setRange(0, 2000)
        self.overhang.setSingleStep(50)
        self.overhang.setSuffix(" mm")
        self.overhang.setValue(d.get("overhang", 400))

        self.add_slab = QtWidgets.QCheckBox("Generate ground slab")
        self.add_slab.setChecked(d.get("slab", True))

        self.slab_thickness = QtWidgets.QDoubleSpinBox()
        self.slab_thickness.setRange(80, 600)
        self.slab_thickness.setSingleStep(10)
        self.slab_thickness.setSuffix(" mm")
        self.slab_thickness.setValue(d.get("slab_thickness", 200))

        form.addRow("Roof pitch:", self.pitch)
        form.addRow("Roof thickness:", self.thickness)
        form.addRow("Overhang:", self.overhang)
        form.addRow("", self.add_slab)
        form.addRow("Slab thickness:", self.slab_thickness)
        root.addLayout(form)

        root.addStretch(1)
        root.addWidget(_buttons(self, "Generate"))

    def values(self) -> dict:
        return {
            "pitch": self.pitch.value(),
            "thickness": self.thickness.value(),
            "overhang": self.overhang.value(),
            "slab": self.add_slab.isChecked(),
            "slab_thickness": self.slab_thickness.value(),
        }


# ---------------------------------------------------------------------------
# Preset house parameters
# ---------------------------------------------------------------------------

class PresetHouseDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Arxio AI - Preset House")
        self.setMinimumWidth(460)
        _style(self)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(_header(
            "Preset House",
            "Generate a complete small house (walls, openings, roof, slab)."
        ))

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        self.length = QtWidgets.QDoubleSpinBox()
        self.length.setRange(4000, 30000)
        self.length.setSingleStep(500)
        self.length.setSuffix(" mm")
        self.length.setValue(10000)

        self.width = QtWidgets.QDoubleSpinBox()
        self.width.setRange(4000, 30000)
        self.width.setSingleStep(500)
        self.width.setSuffix(" mm")
        self.width.setValue(8000)

        self.height = QtWidgets.QDoubleSpinBox()
        self.height.setRange(2200, 6000)
        self.height.setSingleStep(100)
        self.height.setSuffix(" mm")
        self.height.setValue(2800)

        self.doors = QtWidgets.QSpinBox()
        self.doors.setRange(1, 6)
        self.doors.setValue(1)

        self.windows = QtWidgets.QSpinBox()
        self.windows.setRange(0, 20)
        self.windows.setValue(4)

        self.pitch = QtWidgets.QDoubleSpinBox()
        self.pitch.setRange(0, 60)
        self.pitch.setSingleStep(5)
        self.pitch.setSuffix(" °")
        self.pitch.setValue(30)

        form.addRow("House length (X):", self.length)
        form.addRow("House width (Y):", self.width)
        form.addRow("Wall height:", self.height)
        form.addRow("Doors:", self.doors)
        form.addRow("Windows:", self.windows)
        form.addRow("Roof pitch:", self.pitch)
        root.addLayout(form)

        root.addStretch(1)
        root.addWidget(_buttons(self, "Build my house"))

    def values(self) -> dict:
        return {
            "length": self.length.value(),
            "width": self.width.value(),
            "height": self.height.value(),
            "doors": self.doors.value(),
            "windows": self.windows.value(),
            "pitch": self.pitch.value(),
        }


# ---------------------------------------------------------------------------
# Openings parameters
# ---------------------------------------------------------------------------

class OpeningsDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Arxio AI - Smart Openings")
        self.setMinimumWidth(420)
        _style(self)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(_header("Smart Openings",
                               "Place doors and windows on the selected walls."))

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        self.kind = QtWidgets.QComboBox()
        self.kind.addItems(["Door", "Window"])

        self.opening_width = QtWidgets.QDoubleSpinBox()
        self.opening_width.setRange(400, 5000)
        self.opening_width.setSingleStep(50)
        self.opening_width.setSuffix(" mm")
        self.opening_width.setValue(900)

        self.opening_height = QtWidgets.QDoubleSpinBox()
        self.opening_height.setRange(400, 5000)
        self.opening_height.setSingleStep(50)
        self.opening_height.setSuffix(" mm")
        self.opening_height.setValue(2100)

        self.sill = QtWidgets.QDoubleSpinBox()
        self.sill.setRange(0, 3000)
        self.sill.setSingleStep(50)
        self.sill.setSuffix(" mm")
        self.sill.setValue(0)

        self.position = QtWidgets.QComboBox()
        self.position.addItems(["Middle", "One third", "Two thirds"])

        form.addRow("Opening type:", self.kind)
        form.addRow("Opening width:", self.opening_width)
        form.addRow("Opening height:", self.opening_height)
        form.addRow("Sill height:", self.sill)
        form.addRow("Position along wall:", self.position)
        root.addLayout(form)

        root.addStretch(1)
        root.addWidget(_buttons(self, "Place openings"))

        self.kind.currentTextChanged.connect(self._sync_defaults)

    def _sync_defaults(self, kind: str) -> None:
        if kind == "Window":
            self.opening_width.setValue(1200)
            self.opening_height.setValue(1200)
            self.sill.setValue(900)
        else:
            self.opening_width.setValue(900)
            self.opening_height.setValue(2100)
            self.sill.setValue(0)

    def values(self) -> dict:
        return {
            "kind": self.kind.currentText(),
            "width": self.opening_width.value(),
            "height": self.opening_height.value(),
            "sill": self.sill.value(),
            "position": self.position.currentText(),
        }


# ---------------------------------------------------------------------------
# Sun-study parameters
# ---------------------------------------------------------------------------

class SunStudyDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Arxio AI - Sun Study")
        self.setMinimumWidth(420)
        _style(self)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(_header(
            "Sun Study", "Simulate the sun direction for the given site."
        ))

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        self.latitude = QtWidgets.QDoubleSpinBox()
        self.latitude.setRange(-90, 90)
        self.latitude.setDecimals(4)
        self.latitude.setSuffix(" °")
        self.latitude.setValue(48.8566)  # Paris

        self.longitude = QtWidgets.QDoubleSpinBox()
        self.longitude.setRange(-180, 180)
        self.longitude.setDecimals(4)
        self.longitude.setSuffix(" °")
        self.longitude.setValue(2.3522)

        self.month = QtWidgets.QSpinBox()
        self.month.setRange(1, 12)
        self.month.setValue(6)

        self.day = QtWidgets.QSpinBox()
        self.day.setRange(1, 31)
        self.day.setValue(21)

        self.hour = QtWidgets.QDoubleSpinBox()
        self.hour.setRange(0, 23.99)
        self.hour.setSingleStep(0.5)
        self.hour.setSuffix(" h")
        self.hour.setValue(12.0)

        form.addRow("Site latitude:", self.latitude)
        form.addRow("Site longitude:", self.longitude)
        form.addRow("Month:", self.month)
        form.addRow("Day of month:", self.day)
        form.addRow("Solar time (h):", self.hour)
        root.addLayout(form)

        root.addStretch(1)
        root.addWidget(_buttons(self, "Apply sun direction"))

    def values(self) -> dict:
        return {
            "latitude": self.latitude.value(),
            "longitude": self.longitude.value(),
            "month": self.month.value(),
            "day": self.day.value(),
            "hour": self.hour.value(),
        }
