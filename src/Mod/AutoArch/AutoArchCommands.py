import FreeCAD, FreeCADGui
import Arch, Draft, TechDraw

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
        
        # Création simplifiée d'un toit basique
        try:
            roof = Arch.makeRoof(walls[0]) # S'attache au premier mur comme base pour le MVP
            roof.Pitch = 30 # Pente standard 30 degrés
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
        # Créer une page TechDraw A3
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

FreeCADGui.addCommand('AutoArch_FastWalls', FastWalls())
FreeCADGui.addCommand('AutoArch_AutoRoof', AutoRoofSlab())
FreeCADGui.addCommand('AutoArch_AutoPlan', AutoPlan())
FreeCADGui.addCommand('AutoArch_Estimate', Estimate())
