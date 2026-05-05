# ============================================================
#  ai/bfs.py  —  Breadth-First Search pathfinding
#  Used by: Basic Tank (Simple Reflex Agent)
#  Finds shortest-HOP path (ignores terrain cost)
# ============================================================

from collections import deque

# Tile constants
EMPTY  = 0
BRICK  = 1
STEEL  = 2
WATER  = 3
FOREST = 4
EAGLE  = 5

# Passable tiles for BFS (does NOT shoot through brick — takes detour)
BFS_PASSABLE = {EMPTY, FOREST, EAGLE}

# 4-directional moves
DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # UP DOWN LEFT RIGHT


def bfs_next_step(grid: list[list[int]],
                  start: tuple[int, int],
                  goal: tuple[int, int]) -> tuple[int, int] | None:
    """
    Run BFS from start to goal on the given grid.
    Returns the NEXT STEP (one tile toward goal) as (col, row).
    Returns None if no path exists.

    - Treats Empty and Forest as cost=1 (passable)
    - Treats Brick, Steel, Water as walls (impassable)
    - This causes Basic Tank to take the longest detour around walls
      rather than shooting through them — intentional per spec.
    """
    sx, sy = start
    gx, gy = goal

    if start == goal:
        return None

    # BFS queue stores (col, row)
    queue   = deque()
    visited = {}        # (col,row) -> parent (col,row)

    queue.append((sx, sy))
    visited[(sx, sy)] = None

    found = False
    while queue:
        cx, cy = queue.popleft()

        if (cx, cy) == (gx, gy):
            found = True
            break

        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in visited:
                continue
            if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
                continue
            tile = grid[ny][nx]
            # Goal tile is always considered reachable
            if tile in BFS_PASSABLE or (nx, ny) == (gx, gy):
                visited[(nx, ny)] = (cx, cy)
                queue.append((nx, ny))

    if not found:
        return None

    # Reconstruct path and return first step
    path = []
    cur  = (gx, gy)
    while cur is not None:
        path.append(cur)
        cur = visited[cur]
    path.reverse()

    # path[0] = start, path[1] = first step
    if len(path) < 2:
        return None
    return path[1]


def bfs_full_path(grid: list[list[int]],
                  start: tuple[int, int],
                  goal: tuple[int, int]) -> list[tuple[int, int]]:
    """
    Returns the full BFS path from start to goal (list of (col,row) tiles).
    Returns empty list if no path found.
    Used for path caching and change-event invalidation.
    """
    sx, sy = start
    gx, gy = goal

    if start == goal:
        return [start]

    queue   = deque()
    visited = {}

    queue.append((sx, sy))
    visited[(sx, sy)] = None

    found = False
    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) == (gx, gy):
            found = True
            break
        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in visited:
                continue
            if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
                continue
            tile = grid[ny][nx]
            if tile in BFS_PASSABLE or (nx, ny) == (gx, gy):
                visited[(nx, ny)] = (cx, cy)
                queue.append((nx, ny))

    if not found:
        return []

    path = []
    cur  = (gx, gy)
    while cur is not None:
        path.append(cur)
        cur = visited[cur]
    path.reverse()
    return path


def bfs_nearest_steel(grid: list[list[int]],
                      start: tuple[int, int]) -> tuple[int, int] | None:
    """
    Find the nearest Steel Wall tile adjacent to an empty tile
    (so the tank can stand next to it for cover).
    Used by Armor Tank retreat behavior.
    """
    sx, sy = start
    queue   = deque()
    visited = set()

    queue.append((sx, sy))
    visited.add((sx, sy))

    while queue:
        cx, cy = queue.popleft()
        # Check if any neighbour is steel → this tile is "cover"
        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
                continue
            if grid[ny][nx] == STEEL:
                return (cx, cy)   # stand here for cover

        # Expand BFS through passable tiles
        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in visited:
                continue
            if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
                continue
            if grid[ny][nx] in BFS_PASSABLE:
                visited.add((nx, ny))
                queue.append((nx, ny))

    return None   # No steel found


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    # 5x5 test grid with a wall blocking direct path
    #  . . W . E
    #  . . W . .
    #  S . W . .
    #  . . . . .
    #  . . . . .
    W = STEEL
    E = EAGLE
    S_pos = (0, 2)
    E_pos = (4, 0)
    g = [
        [EMPTY, EMPTY, W,     EMPTY, E    ],
        [EMPTY, EMPTY, W,     EMPTY, EMPTY],
        [EMPTY, EMPTY, W,     EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
    ]
    path = bfs_full_path(g, S_pos, E_pos)
    nxt  = bfs_next_step(g, S_pos, E_pos)
    print(f"BFS path: {path}")
    print(f"Next step: {nxt}")
    assert nxt is not None, "BFS should find a detour path"
    # Path must go AROUND the wall (col 2) — check no STEEL tile in path
    steel_in_path = any(g[y][x] == STEEL for x,y in path)
    assert not steel_in_path, "BFS should detour, not pass through steel"
    print("✅ BFS test passed — takes detour around wall")