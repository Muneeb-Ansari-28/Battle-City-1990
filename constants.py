# ============================================================
#  constants.py  —  Battle City (Tank 1990)
#  All magic numbers live here. Import this everywhere.
# ============================================================

# ── Grid ────────────────────────────────────────────────────
GRID_SIZE        = 26          # 26 × 26 tiles
TILE_SIZE        = 24          # pixels per tile
GRID_PIXEL       = GRID_SIZE * TILE_SIZE   # 624 px

# ── Window ──────────────────────────────────────────────────
SIDEBAR_WIDTH    = 120
SCREEN_WIDTH     = GRID_PIXEL + SIDEBAR_WIDTH   # 744
SCREEN_HEIGHT    = GRID_PIXEL                   # 624
FPS              = 30

# ── Tile terrain values ─────────────────────────────────────
EMPTY   = 0
BRICK   = 1
STEEL   = 2
WATER   = 3
FOREST  = 4
EAGLE   = 5

# ── A* movement costs ───────────────────────────────────────
COST = {
    EMPTY:  1,
    FOREST: 1,
    BRICK:  3,
    STEEL:  float('inf'),
    WATER:  float('inf'),
    EAGLE:  0,   # goal tile — no cost needed
}

# ── Directions ──────────────────────────────────────────────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]
DIR_NAMES  = {UP: 'UP', DOWN: 'DOWN', LEFT: 'LEFT', RIGHT: 'RIGHT'}

# ── Fixed positions ─────────────────────────────────────────
EAGLE_POS        = (12, 24)
PLAYER_SPAWN     = (4,  24)
ENEMY_SPAWNS     = [(0, 0), (12, 0), (24, 0)]

# ── Tank speed: ticks between moves ─────────────────────────
SPEED_SLOW   = 8   # Basic
SPEED_MEDIUM = 6   # Armor
SPEED_FAST   = 4   # Fast
SPEED_PLAYER = 6

# ── Fire rate: ticks between shots ──────────────────────────
FIRE_BASIC   = 90   # ~3 s at 30 FPS
FIRE_FAST    = 45   # ~1.5 s
FIRE_ARMOR   = 60   # ~2 s
FIRE_PLAYER  = 20   # ~0.67 s  (responsive feel)
FIRE_BOSS_P1 = 15
FIRE_BOSS_P2 = 45
FIRE_BOSS_P3 = 24

# ── Bullet ──────────────────────────────────────────────────
BULLET_SPEED = 2    # tiles per tick

# ── Spawn constraints ───────────────────────────────────────
MAX_ACTIVE_ENEMIES   = 4
ENEMY_POOL_SIZE      = 20
SPAWN_FAIRNESS_DIST  = 10   # Manhattan distance
SPAWN_DELAY_TICKS    = 60   # 2 s between spawns

# ── Boss HP stages ──────────────────────────────────────────
BOSS_HP         = 10
BOSS_PHASE2_HP  = 6
BOSS_PHASE3_HP  = 2

# ── Boss movement speeds (ticks between moves) ──────────────
BOSS_SPEED_P1   = SPEED_SLOW
BOSS_SPEED_P2   = SPEED_MEDIUM
BOSS_SPEED_P3   = SPEED_FAST

# ── Player ──────────────────────────────────────────────────
PLAYER_LIVES    = 10
PLAYER_HP       = 1

# ── Colors (R, G, B) ────────────────────────────────────────
C_BLACK      = (  0,   0,   0)
C_WHITE      = (255, 255, 255)
C_DARKGRAY   = ( 34,  36,  44)
C_GRAY       = (100, 108, 120)
C_LIGHTGRAY  = (188, 196, 208)

C_EMPTY      = ( 22,  24,  30)       # road / dark floor
C_BRICK      = (183,  78,  30)       # brick red
C_BRICK_DARK = (125,  52,  18)       # mortar lines
C_STEEL      = (150, 155, 170)       # metallic grey
C_WATER      = ( 30,  92, 196)       # blue
C_WATER_DARK = ( 20,  66, 148)
C_FOREST     = ( 26, 110,  46)       # deep green
C_EAGLE      = (232, 188,  36)       # gold

C_PLAYER     = ( 68, 238, 108)       # neon green
C_BASIC      = (214, 204,  72)       # yellow
C_FAST       = (240, 126,  60)       # orange
C_ARMOR      = (106, 186, 230)       # blue-grey
C_POWER      = (206,  84, 224)       # purple
C_BOSS       = (236,  72,  72)       # red

C_BULLET_PLY = (255, 244, 138)
C_BULLET_ENE = (255, 110, 110)
C_SIDEBAR    = ( 22,  24,  32)
C_HUD_TEXT   = (230, 232, 214)

# ── UI accents ─────────────────────────────────────────────
C_BG_TOP     = ( 10,  12,  18)
C_BG_BOTTOM  = ( 24,  26,  34)
C_GRID_LINE  = ( 32,  36,  46)
C_PANEL      = ( 20,  24,  34)
C_PANEL_ACC  = ( 60, 220, 255)

# ── Tank types (used as tags) ────────────────────────────────
TYPE_PLAYER = 'player'
TYPE_BASIC  = 'basic'
TYPE_FAST   = 'fast'
TYPE_ARMOR  = 'armor'
TYPE_POWER  = 'power'
TYPE_BOSS   = 'boss'

# ── Agent retreat / BFS retrigger timing ─────────────────────
BFS_RETRIGGER_TICKS   = 150   # every 5 s
ARMOR_RETREAT_TICKS   = 60    # wait 2 s behind cover

# ── CSP density limit ────────────────────────────────────────
CSP_MAX_WALL_RATIO    = 0.40  # max 40 % wall tiles

# ── Boss arena size ──────────────────────────────────────────
BOSS_ARENA_SIZE = 12