# Arxio AI — FreeCAD workbench

Arxio AI is an architectural-automation workbench that extends FreeCAD with
one-click tools for walls, slabs, roofs, openings, permit drawings and cost
estimation. It is designed to shorten the path from 2D sketch to buildable 3D
model + deliverable documents.

This module is built on top of [FreeCAD](https://www.freecad.org) and is
distributed under the same LGPL-2.1-or-later license. All FreeCAD copyrights
and attributions are preserved.

## Commands

| Command | Description |
|---|---|
| **Initialiser le projet** | Creates Site → Building → Floor scaffold. |
| **Murs rapides** | Converts selected 2D sketches/lines/wires into parametric Arch walls. Defaults read from `User parameter:BaseApp/Preferences/Mod/ArxioAI`. |
| **Toiture & dalle auto** | Generates a ground slab and a pitched roof sized to the selected walls. |
| **Placer portes & fenêtres** | Dialog-driven placement of doors and windows on the selected wall. |
| **Plans 2D automatiques** | Creates a TechDraw A3 landscape page with top + two elevations at 1:50. |
| **Métré & devis** | Reports volumes/areas/counts for walls, slabs, roof, openings and a cost total in configurable currency (default FCFA). |

## Preferences

Store a handful of floats under
`User parameter:BaseApp/Preferences/Mod/ArxioAI`:

- `WallHeight`, `WallWidth`, `WallAlign`
- `WallPricePerM3`, `SlabPricePerM3`, `RoofPricePerM2`
- `WindowPricePerUnit`, `DoorPricePerUnit`
- `Currency` (string, e.g. `FCFA`, `EUR`, `USD`)

Edit them via `Tools ▸ Edit parameters…` until a dedicated preferences page
ships.

## Dependencies

- `BIM` (Arch)
- `Draft`
- `TechDraw`
- `Part`

These are enabled by default in a standard FreeCAD build.

## Building

The module is pure Python. It is enabled via the CMake option
`-DBUILD_ARXIO_AI=ON` (default `ON`).

```
cmake -S . -B build -DBUILD_ARXIO_AI=ON
cmake --build build
cmake --install build
```

After install, launch FreeCAD and choose the **Arxio AI** workbench from the
workbench selector.
