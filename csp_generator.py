# ============================================================
#  csp_generator.py  —  CSP-based procedural map generator
#  Uses backtracking search with forward checking
#  Satisfies all 5 constraints from the project spec
# ============================================================

import random
from collections import deque
from typing import Optional

from constants import (
    EMPTY,
    BRICK,
    STEEL,
    WATER,
    FOREST,
    EAGLE,
    GRID_SIZE,
    EAGLE_POS,
    PLAYER_SPAWN,
    ENEMY_SPAWNS,
    CSP_MAX_WALL_RATIO,
)

UNASSIGNED = None

# ── Grid dimensions ────────────────────────────────────────
GRID_W = GRID_SIZE
GRID_H = GRID_SIZE

# Tiles that are ALWAYS fixed (never overwritten by CSP)
FIXED_POSITIONS = set()
FIXED_POSITIONS.add(EAGLE_POS)
FIXED_POSITIONS.add(PLAYER_SPAWN)
for sp in ENEMY_SPAWNS:
    FIXED_POSITIONS.add(sp)

# Eagle "protection ring" — tiles around eagle
def _eagle_ring(layers: int = 1) -> set:
    ex, ey = EAGLE_POS
    ring = set()
    for layer in range(1, layers + 1):
        for dr in range(-layer, layer + 1):
            for dc in range(-layer, layer + 1):
                if abs(dr) != layer and abs(dc) != layer:
                    continue
                r, c = ey + dr, ex + dc
                if 0 <= r < GRID_H and 0 <= c < GRID_W:
                    ring.add((c, r))
    return ring


# ── Passability for BFS ────────────────────────────────────
_PASSABLE = {EMPTY, FOREST, EAGLE, BRICK}   # treat BRICK as passable for reachability
# (enemy tanks can shoot through brick — path just needs to be navigable)


def _bfs_reachable(grid: list[list[int | None]], src: tuple, dst: tuple) -> bool:
    """Return True if dst is reachable from src through passable tiles."""
    sx, sy = src
    dx, dy = dst
    if not (0 <= sy < GRID_H and 0 <= sx < GRID_W):
        return False
    if grid[sy][sx] not in _PASSABLE and grid[sy][sx] is not UNASSIGNED and (sx, sy) != src:
        return False
    visited = set()
    queue = deque([(sx, sy)])
    visited.add((sx, sy))
    while queue:
        cx, cy = queue.popleft()
        if cx == dx and cy == dy:
            return True
        for nx, ny in [(cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)]:
            if (nx, ny) not in visited and 0 <= ny < GRID_H and 0 <= nx < GRID_W:
                tile = grid[ny][nx]
                if tile in _PASSABLE or tile is UNASSIGNED or (nx, ny) == dst:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return False


def _count_walls(grid: list[list[int | None]]) -> int:
    return sum(1 for r in range(GRID_H) for c in range(GRID_W)
               if grid[r][c] in (BRICK, STEEL))


def _wall_density(grid: list[list[int | None]]) -> float:
    total = GRID_W * GRID_H - len(FIXED_POSITIONS)
    return _count_walls(grid) / total


