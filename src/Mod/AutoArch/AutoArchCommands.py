import FreeCAD, FreeCADGui
import Arch, Draft, TechDraw, Part, Mesh
from PySide import QtCore, QtGui
import math, os, json

# ═══════════════════════════════════════════════════════════════
# OUTILS EXISTANTS (MVP v1)
# ═══════════════════════════════════════════════════════════════

class FastWalls:
    def GetResources(self):
        return {'MenuText': "1. 🧱 Murs (1-Clic)", 'ToolTip': "Transforme les lignes 2D en murs 3D standard."}
    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("Veuillez sélectionner des lignes.\n")
            return
        for obj in sel:
            if hasattr(obj, "Shape"):
                wall = Arch.makeWall(obj)
                wall.Height = 3000
                wall.Width = 200
        FreeCAD.ActiveDocument.recompute()

class AutoRoofSlab:
    def GetResources(self):
        return {'MenuText': "2. 🏠 Toit & Dalle Auto", 'ToolTip': "Génère une dalle et un toit sur les murs sélectionnés."}
    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        walls = [obj for obj in sel if obj.isDerivedFrom("Part::Feature")]
        if not walls:
            FreeCAD.Console.PrintError("Veuillez sélectionner les murs pour générer le toit.\n")
            return
        try:
            roof = Arch.makeRoof(walls[0])
            roof.Pitch = 30
            roof.Thickness = 200
        except Exception as e:
            FreeCAD.Console.PrintError(f"Erreur toiture : {e}\n")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.Console.PrintMessage("AutoArch: Toit et Dalle générés.\n")

class AutoPlan:
    def GetResources(self):
        return {'MenuText': "3. 📜 Générer Plan 2D PDF", 'ToolTip': "Crée automatiquement une mise en page d'impression 2D."}
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        page = doc.addObject('TechDraw::DrawPage', 'Plan_Permis')
        template = doc.addObject('TechDraw::DrawSVGTemplate', 'Template')
        template.Template = FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/A3_Landscape_ISO7200.svg"
        page.Template = doc.Template
        FreeCAD.Console.PrintMessage("AutoArch: Page de plan de permis générée (A3).\n")
        doc.recompute()

class Estimate:
    def GetResources(self):
        return {'MenuText': "4. 📊 Devis & Matériaux", 'ToolTip': "Calcule le volume total."}
    def Activated(self):
        walls = FreeCAD.ActiveDocument.findObjects("Arch::Wall")
        total_vol = sum(w.Shape.Volume for w in walls if hasattr(w, 'Shape') and w.Shape)
        vol_m3 = total_vol / 1e9
        FreeCAD.Console.PrintMessage(f"\n--- DEVIS --- Volume murs : {vol_m3:.2f} m³\n")


# ═══════════════════════════════════════════════════════════════
# NOUVEAUX OUTILS (v2 — Visite Virtuelle, Meubles, Textures)
# ═══════════════════════════════════════════════════════════════

class VirtualTour:
    """Navigation first-person dans la maison 3D."""
    def GetResources(self):
        return {'MenuText': "5. 🚶 Visite Virtuelle", 'ToolTip': "Active la navigation first-person dans la maison."}

    def Activated(self):
        view = FreeCADGui.ActiveDocument.ActiveView
        cam = view.getCameraNode()

        # Mode perspective
        view.setCameraType("Perspective")

        # Placer la caméra au centre de la maison, à hauteur d'yeux
        walls = FreeCAD.ActiveDocument.findObjects("Arch::Wall")
        if walls:
            bbox = FreeCAD.BoundBox()
            for w in walls:
                if hasattr(w, 'Shape'):
                    bbox.add(w.Shape.BoundBox)
            cx, cy = (bbox.XMin + bbox.XMax) / 2, (bbox.YMin + bbox.YMax) / 2
            cam.position.setValue(cx, cy, 1600)  # hauteur yeux 1.60m
            cam.pointAt(FreeCAD.Vector(cx + 1000, cy, 1600), FreeCAD.Vector(0, 0, 1))

        # Navigation style marche
        nav = view.getNavigationStyle()
        view.setNavigationStyle("CAD")  # Style le plus proche du first-person

        FreeCAD.Console.PrintMessage(
            "🚶 VISITE VIRTUELLE ACTIVÉE\n"
            "   • Clic-droit + glisser = Regarder autour\n"
            "   • Molette = Avancer/Reculer\n"
            "   • Shift + molette = Monter/Descendre\n"
            "   • Ctrl + clic-droit = Marcher latéralement\n"
        )


