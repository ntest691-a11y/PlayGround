"""
ModLoader — L4D2-style mod system (VPK / Workshop-like).

Supported mod formats:
  1) Folder:  mods/<mod_id>/mod.json  + optional weapons.json, zombies.json, maps.json, hooks.py
  2) Packed:  mods/<mod_id>.dzm        (zip file, same layout inside — like L4D2 .vpk)

mod.json manifest example:
{
  "id": "golden_ak",
  "name": "Golden AK",
  "version": "1.0.0",
  "author": "You",
  "description": "...",
  "priority": 10,          // higher wins on conflicts
  "enabled_by_default": true
}

Data files (all optional):
  weapons.json : { "<weapon_id>": { ...same fields as config... } }
  zombies.json : { "<zombie_id>": { ... } }
  maps.json    : { "<map_id>": { ... } }

Script hooks (optional): hooks.py may define any of:
  on_wave_start(wave_index, wave_def) -> wave_def | None
  on_zombie_spawn(zombie_id, zombie_def) -> zombie_def | None
  on_weapon_fire(weapon_id, weapon_def) -> weapon_def | None
  on_player_damage(amount) -> amount | None
  modify_damage(weapon_id, base_damage) -> new_damage | None

Pure-python, no engine dependency → unit-testable.
"""
import json
import zipfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import importlib.util
import sys


MANIFEST = "mod.json"
# L4D2-style data files. Character/skin files let EVERY entity be moddable:
#   characters.json    : playable survivors { "<id>": {name, model, texture, color, scale} }
#   player_skins.json  : skins for survivors/players { "<id>": {character, name, model, texture, color} }
#   zombie_skins.json  : skins per zombie type { "<zombie_id>:<skin_id>" or "<skin_id>": {zombie, name, model, ...} }
#   weapon_skins.json  : weapon skins { "<weapon_id>:<skin_id>" or "<skin_id>": {weapon, name, model, texture, color} }
DATA_FILES = ("weapons.json", "zombies.json", "maps.json",
              "characters.json", "player_skins.json",
              "zombie_skins.json", "weapon_skins.json")
HOOKS_FILE = "hooks.py"
PACKED_EXT = ".dzm"
ENABLED_FILE = "enabled.json"


@dataclass
class Mod:
    id: str
    name: str
    version: str = "1.0.0"
    author: str = "unknown"
    description: str = ""
    priority: int = 0
    path: Optional[str] = None          # folder or .dzm path
    packed: bool = False
    enabled: bool = True
    weapons: Dict[str, Any] = field(default_factory=dict)
    zombies: Dict[str, Any] = field(default_factory=dict)
    maps: Dict[str, Any] = field(default_factory=dict)
    characters: Dict[str, Any] = field(default_factory=dict)
    player_skins: Dict[str, Any] = field(default_factory=dict)
    zombie_skins: Dict[str, Any] = field(default_factory=dict)
    weapon_skins: Dict[str, Any] = field(default_factory=dict)
    hooks: Dict[str, Callable] = field(default_factory=dict)
    manifest: Dict[str, Any] = field(default_factory=dict)


def _load_json_from_folder(folder: Path, name: str) -> Dict[str, Any]:
    f = folder / name
    if f.is_file():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ModLoader] WARN: bad {f}: {e}")
    return {}


def _load_json_from_zip(z: zipfile.ZipFile, name: str) -> Dict[str, Any]:
    for candidate in (name, f"./{name}"):
        try:
            raw = z.read(candidate)
            return json.loads(raw.decode("utf-8"))
        except KeyError:
            continue
        except Exception as e:
            print(f"[ModLoader] WARN: bad {name} in zip: {e}")
            return {}
    return {}


def _load_hooks_from_source(mod_id: str, source_path: str, code: str) -> Dict[str, Callable]:
    hooks: Dict[str, Callable] = {}
    try:
        spec = importlib.util.spec_from_loader(f"dz_mod_{mod_id}", loader=None)
        module = importlib.util.module_from_spec(spec)
        # give hooks a safe-ish namespace hint
        exec(compile(code, f"<mod {mod_id}/hooks.py>", "exec"), module.__dict__)
        for fname in ("on_wave_start", "on_zombie_spawn", "on_weapon_fire",
                      "on_player_damage", "modify_damage"):
            fn = getattr(module, fname, None)
            if callable(fn):
                hooks[fname] = fn
    except Exception as e:
        print(f"[ModLoader] WARN: hooks.py failed for '{mod_id}': {e}")
    sys.modules.pop(f"dz_mod_{mod_id}", None)
    return hooks


