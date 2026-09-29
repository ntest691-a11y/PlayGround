"""Builds a 3D level from a map dict (vanilla or modded). Requires ursina at runtime."""


def build_level(map_def, Entity=None, ursina_mods=None):
    """Create ground/props/walls. Returns dict with spawn info.

    Entity: ursina Entity class (injected so this module imports cleanly in tests).
    """
    if Entity is None:
        from ursina import Entity as _E
        Entity = _E

    sky = map_def.get("sky_color", [0.05, 0.07, 0.12])
    try:
        from ursina import Sky
        Sky(color=tuple(sky))
    except Exception:
        pass

    from ursina import Vec3
    ground_size = map_def.get("ground_size", 60)
    ground_color = tuple(map_def.get("ground_color", [0.18, 0.19, 0.22]))

    ground = Entity(model="plane", scale=(ground_size, 1, ground_size),
                    color=ground_color, collider="box")

    created = [ground]
    for p in map_def.get("props", []):
        ptype = p.get("type", "box")
        pos = tuple(p.get("pos", [0, 1, 0]))
        scale = tuple(p.get("scale", [2, 2, 2]))
        color = tuple(p.get("color", [0.4, 0.4, 0.4]))
        if ptype in ("box", "wall", "pillar"):
            e = Entity(model="cube", position=pos, scale=scale, color=color,
                       collider="box")
        else:
            e = Entity(model="cube", position=pos, scale=scale, color=color,
                       collider="box")
        created.append(e)

    return {
        "entities": created,
        "spawn_points": map_def.get("spawn_points", [[0, 1, -10]]),
        "player_spawn": tuple(map_def.get("player_spawn", [0, 2, 10])),
        "waves": map_def.get("waves", [{"count": 6, "types": ["common"]}]),
    }
