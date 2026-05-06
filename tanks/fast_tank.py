# ============================================================
#  tanks/fast_tank.py  —  Fast Tank | Goal-Based Agent
#  Search: Greedy Best-First (Manhattan distance to Eagle)
#  Goal: Destroy Eagle. Ignores player completely.
# ============================================================

from constants import *
from tanks.tank import Tank
from ai.greedy_bfs import (
    greedy_next_step,
    greedy_should_shoot_brick,
    greedy_facing_toward_goal,
)


class FastTank(Tank):
    def __init__(self, x: int = 0, y: int = 0, grid=None):
        super().__init__(
            x=x,
            y=y,
            tank_type=TYPE_FAST,
            hp=1,
            speed=SPEED_FAST,
            fire_rate=FIRE_FAST,
            color=C_FAST,
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

        if self.can_shoot() and greedy_should_shoot_brick(
            grid, (self.x, self.y), EAGLE_POS
        ):
            self.direction = greedy_facing_toward_goal((self.x, self.y), EAGLE_POS)
            self._want_shoot = True
            return

        next_tile = greedy_next_step(grid, (self.x, self.y), EAGLE_POS)
        if next_tile is None:
            return

        tx, ty = next_tile
        direction = (tx - self.x, ty - self.y)
        self._pending_direction = direction

    def on_map_change(self, x: int, y: int, old: int, new: int) -> None:
        return