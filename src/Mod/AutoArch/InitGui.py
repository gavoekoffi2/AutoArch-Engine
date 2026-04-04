import FreeCADGui

class AutoArchWorkbench(Workbench):
    MenuText = "AutoArch Engine"
    ToolTip = "Outils d'automatisation pour Architectes"
    
    def Initialize(self):
        import AutoArchCommands
        cmds = ["AutoArch_FastWalls", "AutoArch_AutoRoof", "AutoArch_AutoPlan", "AutoArch_Estimate"]
        self.appendToolbar("AutoArch MVP", cmds)
        self.appendMenu("AutoArch", cmds)

FreeCADGui.addWorkbench(AutoArchWorkbench())
