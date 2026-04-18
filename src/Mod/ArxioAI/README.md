# Arxio AI — FreeCAD workbench

Arxio AI is an architectural-automation workbench that extends FreeCAD
with one-click tools **and AI-powered features** for walls, slabs,
roofs, openings, permit drawings, cost estimation, solar analysis,
natural-language design and expert review.

It is built on [FreeCAD](https://www.freecad.org) and distributed under
the same LGPL-2.1-or-later license. All FreeCAD copyrights and
attributions are preserved.

## Commands

### Modélisation (no AI)

| Commande | Description |
|---|---|
| **Initialiser le projet** | Crée le trio Site → Bâtiment → Rez-de-chaussée. |
| **Murs rapides** | Convertit esquisses / lignes / polylignes en murs Arch paramétriques. |
| **Toiture & dalle auto** | Dalle + toiture calées sur l'enveloppe des murs sélectionnés. |
| **Placer portes & fenêtres** | Dialogue Qt pour ouvertures paramétriques sur le mur sélectionné. |

### Documents (no AI)

| Commande | Description |
|---|---|
| **Plans 2D automatiques** | Page TechDraw A3 paysage : plan + façade sud + façade est à 1:50. |
| **Métré & devis** | Quantitatif (m³, m², unités) + coût total dans la devise configurée (FCFA par défaut). |
| **Analyse solaire** | Position du soleil (algorithme NOAA SPA) pour un lieu/date/heure ; exposition de chaque mur. Aucune clé API requise. |

### Intelligence (LLM — clé API requise sauf mention contraire)

| Commande | Description |
|---|---|
| **Assistant IA** | Chat conversationnel, contexte du document joint. |
| **Générer depuis brief** | Décrivez un projet en français → l'IA produit un plan de base (pièces + murs + ouvertures). |
| **Revue IA du projet** | Relecture critique : alertes fonctionnelles, réglementaires, optimisations budgétaires. |
| **Configurer l'IA** | Choix du fournisseur (Anthropic / OpenAI / Ollama local), modèle, clé API, test de connexion. |

## Dépendances FreeCAD

- `BIM` (Arch)
- `Draft`
- `TechDraw`
- `Part`

Toutes activées par défaut dans un build FreeCAD standard.

## Dépendances Python

Aucune. Seule la bibliothèque standard est utilisée (`urllib`, `json`,
`datetime`, `math`…). Les commandes IA fonctionnent avec toute clé
Anthropic, OpenAI, ou endpoint compatible OpenAI (Ollama, Together,
Groq, Azure…).

## Préférences

Stockées sous `User parameter:BaseApp/Preferences/Mod/ArxioAI` :

- Géométrie par défaut : `WallHeight`, `WallWidth`, `WallAlign`
- Prix unitaires : `WallPricePerM3`, `SlabPricePerM3`, `RoofPricePerM2`,
  `WindowPricePerUnit`, `DoorPricePerUnit`, `Currency`
- IA : `AIProvider`, `AIBaseURL`, `AIModel`, `AIAPIKey`, `AIMaxTokens`,
  `AITimeout`

La clé API se configure via **Arxio AI → Configurer l'IA** (jamais
committée, stockée dans `user.cfg`).

## Build

Option CMake `BUILD_ARXIO_AI=ON` (par défaut).

```sh
cmake -S . -B build -DBUILD_ARXIO_AI=ON
cmake --build build
cmake --install build
```

Voir `INSTALL.md` pour l'installation rapide sur une FreeCAD existante,
le AppImage Linux, et le paquet Windows.
