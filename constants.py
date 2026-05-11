# ============================================================
#  constants.py  —  Battle City (Tank 1990)
#  All magic numbers live here. Import this everywhere.
# ============================================================

# ── Grid ────────────────────────────────────────────────────
GRID_SIZE        = 26          # 26 × 26 tiles
TILE_SIZE        = 24          # pixels per tile
GRID_PIXEL       = GRID_SIZE * TILE_SIZE   # 624 px

# ── Window ──────────────────────────────────────────────────
SIDEBAR_WIDTH    = 160
SCREEN_WIDTH     = GRID_PIXEL + SIDEBAR_WIDTH   # 784
SCREEN_HEIGHT    = GRID_PIXEL                   # 624
FPS              = 45

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
SPEED_SLOW   = 16   # Basic
SPEED_MEDIUM = 12   # Armor
SPEED_FAST   = 9   # Fast
SPEED_PLAYER = 8   # Player (responsive feel)

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

# ── Colors (R, G, B) — Enhanced Neon Arcade Palette ─────────
C_BLACK      = (  0,   0,   0)
C_WHITE      = (255, 255, 255)
C_DARKGRAY   = ( 28,  30,  38)
C_GRAY       = ( 90,  98, 110)
C_LIGHTGRAY  = (180, 188, 200)

# ── Terrain colors ──────────────────────────────────────────
C_EMPTY      = ( 18,  20,  26)       # dark floor
C_EMPTY_ALT  = ( 24,  26,  34)       # alternate floor (checkerboard)
C_BRICK      = (192,  74,  30)       # brick main
C_BRICK_HI   = (225, 110,  58)       # brick highlight
C_BRICK_DARK = (118,  44,  12)       # mortar / shadow
C_BRICK_MORTAR = ( 85,  34,   8)     # deep mortar groove
C_STEEL      = (158, 165, 182)       # steel main
C_STEEL_HI   = (205, 212, 228)       # steel highlight
C_STEEL_DARK = ( 78,  86, 104)       # steel shadow
C_STEEL_RIVET = (115, 122, 138)      # rivet accent
C_WATER      = ( 28,  88, 205)       # water main
C_WATER_HI   = ( 85, 155, 245)       # water highlight / foam
C_WATER_DARK = ( 16,  58, 145)       # water deep
C_FOREST     = ( 24, 108,  44)       # forest main
C_FOREST_HI  = ( 48, 148,  68)       # forest highlight
C_FOREST_DARK = ( 14,  72,  28)      # forest shadow
C_EAGLE      = (242, 198,  42)       # gold
C_EAGLE_GLOW = (255, 225,  85)       # eagle glow ring

# ── Tank colors — Vivid neon ────────────────────────────────
C_PLAYER     = ( 58, 238, 105)       # neon green
C_PLAYER_DARK = ( 32, 165,  62)      # player body shadow
C_BASIC      = (222, 212,  68)       # yellow
C_BASIC_DARK = (162, 152,  42)       # basic shadow
C_FAST       = (248, 122,  52)       # orange
C_FAST_DARK  = (185,  82,  32)       # fast shadow
C_ARMOR      = (102, 185, 235)       # ice blue
C_ARMOR_DARK = ( 62, 125, 175)       # armor shadow
C_POWER      = (214,  84, 228)       # purple
C_POWER_DARK = (155,  52, 168)       # power shadow
C_BOSS       = (242,  68,  68)       # red
C_BOSS_DARK  = (175,  42,  42)       # boss shadow

# ── Bullet colors ───────────────────────────────────────────
C_BULLET_PLY = (255, 250, 132)
C_BULLET_ENE = (255, 105, 105)
C_BULLET_GLOW_PLY = (255, 255, 195)
C_BULLET_GLOW_ENE = (255, 165, 165)

# ── Sidebar / HUD ──────────────────────────────────────────
C_SIDEBAR    = ( 14,  16,  24)
C_HUD_TEXT   = (232, 234, 220)
C_HUD_DIM    = (105, 112, 125)
C_HUD_LABEL  = (150, 158, 172)

# ── UI accents ─────────────────────────────────────────────
C_BG_TOP     = (  8,  10,  16)
C_BG_BOTTOM  = ( 20,  22,  30)
C_GRID_LINE  = ( 28,  32,  42)
C_PANEL      = ( 16,  20,  30)
C_PANEL_BORDER = ( 38,  46,  62)
C_PANEL_ACC  = ( 52, 218, 255)       # cyan accent

# ── UI gradient + glow helpers ─────────────────────────────
C_SIDEBAR_TOP    = ( 12,  16,  28)
C_SIDEBAR_BOTTOM = (  6,   8,  14)
C_PANEL_TOP      = ( 18,  24,  36)
C_PANEL_BOTTOM   = ( 10,  12,  20)
C_PANEL_GLOW     = ( 90, 230, 255)
C_KEY_BG         = ( 22,  26,  36)
C_KEY_EDGE       = ( 60,  70,  90)
C_KEY_TEXT       = (230, 234, 242)
C_SCANLINE       = (  0,   0,   0)

# ── Tank glows ─────────────────────────────────────────────
C_PLAYER_GLOW = ( 80, 255, 140)
C_BASIC_GLOW  = (255, 230, 120)
C_FAST_GLOW   = (255, 160,  90)
C_ARMOR_GLOW  = (120, 220, 255)
C_POWER_GLOW  = (235, 120, 255)
C_BOSS_GLOW   = (255,  90,  90)

# ── HP bar colors ──────────────────────────────────────────
C_HP_GREEN   = ( 78, 232,  98)
C_HP_YELLOW  = (242, 222,  58)
C_HP_ORANGE  = (248, 158,  52)
C_HP_RED     = (242,  72,  58)
C_HP_BG      = ( 28,  32,  42)

# ── Kill feed / combo accents ──────────────────────────────
C_FEED_GOOD   = (120, 255, 180)
C_FEED_WARN   = (255, 190,  90)
C_FEED_BAD    = (255, 120, 120)
C_COMBO_GLOW  = (255, 210, 110)

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