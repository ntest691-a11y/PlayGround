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
        from ursina import Ursina, Entity, Text, held_keys, mouse, camera, raycast, Vec3, Sky, destroy
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

    # gun viewmodel
    gun = Entity(parent=camera.ui, model="cube", scale=(0.25, 0.25, 0.7),
                 position=(0.35, -0.3, 0.6), color=(0.2, 0.2, 0.25))

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
        c = tuple(w.get("color", [0.2, 0.2, 0.25]))
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
            gun.scale = (0.25, 0.25, ln)
        except Exception:
            pass

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
        z = Zombie(Entity, Text, zid, zdef, tuple(sp), player, on_die=on_zombie_die,
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
        hud_text.text = (
            f"HP {max(0,int(state.hp))}/100   "
            f"{w.get('name','-')}  {state.ammo_mag.get(state.weapon_id,0)}/{state.ammo_reserve.get(state.weapon_id,0)}\n"
            f"Wave {min(wave_index+1,len(waves))}/{len(waves)}  "
            f"Kills {state.kills}  Score {state.score}   Zombies {sum(1 for z in zombies if z.alive)}"
        )

    def update_mod_panel():
        lines = ["== MODS (M to close, click console: enable <id> / disable <id>) =="]
        for s in loader.summary():
            tag = "[ON]" if s["enabled"] else "[off]"
            lines.append(f"{tag} {s['id']} — {s['name']} v{s['version']}")
        lines.append("NOTE: toggling mods reloads data — restart wave recommended.")
        mod_panel.text = "\n".join(lines)

    start_wave(0)

    # console commands via input() thread? Simpler: ursina input keys
    def input(key):
        nonlocal wave_index, spawn_queue
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
        if key == "left mouse down" if False else False:
            pass

    # per-frame: shooting handled with mouse.held
    import time as _time
    def update():
        nonlocal spawn_timer, wave_index, game_over
        if game_over:
            return
        # spawn trickle
        if spawn_queue:
            spawn_timer -= _time.dt if hasattr(_time, "dt") else 0.016
            # use ursina time.dt
            from ursina import time as utime
            spawn_timer -= 0  # already handled below
        from ursina import time as utime
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
                    start_wave(wave_index)

        # shooting
        if mouse.left and state.can_fire():
            state.consume_shot()
            w = state.weapon
            pellets = int(w.get("pellets", 1))
            dmg = state.damage_for(state.weapon_id)
            rng = float(w.get("range", 60))
            for _ in range(pellets):
                hit = raycast(camera.world_position, camera.forward, distance=rng, ignore=[player])
                if hit.hit:
                    for z in zombies:
                        if z.alive and z.entity in (hit.entity, getattr(hit.entity, "parent", None)):
                            z.take_damage(dmg)
                            break
                    else:
                        # check parent chain (head shots)
                        ent = hit.entity
                        for z in zombies:
                            if z.alive and (ent == z.entity or ent == getattr(z, "head", None)):
                                z.take_damage(dmg * 1.5)
                                break
            refresh_gun()

        # zombies
        for z in zombies:
            z.update(utime.dt, _time.time())

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
