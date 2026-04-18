# Installeur Arxio AI

Kit d'installation en 2 minutes du workbench Arxio AI sur un FreeCAD
officiel déjà installé.

## Contenu

| Fichier | Rôle |
|---|---|
| `arxio-ai-workbench.zip` | Tous les fichiers du workbench (41 Ko, 32 fichiers). |
| `install.sh` | Installeur automatique Linux / macOS. |
| `install.ps1` | Installeur automatique Windows. |

## Prérequis

FreeCAD 1.0 ou supérieur (gratuit) :

- **https://www.freecad.org/downloads.php**

Téléchargez et installez la version stable pour votre système.

## Installation

### Linux / macOS

```bash
cd package/arxio-ai-installer
bash install.sh
```

### Windows

Ouvrir PowerShell dans le dossier, puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Le script :

1. Détecte le dossier Mod utilisateur FreeCAD (`~/.local/share/FreeCAD/Mod`
   sur Linux, `~/Library/Application Support/FreeCAD/Mod` sur macOS,
   `%APPDATA%\FreeCAD\Mod` sur Windows).
2. Sauvegarde toute installation Arxio AI précédente sous
   `ArxioAI.bak.YYYYMMDD-HHmmss`.
3. Extrait `arxio-ai-workbench.zip`.
4. Vérifie que `InitGui.py` est bien présent.

## Premier lancement

1. Lancer FreeCAD.
2. Dans le sélecteur de workbench (coin haut gauche) choisir **Arxio AI**.
3. Menu **Arxio AI → Configurer l'IA** pour coller votre clé API (voir
   `INSTALL.md` installé avec le workbench).
4. Les commandes non-IA (Murs, Toiture, Plans, Devis, Analyse solaire)
   sont utilisables immédiatement, sans clé.

## Désinstallation

Supprimer simplement le dossier `ArxioAI` dans le dossier Mod
utilisateur de FreeCAD.

## Mise à jour

Relancer le script. La version précédente est automatiquement
sauvegardée (dossier `ArxioAI.bak.*`).
