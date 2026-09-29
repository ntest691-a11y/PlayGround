"""Player controller wrapper + shooting logic."""
import time


class PlayerState:
    def __init__(self, gamedata, modloader):
        self.gamedata = gamedata
        self.modloader = modloader
        self.hp = 100.0
        self.max_hp = 100.0
        self.score = 0
        self.kills = 0
        self.weapons = list(gamedata.loadout)
        self.current = 0
        self.ammo_mag = {}
        self.ammo_reserve = {}
        self._last_shot = 0.0
        for wid in self.weapons:
            w = gamedata.weapons[wid]
            self.ammo_mag[wid] = int(w.get("magazine", 12))
            self.ammo_reserve[wid] = int(w.get("reserve", 120))

    @property
    def weapon_id(self):
        return self.weapons[self.current] if self.weapons else None

    @property
    def weapon(self):
        wid = self.weapon_id
        return self.gamedata.weapon(wid) if wid else {}

    def switch(self, idx):
        if 0 <= idx < len(self.weapons):
            self.current = idx

    def cycle(self, direction=1):
        if self.weapons:
            self.current = (self.current + direction) % len(self.weapons)

    def can_fire(self):
        w = self.weapon
        import time as _t
        now = _t.time()
        if now - self._last_shot < float(w.get("fire_rate", 0.25)):
            return False
        if self.ammo_mag.get(self.weapon_id, 0) <= 0:
            return False
        return True

    def consume_shot(self):
        import time as _t
        self._last_shot = _t.time()
        self.ammo_mag[self.weapon_id] -= 1

    def reload(self):
        wid = self.weapon_id
        w = self.weapon
        mag_size = int(w.get("magazine", 12))
        need = mag_size - self.ammo_mag[wid]
        take = min(need, self.ammo_reserve[wid])
        self.ammo_mag[wid] += take
        self.ammo_reserve[wid] -= take

    def hurt(self, amount):
        # mods can reduce/negate damage
        r = self.modloader.hook("on_player_damage", float(amount))
        if isinstance(r, (int, float)):
            amount = float(r)
        self.hp -= amount

    def damage_for(self, wid):
        w = self.gamedata.weapons.get(wid, {})
        base = float(w.get("damage", 20))
        return self.modloader.modify_damage(wid, base)

    def add_weapon(self, wid):
        if wid in self.gamedata.weapons and wid not in self.weapons:
            self.weapons.append(wid)
            w = self.gamedata.weapons[wid]
            self.ammo_mag[wid] = int(w.get("magazine", 12))
            self.ammo_reserve[wid] = int(w.get("reserve", 120))
            return True
        return False
