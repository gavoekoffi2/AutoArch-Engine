# Arxio AI — one-line installer for Windows
# Usage :
#   powershell -ExecutionPolicy Bypass -File install.ps1
#
# Detects the FreeCAD user Mod directory, copies the Arxio AI workbench
# into it, then prints next steps.
#
# LGPL-2.1-or-later — Arxio AI contributors

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$zip = Join-Path $scriptDir "arxio-ai-workbench.zip"

if (-not (Test-Path $zip)) {
    Write-Host "ERREUR : $zip introuvable. Placez install.ps1 a cote du ZIP." -ForegroundColor Red
    exit 1
}

# 1) Dossier Mod utilisateur FreeCAD sous Windows
$modDir = Join-Path $env:APPDATA "FreeCAD\Mod"
Write-Host "-> Dossier cible : $modDir"

# 2) Verifier que FreeCAD est installe
$freecadFound = $false
foreach ($p in @(
    "C:\Program Files\FreeCAD 1.0\bin\FreeCAD.exe",
    "C:\Program Files\FreeCAD 0.22\bin\FreeCAD.exe",
    "C:\Program Files (x86)\FreeCAD 1.0\bin\FreeCAD.exe"
)) {
    if (Test-Path $p) { $freecadFound = $true; break }
}
if (-not $freecadFound) {
    Write-Host ""
    Write-Host "!! FreeCAD ne semble pas installe. Telechargez-le d'abord :" -ForegroundColor Yellow
    Write-Host "     https://www.freecad.org/downloads.php"
    $ans = Read-Host "Continuer quand meme ? [o/N]"
    if ($ans.ToLower() -ne "o") { exit 1 }
}

# 3) Sauvegarder un eventuel ArxioAI existant
New-Item -ItemType Directory -Force -Path $modDir | Out-Null
$target = Join-Path $modDir "ArxioAI"
if (Test-Path $target) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = Join-Path $modDir "ArxioAI.bak.$stamp"
    Write-Host "-> Sauvegarde de l'installation precedente : $backup"
    Move-Item $target $backup
}

# 4) Extraire
Write-Host "-> Extraction..."
Expand-Archive -Path $zip -DestinationPath $modDir -Force

# 5) Verification
$marker = Join-Path $target "InitGui.py"
if (-not (Test-Path $marker)) {
    Write-Host "ERREUR : l'extraction a echoue." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "OK  Arxio AI installe dans :" -ForegroundColor Green
Write-Host "    $target"
Write-Host ""
Write-Host "Prochaines etapes :"
Write-Host "  1. Lancer FreeCAD."
Write-Host "  2. Selectionner le workbench 'Arxio AI' dans le selecteur en haut."
Write-Host "  3. Menu 'Arxio AI > Configurer l''IA' pour coller votre cle API."
Write-Host ""
Write-Host "Documentation : $target\INSTALL.md"