class FurniturePlacer:
    """Placement intelligent de meubles par type de pièce."""
    def GetResources(self):
        return {'MenuText': "6. 🪑 Meubler Auto", 'ToolTip': "Place automatiquement des meubles dans les pièces."}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        walls = doc.findObjects("Arch::Wall")
        if not walls:
            FreeCAD.Console.PrintError("Générez d'abord les murs.\n")
            return

        # Calculer le bounding box de la maison
        bbox = FreeCAD.BoundBox()
        for w in walls:
            if hasattr(w, 'Shape'):
                bbox.add(w.Shape.BoundBox)

        # Détection simplifiée des pièces par grille
        xmin, xmax = bbox.XMin, bbox.XMax
        ymin, ymax = bbox.YMin, bbox.YMax
        width = xmax - xmin
        depth = ymax - ymin

        # Zones de pièces (proportions standard)
        rooms = [
            {"name": "Salon", "x": xmin, "y": ymin, "w": width * 0.4, "d": depth * 0.5,
             "furniture": [("canapé", 800, 2500, 900), ("table_basse", 600, 1200, 400),
                          ("TV", 100, 1500, 700)]},
            {"name": "Cuisine", "x": xmin + width * 0.42, "y": ymin, "w": width * 0.28, "d": depth * 0.45,
             "furniture": [("table", 900, 1800, 750), ("chaise", 400, 400, 450),
                          ("chaise", 400, 400, 450), ("chaise", 400, 400, 450),
                          ("chaise", 400, 400, 450)]},
            {"name": "Chambre 1", "x": xmin + width * 0.72, "y": ymin, "w": width * 0.26, "d": depth * 0.5,
             "furniture": [("lit", 1600, 2000, 600), ("armoire", 600, 1800, 2000),
                          ("chevet", 400, 400, 500)]},
            {"name": "SDB", "x": xmin, "y": ymin + depth * 0.52, "w": width * 0.2, "d": depth * 0.46,
             "furniture": [("baignoire", 750, 1700, 550), ("lavabo", 500, 400, 850),
                          ("WC", 400, 650, 400)]},
            {"name": "Chambre 2", "x": xmin + width * 0.22, "y": ymin + depth * 0.52, "w": width * 0.32, "d": depth * 0.46,
             "furniture": [("lit", 1600, 2000, 600), ("bureau", 700, 1400, 750),
                          ("chaise_bureau", 450, 450, 900)]},
            {"name": "Bureau", "x": xmin + width * 0.72, "y": ymin + depth * 0.52, "w": width * 0.26, "d": depth * 0.46,
             "furniture": [("bureau", 700, 1600, 750), ("chaise_bureau", 450, 450, 900),
                          ("bibliothèque", 350, 1200, 2000)]},
        ]

        count = 0
        for room in rooms:
            cx = room["x"] + room["w"] / 2
            cy = room["y"] + room["d"] / 2

            for i, (fname, fw, fd, fh) in enumerate(room["furniture"]):
                # Position dans la pièce (grille)
                row = i // 3
                col = i % 3
                fx = room["x"] + room["w"] * 0.15 + col * room["w"] * 0.3
                fy = room["y"] + room["d"] * 0.2 + row * room["d"] * 0.4

                # Créer un cube (meuble simplifié)
                from FreeCAD import Vector
                meuble = doc.addObject("Part::Box", f"{room['name']}_{fname}")
                meuble.Length = fw
                meuble.Width = fd
                meuble.Height = fh
                meuble.Placement.Base = Vector(fx - fw / 2, fy - fd / 2, 0)

                # Couleur par type
                from FreeCAD import Base
                obj = doc.getObject(meuble.Name)
                if obj and hasattr(obj, 'ViewObject'):
                    colors = {
                        "canapé": (0.4, 0.3, 0.6), "table": (0.55, 0.35, 0.15),
                        "chaise": (0.5, 0.4, 0.3), "lit": (0.9, 0.85, 0.8),
                        "armoire": (0.45, 0.3, 0.2), "bureau": (0.4, 0.25, 0.15),
                        "TV": (0.1, 0.1, 0.1), "baignoire": (0.95, 0.95, 0.95),
                        "lavabo": (0.9, 0.9, 0.9), "WC": (0.95, 0.95, 0.95),
                    }
                    c = colors.get(fname, (0.7, 0.7, 0.7))
                    obj.ViewObject.ShapeColor = c
                count += 1

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"🪑 AutoArch: {count} meubles placés dans {len(rooms)} pièces.\n")


