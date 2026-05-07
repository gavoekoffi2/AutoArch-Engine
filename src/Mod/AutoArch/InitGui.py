import FreeCADGui

class AutoArchWorkbench(Workbench):
    MenuText = "AutoArch Engine"
    ToolTip = "Outils d'automatisation pour Architectes — Génération, Visite, Meubles"

    def Initialize(self):
        import AutoArchCommands

        # Barre d'outils v1 — Construction
        v1_cmds = ["AutoArch_FastWalls", "AutoArch_AutoRoof", "AutoArch_AutoPlan", "AutoArch_Estimate"]
        self.appendToolbar("AutoArch | Construction", v1_cmds)

        # Barre d'outils v2 — Visualisation & Intérieur
        v2_cmds = ["AutoArch_VirtualTour", "AutoArch_Section", "AutoArch_RoomLabels",
                    "AutoArch_Furniture", "AutoArch_Textures", "AutoArch_WebExport"]
        self.appendToolbar("AutoArch | Visite & Déco", v2_cmds)

        # Menu complet
        all_cmds = v1_cmds + v2_cmds
        self.appendMenu("AutoArch", all_cmds)

    def Activated(self):
        FreeCAD.Console.PrintMessage(
            "\n" + "=" * 60 + "\n"
            "  🏗️  AutoArch Engine v2\n"
            "  Construction | Visite Virtuelle | Meubles | Textures | Export Web\n"
            "=" * 60 + "\n"
        )

FreeCADGui.addWorkbench(AutoArchWorkbench())
