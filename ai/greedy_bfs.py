# ============================================================
#  ai/greedy_bfs.py  —  Greedy Best-First Search
#  Used by: Fast Tank (Goal-Based Agent)
#  Single-step decision — no full path, no cost awareness
# ============================================================

# Tile constants
EMPTY  = 0
BRICK  = 1
STEEL  = 2
WATER  = 3
FOREST = 4
EAGLE  = 5

DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]   # UP DOWN LEFT RIGHT

# Tiles the Fast Tank can physically move through
GREEDY_PASSABLE = {EMPTY, FOREST, EAGLE}


def _manhattan(ax: int, ay: int, bx: int, by: int) -> int:
    return abs(ax - bx) + abs(ay - by)


def greedy_next_step(grid: list[list[int]],
                     start: tuple[int, int],
                     goal: tuple[int, int]) -> tuple[int, int] | None:
    """
    Single-step Greedy Best-First move toward goal.
    Picks the passable neighbour with the lowest Manhattan distance.

    Key properties (per spec):
    - NO full path computed — purely reactive each tick
    - CAN get stuck in local minima (intentional — shows greedy's weakness)
    - Does NOT shoot through brick to navigate — just picks best open neighbour
    - Returns None if completely surrounded by impassable tiles
    """
    sx, sy = start
    gx, gy = goal

    best_tile  = None
    best_h     = float('inf')

    for dx, dy in DIRECTIONS:
        nx, ny = sx + dx, sy + dy
        if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
            continue
        tile = grid[ny][nx]
        if tile in GREEDY_PASSABLE or (nx, ny) == (gx, gy):
            h = _manhattan(nx, ny, gx, gy)
            if h < best_h:
                best_h    = h
                best_tile = (nx, ny)

    return best_tile


def greedy_should_shoot_brick(grid: list[list[int]],
                               pos: tuple[int, int],
                               goal: tuple[int, int]) -> bool:
    """
    Fast Tank wall rule: IF the next tile in the direction of the goal
    is Brick, shoot it to clear the path — do NOT detour.
    Returns True if the tank should shoot (brick is directly ahead toward goal).
    """
    sx, sy = pos
    gx, gy = goal

    # Determine primary direction toward goal
    dx = 0 if gx == sx else (1 if gx > sx else -1)
    dy = 0 if gy == sy else (1 if gy > sy else -1)

    # Prefer horizontal movement; check that tile first
    candidates = []
    if dx != 0:
        candidates.append((dx, 0))
    if dy != 0:
        candidates.append((0, dy))

    for cdx, cdy in candidates:
        nx, ny = sx + cdx, sy + cdy
        if not (0 <= nx < len(grid[0]) and 0 <= ny < len(grid)):
            continue
        if grid[ny][nx] == BRICK:
            return True

    return False


def greedy_facing_toward_goal(pos: tuple[int, int],
                               goal: tuple[int, int]) -> tuple[int, int]:
    """
    Returns the direction (dx, dy) the Fast Tank should face
    to move/shoot toward the goal.
    Used to set tank facing direction before shooting brick.
    """
    sx, sy = pos
    gx, gy = goal
    dx = gx - sx
    dy = gy - sy

    # Prefer the axis with larger delta
    if abs(dx) >= abs(dy):
        return (1 if dx > 0 else -1, 0)
    else:
        return (0, 1 if dy > 0 else -1)


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    # 5x5 grid — open path left, wall directly ahead
    #  . . . . E
    #  . . B . .
    #  S . B . .
    #  . . . . .
    #  . . . . .
    g = [
        [EMPTY, EMPTY, EMPTY, EMPTY, EAGLE],
        [EMPTY, EMPTY, BRICK, EMPTY, EMPTY],
        [EMPTY, EMPTY, BRICK, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
    ]
    start = (0, 2)
    goal  = (4, 0)

    nxt = greedy_next_step(g, start, goal)
    print(f"Greedy next step from {start} to {goal}: {nxt}")
    assert nxt is not None

    should_shoot = greedy_should_shoot_brick(g, start, goal)
    print(f"Should shoot brick ahead: {should_shoot}")

    print("✅ Greedy BFS test passed")

    # Local minima test — tank trapped except behind it
    #  W W W
    #  W S W    (S = start, goal is far right)
    #  W . W
    g2 = [
        [STEEL, STEEL, STEEL],
        [STEEL, EMPTY, STEEL],
        [STEEL, EMPTY, STEEL],
    ]
    nxt2 = greedy_next_step(g2, (1, 1), (10, 0))
    print(f"Greedy in near-trap: {nxt2}")
    print("✅ Local minima handled gracefully (returns only escape or None)")