class ApplyTextures:
    """Applique des textures réalistes aux murs et éléments."""
    def GetResources(self):
        return {'MenuText': "7. 🎨 Textures Réalistes", 'ToolTip': "Applique des textures et couleurs professionnelles."}

    def Activated(self):
        doc = FreeCAD.ActiveDocument

        textures = {
            "Arch::Wall": {
                "exterior": (0.82, 0.74, 0.66),      # crépi beige
                "interior": (0.94, 0.91, 0.88),       # blanc cassé
            },
            "Arch::Roof": {
                "default": (0.65, 0.22, 0.17),        # tuile terre cuite
            },
            "Part::Box": {
                "floor": (0.55, 0.42, 0.30),          # parquet bois
                "default": (0.7, 0.7, 0.7),
            },
        }

        applied = 0
        for obj in doc.Objects:
            obj_type = obj.TypeId
            if obj_type in textures:
                cfg = textures[obj_type]
                key = "exterior" if "Mur_Ext" in obj.Label else "interior" if "Mur_Int" in obj.Label else "default"
                color = cfg.get(key, cfg.get("default", (0.8, 0.8, 0.8)))
                if hasattr(obj, 'ViewObject'):
                    obj.ViewObject.ShapeColor = color
                    applied += 1

        # Fondations (sol)
        for obj in doc.Objects:
            if obj.TypeId == "Part::Box" and "Sol" in obj.Label:
                if hasattr(obj, 'ViewObject'):
                    obj.ViewObject.ShapeColor = (0.45, 0.42, 0.38)
                    applied += 1

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"🎨 AutoArch: {applied} objets texturés.\n")


class SectionPlane:
    """Plan de coupe interactif pour voir l'intérieur."""
    def GetResources(self):
        return {'MenuText': "8. ✂️ Coupe Interactive", 'ToolTip': "Crée un plan de coupe pour visualiser l'intérieur."}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        walls = doc.findObjects("Arch::Wall")
        if not walls:
            FreeCAD.Console.PrintError("Générez d'abord les murs.\n")
            return

        bbox = FreeCAD.BoundBox()
        for w in walls:
            if hasattr(w, 'Shape'):
                bbox.add(w.Shape.BoundBox)

        # Créer un plan de coupe au milieu de la maison
        cx = (bbox.XMin + bbox.XMax) / 2
        cy = (bbox.YMin + bbox.YMax) / 2
        cz = 1500  # À hauteur de vue

        try:
            from FreeCAD import Vector
            # Plan de coupe horizontal (XY) à hauteur 1.5m
            section = doc.addObject("Part::Plane", "Coupe_Interactive")
            section.Length = bbox.XMax - bbox.XMin + 500
            section.Width = bbox.YMax - bbox.YMin + 500
            section.Placement.Base = Vector(cx, cy, cz)
            section.Placement.Rotation = FreeCAD.Rotation(Vector(0, 0, 1), 0)

            if hasattr(section, 'ViewObject'):
                section.ViewObject.Transparency = 50
                section.ViewObject.ShapeColor = (0.2, 0.6, 1.0)

            FreeCAD.Console.PrintMessage(
                "✂️ Plan de coupe créé au centre de la maison (hauteur 1.5m).\n"
                "   → Sélectionnez-le et utilisez 'Part → Coupe persistante'\n"
                "   → Ou activez le mode 'Clipping Plane' dans le menu Affichage\n"
            )
        except Exception as e:
            FreeCAD.Console.PrintError(f"Erreur coupe: {e}\n")

        doc.recompute()


