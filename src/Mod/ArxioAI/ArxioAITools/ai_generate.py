# SPDX-License-Identifier: LGPL-2.1-or-later
"""Natural-language brief → Arch building plan.

Flow:
    1. User types a brief ("maison 3 chambres 90 m² salon au sud…").
    2. We ask the LLM for a structured JSON (rooms with axis-aligned
       rectangles).
    3. We validate, then build Draft wires + Arch walls in the active doc.

The JSON schema is intentionally flat and deterministic so the LLM
rarely gets it wrong. Failures are reported verbatim to the user.
"""

import FreeCAD

from ArxioAITools import ai


SYSTEM_PROMPT = """Tu es Arxio AI, un assistant d'architecture expert francophone.

Quand l'utilisateur décrit un bâtiment ou un appartement, tu réponds UNIQUEMENT
par un objet JSON (aucune explication, aucun texte avant ou après) respectant
exactement ce schéma :

{
  "name": "nom du projet, bref",
  "floor_height_mm": 2800,
  "rooms": [
    {
      "name": "Salon",
      "x_mm": 0,
      "y_mm": 0,
      "width_mm": 5000,
      "depth_mm": 4000,
      "openings": [
        {"kind": "door",   "side": "south", "offset_mm": 1500, "width_mm": 900,  "height_mm": 2100, "sill_mm": 0},
        {"kind": "window", "side": "south", "offset_mm": 3000, "width_mm": 1500, "height_mm": 1200, "sill_mm": 900}
      ]
    }
  ]
}

Règles strictes :
- toutes les dimensions en millimètres ;
- l'origine (0,0) est le coin sud-ouest du bâtiment ;
- les pièces sont des rectangles alignés sur les axes et ne se chevauchent pas ;
- "side" ∈ {"north","south","east","west"} ;
- `offset_mm` est mesuré depuis le coin sud-ouest de la pièce le long du côté choisi ;
- `width_mm`, `depth_mm` ≥ 1500 ; `height_mm` pour les ouvertures ≤ floor_height_mm ;
- nombre de pièces raisonnable (2 à 12) ;
- AUCUN commentaire, AUCUN markdown, AUCUN préfixe. Juste l'objet JSON.
"""


def generate_spec(brief):
    """Call the LLM and return a validated spec dict."""
    text = ai.ask(brief, system=SYSTEM_PROMPT)
    spec = ai.extract_json(text)
    _validate(spec)
    return spec


def _validate(spec):
    if not isinstance(spec, dict):
        raise ai.LLMError("La réponse IA n'est pas un objet JSON.")
    rooms = spec.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        raise ai.LLMError("La réponse IA ne contient aucune pièce.")
    for i, room in enumerate(rooms):
        for key in ("name", "x_mm", "y_mm", "width_mm", "depth_mm"):
            if key not in room:
                raise ai.LLMError(f"Pièce {i} : clé '{key}' manquante.")
        for key in ("x_mm", "y_mm", "width_mm", "depth_mm"):
            try:
                float(room[key])
            except (TypeError, ValueError) as exc:
                raise ai.LLMError(
                    f"Pièce {i} : valeur de '{key}' invalide ({exc})."
                ) from exc


def _make_room_walls(doc, room, floor_height):
    """Create the 4 walls of one rectangular room."""
    import Arch
    import Draft

    x = float(room["x_mm"])
    y = float(room["y_mm"])
    w = float(room["width_mm"])
    d = float(room["depth_mm"])

    p_sw = FreeCAD.Vector(x, y, 0)
    p_se = FreeCAD.Vector(x + w, y, 0)
    p_ne = FreeCAD.Vector(x + w, y + d, 0)
    p_nw = FreeCAD.Vector(x, y + d, 0)

    walls = []
    for a, b, side in (
        (p_sw, p_se, "south"),
        (p_se, p_ne, "east"),
        (p_ne, p_nw, "north"),
        (p_nw, p_sw, "west"),
    ):
        line = Draft.makeLine(a, b)
        line.Label = f"{room['name']}_{side}_base"
        wall = Arch.makeWall(line, height=floor_height, width=200.0, align="Center")
        wall.Label = f"{room['name']}_{side}"
        walls.append((wall, side))
    return walls


