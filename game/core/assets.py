"""
Assets resolver — maps mod asset references to real loadable files.

Supported 3D model types (like L4D2 custom models, but modern):
  .glb / .gltf  native (needs panda3d-gltf, auto-used by ursina)
  .obj          native panda3d
  .egg / .bam   native panda3d
  .vrm          VRM 0.x/1.0 avatars (VTuber/VRoid) — VRM is a glTF extension,
                so we treat it as glb: copy to temp *.glb and load.
                Humanoid-bone retargeting is NOT automatic; model shows as-is.
  .fbx          NOT loadable directly — convert once with fbx2gltf/FBX2glTF
                or Blender to .glb, then reference the .glb. See error message.

Reference styles in JSON (all resolve relative to the owning mod):
  "model": "assets/miku.vrm"
  "model": "assets/ak47_skin.glb"
  "texture": "assets/ak47_gold.png"

Packed .dzm: assets live inside the zip. They are extracted on demand to
a temp dir (mods/.cache/<mod_id>/) so the engine can load them by path.
"""
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict

SUPPORTED_MODELS = {".glb", ".gltf", ".obj", ".egg", ".bam", ".vrm", ".dae"}
NEEDS_CONVERSION = {".fbx": "convert to .glb with fbx2gltf (https://github.com/facebookincubator/FBX2glTF) or Blender, then reference the .glb"}

_cache_root: Optional[Path] = None


def cache_root(mods_dir: Path) -> Path:
    global _cache_root
    root = Path(mods_dir) / ".cache"
    root.mkdir(parents=True, exist_ok=True)
    return root


def find_mod_dir(loader, mod_id: str) -> Optional[Path]:
    for m in loader.mods:
        if m.id == mod_id and not m.packed:
            return Path(m.path)
    return None


def resolve_asset(loader, mod_id: str, rel: str) -> Optional[str]:
    """Return a filesystem path for mod_id + relative asset ref, or None.

    Handles folder mods (direct path) and packed .dzm (extract to .cache).
    VRM files are copied to *.glb alias so glTF loaders accept them.
    """
    if not rel:
        return None
    # absolute path passthrough (dev convenience)
    p = Path(rel)
    if p.is_absolute() and p.is_file():
        return _prepare_model_alias(str(p))
    # find owning mod
    target = None
    for m in loader.mods:
        if m.id == mod_id:
            target = m
            break
    if target is None:
        return None
    if not target.packed:
        cand = Path(target.path) / rel
        if cand.is_file():
            return _prepare_model_alias(str(cand))
        # also try assets/ prefix fallback
        cand2 = Path(target.path) / "assets" / Path(rel).name
        if cand2.is_file():
            return _prepare_model_alias(str(cand2))
        return None
    # packed: extract from zip
    try:
        with zipfile.ZipFile(target.path, "r") as z:
            names = z.namelist()
            # manifest prefix
            prefix = ""
            for n in names:
                if n.endswith("mod.json"):
                    prefix = n[: -len("mod.json")]
                    break
            for candidate in (prefix + rel, prefix + "assets/" + Path(rel).name, rel):
                if candidate in names:
                    outdir = cache_root(Path(loader.mods_dir)) / mod_id
                    outdir.mkdir(parents=True, exist_ok=True)
                    out = outdir / Path(candidate).name
                    if not out.is_file():
                        out.write_bytes(z.read(candidate))
                    return _prepare_model_alias(str(out))
    except Exception as e:
        print(f"[Assets] extract failed {mod_id}:{rel}: {e}")
    return None


def _prepare_model_alias(path: str) -> str:
    """If .vrm, create a .glb alias copy (same bytes) for glTF loaders."""
    suf = Path(path).suffix.lower()
    if suf == ".vrm":
        alias = str(Path(path).with_suffix(".glb"))
        try:
            if not Path(alias).is_file():
                shutil.copyfile(path, alias)
        except Exception:
            pass
        return alias
    return path


def check_model_format(path: str) -> Dict[str, str]:
    suf = Path(path).suffix.lower()
    if suf in NEEDS_CONVERSION:
        return {"ok": "no", "reason": f"{suf} not loadable directly — {NEEDS_CONVERSION[suf]}"}
    if suf in SUPPORTED_MODELS:
        note = "VRM treated as glTF; humanoid rig shown as-is" if suf == ".vrm" else "native"
        return {"ok": "yes", "note": note}
    return {"ok": "maybe", "reason": f"unknown suffix {suf}, trying anyway"}


def load_model_into_entity(Entity, model_path: str, fallback_color=(0.5, 0.5, 0.5), scale=1.0):
    """Try to build an ursina Entity from a model file. Falls back to cube."""
    chk = check_model_format(model_path)
    if chk.get("ok") == "no":
        print(f"[Assets] {model_path}: {chk['reason']} — using fallback cube")
        return Entity(model="cube", color=fallback_color, scale=scale)
    try:
        return Entity(model=model_path, scale=scale)
    except Exception as e:
        print(f"[Assets] load failed {model_path}: {e} — fallback cube")
        return Entity(model="cube", color=fallback_color, scale=scale)