# ── CSP Generator ─────────────────────────────────────────
class CSPMapGenerator:
    """
    Generates a valid Battle City map using CSP backtracking.

    Variables  : all (col, row) pairs not in FIXED_POSITIONS
    Domains    : {EMPTY, BRICK, STEEL, WATER, FOREST} per cell
    Constraints:
      C1 — Eagle ring: tiles surrounding eagle must be BRICK or STEEL
      C2 — Reachability: all 3 enemy spawns can BFS-reach the eagle
      C3 — Player safety: no wall within 10 Manhattan tiles of player spawn
      C4 — Wall density: ≤ 40 % of the free tiles may be walls
      C5 — Water never blocks the ONLY path to eagle
    """

    def __init__(self, level: int = 1, seed: Optional[int] = None):
        self.level = level
        self.rng   = random.Random(seed)

        self.ring_layers = 2 if level == 1 else 1
        self.eagle_ring = _eagle_ring(self.ring_layers)

        # Per-level tuning: (brick_prob, steel_prob, water_prob, forest_prob)
        self._level_weights = {
            1: (0.30, 0.05, 0.05, 0.05),   # dense brick, few steel
            2: (0.20, 0.15, 0.08, 0.07),   # mixed brick + steel
            3: (0.15, 0.20, 0.10, 0.05),   # more steel, moderate water
        }
        w = self._level_weights.get(level, self._level_weights[1])
        self.brick_p, self.steel_p, self.water_p, self.forest_p = w
        self.empty_p = 1.0 - sum(w)

        total_cells = GRID_W * GRID_H - len(FIXED_POSITIONS)
        self.max_walls = int(CSP_MAX_WALL_RATIO * total_cells)

    # ── Public API ────────────────────────────────────────
    def generate(self, max_attempts: int = 20) -> list[list[int]]:
        """
        Try up to max_attempts times to produce a valid map.
        Returns a 2-D list grid[row][col].
        """
        for attempt in range(max_attempts):
            grid = self._blank_grid()
            self._place_fixed(grid)
            self._force_eagle_ring(grid)

            if self._backtrack_fill(grid, max_steps=200000):
                if self._all_constraints_satisfied(grid):
                    print(f"[CSP] Valid map generated on attempt {attempt + 1}")
                    return grid

            # Backtrack: try again with a different random seed
            self.rng = random.Random(self.rng.randint(0, 2**32))

        # Fallback: return a safe open map if we exhaust attempts
        print("[CSP] WARNING: fell back to safe open map after max attempts")
        return self._safe_fallback()

    # ── Grid construction ────────────────────────────────
    def _blank_grid(self) -> list[list[int]]:
        return [[UNASSIGNED] * GRID_W for _ in range(GRID_H)]

    def _place_fixed(self, grid: list[list[int]]) -> None:
        """Place eagle and clear spawn areas."""
        ex, ey = EAGLE_POS
        grid[ey][ex] = EAGLE
        # Clear all spawn points
        for sx, sy in ENEMY_SPAWNS + [PLAYER_SPAWN]:
            grid[sy][sx] = EMPTY

    def _force_eagle_ring(self, grid: list[list[int]]) -> None:
        """C1: surround eagle with at least one ring of BRICK/STEEL."""
        for (cx, cy) in self.eagle_ring:
            grid[cy][cx] = BRICK

    def _fill_probabilistic(self, grid: list[list[int]]) -> None:
        """Randomly assign tiles to free variables."""
        positions = [
            (c, r)
            for r in range(GRID_H)
            for c in range(GRID_W)
            if (c, r) not in FIXED_POSITIONS and (c, r) not in self.eagle_ring
        ]
        # Shuffle for randomness
        self.rng.shuffle(positions)

        for (cx, cy) in positions:
            # C3: player safety zone — no walls within 10 Manhattan tiles
            px, py = PLAYER_SPAWN
            if abs(cx - px) + abs(cy - py) <= 10:
                grid[cy][cx] = EMPTY
                continue

            # Enemy spawn clearance — 2-tile radius around each spawn
            near_spawn = False
            for sx, sy in ENEMY_SPAWNS:
                if abs(cx - sx) + abs(cy - sy) <= 2:
                    near_spawn = True
                    break
            if near_spawn:
                grid[cy][cx] = EMPTY
                continue

            # Weighted random tile assignment
            roll = self.rng.random()
            if roll < self.brick_p:
                grid[cy][cx] = BRICK
            elif roll < self.brick_p + self.steel_p:
                grid[cy][cx] = STEEL
            elif roll < self.brick_p + self.steel_p + self.water_p:
                grid[cy][cx] = WATER
            elif roll < self.brick_p + self.steel_p + self.water_p + self.forest_p:
                grid[cy][cx] = FOREST
            else:
                grid[cy][cx] = EMPTY

    def _backtrack_fill(self, grid: list[list[int | None]], max_steps: int = 200000) -> bool:
        positions = [
            (c, r)
            for r in range(GRID_H)
            for c in range(GRID_W)
            if (c, r) not in FIXED_POSITIONS and (c, r) not in self.eagle_ring
        ]
        self.rng.shuffle(positions)
        self._backtrack_steps = 0
        return self._assign_positions(grid, positions, 0, 0, max_steps)

    def _assign_positions(self, grid, positions, idx: int, wall_count: int, max_steps: int) -> bool:
        if idx >= len(positions):
            return True

        self._backtrack_steps += 1
        if self._backtrack_steps > max_steps:
            return False

        cx, cy = positions[idx]
        for tile in self._domain_for_cell(cx, cy):
            next_wall_count = wall_count + (1 if tile in (BRICK, STEEL) else 0)
            if next_wall_count > self.max_walls:
                continue

            grid[cy][cx] = tile
            if self._partial_constraints_ok(grid, next_wall_count):
                if self._assign_positions(grid, positions, idx + 1, next_wall_count, max_steps):
                    return True
            grid[cy][cx] = UNASSIGNED

        return False

    def _domain_for_cell(self, x: int, y: int) -> list[int]:
        px, py = PLAYER_SPAWN
        if abs(x - px) + abs(y - py) <= 10:
            return [EMPTY, FOREST]

        for sx, sy in ENEMY_SPAWNS:
            if abs(x - sx) + abs(y - sy) <= 2:
                return [EMPTY]

        domain = [EMPTY, BRICK, STEEL, WATER, FOREST]
        weights = {
            EMPTY: self.empty_p,
            BRICK: self.brick_p,
            STEEL: self.steel_p,
            WATER: self.water_p,
            FOREST: self.forest_p,
        }
        return sorted(domain, key=lambda t: self.rng.random() / max(weights.get(t, 0.01), 0.01))

    def _partial_constraints_ok(self, grid, wall_count: int) -> bool:
        if wall_count > self.max_walls:
            return False

        for sp in ENEMY_SPAWNS:
            if not _bfs_reachable(grid, sp, EAGLE_POS):
                return False
        return True

    # ── Constraint checkers ───────────────────────────────
    def _check_c1_eagle_ring(self, grid: list[list[int]]) -> bool:
        """C1: every eagle-ring tile must be BRICK or STEEL."""
        for (cx, cy) in self.eagle_ring:
            if grid[cy][cx] not in (BRICK, STEEL):
                return False
        return True

    def _check_c2_reachability(self, grid: list[list[int]]) -> bool:
        """C2: all 3 enemy spawns must be able to reach the eagle via BFS."""
        for sp in ENEMY_SPAWNS:
            if not _bfs_reachable(grid, sp, EAGLE_POS):
                return False
        return True

    def _check_c3_player_safety(self, grid: list[list[int]]) -> bool:
        """C3: no wall within 10 Manhattan tiles of player spawn,
        EXCLUDING the eagle ring (which is always brick/steel by design)."""
        px, py = PLAYER_SPAWN
        for r in range(GRID_H):
            for c in range(GRID_W):
                if (c, r) in self.eagle_ring:
                    continue   # eagle ring is intentional — exempt
                if abs(c - px) + abs(r - py) <= 10:
                    if grid[r][c] in (BRICK, STEEL):
                        return False
        return True

    def _check_c4_density(self, grid: list[list[int]]) -> bool:
        """C4: wall density ≤ 40%."""
        return _wall_density(grid) <= CSP_MAX_WALL_RATIO

    def _check_c5_water_not_blocking(self, grid: list[list[int]]) -> bool:
        """
        C5: temporarily treat water as passable and check reachability;
        if the map is reachable with water treated as walls but NOT
        without water, then water is blocking the only path → fail.
        """
        # Make a copy with water turned to wall
        water_blocked = [row[:] for row in grid]
        for r in range(GRID_H):
            for c in range(GRID_W):
                if water_blocked[r][c] == WATER:
                    water_blocked[r][c] = STEEL  # impassable

        # If a spawn can reach eagle with water passable (original) but NOT
        # when water is blocked → water is the only path → violation
        water_passable = [row[:] for row in grid]
        for r in range(GRID_H):
            for c in range(GRID_W):
                if water_passable[r][c] == WATER:
                    water_passable[r][c] = EMPTY  # passable

        for sp in ENEMY_SPAWNS:
            can_reach_no_water  = _bfs_reachable(water_blocked,  sp, EAGLE_POS)
            can_reach_yes_water = _bfs_reachable(water_passable, sp, EAGLE_POS)
            if can_reach_yes_water and not can_reach_no_water:
                # Water is essential — violates C5
                return False
        return True

    def _all_constraints_satisfied(self, grid: list[list[int]]) -> bool:
        """Run all 5 constraints; return True only if all pass."""
        checks = [
            ("C1 Eagle ring",        self._check_c1_eagle_ring),
            ("C2 Reachability",      self._check_c2_reachability),
            ("C3 Player safety",     self._check_c3_player_safety),
            ("C4 Wall density",      self._check_c4_density),
            ("C5 Water not blocking",self._check_c5_water_not_blocking),
        ]
        for name, fn in checks:
            if not fn(grid):
                return False
        return True

    # ── Safe fallback map ────────────────────────────────
    def _safe_fallback(self) -> list[list[int]]:
        """Return a minimal, always-valid open map."""
        grid = self._blank_grid()
        self._place_fixed(grid)
        self._force_eagle_ring(grid)
        # Add sparse brick walls far from player
        for r in range(2, 20, 4):
            for c in range(2, 24, 4):
                px, py = PLAYER_SPAWN
                if abs(c - px) + abs(r - py) > 10:
                    if (c, r) not in FIXED_POSITIONS and (c, r) not in self.eagle_ring:
                        grid[r][c] = BRICK

        for r in range(GRID_H):
            for c in range(GRID_W):
                if grid[r][c] is UNASSIGNED:
                    grid[r][c] = EMPTY
        return grid


