<p align="center">
  <img src="src/Mod/Arxio/Resources/icons/ArxioWorkbench.svg" width="96" height="96" alt="Arxio AI"/>
</p>

<h1 align="center">Arxio AI</h1>
<p align="center"><em>Smart automation for architects — from sketch to permit in minutes.</em></p>

---

## What is Arxio AI?

**Arxio AI** is an opinionated, automation-first architecture workbench.
It gives architects a small, carefully curated set of one-click tools
that turn 2D sketches into a permit-ready 3D building — walls, doors,
windows, roof, slab, estimate and printed plan — without having to
learn a full parametric CAD application first.

Arxio AI is built on top of the battle-tested
[FreeCAD](https://www.freecad.org) kernel, so every object remains a
fully editable, IFC-compatible BIM model. You keep every door you want
open: edit the details, export to IFC/DXF/PDF, collaborate with any BIM
partner.

## Key features

| Command            | What it does                                                              |
|--------------------|---------------------------------------------------------------------------|
| 🏠 Preset House    | Generate a full single-story house (walls, door, windows, slab, roof).    |
| 🧱 Fast Walls      | Turn every selected line, rectangle or sketch into a 3D wall.             |
| 🚪 Smart Openings  | Place doors or windows on any selected wall with a single click.          |
| 🏚 Auto Roof & Slab| Cap the building with a pitched roof and drop a ground slab underneath.  |
| 📊 Estimate        | Quantity takeoff + first-pass cost estimate using standard unit prices.   |
| ☀️ Sun Study       | Compute the sun direction for any site, date and hour.                    |
| 📜 Auto Plan 2D    | Create a permit-ready TechDraw page with plan and elevations at 1/50.     |
| 📄 Export PDF      | Export the active plan to a printable PDF.                                |

## Quick start

1. Open FreeCAD.
2. Switch the workbench selector to **Arxio AI**.
3. Click **Preset House** (shortcut `A, H`) and pick your dimensions.
4. Run **Auto Plan 2D** to generate the permit page.
5. Run **Export PDF** to share the drawing with your client.

## Building from source

Arxio AI ships as a standard FreeCAD module. The build system already
knows about it (`BUILD_ARXIO`, default `ON`). Follow the [FreeCAD
Developers Handbook](https://freecad.github.io/DevelopersHandbook/) for
platform-specific instructions, then build as usual:

```bash
cmake -S . -B build -DBUILD_ARXIO=ON
cmake --build build --parallel
```

The workbench is pure Python — there is no native code to cross-compile.

## Licensing & attribution

- Arxio AI source code: **LGPL v2.1 or later** (same as FreeCAD).
- Built on top of FreeCAD © the FreeCAD developers. See `LICENSE` for
  the full text and the upstream attribution.

## Support

- Documentation: inside the workbench (`Arxio AI → Welcome`).
- Website: <https://arxio.ai>
- Contact: hello@arxio.ai
