"""Example hooks.py — like L4D2 VScript. All functions optional."""


def on_wave_start(wave_index, wave_def):
    # Every 3rd wave: add a Tank
    if (wave_index + 1) % 3 == 0:
        types = list(wave_def.get("types", []))
        if "tank" not in types:
            types.append("tank")
        wave_def["types"] = types
        wave_def["count"] = int(wave_def.get("count", 8)) + 2
    return wave_def


def modify_damage(weapon_id, base_damage):
    # Tank-buster bonus: shotgun does +50% vs tank handled in game? here global small buff
    if weapon_id == "shotgun":
        return base_damage * 1.2
    return base_damage


def on_player_damage(amount):
    # Slight armor: reduce all damage by 10%
    return amount * 0.9