def _place_opening(doc, wall, side, opening, floor_height):
    """Place a door or window by creating a rectangular face on the wall."""
    import Arch
    import Draft

    kind = opening.get("kind", "window")
    width = float(opening.get("width_mm", 900))
    height = float(opening.get("height_mm", 2100 if kind == "door" else 1200))
    sill = float(opening.get("sill_mm", 0 if kind == "door" else 900))
    offset = float(opening.get("offset_mm", 0))

    # Sanity clamps
    if height > floor_height - 100:
        height = floor_height - 100
    if sill + height > floor_height:
        sill = max(0.0, floor_height - height - 50)

    base = wall.Placement.Base
    shape = getattr(wall, "Shape", None)
    if shape is None:
        return None

    # Build rectangle in the wall's local X (along base) plane.
    # We approximate by using the wall's base line direction.
    base_obj = getattr(wall, "Base", None)
    if base_obj is None or not base_obj.Shape.Edges:
        return None
    edge = base_obj.Shape.Edges[0]
    start = edge.Vertexes[0].Point
    end = edge.Vertexes[-1].Point
    direction = (end - start)
    length = direction.Length or 1.0
    unit = FreeCAD.Vector(direction.x / length, direction.y / length, 0.0)

    origin = start + unit.multiply(offset)
    z = sill
    p1 = FreeCAD.Vector(origin.x, origin.y, z)
    p2 = FreeCAD.Vector(origin.x + unit.x * width, origin.y + unit.y * width, z)
    p3 = FreeCAD.Vector(p2.x, p2.y, z + height)
    p4 = FreeCAD.Vector(origin.x, origin.y, z + height)

    rect = Draft.makeWire([p1, p2, p3, p4], closed=True, face=True)
    rect.Label = f"{wall.Label}_{kind}_profile"
    try:
        opening_obj = Arch.makeWindow(rect, width=width, height=height)
        opening_obj.Label = f"{wall.Label}_{kind}"
        Arch.addComponents(opening_obj, wall)
        return opening_obj
    except Exception as exc:  # pragma: no cover - surfaced to user
        FreeCAD.Console.PrintWarning(
            f"Arxio AI: opening placement failed ({exc}). Profil conservé.\n"
        )
        return None


def apply_spec(doc, spec):
    """Build the Arch geometry described by `spec` in `doc`.

    Returns a summary dict.
    """
    from ArxioAITools import project as aa_project

    floor_height = float(spec.get("floor_height_mm", 2800.0))
    site, building, floor = aa_project.setup_project(doc)

    created_rooms = []
    openings_count = 0

    for room in spec.get("rooms", []):
        walls = _make_room_walls(doc, room, floor_height)
        # Map side → wall for opening placement
        wall_by_side = {side: w for w, side in walls}
        for opening in room.get("openings", []) or []:
            side = opening.get("side", "south")
            wall = wall_by_side.get(side)
            if wall is None:
                continue
            result = _place_opening(doc, wall, side, opening, floor_height)
            if result is not None:
                openings_count += 1
        created_rooms.append(room["name"])

    doc.recompute()
    return {
        "project_name": spec.get("name", "Arxio_Project"),
        "rooms": created_rooms,
        "openings": openings_count,
        "floor_height_mm": floor_height,
    }


def prompt_brief():
    """Qt text dialog to capture the user's brief.

    Returns the trimmed string or None on cancel.
    """
    try:
        from PySide import QtWidgets
    except ImportError:  # pragma: no cover
        return None

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle("Arxio AI — Brief architectural")
    dlg.setMinimumSize(520, 320)
    layout = QtWidgets.QVBoxLayout(dlg)
    layout.addWidget(
        QtWidgets.QLabel(
            "Décrivez le bâtiment en langage naturel. Exemple :\n"
            "« Maison individuelle RDC, 90 m², 3 chambres, salon/cuisine au sud, "
            "salle de bain, hauteur 2,80 m. »"
        )
    )
    editor = QtWidgets.QPlainTextEdit()
    editor.setPlainText(
        "Maison RDC 90 m², salon/cuisine ouverts au sud, "
        "3 chambres côté nord, salle de bain, hauteur 2,80 m."
    )
    layout.addWidget(editor)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec_() != QtWidgets.QDialog.Accepted:
        return None
    return editor.toPlainText().strip()
