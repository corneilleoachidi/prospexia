#!/usr/bin/env bash
# Installe un lanceur Prospexia dans le menu des applications (Linux, utilisateur courant).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
[ -x "$UV" ] || { echo "uv introuvable : https://docs.astral.sh/uv/"; exit 1; }
"$UV" sync --inexact --project "$ROOT" >/dev/null
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"
cp "$ROOT/assets/prospexia.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/prospexia.svg"
sed -e "s|__EXEC__|$UV run --project $ROOT prospexia|" -e "s|__ICON__|prospexia|" \
    "$ROOT/assets/prospexia.desktop" > "$HOME/.local/share/applications/prospexia.desktop"
command -v update-desktop-database >/dev/null && update-desktop-database "$HOME/.local/share/applications" || true
echo "✔ Lanceur installé : cherchez « Prospexia » dans le menu des applications."
