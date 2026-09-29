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
  mods/<id>/mod.json + weapons.json/zombies.json/maps.json/hooks.py
  mods/<id>.dzm  (zip with same layout)
  See mods/example_* + README_MODDING_AR.md
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from core.modloader import ModLoader
from core.gamedata import GameData


def parse_args():
    p = argparse.ArgumentParser(description="DEADZONE: Survivors")
    p.add_argument("--map", default="rooftop")
    p.add_argument("--list-mods", action="store_true")
    p.add_argument("--enable-mod", action="append", default=[])
    p.add_argument("--disable-mod", action="append", default=[])
    return p.parse_args()


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

    if args.list_mods:
        print("=== Mods ===")
        for s in loader.summary():
            tag = "ON " if s["enabled"] else "OFF"
            print(f"[{tag}] {s['id']} v{s['version']} by {s['author']} — {s['name']}")
            if s["weapons"]: print(f"     weapons: {s['weapons']}")
            if s["zombies"]: print(f"     zombies: {s['zombies']}")
            if s["maps"]: print(f"     maps: {s['maps']}")
            if s["hooks"]: print(f"     hooks: {s['hooks']}")
        print(f"\nWeapons: {sorted(data.weapons)}")
        print(f"Zombies: {sorted(data.zombies)}")
        print(f"Maps: {sorted(data.maps)}")
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
    app.exit_button.visible = False

    state = PlayerState(data, loader)
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
        c = tuple(w.get("color", [0.2, 0.2, 0.25]))
        try:
            gun.color = c
            ln = float(w.get("length", 0.8))
            gun.scale = (0.25, 0.25, ln)
        except Exception:
            pass

    def spawn_one(zid):
        import random
        zdef = data.zombie(zid)
        sp = random.choice(spawn_points)
        z = Zombie(Entity, Text, zid, zdef, tuple(sp), player, on_die=on_zombie_die, modloader=loader)
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
