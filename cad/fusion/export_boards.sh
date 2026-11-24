#!/usr/bin/env bash
# Export the four Ansonia rev A boards as STEP (with components) for the rev G Fusion build.
# Output: cad/boards/<board>.step in DEVICE mm (KiCad (100,100) = device origin, Z 0 = board back face).
# The carrier's ESP32 model path is ${KIPRJMOD}/3dmodels/..., so the board is exported from a temp copy
# that carries Hardware/heartsync_kicad/3dmodels/ESP32-S3-WROOM-1U.step. Re-run after any placement change,
# then rebuild in Fusion (ansonia_revG.py imports these files).
# Usage: export_boards.sh [git-rev]   (default HEAD: the last committed placement; "worktree" = files on disk)
set -euo pipefail
REV="${1:-HEAD}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CLI="${KICAD_CLI:-/c/Program Files/KiCad/10.0/bin/kicad-cli.exe}"
OUT="$ROOT/cad/boards"
mkdir -p "$OUT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
for b in carrier power front_sensor front_touch; do
  mkdir -p "$TMP/$b/3dmodels"
  for ext in kicad_pcb kicad_pro; do
    if [ "$REV" = worktree ]; then cp "$ROOT/Hardware/pcb/$b/$b.$ext" "$TMP/$b/"
    else git -C "$ROOT" show "$REV:Hardware/pcb/$b/$b.$ext" > "$TMP/$b/$b.$ext"; fi
  done
  cp "$ROOT/Hardware/heartsync_kicad/3dmodels/ESP32-S3-WROOM-1U.step" "$TMP/$b/3dmodels/"
  "$CLI" pcb export step --force --subst-models --user-origin 100x100mm \
      -o "$OUT/$b.step" "$TMP/$b/$b.kicad_pcb" > "$OUT/$b.log" 2>&1
  echo "$b ($REV): $(grep -c 'Could not add' "$OUT/$b.log" || true) parts without a 3D model"
done
