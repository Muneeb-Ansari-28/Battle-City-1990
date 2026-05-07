# ============================================================
#  bullet.py  —  Bullet entity
# ============================================================
from constants import *


class Bullet:
    _id_counter = 0

    def __init__(self, x: int, y: int, direction: tuple,
                 owner_type: str, owner):
        Bullet._id_counter += 1
        self.id         = Bullet._id_counter
        self.x: int     = x
        self.y: int     = y
        self.direction  = direction
        self.owner_type = owner_type
        self.owner      = owner
        self.active     = True

    @property
    def is_player_bullet(self) -> bool:
        return self.owner_type == TYPE_PLAYER

    def step(self) -> None:
        dx, dy = self.direction
        self.x += dx
        self.y += dy

    def destroy(self) -> None:
        if self.active:
            if hasattr(self.owner, "_active_bullet") and self.owner._active_bullet is self:
                self.owner._active_bullet = None
            self.active = False

    def __repr__(self) -> str:
        return (f"Bullet(id={self.id}, pos=({self.x},{self.y}), "
                f"dir={DIR_NAMES.get(self.direction,'?')}, "
                f"owner={self.owner_type})")