class ModLoader:
    """Scans mods dir, merges data with priority, dispatches hooks."""

    def __init__(self, mods_dir: str | Path):
        self.mods_dir = Path(mods_dir)
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.mods: List[Mod] = []
        self._enabled_overrides: Dict[str, bool] = self._read_enabled_file()

    # ---------- discovery ----------

    def _read_enabled_file(self) -> Dict[str, bool]:
        f = self.mods_dir / ENABLED_FILE
        if f.is_file():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_enabled(self):
        data = {m.id: m.enabled for m in self.mods}
        (self.mods_dir / ENABLED_FILE).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def scan(self) -> List[Mod]:
        found: List[Mod] = []
        # 1) folders
        for child in sorted(self.mods_dir.iterdir()):
            if child.is_dir():
                mod = self._load_folder_mod(child)
                if mod:
                    found.append(mod)
        # 2) packed .dzm
        for child in sorted(self.mods_dir.glob(f"*{PACKED_EXT}")):
            mod = self._load_packed_mod(child)
            if mod:
                found.append(mod)
        # apply enabled overrides
        for m in found:
            if m.id in self._enabled_overrides:
                m.enabled = bool(self._enabled_overrides[m.id])
        # sort by priority (higher first)
        found.sort(key=lambda m: -m.priority)
        self.mods = found
        return found

    def _load_folder_mod(self, folder: Path) -> Optional[Mod]:
        mf = folder / MANIFEST
        if not mf.is_file():
            return None
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ModLoader] WARN: bad manifest {mf}: {e}")
            return None
        mod_id = manifest.get("id", folder.name)
        mod = Mod(
            id=mod_id,
            name=manifest.get("name", mod_id),
            version=manifest.get("version", "1.0.0"),
            author=manifest.get("author", "unknown"),
            description=manifest.get("description", ""),
            priority=int(manifest.get("priority", 0)),
            path=str(folder),
            packed=False,
            enabled=bool(manifest.get("enabled_by_default", True)),
            manifest=manifest,
        )
        mod.weapons = _load_json_from_folder(folder, "weapons.json")
        mod.zombies = _load_json_from_folder(folder, "zombies.json")
        mod.maps = _load_json_from_folder(folder, "maps.json")
        mod.characters = _load_json_from_folder(folder, "characters.json")
        mod.player_skins = _load_json_from_folder(folder, "player_skins.json")
        mod.zombie_skins = _load_json_from_folder(folder, "zombie_skins.json")
        mod.weapon_skins = _load_json_from_folder(folder, "weapon_skins.json")
        hf = folder / HOOKS_FILE
        if hf.is_file():
            try:
                mod.hooks = _load_hooks_from_source(mod_id, str(hf), hf.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[ModLoader] WARN hooks {hf}: {e}")
        return mod

    def _load_packed_mod(self, zpath: Path) -> Optional[Mod]:
        try:
            with zipfile.ZipFile(zpath, "r") as z:
                names = z.namelist()
                # find manifest (allow root or single top folder)
                manifest_name = None
                for n in names:
                    if n.endswith(MANIFEST):
                        manifest_name = n
                        break
                if not manifest_name:
                    print(f"[ModLoader] WARN: {zpath.name} has no mod.json, skipped")
                    return None
                prefix = manifest_name[: -len(MANIFEST)]
                manifest = json.loads(z.read(manifest_name).decode("utf-8"))
                mod_id = manifest.get("id", zpath.stem)
                mod = Mod(
                    id=mod_id,
                    name=manifest.get("name", mod_id),
                    version=manifest.get("version", "1.0.0"),
                    author=manifest.get("author", "unknown"),
                    description=manifest.get("description", ""),
                    priority=int(manifest.get("priority", 0)),
                    path=str(zpath),
                    packed=True,
                    enabled=bool(manifest.get("enabled_by_default", True)),
                    manifest=manifest,
                )
                for df in DATA_FILES:
                    try:
                        raw = z.read(prefix + df).decode("utf-8")
                        setattr(mod, df.split(".")[0], json.loads(raw))
                    except KeyError:
                        pass
                    except Exception as e:
                        print(f"[ModLoader] WARN {df} in {zpath.name}: {e}")
                try:
                    code = z.read(prefix + HOOKS_FILE).decode("utf-8")
                    mod.hooks = _load_hooks_from_source(mod_id, str(zpath), code)
                except KeyError:
                    pass
                return mod
        except zipfile.BadZipFile:
            print(f"[ModLoader] WARN: {zpath.name} is not a valid .dzm (zip)")
            return None

    # ---------- enable/disable ----------

    def enabled_mods(self) -> List[Mod]:
        return [m for m in self.mods if m.enabled]

    def set_enabled(self, mod_id: str, enabled: bool) -> bool:
        for m in self.mods:
            if m.id == mod_id:
                m.enabled = enabled
                self.save_enabled()
                return True
        return False

    def toggle(self, mod_id: str) -> Optional[bool]:
        for m in self.mods:
            if m.id == mod_id:
                m.enabled = not m.enabled
                self.save_enabled()
                return m.enabled
        return None

    # ---------- merge (priority: higher first; first writer wins per-key unless override flag) ----------

    def merged_weapons(self, vanilla: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(vanilla)
        # apply lower priority first so higher overwrites
        for m in reversed(self.enabled_mods()):
            for k, v in m.weapons.items():
                out[k] = v
        return out

    def merged_zombies(self, vanilla: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(vanilla)
        for m in reversed(self.enabled_mods()):
            for k, v in m.zombies.items():
                out[k] = v
        return out

    def merged_maps(self, vanilla: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(vanilla)
        for m in reversed(self.enabled_mods()):
            for k, v in m.maps.items():
                out[k] = v
        return out

    def _merge_generic(self, attr: str, vanilla: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(vanilla)
        for m in reversed(self.enabled_mods()):
            for k, v in getattr(m, attr, {}).items():
                out[k] = v
        return out

    def merged_characters(self, vanilla): return self._merge_generic("characters", vanilla)
    def merged_player_skins(self, vanilla): return self._merge_generic("player_skins", vanilla)
    def merged_zombie_skins(self, vanilla): return self._merge_generic("zombie_skins", vanilla)
    def merged_weapon_skins(self, vanilla): return self._merge_generic("weapon_skins", vanilla)

    # ---------- hooks dispatch ----------

    def hook(self, name: str, *args):
        """Call hook `name` on all enabled mods in priority order. Returns last non-None result."""
        result = None
        for m in self.enabled_mods():
            fn = m.hooks.get(name)
            if fn:
                try:
                    r = fn(*args)
                    if r is not None:
                        result = r
                        # for transforming hooks, feed result to next mod
                        if name in ("on_wave_start", "on_zombie_spawn", "on_weapon_fire",
                                    "on_player_damage", "modify_damage"):
                            args = (r,) if name in ("on_player_damage", "modify_damage") else (args[0], r) if len(args) == 2 else (r,)
                except Exception as e:
                    print(f"[ModLoader] hook '{name}' failed in '{m.id}': {e}")
        return result

    def modify_damage(self, weapon_id: str, base: float) -> float:
        out = base
        for m in self.enabled_mods():
            fn = m.hooks.get("modify_damage")
            if fn:
                try:
                    r = fn(weapon_id, out)
                    if isinstance(r, (int, float)):
                        out = float(r)
                except Exception as e:
                    print(f"[ModLoader] modify_damage failed in '{m.id}': {e}")
        return out

    # ---------- summary for UI ----------

    def summary(self) -> List[Dict[str, Any]]:
        return [{
            "id": m.id, "name": m.name, "version": m.version,
            "author": m.author, "description": m.description,
            "priority": m.priority, "enabled": m.enabled,
            "packed": m.packed,
            "weapons": list(m.weapons.keys()),
            "zombies": list(m.zombies.keys()),
            "maps": list(m.maps.keys()),
            "characters": list(m.characters.keys()),
            "player_skins": list(m.player_skins.keys()),
            "zombie_skins": list(m.zombie_skins.keys()),
            "weapon_skins": list(m.weapon_skins.keys()),
            "hooks": list(m.hooks.keys()),
        } for m in self.mods]
