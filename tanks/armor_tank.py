# ============================================================
#  tanks/armor_tank.py  —  Armor Tank | Model-Based Reflex Agent
#  Search: A* (cost-aware) + BFS for cover retreat
#  State: hitCount (0-3) drives behavior change
# ============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.astar import astar_next_step, astar_full_path, path_contains_tile
from ai.bfs   import bfs_next_step, bfs_nearest_steel

EMPTY   = 0
BRICK   = 1
STEEL   = 2
WATER   = 3
FOREST  = 4
EAGLE   = 5

TYPE_ARMOR  = "armor"
TYPE_PLAYER = "player"

DIR_UP    = ( 0, -1)
DIR_DOWN  = ( 0,  1)
DIR_LEFT  = (-1,  0)
DIR_RIGHT = ( 1,  0)
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]

STATE_ATTACK  = "attack"
STATE_RETREAT = "retreat"
STATE_COVER   = "cover"

COVER_WAIT_TICKS = 60
BFS_RETRIGGER    = 150


class ArmorTank:
    MAX_HP      = 4
    SPEED_TICKS = 12
    FIRE_TICKS  = 60

    def __init__(self, x, y, grid, eagle_pos=(12, 24)):
        self.x           = x
        self.y           = y
        self.grid        = grid
        self.eagle_pos   = eagle_pos
        self.type        = TYPE_ARMOR
        self.hp          = self.MAX_HP
        self.active      = True
        self.direction   = DIR_DOWN
        self.hit_count   = 0
        self.color       = (200, 100, 0)
        self._last_move  = None
        self._last_shoot = False
        self._move_timer  = 0
        self._fire_timer  = 0
        self._bfs_timer   = 0
        self._cover_timer = 0
        self._state       = STATE_ATTACK
        self._cover_pos   = None
        self._astar_path  = []
        self._recompute_astar()
        self.flash_ticks  = 0

    @property
    def alive(self):
        return self.active

    @property
    def _pending_direction(self):
        return self._last_move

    @property
    def _want_shoot(self):
        return self._last_shoot

    @property
    def is_flashing(self):
        return self.flash_ticks > 0

    def on_map_changed(self, destroyed_tile):
        if path_contains_tile(self._astar_path, destroyed_tile):
            self._recompute_astar()

    def decide(self, player_pos):
        self._move_timer += 1
        self._fire_timer += 1
        self._bfs_timer  += 1

        if self.flash_ticks > 0:
            self.flash_ticks -= 1

        if self._state == STATE_ATTACK and self._bfs_timer >= BFS_RETRIGGER:
            self._recompute_astar()
            self._bfs_timer = 0

        can_move  = self._move_timer >= self.SPEED_TICKS
        can_shoot = self._fire_timer >= self.FIRE_TICKS

        move  = None
        shoot = False

        if self._state == STATE_ATTACK:
            move, shoot = self._attack_behavior(player_pos, can_move, can_shoot)
        elif self._state == STATE_RETREAT:
            move, shoot = self._retreat_behavior(can_move)
        elif self._state == STATE_COVER:
            self._cover_timer += 1
            if self._cover_timer >= COVER_WAIT_TICKS:
                self._state       = STATE_ATTACK
                self._cover_timer = 0
                self._recompute_astar()

        self._last_move  = move
        self._last_shoot = shoot
        return {'move': move, 'shoot': shoot}

    def take_hit(self):
        self.hp        -= 1
        self.hit_count += 1
        self.flash_ticks = 20

        if self.hp <= 0:
            self.active = False
            return True

        if self.hit_count == 3 and self._state == STATE_ATTACK:
            self._enter_retreat()

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

    def _attack_behavior(self, player_pos, can_move, can_shoot):
        move  = None
        shoot = False

        if can_shoot and player_pos:
            los_dir = self._line_of_sight(player_pos)
            if los_dir:
                self.direction   = los_dir
                shoot            = True
                self._fire_timer = 0

        if can_move:
            next_tile = self._get_next_astar_step()
            if next_tile is None:
                move = self._random_free_direction()
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
                    self.direction   = (dx, dy)
                    move             = (dx, dy)
                    self._move_timer = 0
                    if self._astar_path and self._astar_path[0] == (self.x, self.y):
                        self._astar_path.pop(0)

        return move, shoot

    def _retreat_behavior(self, can_move):
        if self._cover_pos is None:
            self._state = STATE_COVER
            return None, False

        if (self.x, self.y) == self._cover_pos:
            self._state       = STATE_COVER
            self._cover_timer = 0
            self._cover_pos   = None
            return None, False

        if can_move:
            nxt = bfs_next_step(self.grid, (self.x, self.y), self._cover_pos)
            if nxt:
                tx, ty = nxt
                dx, dy = tx - self.x, ty - self.y
                self.direction   = (dx, dy)
                self._move_timer = 0
                return (dx, dy), False

        return None, False

    def _enter_retreat(self):
        self._state      = STATE_RETREAT
        self._astar_path = []
        self._cover_pos  = bfs_nearest_steel(self.grid, (self.x, self.y))

    def _recompute_astar(self):
        full = astar_full_path(self.grid, (self.x, self.y), self.eagle_pos)
        self._astar_path = full[1:] if len(full) > 1 else []

    def _get_next_astar_step(self):
        if self._astar_path:
            return self._astar_path[0]
        return astar_next_step(self.grid, (self.x, self.y), self.eagle_pos)

    def _line_of_sight(self, player_pos):
        px, py = player_pos
        if px == self.x:
            direction = DIR_UP if py < self.y else DIR_DOWN
            if self._clear_los(self.x, self.y, px, py):
                return direction
        if py == self.y:
            direction = DIR_LEFT if px < self.x else DIR_RIGHT
            if self._clear_los(self.x, self.y, px, py):
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
        return (f"ArmorTank(pos=({self.x},{self.y}), "
                f"hp={self.hp}, hits={self.hit_count}, state={self._state})")