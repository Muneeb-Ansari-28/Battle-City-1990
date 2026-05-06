# ============================================================
#  tanks/armor_tank.py  —  Armor Tank | Model-Based Reflex Agent
#  Search: A* (cost-aware) + BFS for cover retreat
#  State: hitCount (0-3) drives behavior change
# ============================================================

import random

from constants import *
from tanks.tank import Tank
from ai.astar import astar_next_step, astar_full_path, path_contains_tile
from ai.bfs import bfs_next_step, bfs_nearest_steel

STATE_ATTACK = "attack"
STATE_RETREAT = "retreat"
STATE_COVER = "cover"


class ArmorTank(Tank):
    def __init__(self, x: int = 0, y: int = 0, grid=None):
        super().__init__(
            x=x,
            y=y,
            tank_type=TYPE_ARMOR,
            hp=4,
            speed=SPEED_MEDIUM,
            fire_rate=FIRE_ARMOR,
            color=C_ARMOR,
        )
        self.grid = grid
        self.direction = DOWN
        self.active = False
        self.hit_count = 0
        self.flash_ticks = 0
        self._state = STATE_ATTACK
        self._cover_pos = None
        self._cover_timer = 0
        self._astar_path: list[tuple[int, int]] = []
        self._bfs_timer = 0

    def decide(self, game_state: dict) -> None:
        self._pending_direction = None
        self._want_shoot = False

        if not (self.alive and self.active):
            return

        grid = game_state['grid']
        player = game_state.get('player')

        if self.flash_ticks > 0:
            self.flash_ticks -= 1

        if self._state == STATE_ATTACK:
            self._bfs_timer += 1
            if not self._astar_path or self._bfs_timer >= BFS_RETRIGGER_TICKS:
                self._recompute_astar(grid)
                self._bfs_timer = 0
            self._attack_behavior(grid, player)
        elif self._state == STATE_RETREAT:
            self._retreat_behavior(grid)
        elif self._state == STATE_COVER:
            self._cover_timer += 1
            if self._cover_timer >= ARMOR_RETREAT_TICKS:
                self._state = STATE_ATTACK
                self._cover_timer = 0
                self._recompute_astar(grid)

    def take_hit(self) -> None:
        self.hp -= 1
        self.hit_count += 1
        self.flash_ticks = 20

        if self.hp <= 0:
            self.alive = False
            return

        if self.hit_count == 3 and self._state == STATE_ATTACK:
            self._enter_retreat()

    def on_map_change(self, x: int, y: int, old: int, new: int) -> None:
        if old == BRICK and new == EMPTY and path_contains_tile(self._astar_path, (x, y)):
            if self.grid:
                self._recompute_astar(self.grid)

    def _attack_behavior(self, grid, player) -> None:
        if self.can_shoot() and player and player.alive:
            if grid.line_of_sight(self.x, self.y, player.x, player.y):
                self.direction = self._direction_toward(player.x, player.y)
                self._want_shoot = True
                return

        next_tile = self._next_astar_step(grid)
        if next_tile is None:
            direction = self._random_free_direction(grid)
        else:
            tx, ty = next_tile
            direction = (tx - self.x, ty - self.y)

        if direction is None:
            return

        fx, fy = self.x + direction[0], self.y + direction[1]
        if grid.get(fx, fy) == BRICK and self.can_shoot():
            self.direction = direction
            self._want_shoot = True
            return

        self._pending_direction = direction

    def _retreat_behavior(self, grid) -> None:
        if self._cover_pos is None:
            self._state = STATE_COVER
            return

        if (self.x, self.y) == self._cover_pos:
            self._state = STATE_COVER
            self._cover_timer = 0
            self._cover_pos = None
            return

        nxt = bfs_next_step(grid, (self.x, self.y), self._cover_pos)
        if nxt:
            tx, ty = nxt
            self._pending_direction = (tx - self.x, ty - self.y)

    def _enter_retreat(self) -> None:
        self._state = STATE_RETREAT
        self._astar_path = []
        if self.grid:
            self._cover_pos = bfs_nearest_steel(self.grid, (self.x, self.y))

    def _recompute_astar(self, grid) -> None:
        full = astar_full_path(grid, (self.x, self.y), EAGLE_POS)
        self._astar_path = full[1:] if len(full) > 1 else []

    def _next_astar_step(self, grid):
        if self._astar_path:
            return self._astar_path[0]
        return astar_next_step(grid, (self.x, self.y), EAGLE_POS)

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