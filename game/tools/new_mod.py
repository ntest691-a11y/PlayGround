#!/usr/bin/env python3
"""Scaffold a new mod + optionally pack it to .dzm (L4D2 .vpk style)."""
import argparse, json, zipfile, re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MODS = HERE / "mods"

TEMPLATE_MANIFEST = {
    "id": "my_mod",
    "name": "My Mod",
    "version": "1.0.0",
    "author": "You",
    "description": "Describe your mod",
    "priority": 10,
    "enabled_by_default": True,
}
TEMPLATE_HOOKS = '''"""hooks.py — optional. Delete functions you don't need."""

def on_wave_start(wave_index, wave_def):
    return wave_def

def on_zombie_spawn(zombie_id, zombie_def):
    return zombie_def

def modify_damage(weapon_id, base_damage):
    return base_damage

def on_player_damage(amount):
    return amount
'''


def slug(s): return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_") or "my_mod"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("id", help="mod id, e.g. my_cool_gun")
    p.add_argument("--name", default=None)
    p.add_argument("--pack", action="store_true", help="also build mods/<id>.dzm")
    a = p.parse_args()
    mid = slug(a.id)
    folder = MODS / mid
    folder.mkdir(parents=True, exist_ok=True)
    manifest = dict(TEMPLATE_MANIFEST, id=mid, name=a.name or mid.replace("_", " ").title())
    (folder / "mod.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "weapons.json").write_text(json.dumps({
        "example_gun": {"name": "Example Gun", "damage": 30, "magazine": 20,
                        "reserve": 200, "fire_rate": 0.15, "auto": True,
                        "spread": 1.0, "range": 60.0, "color": [0.8, 0.6, 0.2],
                        "length": 0.9, "sound": "rifle", "starter": False}
    }, indent=2), encoding="utf-8")
    (folder / "zombies.json").write_text(json.dumps({}, indent=2), encoding="utf-8")
    (folder / "maps.json").write_text(json.dumps({}, indent=2), encoding="utf-8")
    (folder / "characters.json").write_text(json.dumps({
        "my_hero": {"name": "My Hero", "color": [0.6, 0.4, 0.9],
                    "scale": 1.0, "model": "assets/my_hero.vrm", "texture": None}
    }, indent=2), encoding="utf-8")
    (folder / "player_skins.json").write_text(json.dumps({}, indent=2), encoding="utf-8")
    (folder / "zombie_skins.json").write_text(json.dumps({}, indent=2), encoding="utf-8")
    (folder / "weapon_skins.json").write_text(json.dumps({
        "my_gold": {"weapon": "rifle", "name": "My Gold", "color": [0.95, 0.75, 0.15],
                    "model": "assets/my_gun.glb", "texture": None}
    }, indent=2), encoding="utf-8")
    (folder / "hooks.py").write_text(TEMPLATE_HOOKS, encoding="utf-8")
    adir = folder / "assets"
    adir.mkdir(exist_ok=True)
    (adir / "README.md").write_text(
        "# Put models here: .glb/.gltf/.obj native | .vrm auto | .fbx convert to .glb first\n",
        encoding="utf-8")
    print(f"Created {folder}")
    if a.pack:
        dzm = MODS / f"{mid}.dzm"
        with zipfile.ZipFile(dzm, "w", zipfile.ZIP_DEFLATED) as z:
            for f in folder.rglob("*"):
                if f.is_file():
                    z.write(f, str(f.relative_to(folder)))
        print(f"Packed {dzm}")


if __name__ == "__main__":
    main()
