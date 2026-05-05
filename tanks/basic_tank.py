# ============================================================
#  tanks/basic_tank.py  —  Basic Tank | Simple Reflex Agent
#  Search: BFS to Eagle
#  Rules: shoot player on line-of-sight, shoot brick in path
# ============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.bfs import bfs_next_step, bfs_full_path

EMPTY   = 0
BRICK   = 1
STEEL   = 2
WATER   = 3
FOREST  = 4
EAGLE   = 5

TYPE_BASIC  = "basic"
TYPE_PLAYER = "player"

DIR_UP    = ( 0, -1)
DIR_DOWN  = ( 0,  1)
DIR_LEFT  = (-1,  0)
DIR_RIGHT = ( 1,  0)
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]


class BasicTank:
    MAX_HP      = 1
    SPEED_TICKS = 15
    FIRE_TICKS  = 90
    BFS_RETRIGGER_TICKS = 150

    def __init__(self, x, y, grid, eagle_pos=(12, 24)):
        self.x          = x
        self.y          = y
        self.grid       = grid
        self.eagle_pos  = eagle_pos
        self.type       = TYPE_BASIC
        self.hp         = self.MAX_HP
        self.active     = True
        self.direction  = DIR_DOWN
        self.color      = (180, 180, 0)
        self._last_move  = None
        self._last_shoot = False
        self._move_timer = 0
        self._fire_timer = 0
        self._bfs_timer  = 0
        self._path       = []
        self._recompute_bfs()
        self._action     = None

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
        if destroyed_tile in self._path:
            self._recompute_bfs()

    def decide(self, player_pos):
        self._move_timer += 1
        self._fire_timer += 1
        self._bfs_timer  += 1

        if self._bfs_timer >= self.BFS_RETRIGGER_TICKS:
            self._recompute_bfs()
            self._bfs_timer = 0

        move  = None
        shoot = False
        can_move  = self._move_timer >= self.SPEED_TICKS
        can_shoot = self._fire_timer >= self.FIRE_TICKS

        if can_shoot and player_pos:
            los_dir = self._line_of_sight(player_pos)
            if los_dir:
                self.direction   = los_dir
                shoot            = True
                self._fire_timer = 0

        if can_move:
            next_tile = self._get_next_bfs_step()
            if next_tile is None:
                move = self._random_free_direction()
            else:
                tx, ty = next_tile
                dx, dy = tx - self.x, ty - self.y
                tile   = self.grid[ty][tx]
                if tile == BRICK and can_shoot:
                    self.direction   = (dx, dy)
                    shoot            = True
                    self._fire_timer = 0
                else:
                    self.direction   = (dx, dy)
                    move             = (dx, dy)
                    self._move_timer = 0
                    if self._path and self._path[0] == (self.x, self.y):
                        self._path.pop(0)

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

    def _recompute_bfs(self):
        full = bfs_full_path(self.grid, (self.x, self.y), self.eagle_pos)
        self._path = full[1:] if len(full) > 1 else []

    def _get_next_bfs_step(self):
        if self._path:
            return self._path[0]
        return bfs_next_step(self.grid, (self.x, self.y), self.eagle_pos)

    def _line_of_sight(self, player_pos):
        px, py = player_pos
        tx, ty = self.x, self.y
        if px == tx:
            direction = DIR_UP if py < ty else DIR_DOWN
            if self._clear_los(tx, ty, px, py):
                return direction
        if py == ty:
            direction = DIR_LEFT if px < tx else DIR_RIGHT
            if self._clear_los(tx, ty, px, py):
                return direction
        return None

    def _clear_los(self, x1, y1, x2, y2):
        if x1 == x2:
            for y in range(min(y1,y2)+1, max(y1,y2)):
                if self.grid[y][x1] in (BRICK, STEEL, WATER):
                    return False
        elif y1 == y2:
            for x in range(min(x1,x2)+1, max(x1,x2)):
                if self.grid[y1][x] in (BRICK, STEEL, WATER):
                    return False
        return True

    def _random_free_direction(self):
        import random
        free = []
        for dx, dy in DIRECTIONS:
            nx, ny = self.x+dx, self.y+dy
            if (0 <= nx < len(self.grid[0]) and 0 <= ny < len(self.grid)
                    and self.grid[ny][nx] in (EMPTY, FOREST, EAGLE)):
                free.append((dx, dy))
        return random.choice(free) if free else None

    def __repr__(self):
        return f"BasicTank(pos=({self.x},{self.y}), hp={self.hp})"