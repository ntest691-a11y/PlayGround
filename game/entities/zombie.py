"""Zombie entity (ursina). Logic-light; HP/speed from data dict so mods just work."""
import random


class Zombie:
    def __init__(self, Entity, text, zid, zdef, pos, target, on_die, modloader=None,
                 model_path=None, texture_path=None):
        from ursina import Vec3
        self.zid = zid
        self.defn = zdef
        self.target = target
        self.on_die = on_die
        self.modloader = modloader
        self.hp = float(zdef.get("hp", 100))
        self.max_hp = self.hp
        self.speed = float(zdef.get("speed", 3.0))
        self.damage = float(zdef.get("damage", 10))
        self.attack_range = float(zdef.get("attack_range", 2.0))
        self.attack_rate = float(zdef.get("attack_rate", 1.0))
        self.score = int(zdef.get("score", 100))
        self.ranged = bool(zdef.get("ranged", False))
        self._cd = 0.0
        color = tuple(zdef.get("color", [0.3, 0.6, 0.3]))
        scale = float(zdef.get("scale", 1.0))
        # Custom modded model (VRM/GLB/OBJ/...) — falls back to cube
        if model_path:
            try:
                kwargs = dict(model=model_path, position=pos,
                              scale=(scale, scale, scale), collider="box")
                if texture_path:
                    kwargs["texture"] = texture_path
                else:
                    kwargs["color"] = color
                self.entity = Entity(**kwargs)
            except Exception as e:
                print(f"[Zombie] custom model failed ({model_path}): {e}")
                self.entity = Entity(model="cube", position=pos,
                                     scale=(0.9 * scale, 1.8 * scale, 0.9 * scale),
                                     color=color, collider="box")
        else:
            self.entity = Entity(model="cube", position=pos,
                                 scale=(0.9 * scale, 1.8 * scale, 0.9 * scale),
                                 color=color, collider="box")
        # head
        self.head = Entity(parent=self.entity, model="cube",
                           position=(0, 0.65, 0), scale=(0.6, 0.35, 0.6),
                           color=color, collider=None)
        self.hp_bar = None
        try:
            self.hp_bar = text(f"{int(self.hp)}", parent=self.entity,
                               position=(0, 1.1, 0), scale=1.0)
        except Exception:
            pass

    @property
    def alive(self):
        return self.hp > 0 and self.entity.enabled

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp_bar is not None:
            try:
                self.hp_bar.text = str(max(0, int(self.hp)))
            except Exception:
                pass
        if self.hp <= 0:
            self.die()

    def die(self):
        try:
            self.entity.enabled = False
            if self.head:
                self.head.enabled = False
        except Exception:
            pass
        if self.on_die:
            self.on_die(self)

    def update(self, dt, time_now):
        if not self.alive:
            return
        # move toward target
        try:
            tp = self.target.position
            ep = self.entity.position
            dx, dz = tp.x - ep.x, tp.z - ep.z
            dist = (dx * dx + dz * dz) ** 0.5
            if dist > 0.01:
                nx, nz = dx / dist, dz / dist
                if dist > self.attack_range * 0.8:
                    self.entity.x += nx * self.speed * dt
                    self.entity.z += nz * self.speed * dt
                self.entity.look_at_2d(tp, axis="y")
            # attack
            self._cd -= dt
            if dist <= self.attack_range and self._cd <= 0:
                self._cd = self.attack_rate
                hurt = getattr(self.target, "hurt", None)
                if callable(hurt):
                    hurt(self.damage)
                elif hasattr(self.target, "hp"):
                    self.target.hp -= self.damage
        except Exception:
            pass
