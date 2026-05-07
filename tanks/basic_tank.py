# ============================================================
#  tanks/basic_tank.py  —  Basic Tank | Simple Reflex Agent
#  Search: BFS to Eagle
#  Rules: shoot player on line-of-sight, shoot brick ahead
# ============================================================

import random

from constants import *
from tanks.tank import Tank
from ai.bfs import bfs_next_step


class BasicTank(Tank):
    def __init__(self, x: int = 0, y: int = 0, grid=None):
        super().__init__(
            x=x,
            y=y,
            tank_type=TYPE_BASIC,
            hp=1,
            speed=SPEED_SLOW,
            fire_rate=FIRE_BASIC,
            color=C_BASIC,
        )
        self.grid = grid
        self.direction = DOWN
        self.active = False

    def decide(self, game_state: dict) -> None:
        self._pending_direction = None
        self._want_shoot = False

        if not (self.alive and self.active):
            return

        grid = game_state['grid']
        player = game_state.get('player')

        if self.can_shoot() and player and player.alive:
            if grid.line_of_sight(self.x, self.y, player.x, player.y):
                self.direction = self._direction_toward(player.x, player.y)
                self._want_shoot = True
                return

        if self.can_shoot():
            fx, fy = self.facing_tile()
            if grid.get(fx, fy) == BRICK:
                self._want_shoot = True
                return

        next_tile = bfs_next_step(grid, (self.x, self.y), EAGLE_POS)
        if next_tile is None:
            direction = self._random_free_direction(grid)
        else:
            tx, ty = next_tile
            direction = (tx - self.x, ty - self.y)

        if direction is None:
            return

        self._pending_direction = direction

    def on_map_change(self, x: int, y: int, old: int, new: int) -> None:
        return

    def _random_free_direction(self, grid) -> tuple[int, int] | None:
        candidates = []
        for dx, dy in DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if grid.is_passable(nx, ny) or grid.is_eagle(nx, ny):
                candidates.append((dx, dy))
        return random.choice(candidates) if candidates else None

    def _direction_toward(self, tx: int, ty: int) -> tuple[int, int]:
        if tx == self.x:
            return UP if ty < self.y else DOWN
        return LEFT if tx < self.x else RIGHT