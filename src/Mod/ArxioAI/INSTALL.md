# Installer Arxio AI sur votre ordinateur

Arxio AI est un *workbench* pour FreeCAD. Il existe deux manières de
l'installer pour un architecte :

1. **Build complet de FreeCAD + Arxio AI** (pour distribuer un binaire
   unique aux utilisateurs).
2. **Greffer Arxio AI sur un FreeCAD déjà installé** (installation rapide
   en attendant de packager un binaire).

---

## A. Greffer sur un FreeCAD existant (≤ 2 min)

Prérequis : FreeCAD 1.0+ installé (`freecad.org/downloads`).

### Linux / macOS

```bash
# 1) Localiser le dossier "Mod" utilisateur de FreeCAD
#    Linux  : ~/.local/share/FreeCAD/Mod
#    macOS  : ~/Library/Application\ Support/FreeCAD/Mod

MOD_DIR="$HOME/.local/share/FreeCAD/Mod"            # Linux
# MOD_DIR="$HOME/Library/Application Support/FreeCAD/Mod"  # macOS
mkdir -p "$MOD_DIR"

# 2) Copier le workbench
cp -r src/Mod/ArxioAI "$MOD_DIR/"

# 3) Lancer FreeCAD, sélectionner "Arxio AI" dans le sélecteur de workbenches.
```

### Windows

```powershell
# Dossier utilisateur Mod :
$mod = "$env:APPDATA\FreeCAD\Mod"
New-Item -ItemType Directory -Force -Path $mod | Out-Null
Copy-Item -Recurse -Path .\src\Mod\ArxioAI -Destination $mod
```

Relancer FreeCAD.

---

## B. Build complet depuis les sources

### Dépendances

| Plateforme | Commande |
|---|---|
| Debian / Ubuntu | `sudo apt install cmake g++ qtbase5-dev libqt5svg5-dev libboost-all-dev libopencascade-dev libcoin-dev python3-dev` |
| Fedora | `sudo dnf install cmake gcc-c++ qt5-qtbase-devel qt5-qtsvg-devel boost-devel opencascade-devel coin3-devel python3-devel` |
| macOS | `brew install cmake qt@5 boost opencascade coin3d` |
| Windows | Installer Visual Studio 2022 + LibPack FreeCAD depuis le site officiel |

Voir `CONTRIBUTING.md` pour la liste complète.

### Compiler

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_ARXIO_AI=ON
cmake --build build -j$(nproc)
cmake --install build --prefix /opt/arxio-ai     # ou DESTDIR=stage
```

Lancer avec : `/opt/arxio-ai/bin/FreeCAD`.

### Variante `pixi` (recommandée, reproductible)

```bash
pixi install
pixi run build
pixi run run
```

### AppImage Linux

Un template `pkg2appimage`-compatible est fourni :

```bash
# 1) Compiler avec l'option DESTDIR
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_ARXIO_AI=ON
cmake --build build -j$(nproc)
DESTDIR=$PWD/AppDir cmake --install build

# 2) Télécharger linuxdeploy + AppImage tool (une seule fois)
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage

# 3) Produire l'AppImage
./linuxdeploy-x86_64.AppImage \
    --appdir AppDir \
    --desktop-file package/arxio-ai.desktop \
    --icon-file src/Mod/ArxioAI/Resources/icons/ArxioAIWorkbench.svg \
    --output appimage

# Vous obtenez : Arxio_AI-x86_64.AppImage
```

L'AppImage est un fichier unique, portable, signable ; c'est le format
recommandé pour distribuer aux utilisateurs Linux sans dépendances.

### Installer Windows (.msi)

FreeCAD utilise WiX (voir `package/wix/` dans la distribution FreeCAD
officielle). Dupliquer la recette et remplacer :

- `ProductName` → `Arxio AI`
- `Manufacturer` → votre société
- `UpgradeCode` → régénérer un GUID unique
- Icône principale → `Resources/icons/ArxioAIWorkbench.svg` (convertir
  en `.ico` via ImageMagick : `convert ArxioAIWorkbench.svg -resize 256x256 arxio.ico`)

---

## C. Configurer la clé API (pour les commandes IA)

Les commandes IA (**Assistant**, **Générer depuis brief**, **Revue IA**)
nécessitent une clé pour un fournisseur LLM.

1. Lancer Arxio AI.
2. Menu **Arxio AI → Configurer l'IA**.
3. Choisir `anthropic` (recommandé) et coller votre clé `sk-ant-…`.
4. Cliquer **Tester la connexion**, puis **Save**.

La clé est stockée localement dans le fichier de paramètres FreeCAD
(`~/.config/FreeCAD/user.cfg` sur Linux). Elle n'est jamais committée
dans Git ni transmise ailleurs qu'à l'API du fournisseur choisi.

**Alternatives sans clé payante :**

- **GitHub Models** (recommandé si vous avez déjà un compte GitHub —
  quota gratuit généreux). Dans le préréglage « GitHub Models » :
  1. Sur https://github.com/settings/tokens → *Generate new token
     (fine-grained)*.
  2. Scope minimal : **Models → Read**. Aucun autre scope nécessaire.
  3. Coller le token `github_pat_…` dans le champ « Clé API » du
     dialogue Arxio AI.
  4. Modèles utiles : `openai/gpt-4o-mini` (rapide, peu cher),
     `openai/gpt-4o` (qualité), `meta/Llama-3.3-70B-Instruct`,
     `microsoft/Phi-4`.
  
  ⚠️ **Ne jamais coller le token dans un chat, un email, ou un fichier
  versionné.** Il est stocké uniquement dans `user.cfg` local FreeCAD.
  Si vous pensez qu'un token a fuité, **révoquez-le immédiatement**
  sur github.com/settings/tokens.

- **Ollama** en local (gratuit, 100 % offline, aucune donnée ne quitte
  la machine). Dans le préréglage « Ollama local » :
  `ollama pull llama3.1:8b` puis pointer sur `http://localhost:11434/v1`.

- Les commandes **non-IA** (Murs, Toiture, Ouvertures, Plans, Devis,
  **Analyse solaire**) fonctionnent toujours sans clé.

---

## D. Premier test

1. Ouvrir FreeCAD → choisir le workbench **Arxio AI**.
2. Barre d'outils **Modélisation** → **Initialiser le projet**.
3. Dessiner quelques lignes avec Draft, les sélectionner, cliquer **Murs rapides**.
4. Sélectionner les murs → **Toiture & dalle auto**.
5. Barre d'outils **Intelligence** → **Analyse solaire** (aucune clé requise).
6. **Métré & devis** pour vérifier les volumes / coûts.
7. Pour la génération IA : **Générer depuis brief** puis décrire un projet.

Si une étape échoue, la console FreeCAD (menu **Vue → Panneaux → Vue rapport**)
affiche un message d'erreur précis préfixé `Arxio AI —`.
