"""Tests for characters/skins/assets (no window needed)."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.modloader import ModLoader
from core.gamedata import GameData
from core.assets import resolve_asset, check_model_format, _prepare_model_alias


def _mod_with(folder: Path, manifest, **files):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "mod.json").write_text(json.dumps(manifest), encoding="utf-8")
    for name, data in files.items():
        if name.endswith(".json"):
            (folder / name).write_text(json.dumps(data), encoding="utf-8")
        else:
            (folder / name).write_text(data, encoding="utf-8")


def test_characters_and_skins_merge(tmp_path):
    mods = tmp_path / "mods"
    mods.mkdir()
    _mod_with(mods / "c1", {"id": "c1", "name": "C1"},
              **{"characters.json": {"hero": {"name": "Hero", "model": "assets/hero.vrm"}},
                 "player_skins.json": {"hero_gold": {"character": "hero", "color": [1, 0, 0]}},
                 "zombie_skins.json": {"common_neon": {"zombie": "common", "color": [0, 1, 1]}},
                 "weapon_skins.json": {"rifle_gold": {"weapon": "rifle", "color": [1, 0.8, 0]}}})
    loader = ModLoader(mods)
    loader.scan()
    data = GameData(loader)
    assert "hero" in data.characters
    assert "hero_gold" in data.player_skins
    assert "common_neon" in data.zombie_skins
    assert "rifle_gold" in data.weapon_skins
    assert data.skin_owner("w", "rifle_gold") == "c1"
    # skin overlay works
    out = data.apply_skin_to_weapon_def({"name": "R", "color": [0, 0, 0]}, {"name": "G", "color": [1, 1, 0]})
    assert out["color"] == [1, 1, 0] and out["_skin"] == "G"


def test_vrm_treated_as_glb_and_resolves(tmp_path):
    mods = tmp_path / "mods"
    (mods / "v").mkdir(parents=True)
    m = mods / "v"
    (m / "mod.json").write_text(json.dumps({"id": "v", "name": "V"}), encoding="utf-8")
    (m / "characters.json").write_text(json.dumps({"h": {"model": "assets/h.vrm"}}), encoding="utf-8")
    adir = m / "assets"
    adir.mkdir(exist_ok=True)
    (adir / "h.vrm").write_bytes(b"glTF-BINARY-PLACEHOLDER")
    loader = ModLoader(mods)
    loader.scan()
    p = resolve_asset(loader, "v", "assets/h.vrm")
    assert p and p.endswith(".glb"), f"vrm should alias to glb, got {p}"
    assert Path(p).is_file()
    chk = check_model_format("x.vrm")
    assert chk["ok"] == "yes"
    assert check_model_format("x.fbx")["ok"] == "no"
    assert check_model_format("x.glb")["ok"] == "yes"


def test_repo_ships_skin_examples():
    repo_mods = Path(__file__).resolve().parent.parent / "mods"
    loader = ModLoader(repo_mods)
    loader.scan()
    ids = {m.id for m in loader.mods}
    assert "skins_pack" in ids and "vrm_avatar" in ids
    data = GameData(loader)
    assert "gold" in data.weapon_skins and "neon" in data.zombie_skins
    assert "vrm_hero" in data.characters
    # asset files resolve (placeholders exist)
    p = resolve_asset(loader, "skins_pack", "assets/gold_rifle.glb")
    assert p and Path(p).is_file()
    pv = resolve_asset(loader, "vrm_avatar", "assets/hero.vrm")
    assert pv and pv.endswith(".glb")
