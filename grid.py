# ============================================================
#  grid.py  —  26×26 tile grid + terrain helpers
# ============================================================
from constants import *


class Grid:
    """
    Wraps the 26×26 tile matrix.
    grid[row][col]  →  terrain value (EMPTY, BRICK, STEEL …)
    Note: row = y, col = x  (grid[y][x])
    """

    def __init__(self):
        # Default: all empty
        self._tiles: list[list[int]] = [
            [EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        # Place eagle
        ex, ey = EAGLE_POS
        self._tiles[ey][ex] = EAGLE

        # Listeners called when a tile changes (e.g. brick destroyed)
        self._change_listeners: list = []

    # ── Tile access ──────────────────────────────────────────
    def get(self, x: int, y: int) -> int:
        if not self.in_bounds(x, y):
            return STEEL   # treat out-of-bounds as impassable
        return self._tiles[y][x]

    def set(self, x: int, y: int, value: int) -> None:
        if self.in_bounds(x, y):
            old = self._tiles[y][x]
            self._tiles[y][x] = value
            if old != value:
                for cb in self._change_listeners:
                    cb(x, y, old, value)

    def load(self, tiles: list[list[int]]) -> None:
        """Replace entire grid from a 2-D list (CSP output)."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self._tiles[y][x] = tiles[y][x]

    def copy_tiles(self) -> list[list[int]]:
        """Return a deep copy of the tile matrix."""
        return [row[:] for row in self._tiles]

    # ── Terrain queries ──────────────────────────────────────
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

    def is_passable(self, x: int, y: int) -> bool:
        """Can a tank enter this tile?"""
        t = self.get(x, y)
        return t in (EMPTY, FOREST)

    def is_destructible(self, x: int, y: int) -> bool:
        return self.get(x, y) == BRICK

    def is_eagle(self, x: int, y: int) -> bool:
        return self.get(x, y) == EAGLE

    def destroys_bullet(self, x: int, y: int) -> bool:
        """Returns True if this tile stops/destroys a bullet."""
        t = self.get(x, y)
        return t in (BRICK, STEEL, EAGLE)

    def destroy_brick(self, x: int, y: int) -> None:
        """Called when a bullet hits a brick tile."""
        if self.get(x, y) == BRICK:
            self.set(x, y, EMPTY)

    # ── Pathfinding helpers ──────────────────────────────────
    def neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """4-connected passable neighbors (for BFS)."""
        result = []
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and self.is_passable(nx, ny):
                result.append((nx, ny))
        return result

    def neighbors_with_cost(self, x: int, y: int) -> list[tuple[tuple, float]]:
        """4-connected neighbors with A* costs (including brick)."""
        result = []
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if not self.in_bounds(nx, ny):
                continue
            t = self.get(nx, ny)
            c = COST.get(t, float('inf'))
            if c < float('inf'):
                result.append(((nx, ny), c))
        return result

    def line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """
        True if x1==x2 (same column) or y1==y2 (same row)
        AND no BRICK/STEEL/WATER tile lies between the two points.
        Used by enemy tanks to decide whether to shoot the player.
        """
        if x1 != x2 and y1 != y2:
            return False
        if x1 == x2:
            miny, maxy = min(y1, y2), max(y1, y2)
            for y in range(miny + 1, maxy):
                t = self.get(x1, y)
                if t in (BRICK, STEEL, WATER):
                    return False
        else:
            minx, maxx = min(x1, x2), max(x1, x2)
            for x in range(minx + 1, maxx):
                t = self.get(x, y1)
                if t in (BRICK, STEEL, WATER):
                    return False
        return True

    # ── Change notification ──────────────────────────────────
    def add_change_listener(self, callback) -> None:
        """Register fn(x, y, old_val, new_val) called on tile change."""
        self._change_listeners.append(callback)

    # ── Utility ──────────────────────────────────────────────
    def count_tile_type(self, tile_type: int) -> int:
        return sum(row.count(tile_type) for row in self._tiles)

    def find_tiles(self, tile_type: int) -> list[tuple[int, int]]:
        """Return list of (x,y) for all tiles of given type."""
        return [
            (x, y)
            for y in range(GRID_SIZE)
            for x in range(GRID_SIZE)
            if self._tiles[y][x] == tile_type
        ]

    def __repr__(self) -> str:
        symbols = {EMPTY: '.', BRICK: 'B', STEEL: 'S',
                   WATER: '~', FOREST: 'F', EAGLE: 'E'}
        lines = []
        for row in self._tiles:
            lines.append(''.join(symbols.get(t, '?') for t in row))
        return '\n'.join(lines)