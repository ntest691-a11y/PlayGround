"""Merged game-data registry: vanilla + enabled mods."""
from .config import (VANILLA_WEAPONS, VANILLA_ZOMBIES, VANILLA_MAPS, STARTING_LOADOUT,
                     VANILLA_CHARACTERS, VANILLA_PLAYER_SKINS,
                     VANILLA_ZOMBIE_SKINS, VANILLA_WEAPON_SKINS)
from .modloader import ModLoader


class GameData:
    def __init__(self, loader: ModLoader):
        self.loader = loader
        self.refresh()

    def refresh(self):
        self.weapons = self.loader.merged_weapons(VANILLA_WEAPONS)
        self.zombies = self.loader.merged_zombies(VANILLA_ZOMBIES)
        self.maps = self.loader.merged_maps(VANILLA_MAPS)
        self.characters = self.loader.merged_characters(VANILLA_CHARACTERS)
        self.player_skins = self.loader.merged_player_skins(VANILLA_PLAYER_SKINS)
        self.zombie_skins = self.loader.merged_zombie_skins(VANILLA_ZOMBIE_SKINS)
        self.weapon_skins = self.loader.merged_weapon_skins(VANILLA_WEAPON_SKINS)
        # loadout: vanilla + any mod weapon flagged starter:true
        loadout = list(STARTING_LOADOUT)
        for m in self.loader.enabled_mods():
            for wid, w in m.weapons.items():
                if isinstance(w, dict) and w.get("starter"):
                    if wid not in loadout:
                        loadout.append(wid)
        self.loadout = [w for w in loadout if w in self.weapons]
        # track which mod owns each skin (for asset resolution)
        self._skin_owner: dict[str, str] = {}
        self._char_owner: dict[str, str] = {}
        for m in self.loader.enabled_mods():
            for k in m.player_skins: self._skin_owner[f"p:{k}"] = m.id
            for k in m.zombie_skins: self._skin_owner[f"z:{k}"] = m.id
            for k in m.weapon_skins: self._skin_owner[f"w:{k}"] = m.id
            for k in m.characters: self._char_owner[k] = m.id

    def skin_owner(self, kind: str, skin_id: str):
        return self._skin_owner.get(f"{kind}:{skin_id}")

    def weapon(self, wid):
        d = self.weapons.get(wid, {})
        # allow hooks to tweak per-fire
        tweaked = self.loader.hook("on_weapon_fire", wid, dict(d))
        return tweaked if isinstance(tweaked, dict) else d

    def zombie(self, zid):
        d = dict(self.zombies.get(zid, {}))
        tweaked = self.loader.hook("on_zombie_spawn", zid, d)
        return tweaked if isinstance(tweaked, dict) else d

    def apply_skin_to_zombie_def(self, zdef: dict, skin: dict) -> dict:
        """Overlay a zombie skin onto a zombie def (model/texture/color/scale)."""
        out = dict(zdef)
        for k in ("model", "texture", "color", "scale"):
            if skin.get(k) is not None:
                out[k] = skin[k]
        out["_skin"] = skin.get("name", "custom")
        return out

    def apply_skin_to_weapon_def(self, wdef: dict, skin: dict) -> dict:
        out = dict(wdef)
        for k in ("model", "texture", "color", "length"):
            if skin.get(k) is not None:
                out[k] = skin[k]
        out["_skin"] = skin.get("name", "custom")
        return out
