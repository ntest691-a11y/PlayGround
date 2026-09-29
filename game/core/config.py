"""Default game data (vanilla) — L4D2-like. Mods can extend/override these."""

VANILLA_WEAPONS = {
    "pistol": {
        "name": "Pistol",
        "damage": 25,
        "magazine": 12,
        "reserve": 120,
        "fire_rate": 0.28,      # seconds between shots
        "auto": False,
        "spread": 0.6,
        "range": 60.0,
        "color": [0.2, 0.2, 0.25],
        "length": 0.6,
        "sound": "pistol",
    },
    "smg": {
        "name": "SMG",
        "damage": 18,
        "magazine": 30,
        "reserve": 240,
        "fire_rate": 0.11,
        "auto": True,
        "spread": 1.2,
        "range": 55.0,
        "color": [0.25, 0.25, 0.3],
        "length": 0.8,
        "sound": "smg",
    },
    "shotgun": {
        "name": "Shotgun",
        "damage": 12,            # x8 pellets
        "pellets": 8,
        "magazine": 8,
        "reserve": 64,
        "fire_rate": 0.9,
        "auto": False,
        "spread": 4.0,
        "range": 25.0,
        "color": [0.4, 0.25, 0.12],
        "length": 1.0,
        "sound": "shotgun",
    },
    "rifle": {
        "name": "Rifle",
        "damage": 32,
        "magazine": 30,
        "reserve": 210,
        "fire_rate": 0.14,
        "auto": True,
        "spread": 0.9,
        "range": 80.0,
        "color": [0.15, 0.3, 0.15],
        "length": 0.95,
        "sound": "rifle",
    },
}

VANILLA_ZOMBIES = {
    "common": {
        "name": "Common Infected",
        "hp": 100,
        "speed": 3.2,
        "damage": 12,
        "attack_range": 2.0,
        "attack_rate": 1.0,
        "score": 100,
        "color": [0.3, 0.6, 0.3],
        "scale": 1.0,
    },
    "runner": {
        "name": "Runner",
        "hp": 60,
        "speed": 6.0,
        "damage": 8,
        "attack_range": 1.8,
        "attack_rate": 0.7,
        "score": 150,
        "color": [0.7, 0.3, 0.2],
        "scale": 0.9,
    },
    "brute": {
        "name": "Brute",
        "hp": 350,
        "speed": 2.0,
        "damage": 30,
        "attack_range": 2.4,
        "attack_rate": 1.6,
        "score": 300,
        "color": [0.4, 0.2, 0.5],
        "scale": 1.5,
    },
    "spitter": {
        "name": "Spitter",
        "hp": 80,
        "speed": 2.8,
        "damage": 15,
        "attack_range": 12.0,
        "attack_rate": 2.0,
        "ranged": True,
        "score": 250,
        "color": [0.2, 0.7, 0.6],
        "scale": 1.0,
    },
}

VANILLA_MAPS = {
    "rooftop": {
        "name": "Rooftop Siege",
        "description": "Vanilla map: hold the rooftop helipad.",
        "sky_color": [0.05, 0.07, 0.12],
        "fog": True,
        "ground_size": 60,
        "ground_color": [0.18, 0.19, 0.22],
        "props": [
            {"type": "box", "pos": [0, 0.5, -10], "scale": [8, 1, 1], "color": [0.3, 0.3, 0.35]},
            {"type": "box", "pos": [-8, 1.5, 5], "scale": [2, 3, 2], "color": [0.35, 0.3, 0.25]},
            {"type": "box", "pos": [8, 1.0, 6], "scale": [2, 2, 2], "color": [0.3, 0.35, 0.3]},
            {"type": "pillar", "pos": [-12, 2, -12], "scale": [1, 4, 1], "color": [0.25, 0.25, 0.3]},
            {"type": "pillar", "pos": [12, 2, -12], "scale": [1, 4, 1], "color": [0.25, 0.25, 0.3]},
            {"type": "wall", "pos": [0, 2, -20], "scale": [30, 4, 1], "color": [0.2, 0.2, 0.25]},
        ],
        "spawn_points": [[-10, 1, -15], [10, 1, -15], [0, 1, -18], [-15, 1, 0], [15, 1, 0]],
        "player_spawn": [0, 2, 10],
        "waves": [
            {"count": 6, "types": ["common"]},
            {"count": 10, "types": ["common", "runner"]},
            {"count": 14, "types": ["common", "runner", "brute"]},
            {"count": 18, "types": ["common", "runner", "brute", "spitter"]},
        ],
    },
    "warehouse": {
        "name": "Abandoned Warehouse",
        "description": "Vanilla map: crates maze, close quarters.",
        "sky_color": [0.08, 0.06, 0.06],
        "fog": True,
        "ground_size": 50,
        "ground_color": [0.22, 0.18, 0.14],
        "props": [
            {"type": "box", "pos": [0, 1, 0], "scale": [3, 2, 3], "color": [0.5, 0.35, 0.2]},
            {"type": "box", "pos": [-6, 1, -4], "scale": [3, 2, 3], "color": [0.45, 0.32, 0.18]},
            {"type": "box", "pos": [6, 1, -4], "scale": [3, 2, 3], "color": [0.45, 0.32, 0.18]},
            {"type": "box", "pos": [0, 1, -10], "scale": [10, 2, 1], "color": [0.4, 0.3, 0.2]},
            {"type": "wall", "pos": [0, 2, -18], "scale": [26, 4, 1], "color": [0.25, 0.2, 0.16]},
        ],
        "spawn_points": [[-8, 1, -14], [8, 1, -14], [0, 1, -15]],
        "player_spawn": [0, 2, 8],
        "waves": [
            {"count": 8, "types": ["common", "runner"]},
            {"count": 12, "types": ["common", "runner", "brute"]},
        ],
    },
}

STARTING_LOADOUT = ["pistol", "smg"]

# Playable survivors — every field moddable via characters.json / player_skins.json
VANILLA_CHARACTERS = {
    "survivor_1": {"name": "Rookie", "color": [0.2, 0.4, 0.8], "scale": 1.0, "model": None, "texture": None},
    "survivor_2": {"name": "Doc", "color": [0.8, 0.4, 0.2], "scale": 1.0, "model": None, "texture": None},
    "survivor_3": {"name": "Ghost", "color": [0.4, 0.8, 0.4], "scale": 1.0, "model": None, "texture": None},
    "survivor_4": {"name": "Veteran", "color": [0.7, 0.7, 0.2], "scale": 1.0, "model": None, "texture": None},
}
VANILLA_PLAYER_SKINS = {
    "default": {"character": "survivor_1", "name": "Default", "color": [0.2, 0.4, 0.8], "model": None, "texture": None},
}
VANILLA_ZOMBIE_SKINS = {
    "common_default": {"zombie": "common", "name": "Default", "color": [0.3, 0.6, 0.3], "model": None, "texture": None},
}
VANILLA_WEAPON_SKINS = {
    "pistol_default": {"weapon": "pistol", "name": "Default", "color": [0.2, 0.2, 0.25], "model": None, "texture": None},
}

# Which skin is active by default. Mods/players change via --character/--skin args or skins.json "default_for"
DEFAULT_CHARACTER = "survivor_1"
DEFAULT_SKIN = "default"