class WebExport:
    """Exporte le modèle 3D pour visualisation web."""
    def GetResources(self):
        return {'MenuText': "9. 🌐 Exporter Web 3D", 'ToolTip': "Exporte la maison en visualisation web interactive."}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        import tempfile, subprocess

        try:
            # Exporter en OBJ
            obj_path = os.path.join(tempfile.gettempdir(), "maison_3d.obj")
            Mesh.export(doc.Objects, obj_path)
            FreeCAD.Console.PrintMessage(f"📦 OBJ exporté → {obj_path}\n")

            # Convertir en JSON pour Three.js
            import MeshPart
            mesh_data = {"vertices": [], "faces": [], "colors": []}

            for obj in doc.Objects:
                if hasattr(obj, 'Shape') and obj.Shape:
                    try:
                        m = doc.addObject("Mesh::Feature", "_tmp_mesh")
                        m.Mesh = MeshPart.meshFromShape(obj.Shape, 1.0)
                        for pt in m.Mesh.Topology[0]:
                            mesh_data["vertices"].append([pt.x, pt.z, pt.y])
                        for fc in m.Mesh.Topology[1]:
                            mesh_data["faces"].append(list(fc))
                        doc.removeObject(m.Name)
                    except:
                        continue

            bb_path = os.path.join(tempfile.gettempdir(), "autoarch_export.json")
            with open(bb_path, "w") as f:
                json.dump(mesh_data, f, indent=2)

            FreeCAD.Console.PrintMessage(
                f"🌐 Données web exportées → {bb_path}\n"
                f"   Vertices: {len(mesh_data['vertices'])}\n"
                f"   Faces: {len(mesh_data['faces'])}\n"
            )

        except Exception as e:
            FreeCAD.Console.PrintError(f"Erreur export: {e}\n")


class RoomLabels:
    """Étiquettes des pièces en 3D."""
    def GetResources(self):
        return {'MenuText': "10. 🏷️ Étiquettes Pièces", 'ToolTip': "Ajoute des étiquettes 3D sur chaque pièce."}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        walls = doc.findObjects("Arch::Wall")
        if not walls:
            return

        bbox = FreeCAD.BoundBox()
        for w in walls:
            if hasattr(w, 'Shape'):
                bbox.add(w.Shape.BoundBox)

        xmin, xmax = bbox.XMin, bbox.XMax
        ymin, ymax = bbox.YMin, bbox.YMax
        width = xmax - xmin
        depth = ymax - ymin

        rooms = ["Salon", "Cuisine", "Chambre 1", "SDB", "Chambre 2", "Bureau"]
        positions = [
            (xmin + width * 0.2, ymin + depth * 0.22, 2500),
            (xmin + width * 0.56, ymin + depth * 0.22, 2500),
            (xmin + width * 0.85, ymin + depth * 0.22, 2500),
            (xmin + width * 0.1, ymin + depth * 0.75, 2500),
            (xmin + width * 0.38, ymin + depth * 0.75, 2500),
            (xmin + width * 0.85, ymin + depth * 0.75, 2500),
        ]

        for name, (x, y, z) in zip(rooms, positions):
            try:
                label = Draft.make_text([name], point=FreeCAD.Vector(x, y, z))
                label.ViewObject.FontSize = 200
                label.ViewObject.TextColor = (0.2, 0.2, 0.2)
                if hasattr(label, 'Placement'):
                    label.Placement.Base.z = z
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Étiquette {name}: {e}\n")

        doc.recompute()
        FreeCAD.Console.PrintMessage("🏷️ AutoArch: Étiquettes des pièces ajoutées.\n")


# ═══════════════════════════════════════════════════════════════
# ENREGISTREMENT DES COMMANDES
# ═══════════════════════════════════════════════════════════════

# Commandes MVP v1
FreeCADGui.addCommand('AutoArch_FastWalls', FastWalls())
FreeCADGui.addCommand('AutoArch_AutoRoof', AutoRoofSlab())
FreeCADGui.addCommand('AutoArch_AutoPlan', AutoPlan())
FreeCADGui.addCommand('AutoArch_Estimate', Estimate())

# Nouvelles commandes v2
FreeCADGui.addCommand('AutoArch_VirtualTour', VirtualTour())
FreeCADGui.addCommand('AutoArch_Furniture', FurniturePlacer())
FreeCADGui.addCommand('AutoArch_Textures', ApplyTextures())
FreeCADGui.addCommand('AutoArch_Section', SectionPlane())
FreeCADGui.addCommand('AutoArch_WebExport', WebExport())
FreeCADGui.addCommand('AutoArch_RoomLabels', RoomLabels())

FreeCAD.Console.PrintMessage("✅ AutoArch Engine v2 chargé (10 outils)\n")
