import FreeCADGui

class AutoArchWorkbench(Workbench):
    MenuText = "AutoArch Engine"
    ToolTip = "Outils d'automatisation avancés pour Architectes"
    
    def Initialize(self):
        import AutoArchCommands
        self.appendToolbar("AutoArch Automations", ["AutoArch_FastWalls", "AutoArch_Estimate"])
        self.appendMenu("AutoArch", ["AutoArch_FastWalls", "AutoArch_Estimate"])

FreeCADGui.addWorkbench(AutoArchWorkbench())
