# ============================================================
#  tanks/fast_tank.py  —  Fast Tank | Goal-Based Agent
#  Search: Greedy Best-First (Manhattan distance to Eagle)
#  Goal: Destroy Eagle. IGNORES player completely.
# ============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.greedy_bfs import greedy_next_step, greedy_should_shoot_brick, greedy_facing_toward_goal

EMPTY   = 0
BRICK   = 1
STEEL   = 2
WATER   = 3
FOREST  = 4
EAGLE   = 5

TYPE_FAST   = "fast"
TYPE_PLAYER = "player"

DIR_UP    = ( 0, -1)
DIR_DOWN  = ( 0,  1)
DIR_LEFT  = (-1,  0)
DIR_RIGHT = ( 1,  0)
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]


class FastTank:
    MAX_HP      = 1
    SPEED_TICKS = 8
    FIRE_TICKS  = 45

    def __init__(self, x, y, grid, eagle_pos=(12, 24)):
        self.x           = x
        self.y           = y
        self.grid        = grid
        self.eagle_pos   = eagle_pos
        self.type        = TYPE_FAST
        self.hp          = self.MAX_HP
        self.active      = True
        self.direction   = DIR_DOWN
        self.color       = (0, 200, 200)
        self._last_move  = None
        self._last_shoot = False
        self._move_timer = 0
        self._fire_timer = 0

    @property
    def alive(self):
        return self.active

    @property
    def _pending_direction(self):
        return self._last_move

    @property
    def _want_shoot(self):
        return self._last_shoot

    def on_map_changed(self, destroyed_tile):
        pass

    def decide(self, player_pos):
        self._move_timer += 1
        self._fire_timer += 1

        can_move  = self._move_timer >= self.SPEED_TICKS
        can_shoot = self._fire_timer >= self.FIRE_TICKS

        move  = None
        shoot = False

        if can_move or can_shoot:
            next_tile = greedy_next_step(self.grid,
                                         (self.x, self.y),
                                         self.eagle_pos)

            if next_tile is None:
                if can_shoot and greedy_should_shoot_brick(
                        self.grid, (self.x, self.y), self.eagle_pos):
                    face_dir = greedy_facing_toward_goal(
                        (self.x, self.y), self.eagle_pos)
                    self.direction   = face_dir
                    shoot            = True
                    self._fire_timer = 0
            else:
                tx, ty = next_tile
                dx, dy = tx - self.x, ty - self.y
                tile   = self.grid[ty][tx]

                if tile == BRICK:
                    if can_shoot:
                        self.direction   = (dx, dy)
                        shoot            = True
                        self._fire_timer = 0
                else:
                    if can_move:
                        self.direction   = (dx, dy)
                        move             = (dx, dy)
                        self._move_timer = 0

        self._last_move  = move
        self._last_shoot = shoot
        return {'move': move, 'shoot': shoot}

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def apply_move(self, dx, dy):
        self.x += dx
        self.y += dy

    def update_timers(self):
        pass

    def try_move(self, direction, grid):
        dx, dy = direction
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < len(grid._tiles[0]) and 0 <= ny < len(grid._tiles):
            tile = grid._tiles[ny][nx]
            if tile in (0, 4, 5):
                self.x = nx
                self.y = ny

    def shoot(self):
        from bullet import Bullet
        dx, dy = self.direction
        bx, by = self.x + dx, self.y + dy
        return Bullet(bx, by, self.direction, "enemy", self)

    def __repr__(self):
        return f"FastTank(pos=({self.x},{self.y}), hp={self.hp})"