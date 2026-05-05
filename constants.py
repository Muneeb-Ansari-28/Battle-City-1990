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
SPEED_SLOW   = 4   # Basic
SPEED_MEDIUM = 3   # Armor
SPEED_FAST   = 2   # Fast
SPEED_PLAYER = 3

# ── Fire rate: ticks between shots ──────────────────────────
FIRE_BASIC   = 90   # ~3 s at 30 FPS
FIRE_FAST    = 45   # ~1.5 s
FIRE_ARMOR   = 60   # ~2 s
FIRE_PLAYER  = 20   # ~0.67 s  (responsive feel)
FIRE_BOSS_P1 = 60
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

# ── Player ──────────────────────────────────────────────────
PLAYER_LIVES    = 3
PLAYER_HP       = 1

# ── Colors (R, G, B) ────────────────────────────────────────
C_BLACK      = (  0,   0,   0)
C_WHITE      = (255, 255, 255)
C_DARKGRAY   = ( 40,  40,  40)
C_GRAY       = (100, 100, 100)
C_LIGHTGRAY  = (180, 180, 180)

C_EMPTY      = ( 20,  20,  20)       # road / dark floor
C_BRICK      = (180,  80,  20)       # brownish red
C_BRICK_DARK = (120,  50,  10)       # mortar lines
C_STEEL      = (140, 140, 160)       # metallic grey
C_WATER      = ( 30,  80, 180)       # blue
C_WATER_DARK = ( 20,  55, 130)
C_FOREST     = ( 30, 100,  30)       # dark green
C_EAGLE      = (220, 180,   0)       # gold

C_PLAYER     = ( 50, 220,  50)       # green
C_BASIC      = (200, 200,  50)       # yellow
C_FAST       = (220, 100,  50)       # orange
C_ARMOR      = (100, 180, 220)       # blue-grey
C_POWER      = (200,  50, 200)       # purple
C_BOSS       = (220,  50,  50)       # red

C_BULLET_PLY = (255, 255, 100)
C_BULLET_ENE = (255,  80,  80)
C_SIDEBAR    = ( 28,  28,  36)
C_HUD_TEXT   = (220, 220, 180)

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