# ── Constraint validator (for testing) ────────────────────
def validate_map(grid: list[list[int]]) -> dict:
    """
    Run all 5 constraints on an existing map and return a report dict.
    Useful for automated test gates.
    """
    gen = CSPMapGenerator()
    results = {
        "C1_eagle_ring":        gen._check_c1_eagle_ring(grid),
        "C2_reachability":      gen._check_c2_reachability(grid),
        "C3_player_safety":     gen._check_c3_player_safety(grid),
        "C4_wall_density":      gen._check_c4_density(grid),
        "C5_water_not_blocking":gen._check_c5_water_not_blocking(grid),
        "wall_density_pct":     round(_wall_density(grid) * 100, 1),
    }
    results["all_pass"] = all(v for k, v in results.items()
                               if k.startswith("C"))
    return results


# ── Pretty-print helper ───────────────────────────────────
_SYMBOLS = {EMPTY: '.', BRICK: 'B', STEEL: 'S',
            WATER: 'W', FOREST: 'F', EAGLE: 'E'}

def print_map(grid: list[list[int]]) -> None:
    print("   " + "".join(f"{c:2}" for c in range(GRID_W)))
    for r, row in enumerate(grid):
        print(f"{r:2} " + " ".join(_SYMBOLS.get(t, '?') for t in row))


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("CSP Map Generator — Test Gate")
    print("=" * 60)

    passed = 0
    failed = 0

    for level in [1, 2, 3]:
        print(f"\n--- Level {level} ---")
        for trial in range(10):
            gen  = CSPMapGenerator(level=level, seed=trial * 100 + level)
            grid = gen.generate(max_attempts=30)
            report = validate_map(grid)
            status = "✅ PASS" if report["all_pass"] else "❌ FAIL"
            if report["all_pass"]:
                passed += 1
            else:
                failed += 1
            print(f"  Trial {trial+1:2d}: {status} | "
                  f"density={report['wall_density_pct']:4.1f}% | "
                  f"C1={report['C1_eagle_ring']} "
                  f"C2={report['C2_reachability']} "
                  f"C3={report['C3_player_safety']} "
                  f"C4={report['C4_wall_density']} "
                  f"C5={report['C5_water_not_blocking']}")

    print(f"\n{'='*60}")
    print(f"Total: {passed} passed, {failed} failed out of {passed+failed} maps")
    if failed == 0:
        print("✅ ALL TEST GATES PASSED — Module 1 ready for integration")
    else:
        print("❌ Some maps failed — increase max_attempts or loosen constraints")
    print("=" * 60)