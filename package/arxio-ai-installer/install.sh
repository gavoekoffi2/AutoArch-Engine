#!/usr/bin/env bash
# Arxio AI — one-line installer for Linux and macOS
# Usage :
#   bash install.sh
# or:
#   curl -fsSL <url>/install.sh | bash
#
# Detects the running OS, finds the FreeCAD user Mod directory,
# copies the ArxioAI workbench into it, then prints next steps.
#
# LGPL-2.1-or-later — Arxio AI contributors

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIP="$SCRIPT_DIR/arxio-ai-workbench.zip"

if [[ ! -f "$ZIP" ]]; then
    echo "ERREUR : $ZIP introuvable. Placez install.sh à côté du ZIP." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 1) Détection du dossier Mod FreeCAD
# ---------------------------------------------------------------------------
case "$(uname -s)" in
    Linux*)
        MOD_DIR="$HOME/.local/share/FreeCAD/Mod"
        OS_NAME="Linux"
        ;;
    Darwin*)
        MOD_DIR="$HOME/Library/Application Support/FreeCAD/Mod"
        OS_NAME="macOS"
        ;;
    *)
        echo "ERREUR : OS non supporté. Utilisez install.ps1 sous Windows." >&2
        exit 1
        ;;
esac

echo "→ OS détecté : $OS_NAME"
echo "→ Dossier cible : $MOD_DIR"

# ---------------------------------------------------------------------------
# 2) Vérifier que FreeCAD est installé
# ---------------------------------------------------------------------------
if ! command -v freecad >/dev/null 2>&1 \
    && ! command -v FreeCAD >/dev/null 2>&1 \
    && [[ ! -d "/Applications/FreeCAD.app" ]]; then
    echo ""
    echo "⚠  FreeCAD ne semble pas installé. Téléchargez-le d'abord :"
    echo "     https://www.freecad.org/downloads.php"
    echo ""
    read -rp "Continuer quand même ? [o/N] " answer
    [[ "${answer,,}" == "o" ]] || exit 1
fi

# ---------------------------------------------------------------------------
# 3) Sauvegarder un éventuel ArxioAI existant
# ---------------------------------------------------------------------------
mkdir -p "$MOD_DIR"
if [[ -d "$MOD_DIR/ArxioAI" ]]; then
    stamp=$(date +%Y%m%d-%H%M%S)
    echo "→ Sauvegarde de l'installation précédente : ArxioAI.bak.$stamp"
    mv "$MOD_DIR/ArxioAI" "$MOD_DIR/ArxioAI.bak.$stamp"
fi

# ---------------------------------------------------------------------------
# 4) Extraire
# ---------------------------------------------------------------------------
if ! command -v unzip >/dev/null 2>&1; then
    echo "ERREUR : 'unzip' n'est pas installé (sudo apt install unzip)." >&2
    exit 1
fi
unzip -q "$ZIP" -d "$MOD_DIR"

# ---------------------------------------------------------------------------
# 5) Vérification
# ---------------------------------------------------------------------------
if [[ ! -f "$MOD_DIR/ArxioAI/InitGui.py" ]]; then
    echo "ERREUR : l'extraction a échoué." >&2
    exit 1
fi

echo ""
echo "✅  Arxio AI installé dans :"
echo "    $MOD_DIR/ArxioAI"
echo ""
echo "Prochaines étapes :"
echo "  1. Lancer FreeCAD."
echo "  2. Sélectionner le workbench « Arxio AI » dans le sélecteur en haut."
echo "  3. Menu 'Arxio AI → Configurer l'IA' pour coller votre clé API."
echo ""
echo "Documentation : $MOD_DIR/ArxioAI/INSTALL.md"
