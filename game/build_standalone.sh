#!/usr/bin/env bash
# Build standalone Desktop binary (no Python needed for players).
# Usage: ./build_standalone.sh   -> output in dist/DEADZONE/
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q pyinstaller ursina
python3 -m PyInstaller --noconfirm --clean \
  --name DEADZONE \
  --onedir --windowed \
  --collect-all ursina \
  --collect-all panda3d \
  --collect-all direct \
  --add-data "core:core" \
  --add-data "entities:entities" \
  --add-data "world:world" \
  --add-data "mods:mods" \
  main.py
echo "DONE -> dist/DEADZONE/DEADZONE (run without Python)"
