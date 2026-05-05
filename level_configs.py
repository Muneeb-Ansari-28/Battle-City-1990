# ============================================================
#  level_configs.py  —  Level definitions + CSP map integration
# ============================================================

from csp_generator import CSPMapGenerator, validate_map

# ── Tile constants (mirror constants.py) ──────────────────
EMPTY  = 0
BRICK  = 1
STEEL  = 2
WATER  = 3
FOREST = 4
EAGLE  = 5

# ── Tank type identifiers ─────────────────────────────────
TYPE_BASIC  = "basic"
TYPE_FAST   = "fast"
TYPE_ARMOR  = "armor"
TYPE_POWER  = "power"
TYPE_BOSS   = "boss"


# ── Level configurations ──────────────────────────────────
LEVEL_CONFIGS = {

    1: {
        "name"          : "Level 1",
        "csp_level"     : 1,          # passed to CSPMapGenerator
        "enemy_pool"    : (
            [(TYPE_BASIC, 7)] +       # 7 Basic tanks from start
            [(TYPE_FAST,  5)]         # 5 Fast tanks after 10 kills
        ),
        "fast_unlock_kills": 10,      # Fast tanks enter after 10 kills
        "total_enemies" : 12,
        "description"   : "Dense brick map. Learn the basics.",
    },

    2: {
        "name"          : "Level 2",
        "csp_level"     : 2,
        "enemy_pool"    : (
            [(TYPE_FAST,  4)] +
            [(TYPE_ARMOR, 3)] +
            [(TYPE_POWER, 2)]
        ),
        "fast_unlock_kills": 0,       # All types active immediately
        "total_enemies" : 9,
        "description"   : "Mixed brick and steel. Armor tanks seek cover.",
    },

    3: {   # Boss level — uses hardcoded arena, not CSP
        "name"          : "Boss Level",
        "csp_level"     : None,       # None = use boss arena
        "enemy_pool"    : [(TYPE_BOSS, 1)],
        "fast_unlock_kills": 0,
        "total_enemies" : 1,
        "description"   : "12×12 arena. Defeat the Boss Tank.",
    },
}


# ── Boss arena (hardcoded 26×26, centred 12×12 play area) ─
def get_boss_arena() -> list[list[int]]:
    """
    Returns a 26×26 grid with a 12×12 mixed arena in the centre.
    Outer border is STEEL walls. Interior has brick columns and
    one water patch to give the boss cover and terrain variety.
    """
    g = [[STEEL] * 26 for _ in range(26)]

    # Clear interior (cols 7–18, rows 7–18)
    for r in range(7, 19):
        for c in range(7, 19):
            g[r][c] = EMPTY

    # Place Eagle at standard position
    g[24][12] = EAGLE

    # Clear path from eagle to interior
    for r in range(19, 25):
        g[r][12] = EMPTY

    # Steel pillars (4 corners of interior)
    for (r, c) in [(8,8),(8,17),(17,8),(17,17)]:
        g[r][c] = STEEL
        g[r][c+1] = STEEL if c+1 < 19 else STEEL

    # Brick walls (horizontal cover strips)
    for c in range(10, 16):
        g[10][c] = BRICK
        g[15][c] = BRICK

    # Water patch (centre-left)
    for r in range(12, 15):
        for c in range(8, 10):
            g[r][c] = WATER

    # Enemy (boss) spawn at top-centre of arena
    g[7][12] = EMPTY

    # Player spawn
    g[22][12] = EMPTY

    return g


# ── Map loader ────────────────────────────────────────────
def load_map(level: int, seed: int = None) -> list[list[int]]:
    """
    Return the map grid for the given level.
    Levels 1 & 2: procedurally generated via CSP.
    Level 3 (Boss): hardcoded arena.
    """
    cfg = LEVEL_CONFIGS.get(level)
    if cfg is None:
        raise ValueError(f"Unknown level {level}")

    if cfg["csp_level"] is None:
        # Boss arena
        return get_boss_arena()

    # Use CSP generator
    gen  = CSPMapGenerator(level=cfg["csp_level"], seed=seed)
    grid = gen.generate(max_attempts=30)

    # Validate (debug / logging)
    report = validate_map(grid)
    if not report["all_pass"]:
        print(f"[WARNING] Level {level} map failed constraints: {report}")

    return grid


# ── Enemy pool builder ────────────────────────────────────
def build_enemy_pool(level: int, kills: int = 0) -> list[str]:
    """
    Returns a flat list of tank-type strings representing the
    enemy queue for this level.  Fast-unlock gate is respected.
    """
    cfg = LEVEL_CONFIGS[level]
    pool = []
    for (tank_type, count) in cfg["enemy_pool"]:
        if tank_type == TYPE_FAST and kills < cfg.get("fast_unlock_kills", 0):
            # Replace fast tanks with basics until unlock threshold
            pool.extend([TYPE_BASIC] * count)
        else:
            pool.extend([tank_type] * count)
    return pool


# ── Quick test ────────────────────────────────────────────
if __name__ == "__main__":
    for lvl in [1, 2, 3]:
        print(f"\nLoading Level {lvl}...")
        grid = load_map(lvl, seed=42)
        pool = build_enemy_pool(lvl)
        print(f"  Pool: {pool}")
        # Spot-check eagle tile
        assert grid[24][12] == EAGLE, "Eagle not at (12,24)!"
        print(f"  Eagle confirmed at (12,24) ✅")
    print("\nAll level configs OK ✅")