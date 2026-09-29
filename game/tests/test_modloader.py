"""Unit tests for ModLoader + GameData (no window needed). Run: python -m pytest tests/ -v"""
import json, zipfile, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.modloader import ModLoader
from core.gamedata import GameData
from core.config import VANILLA_WEAPONS


def make_mod(folder: Path, manifest, weapons=None, zombies=None, maps=None, hooks=None):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "mod.json").write_text(json.dumps(manifest), encoding="utf-8")
    if weapons is not None:
        (folder / "weapons.json").write_text(json.dumps(weapons), encoding="utf-8")
    if zombies is not None:
        (folder / "zombies.json").write_text(json.dumps(zombies), encoding="utf-8")
    if maps is not None:
        (folder / "maps.json").write_text(json.dumps(maps), encoding="utf-8")
    if hooks is not None:
        (folder / "hooks.py").write_text(hooks, encoding="utf-8")


def test_folder_mod_merge_and_priority():
    with tempfile.TemporaryDirectory() as td:
        mods = Path(td)
        make_mod(mods / "a", {"id": "a", "name": "A", "priority": 1},
                 weapons={"pistol": {"name": "Pistol-A", "damage": 999, "magazine": 12,
                                     "reserve": 99, "fire_rate": 0.2, "auto": False,
                                     "spread": 1, "range": 10, "color": [1, 0, 0], "length": 1}})
        make_mod(mods / "b", {"id": "b", "name": "B", "priority": 10},
                 weapons={"pistol": {"name": "Pistol-B", "damage": 1, "magazine": 12,
                                     "reserve": 99, "fire_rate": 0.2, "auto": False,
                                     "spread": 1, "range": 10, "color": [0, 1, 0], "length": 1}})
        loader = ModLoader(mods)
        loader.scan()
        assert [m.id for m in loader.mods] == ["b", "a"], "higher priority first"
        merged = loader.merged_weapons(VANILLA_WEAPONS)
        assert merged["pistol"]["name"] == "Pistol-B", "higher priority wins"


def test_packed_dzm_loads_like_vpk():
    with tempfile.TemporaryDirectory() as td:
        mods = Path(td)
        dzm = mods / "cool.dzm"
        with zipfile.ZipFile(dzm, "w") as z:
            z.writestr("mod.json", json.dumps({"id": "cool", "name": "Cool", "priority": 5}))
            z.writestr("zombies.json", json.dumps({"mega": {"hp": 5, "speed": 1}}))
            z.writestr("hooks.py", "def modify_damage(wid, base):\n    return base*2\n")
        loader = ModLoader(mods)
        loader.scan()
        assert len(loader.mods) == 1 and loader.mods[0].id == "cool"
        assert "mega" in loader.mods[0].zombies
        assert loader.modify_damage("any", 10) == 20


def test_enable_disable_persists():
    with tempfile.TemporaryDirectory() as td:
        mods = Path(td)
        make_mod(mods / "x", {"id": "x", "name": "X"}, weapons={"w1": {"damage": 1}})
        loader = ModLoader(mods)
        loader.scan()
        assert loader.enabled_mods()
        loader.set_enabled("x", False)
        loader2 = ModLoader(mods)
        loader2.scan()
        assert loader2.mods[0].enabled is False
        assert "w1" not in loader2.merged_weapons({})


def test_hooks_chain_and_gamedata():
    with tempfile.TemporaryDirectory() as td:
        mods = Path(td)
        make_mod(mods / "h", {"id": "h", "name": "H"},
                 hooks="def on_player_damage(a):\n    return a*0.5\n")
        loader = ModLoader(mods)
        loader.scan()
        data = GameData(loader)
        assert "pistol" in data.weapons  # vanilla preserved
        assert loader.hook("on_player_damage", 100) == 50


def test_example_mods_ship_with_repo():
    repo_mods = Path(__file__).resolve().parent.parent / "mods"
    loader = ModLoader(repo_mods)
    loader.scan()
    ids = {m.id for m in loader.mods}
    assert "golden_ak" in ids, f"missing golden_ak, got {ids}"
    assert "tank_mod" in ids
    assert "neon_arena" in ids
    data = GameData(loader)
    assert "golden_ak" in data.weapons
    assert "tank" in data.zombies
    assert "neon_arena" in data.maps
