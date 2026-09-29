"""Merged game-data registry: vanilla + enabled mods."""
from .config import VANILLA_WEAPONS, VANILLA_ZOMBIES, VANILLA_MAPS, STARTING_LOADOUT
from .modloader import ModLoader


class GameData:
    def __init__(self, loader: ModLoader):
        self.loader = loader
        self.refresh()

    def refresh(self):
        self.weapons = self.loader.merged_weapons(VANILLA_WEAPONS)
        self.zombies = self.loader.merged_zombies(VANILLA_ZOMBIES)
        self.maps = self.loader.merged_maps(VANILLA_MAPS)
        # loadout: vanilla + any mod weapon flagged starter:true
        loadout = list(STARTING_LOADOUT)
        for m in self.loader.enabled_mods():
            for wid, w in m.weapons.items():
                if isinstance(w, dict) and w.get("starter"):
                    if wid not in loadout:
                        loadout.append(wid)
        self.loadout = [w for w in loadout if w in self.weapons]

    def weapon(self, wid):
        d = self.weapons.get(wid, {})
        # allow hooks to tweak per-fire
        tweaked = self.loader.hook("on_weapon_fire", wid, dict(d))
        return tweaked if isinstance(tweaked, dict) else d

    def zombie(self, zid):
        d = dict(self.zombies.get(zid, {}))
        tweaked = self.loader.hook("on_zombie_spawn", zid, d)
        return tweaked if isinstance(tweaked, dict) else d
