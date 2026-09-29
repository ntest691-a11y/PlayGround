#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEADZONE: Survivors — L4D2-like moddable 3D zombie FPS (Desktop).

Run:
  pip install -r requirements.txt
  python main.py [--map rooftop] [--list-mods]

Controls:
  WASD move | Mouse look | LMB shoot | R reload | 1-4 weapons | Q cycle
  M mod menu | F1 help | Esc quit
  ~ console (spawn / give / god) — type: help

Mods (like L4D2 VPK/Workshop):
  mods/<id>/mod.json + weapons.json/zombies.json/maps.json/characters.json/
                 player_skins.json/zombie_skins.json/weapon_skins.json/hooks.py
                 + assets/*.glb/*.vrm/*.obj/*.png
  mods/<id>.dzm  (zip with same layout)
  See mods/example_* + README_MODDING_AR.md

Characters & skins:
  --character ID --player-skin ID --zombie-skin Z:ZSKIN --weapon-skin W:WSKIN
  Supported models: .glb/.gltf/.obj/.egg/.bam native, .vrm auto (as glTF),
                    .fbx must be converted to .glb first.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from core.modloader import ModLoader
from core.gamedata import GameData
from core.assets import resolve_asset


def _c(c, default=(0.5, 0.5, 0.5)):
    """JSON [r,g,b] floats -> ursina Color (Entity color needs 4 components)."""
    try:
        from ursina import Color
        c = list(c if c is not None else default)
        while len(c) < 4:
            c.append(1.0)
        return Color(float(c[0]), float(c[1]), float(c[2]), float(c[3]))
    except Exception:
        return tuple(c) if c else default


def parse_args():
    p = argparse.ArgumentParser(description="DEADZONE: Survivors")
    p.add_argument("--map", default="rooftop")
    p.add_argument("--list-mods", action="store_true")
    p.add_argument("--list-skins", action="store_true")
    p.add_argument("--enable-mod", action="append", default=[])
    p.add_argument("--disable-mod", action="append", default=[])
    p.add_argument("--character", default=None, help="playable character id")
    p.add_argument("--player-skin", default=None, help="player skin id")
    p.add_argument("--zombie-skin", action="append", default=[],
                   help="ZID:SKINID, e.g. common:neon (repeatable)")
    p.add_argument("--weapon-skin", action="append", default=[],
                   help="WID:SKINID, e.g. rifle:gold (repeatable)")
    p.add_argument("--bots", type=int, default=2,
                   help="number of survivor bots (0-4, default 2)")
    return p.parse_args()


def _parse_skin_args(items):
    out = {}
    for it in items:
        if ":" in it:
            k, v = it.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def main():
    args = parse_args()
    loader = ModLoader(HERE / "mods")
    loader.scan()

    for mid in args.enable_mod:
        loader.set_enabled(mid, True)
    for mid in args.disable_mod:
        loader.set_enabled(mid, False)
    if args.enable_mod or args.disable_mod:
        loader.scan()

    data = GameData(loader)

    if args.list_mods or args.list_skins:
        print("=== Mods ===")
        for s in loader.summary():
            tag = "ON " if s["enabled"] else "OFF"
            print(f"[{tag}] {s['id']} v{s['version']} by {s['author']} — {s['name']}")
            if s["weapons"]: print(f"     weapons: {s['weapons']}")
            if s["zombies"]: print(f"     zombies: {s['zombies']}")
            if s["maps"]: print(f"     maps: {s['maps']}")
            if s.get("characters"): print(f"     characters: {s['characters']}")
            if s.get("player_skins"): print(f"     player_skins: {s['player_skins']}")
            if s.get("zombie_skins"): print(f"     zombie_skins: {s['zombie_skins']}")
            if s.get("weapon_skins"): print(f"     weapon_skins: {s['weapon_skins']}")
            if s["hooks"]: print(f"     hooks: {s['hooks']}")
        print(f"\nWeapons: {sorted(data.weapons)}")
        print(f"Zombies: {sorted(data.zombies)}")
        print(f"Maps: {sorted(data.maps)}")
        print(f"Characters: {sorted(data.characters)}")
        print(f"PlayerSkins: {sorted(data.player_skins)}")
        print(f"ZombieSkins: {sorted(data.zombie_skins)}")
        print(f"WeaponSkins: {sorted(data.weapon_skins)}")
        print("\nModels: .glb/.gltf/.obj/.egg/.bam native | .vrm auto-as-glb | .fbx convert to .glb first")
        return

    if args.map not in data.maps:
        print(f"Unknown map '{args.map}'. Available: {sorted(data.maps)}")
        sys.exit(1)

    # ---- start ursina game ----
    try:
        from ursina import (Ursina, Entity, Text, held_keys, mouse, camera, raycast,
                            Vec3, Sky, destroy, DirectionalLight, AmbientLight)
        from ursina.prefabs.first_person_controller import FirstPersonController
    except ImportError:
        print("Ursina not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    from entities.player import PlayerState
    from entities.zombie import Zombie
    from world.map_loader import build_level

    app = Ursina(title="DEADZONE: Survivors (moddable L4D2-like)", fullscreen=False, borderless=False)
    try:
        app.exit_button.visible = False
    except AttributeError:
        pass  # ursina versions differ; exit via Esc
    try:
        app.cog_button.visible = False
    except AttributeError:
        pass

    # FIX white/washed-out scene: ursina lit-shader needs real lights
    try:
        sun = DirectionalLight()
        sun.look_at(Vec3(1, -1, -1))
    except Exception as e:
        print(f"[warn] sun light failed: {e}")
    try:
        AmbientLight(color=(0.55, 0.55, 0.55, 1))
    except Exception as e:
        print(f"[warn] ambient light failed: {e}")

    state = PlayerState(data, loader)
    # --- character + skins selection (all moddable) ---
    zombie_skin_map = _parse_skin_args(args.zombie_skin)
    weapon_skin_map = _parse_skin_args(args.weapon_skin)
    active_character = args.character or None
    if active_character and active_character not in data.characters:
        print(f"Unknown character '{active_character}'. Available: {sorted(data.characters)}")
        sys.exit(1)
    if args.player_skin and args.player_skin not in data.player_skins:
        print(f"Unknown player skin '{args.player_skin}'. Available: {sorted(data.player_skins)}")
        sys.exit(1)
    for zid, sk in zombie_skin_map.items():
        if zid not in data.zombies: print(f"WARN unknown zombie '{zid}'"); 
        if sk not in data.zombie_skins: print(f"WARN unknown zombie skin '{sk}'")
    for wid, sk in weapon_skin_map.items():
        if wid not in data.weapons: print(f"WARN unknown weapon '{wid}'")
        if sk not in data.weapon_skins: print(f"WARN unknown weapon skin '{sk}'")
    if active_character:
        print(f"Character: {active_character} ({data.characters[active_character].get('name')})")
    if args.player_skin:
        print(f"Player skin: {args.player_skin}")

    def _resolve_skin_model(kind: str, skin_id: str):
        skin = {"p": data.player_skins, "z": data.zombie_skins, "w": data.weapon_skins}[kind].get(skin_id, {})
        ref = skin.get("model")
        if not ref:
            return None, None
        owner = data.skin_owner(kind, skin_id)
        path = resolve_asset(loader, owner, ref) if owner else None
        tex = skin.get("texture")
        tex_path = resolve_asset(loader, owner, tex) if (owner and tex) else None
        return path, tex_path

    map_def = data.maps[args.map]
    # mod hook can rewrite wave
    level = build_level(map_def)
    spawn_points = level["spawn_points"]
    waves = level["waves"]

    player = FirstPersonController(position=level["player_spawn"], speed=7)
    player.cursor.visible = False
    try:
        from ursina import mouse as _mouse
        _mouse.locked = True
    except Exception:
        pass

    # gun viewmodel — FIX: must be parented to 3D camera, not camera.ui (2D overlay)
    gun = Entity(parent=camera, model="cube", scale=(0.2, 0.2, 0.6),
                 position=(0.4, -0.3, 0.7), color=_c([0.2, 0.2, 0.25]))
    muzzle = Entity(parent=gun, model="cube", scale=(0.3, 0.3, 0.3),
                    position=(0, 0, -0.7), color=_c([1, 0.8, 0.2]), enabled=False)
    gun_kick = 0.0

    hud_text = Text(position=(-0.85, 0.45), scale=1.4, text="")
    crosshair = Text(parent=camera.ui, text="+", scale=2, origin=(0, 0))
    msg = Text(position=(0, 0.35), origin=(0, 0), scale=1.2, text="WAVE 1 — survive!  (M=mods, F1=help)")
    mod_panel = Text(position=(-0.85, 0.1), scale=1.0, text="", enabled=False)
    help_panel = Text(
        position=(0, 0), origin=(0, 0), scale=1.1, enabled=False,
        text="WASD move | LMB shoot | R reload | 1-4 switch | Q cycle\nM mods | F1 help | ESC quit")

    zombies: list[Zombie] = []
    wave_index = 0
    spawn_queue: list[str] = []
    spawn_timer = 0.0
    game_over = False

    def start_wave(i):
        nonlocal spawn_queue, spawn_timer
        w = dict(waves[i]) if i < len(waves) else {"count": 10 + i * 4, "types": list(data.zombies.keys())}
        hooked = loader.hook("on_wave_start", i, w)
        if isinstance(hooked, dict):
            w = hooked
        count = int(w.get("count", 8))
        types = w.get("types", ["common"])
        import random
        spawn_queue = [random.choice(types) for _ in range(count)]
        spawn_timer = 1.0
        msg.text = f"WAVE {i+1}/{len(waves)} — {count} infected! Good luck."
        # refresh gun color per weapon
        refresh_gun()

    def refresh_gun():
        w = state.weapon
        # weapon skin override (mods can change model/color per weapon)
        skin_id = weapon_skin_map.get(state.weapon_id)
        if skin_id and skin_id in data.weapon_skins:
            w = data.apply_skin_to_weapon_def(dict(w), data.weapon_skins[skin_id])
        c = _c(w.get("color", [0.2, 0.2, 0.25]))
        try:
            model_ref = w.get("model")
            if model_ref:
                # find owner mod: weapon itself or skin
                owner = None
                for m in loader.enabled_mods():
                    if state.weapon_id in m.weapons or (skin_id and skin_id in m.weapon_skins):
                        owner = m.id; break
                mpath = resolve_asset(loader, owner, model_ref) if owner else None
                if mpath:
                    gun.model = mpath
            gun.color = c
            ln = float(w.get("length", 0.8))
            gun.scale = (0.2, 0.2, 0.4 + ln * 0.3)
        except Exception:
            pass

    # ---------- survivor bots (L4D2-style teammates) ----------
    class Buddy:
        """AI teammate: follows you, auto-shoots zombies, can be hurt/revived."""

        def __init__(self, name, color, side):
            self.name = name
            self.side = side  # -1 left, +1 right
            self.hp = 100.0
            self.max_hp = 100.0
            self.alive_now = True
            self._cd = 0.0
            self.position = Vec3(player.position.x, player.position.y, player.position.z)
            self.body = Entity(model="cube", color=_c(color),
                               scale=(0.8, 1.8, 0.8), collider="box",
                               position=self.position)
            self.head = Entity(parent=self.body, model="cube",
                               position=(0, 0.65, 0), scale=(0.6, 0.35, 0.6),
                               color=_c(color))

        @property
        def position(self):
            return self._pos

        @position.setter
        def position(self, v):
            self._pos = v

        def hurt(self, amount):
            if not self.alive_now:
                return
            self.hp -= amount
            if self.hp <= 0:
                self.hp = 0
                self.alive_now = False
                try:
                    self.body.enabled = False
                except Exception:
                    pass
                msg.text = f"{self.name} is DOWN! (revives next wave)"

        def revive(self):
            self.hp = 60.0
            self.alive_now = True
            try:
                self.body.enabled = True
                self.body.position = Vec3(player.position.x + self.side,
                                          player.position.y, player.position.z)
            except Exception:
                pass

        def nearest_zombie(self):
            best, bd = None, 1e9
            for z in zombies:
                if not z.alive:
                    continue
                d = (z.entity.position - self.body.position).length()
                if d < bd:
                    bd, best = d, z
            return best, bd

        def update(self, dt):
            if not self.alive_now:
                return
            try:
                fp = Vec3(player.forward.x, 0, player.forward.z)
                if fp.length() < 0.01:
                    fp = Vec3(0, 0, 1)
                fp = fp.normalized()
                right = Vec3(fp.z, 0, -fp.x)
                want = player.position - fp * 2.5 + right * (1.5 * self.side)
                want.y = player.position.y - 0.4
                cur = self.body.position
                diff = want - cur
                dist = diff.length()
                if dist > 0.3:
                    step = min(dist, 6.5 * dt)
                    self.body.position = cur + diff.normalized() * step
                tgt, td = self.nearest_zombie()
                if tgt is not None and td < 35:
                    self.body.look_at_2d(tgt.entity.position, axis="y")
                    self._cd -= dt
                    if self._cd <= 0:
                        self._cd = 0.7
                        tgt.take_damage(14)
                else:
                    self.body.look_at_2d(player.position, axis="y")
            except Exception:
                pass

    _survivor_defs = [("survivor_2", -1), ("survivor_3", 1),
                      ("survivor_4", -2), ("survivor_1", 2)]
    buddies: list[Buddy] = []
    try:
        n_bots = max(0, int(getattr(args, "bots", 2)))
    except Exception:
        n_bots = 2
    for _cid, _side in _survivor_defs[:n_bots]:
        _cdef = data.characters.get(_cid, {})
        try:
            buddies.append(Buddy(_cdef.get("name", _cid),
                                 _cdef.get("color", [0.5, 0.5, 0.8]), _side))
        except Exception as e:
            print(f"[warn] buddy spawn failed: {e}")

    def nearest_target(pos):
        """Zombies chase whoever is closest: you or a living bot."""
        best, bd = player, (player.position - pos).length()
        for b in buddies:
            if b.alive_now:
                d = (b.body.position - pos).length()
                if d < bd:
                    bd, best = d, b
        return best

    def spawn_one(zid):
        import random
        zdef = data.zombie(zid)
        # zombie skin override: explicit --zombie-skin or skin's default_for
        skin_id = zombie_skin_map.get(zid)
        if not skin_id:
            for sid, s in data.zombie_skins.items():
                if s.get("zombie") == zid or s.get("default_for") == zid:
                    skin_id = sid; break
        model_path, tex_path = None, None
        if skin_id and skin_id in data.zombie_skins:
            zdef = data.apply_skin_to_zombie_def(dict(zdef), data.zombie_skins[skin_id])
            model_path, tex_path = _resolve_skin_model("z", skin_id)
        elif zdef.get("model"):
            owner = next((m.id for m in loader.enabled_mods() if zid in m.zombies), None)
            if owner:
                model_path = resolve_asset(loader, owner, zdef["model"])
        sp = random.choice(spawn_points)
        tgt = nearest_target(Vec3(*sp))
        z = Zombie(Entity, Text, zid, zdef, tuple(sp), tgt, on_die=on_zombie_die,
                   modloader=loader, model_path=model_path, texture_path=tex_path)
        zombies.append(z)

    def on_zombie_die(z):
        state.kills += 1
        state.score += z.score
        # 20% ammo drop feel: small reserve refill
        wid = state.weapon_id
        if wid and state.ammo_reserve.get(wid, 0) < 400:
            state.ammo_reserve[wid] += 2

    def update_hud():
        w = state.weapon
        bots_line = "  ".join(f"{b.name} {max(0,int(b.hp))}" for b in buddies if b.alive_now)
        hud_text.text = (
            f"HP {max(0,int(state.hp))}/100   "
            f"{w.get('name','-')}  {state.ammo_mag.get(state.weapon_id,0)}/{state.ammo_reserve.get(state.weapon_id,0)}\n"
            f"Wave {min(wave_index+1,len(waves))}/{len(waves)}  "
            f"Kills {state.kills}  Score {state.score}   Zombies {sum(1 for z in zombies if z.alive)}"
            + (f"\nBots: {bots_line}" if bots_line else "")
        )

    def update_mod_panel():
        lines = ["== MODS (M to close, click console: enable <id> / disable <id>) =="]
        for s in loader.summary():
            tag = "[ON]" if s["enabled"] else "[off]"
            lines.append(f"{tag} {s['id']} — {s['name']} v{s['version']}")
        lines.append("NOTE: toggling mods reloads data — restart wave recommended.")
        mod_panel.text = "\n".join(lines)

    start_wave(0)
    for b in buddies:
        try:
            b.body.position = Vec3(player.position.x + b.side * 1.5,
                                   player.position.y - 0.4,
                                   player.position.z - 2)
        except Exception:
            pass

    # FIX: track trigger via input events (reliable across ursina versions)
    firing = False

    # console commands via input() thread? Simpler: ursina input keys
    def input(key):
        nonlocal wave_index, spawn_queue, firing
        if key == "escape":
            app.destroy()
            sys.exit(0)
        if key == "f1":
            help_panel.enabled = not help_panel.enabled
        if key == "m":
            mod_panel.enabled = not mod_panel.enabled
            if mod_panel.enabled:
                update_mod_panel()
        if key == "r":
            state.reload()
        if key == "q":
            state.cycle(1)
            refresh_gun()
        for i in range(1, 6):
            if key == str(i):
                state.switch(i - 1)
                refresh_gun()
        if key == "left mouse down":
            firing = True
        if key == "left mouse up":
            firing = False

    # per-frame game logic
    import time as _time
    from ursina import time as utime
    retarget_timer = 0.0

    def do_shoot():
        nonlocal gun_kick
        state.consume_shot()
        w = state.weapon
        pellets = int(w.get("pellets", 1))
        dmg = state.damage_for(state.weapon_id)
        rng = float(w.get("range", 60))
        ignore = [player] + [b.body for b in buddies if b.alive_now]
        for _ in range(pellets):
            hit = raycast(camera.world_position, camera.forward, distance=rng, ignore=ignore)
            if hit.hit:
                ent = hit.entity
                for z in zombies:
                    if z.alive and (ent == z.entity or ent == getattr(z, "head", None)
                                    or getattr(ent, "parent", None) == z.entity):
                        z.take_damage(dmg * (1.5 if ent == getattr(z, "head", None) else 1.0))
                        break
        try:
            muzzle.enabled = True
            gun_kick = 0.08
        except Exception:
            pass

    def update():
        nonlocal spawn_timer, wave_index, game_over, retarget_timer, gun_kick
        if game_over:
            return
        # spawn trickle
        if spawn_queue:
            spawn_timer -= utime.dt
            if spawn_timer <= 0:
                spawn_timer = 0.6
                zid = spawn_queue.pop(0)
                if zid not in data.zombies:
                    zid = "common"
                spawn_one(zid)
        else:
            alive = sum(1 for z in zombies if z.alive)
            if alive == 0:
                if wave_index + 1 < len(waves) or True:
                    # endless scaling after vanilla waves
                    wave_index += 1
                    if wave_index >= len(waves):
                        # generate endless
                        waves.append({"count": 12 + wave_index * 4,
                                      "types": list(data.zombies.keys())})
                        data.maps[args.map]["waves"] = waves
                    # cleanup corpses
                    for z in zombies:
                        try: destroy(z.entity)
                        except Exception: pass
                    zombies.clear()
                    for b in buddies:
                        if not b.alive_now:
                            b.revive()
                    start_wave(wave_index)

        # shooting (hold LMB; auto-reload when empty)
        if firing:
            if state.ammo_mag.get(state.weapon_id, 0) <= 0:
                if state.ammo_reserve.get(state.weapon_id, 0) > 0:
                    state.reload()
            elif state.can_fire():
                do_shoot()

        # gun kick + muzzle flash decay
        try:
            if gun_kick > 0:
                gun_kick = max(0.0, gun_kick - utime.dt)
                gun.z = 0.7 + gun_kick
            if muzzle.enabled and gun_kick <= 0:
                muzzle.enabled = False
        except Exception:
            pass

        # zombies chase nearest target (you or bots), retarget every 2s
        retarget_timer -= utime.dt
        if retarget_timer <= 0:
            retarget_timer = 2.0
            for z in zombies:
                if z.alive:
                    try:
                        z.target = nearest_target(z.entity.position)
                    except Exception:
                        pass
        for z in zombies:
            z.update(utime.dt, _time.time())

        # bots
        for b in buddies:
            b.update(utime.dt)

        # player death
        if state.hp <= 0 and not game_over:
            game_over = True
            msg.text = f"YOU DIED — Score {state.score} Kills {state.kills}. Restart: python main.py"
        # hp regen slow (L4D2-ish temp health feel)
        if state.hp < state.max_hp and state.hp > 0:
            state.hp = min(state.max_hp, state.hp + 2.0 * utime.dt)

        update_hud()

    app.run()


if __name__ == "__main__":
    main()
