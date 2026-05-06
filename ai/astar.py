# ============================================================
#  ai/astar.py  —  A* Search with terrain costs
#  Used by: Armor Tank (Model-Based Reflex Agent)
#  Cost-aware: brick=3, steel=inf, water=inf, empty/forest=1
# ============================================================

import heapq

# Tile constants
EMPTY  = 0
BRICK  = 1
STEEL  = 2
WATER  = 3
FOREST = 4
EAGLE  = 5

# A* terrain costs (per spec §5)
ASTAR_COSTS = {
    EMPTY : 1,
    FOREST: 1,
    BRICK : 3,       # cheaper to shoot through than walk 6+ tiles around
    STEEL : float('inf'),
    WATER : float('inf'),
    EAGLE : 0,       # goal tile — free to enter
}

DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]   # UP DOWN LEFT RIGHT


def _tiles_and_size(grid) -> tuple[list[list[int]], int, int]:
    tiles = grid._tiles if hasattr(grid, "_tiles") else grid
    return tiles, len(tiles[0]), len(tiles)


def _tile_at(grid, x: int, y: int) -> int:
    tiles = grid._tiles if hasattr(grid, "_tiles") else grid
    return tiles[y][x]


def _manhattan(ax: int, ay: int, bx: int, by: int) -> int:
    return abs(ax - bx) + abs(ay - by)


def astar_next_step(grid: list[list[int]],
                    start: tuple[int, int],
                    goal: tuple[int, int]) -> tuple[int, int] | None:
    """
    Run A* from start to goal.
    Returns the NEXT STEP (col, row) toward goal.
    Returns None if no path exists.

    Key insight per spec:
    Cost to shoot through 1 brick wall = 3
    Cost to walk 6+ empty tiles around = 6+
    → A* prefers drilling through thin walls over long detours.
    """
    sx, sy = start
    gx, gy = goal

    if start == goal:
        return None

    # Priority queue: (f, g, (col, row))
    open_heap = []
    heapq.heappush(open_heap, (0 + _manhattan(sx, sy, gx, gy), 0, (sx, sy)))

    came_from = {(sx, sy): None}
    g_cost    = {(sx, sy): 0}

    tiles, w, h = _tiles_and_size(grid)

    while open_heap:
        f, g, (cx, cy) = heapq.heappop(open_heap)

        if (cx, cy) == (gx, gy):
            # Reconstruct and return first step
            path = []
            cur  = (gx, gy)
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path[1] if len(path) >= 2 else None

        # Skip stale entries
        if g > g_cost.get((cx, cy), float('inf')):
            continue

        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue

            tile      = _tile_at(tiles, nx, ny)
            step_cost = ASTAR_COSTS.get(tile, float('inf'))

            if step_cost == float('inf'):
                continue   # impassable

            new_g = g + step_cost
            if new_g < g_cost.get((nx, ny), float('inf')):
                g_cost[(nx, ny)]    = new_g
                came_from[(nx, ny)] = (cx, cy)
                h = _manhattan(nx, ny, gx, gy)
                heapq.heappush(open_heap, (new_g + h, new_g, (nx, ny)))

    return None   # No path found


def astar_full_path(grid: list[list[int]],
                    start: tuple[int, int],
                    goal: tuple[int, int]) -> list[tuple[int, int]]:
    """
    Returns full A* path as list of (col, row) tiles.
    Used for path caching and wall-destroy invalidation.
    """
    sx, sy = start
    gx, gy = goal

    if start == goal:
        return [start]

    open_heap = []
    heapq.heappush(open_heap, (0 + _manhattan(sx, sy, gx, gy), 0, (sx, sy)))

    came_from = {(sx, sy): None}
    g_cost    = {(sx, sy): 0}

    tiles, w, h = _tiles_and_size(grid)

    while open_heap:
        f, g, (cx, cy) = heapq.heappop(open_heap)

        if (cx, cy) == (gx, gy):
            path = []
            cur  = (gx, gy)
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path

        if g > g_cost.get((cx, cy), float('inf')):
            continue

        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            tile      = _tile_at(tiles, nx, ny)
            step_cost = ASTAR_COSTS.get(tile, float('inf'))
            if step_cost == float('inf'):
                continue
            new_g = g + step_cost
            if new_g < g_cost.get((nx, ny), float('inf')):
                g_cost[(nx, ny)]    = new_g
                came_from[(nx, ny)] = (cx, cy)
                h = _manhattan(nx, ny, gx, gy)
                heapq.heappush(open_heap, (new_g + h, new_g, (nx, ny)))

    return []


def path_contains_tile(path: list[tuple[int, int]],
                        tile_pos: tuple[int, int]) -> bool:
    """Check if a cached path passes through a destroyed tile."""
    return tile_pos in path


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("A* Test — Key Demonstration from Spec §7")
    print("Thin brick wall vs long detour")
    print("=" * 50)

    # Grid: direct path has 1 brick wall (cost 3)
    #       detour is 7 empty tiles (cost 7)
    #
    #  S . . B . . . . E
    #  . . . B . . . . .
    #  . . . . . . . . .   ← detour goes down here
    #
    W = BRICK
    rows = 3
    cols = 9
    g = [[EMPTY]*cols for _ in range(rows)]
    g[0][3] = BRICK   # wall on direct path
    g[1][3] = BRICK
    g[0][8] = EAGLE

    start = (0, 0)
    goal  = (8, 0)

    path_astar = astar_full_path(g, start, goal)
    print(f"A* path: {path_astar}")

    # A* should go through brick (cost=3) not around (cost=7+)
    has_brick = any(g[y][x] == BRICK for x, y in path_astar if 0<=y<rows and 0<=x<cols)
    print(f"A* goes through brick wall: {has_brick}")
    assert has_brick, "A* should drill through brick (cost 3 < detour cost 7)"
    print("✅ A* test passed — drills through brick wall instead of long detour")

    # Now test BFS on same grid (should detour)
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from bfs import bfs_full_path
    path_bfs = bfs_full_path(g, start, goal)
    print(f"\nBFS path: {path_bfs}")
    has_brick_bfs = any(g[y][x] == BRICK for x, y in path_bfs if 0<=y<rows and 0<=x<cols)
    print(f"BFS goes through brick wall: {has_brick_bfs}")
    assert not has_brick_bfs, "BFS should detour, not go through brick"
    print("✅ BFS test passed — takes detour around wall")

    print("\n✅ KEY DEMONSTRATION VERIFIED:")
    print("   BFS  → detour (ignores cost)")
    print("   A*   → drills through brick (cost 3 < detour)")