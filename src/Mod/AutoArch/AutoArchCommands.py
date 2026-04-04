import FreeCAD, FreeCADGui
import Arch, Draft

class FastWalls:
    def GetResources(self):
        return {'MenuText': "🏗️ Générer Murs (1-Clic)", 'ToolTip': "Transforme les lignes 2D sélectionnées en murs 3D standard (3m hauteur, 20cm épaisseur)."}
    
    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("AutoArch: Veuillez d'abord sélectionner des lignes 2D.\n")
            return
        for obj in sel:
            if hasattr(obj, "Shape"):
                wall = Arch.makeWall(obj)
                wall.Height = 3000 # 3 mètres
                wall.Width = 200   # 20 centimètres
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.Console.PrintMessage("AutoArch: Murs générés avec succès.\n")

class Estimate:
    def GetResources(self):
        return {'MenuText': "📊 Estimateur de Matériaux", 'ToolTip': "Calcule automatiquement le volume total de béton/matériaux pour le devis."}
    
    def Activated(self):
        walls = FreeCAD.ActiveDocument.findObjects("Arch::Wall")
        total_vol = 0
        for w in walls:
            if hasattr(w, 'Shape') and w.Shape is not None:
                total_vol += w.Shape.Volume
        
        vol_m3 = total_vol / 1000000000 # Conversion de mm3 en m3
        FreeCAD.Console.PrintMessage(f"\n--- AUTOARCH DEVIS ---\nVolume total des murs : {vol_m3:.2f} m³\n----------------------\n")

FreeCADGui.addCommand('AutoArch_FastWalls', FastWalls())
FreeCADGui.addCommand('AutoArch_Estimate', Estimate())
