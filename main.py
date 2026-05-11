# ============================================================
#  main.py  —  Battle City (Tank 1990) — Module 0 Entry Point
#  Run:  python main.py
# ============================================================
import sys
import os
import math
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tanks'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'csp'))

import pygame

from constants       import *
from grid            import Grid
from renderer        import Renderer
from game_loop       import GameLoop
from spawner         import Spawner
from level_configs   import load_map, LEVEL_CONFIGS, build_enemy_pool
from tanks.player    import PlayerTank
from tanks.basic_tank import BasicTank
from tanks.fast_tank  import FastTank
from tanks.armor_tank import ArmorTank
from tanks.power_tank import PowerTank
from tanks.boss_tank  import BossTank


# ── State machine ─────────────────────────────────────────────
STATE_MENU     = 'menu'
STATE_PLAYING  = 'playing'
STATE_PAUSED   = 'paused'
STATE_WIN      = 'win'
STATE_LOSE     = 'lose'
STATE_BETWEEN  = 'between'   # inter-level screen

MENU_MODES = [
    {"label": "Adventure (Normal)", "desc": "Play stages 1-3 in order", "start_level": 1},
    {"label": "Stage 1", "desc": "Start at Level 1", "start_level": 1},
    {"label": "Stage 2", "desc": "Start at Level 2", "start_level": 2},
    {"label": "Stage 3", "desc": "Start at Level 3", "start_level": 3},
]

def build_enemy_queue(pool: list, grid: Grid) -> list:
    """Create real AI tank instances from a pool type list."""
    tanks = []
    for t in pool:
        if t == "basic":
            tanks.append(BasicTank(0, 0, grid))
        elif t == "fast":
            tanks.append(FastTank(0, 0, grid))
        elif t == "armor":
            tanks.append(ArmorTank(0, 0, grid))
        elif t == "power":
            tanks.append(PowerTank(0, 0, grid))
        elif t == "boss":
            tanks.append(BossTank(0, 0, grid))
        else:
            tanks.append(BasicTank(0, 0, grid))
    return tanks
def load_level(level_num: int, grid: Grid) -> tuple:
    """
    Load a level:
      - Apply the fallback map (CSP map will replace this in Module 1)
      - Build enemy queue
      - Return (player, spawner, game_loop)
    """
    # Load map
    tiles = load_map(level_num)
    grid.load(tiles)

    # Player
    if level_num == 3:
        player = PlayerTank(12, 22)
    else:
        player = PlayerTank()

    # Enemy pool
    config = LEVEL_CONFIGS.get(level_num, LEVEL_CONFIGS[1])
    pool   = build_enemy_pool(level_num)
    queue  = build_enemy_queue(pool, grid)
    if level_num == 3:
        spawnr = Spawner(queue, spawn_points=[(12, 7)],
                         fast_unlock_kills=config.get('fast_unlock_kills', 0))
    else:
        spawnr = Spawner(queue,
                         fast_unlock_kills=config.get('fast_unlock_kills', 0))

    return player, spawnr


def draw_menu(renderer: Renderer, selected_index: int, modes: list[dict]) -> None:
    import pygame
    time_s = pygame.time.get_ticks() / 1000.0
    screen_width, screen_height = renderer.screen.get_size()
    bg = renderer.get_menu_bg((screen_width, screen_height))
    if bg:
        renderer.screen.blit(bg, (0, 0))
        dark = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        dark.fill((8, 10, 16, 190))
        renderer.screen.blit(dark, (0, 0))
    else:
        for y in range(screen_height):
            tv = y / screen_height
            r = int(C_BG_TOP[0] * (1 - tv) + C_BG_BOTTOM[0] * tv)
            g = int(C_BG_TOP[1] * (1 - tv) + C_BG_BOTTOM[1] * tv)
            b = int(C_BG_TOP[2] * (1 - tv) + C_BG_BOTTOM[2] * tv)
            pygame.draw.line(renderer.screen, (r, g, b), (0, y), (screen_width, y), 1)

    def draw_tank_silhouette(x, y, scale, alpha):
        w = int(28 * scale)
        h = int(20 * scale)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (40, 90, 120, alpha)
        pygame.draw.rect(s, col, (2, 6, w - 4, h - 10), border_radius=4)
        pygame.draw.rect(s, col, (6, 2, w - 12, 6), border_radius=3)
        pygame.draw.line(s, (90, 160, 200, alpha), (w // 2, 6), (w // 2, 0), 2)
        renderer.screen.blit(s, (x, y))

    for i in range(7):
        drift = (time_s * 24 + i * 120) % (screen_width + 200)
        x = int(drift - 100)
        y = int(80 + (i % 3) * 160 + math.sin(time_s * 1.4 + i) * 18)
        scale = 0.9 + 0.08 * math.sin(time_s * 1.8 + i)
        draw_tank_silhouette(x, y, scale, 60)

    cx = screen_width // 2
    font_title = pygame.font.SysFont('Bahnschrift', 58, bold=True)
    font_sub   = pygame.font.SysFont('Bahnschrift', 20)
    font_small = pygame.font.SysFont('Bahnschrift', 14)

    title = font_title.render("BATTLE CITY", True, C_EAGLE)
    glow = pygame.Surface((title.get_width() + 50, title.get_height() + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 200, 80, 120), glow.get_rect())
    renderer.screen.blit(glow, (cx - glow.get_width() // 2, 110))
    renderer.screen.blit(title, title.get_rect(center=(cx, 140)))

    sub = font_sub.render("TANK 1990  |  AI LAB EDITION", True, C_HUD_TEXT)
    renderer.screen.blit(sub, sub.get_rect(center=(cx, 190)))

    def draw_keycap(x, y, label, w=24):
        rect = pygame.Rect(x, y, w, 18)
        pygame.draw.rect(renderer.screen, C_KEY_BG, rect, border_radius=4)
        pygame.draw.rect(renderer.screen, C_KEY_EDGE, rect, 1, border_radius=4)
        text = font_small.render(label, True, C_KEY_TEXT)
        renderer.screen.blit(text, text.get_rect(center=rect.center))

    def draw_glow_rect(rect, color, alpha):
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=10)
        renderer.screen.blit(glow, rect.topleft)

    # Mode selection list
    list_w = 360
    list_x = max(40, cx - list_w // 2 - 80)
    list_y = 235
    label = font_small.render("GAME MODES", True, C_HUD_LABEL)
    renderer.screen.blit(label, (list_x, list_y - 20))

    preview_sets = [
        ("Adventure", [C_BRICK, C_STEEL, C_FOREST]),
        ("Outpost", [C_BRICK, C_WATER, C_FOREST]),
        ("Steel Works", [C_WATER, C_STEEL, C_BRICK]),
        ("Boss Mode", [C_EAGLE, C_BOSS_GLOW, C_WATER]),
    ]

    for i, mode in enumerate(modes):
        rect = pygame.Rect(list_x, list_y + i * 52, list_w, 44)
        is_sel = i == selected_index
        base_col = C_PANEL if is_sel else C_PANEL_TOP
        border_col = C_PANEL_ACC if is_sel else C_PANEL_BORDER
        pygame.draw.rect(renderer.screen, base_col, rect, border_radius=10)
        pygame.draw.rect(renderer.screen, border_col, rect, 2, border_radius=10)
        if is_sel:
            draw_glow_rect(rect.inflate(6, 6), C_PANEL_ACC, 50)
        title_txt = font_sub.render(mode["label"], True, C_HUD_TEXT)
        desc_txt = font_small.render(mode["desc"], True, C_HUD_DIM)
        renderer.screen.blit(title_txt, (rect.x + 14, rect.y + 6))
        renderer.screen.blit(desc_txt, (rect.x + 14, rect.y + 24))

        badge_label, badge_colors = preview_sets[i]
        bx = rect.right - 68
        by = rect.y + 10
        for bi, col in enumerate(badge_colors):
            tile = pygame.Rect(bx + bi * 14, by, 10, 10)
            pygame.draw.rect(renderer.screen, col, tile, border_radius=2)
            pygame.draw.rect(renderer.screen, C_PANEL_BORDER, tile, 1, border_radius=2)
        badge_txt = font_small.render(badge_label, True, C_HUD_DIM)
        renderer.screen.blit(badge_txt, (bx, by + 14))

    hint = font_small.render("W/S or ARROWS to select  |  ENTER to start", True, C_LIGHTGRAY)
    renderer.screen.blit(hint, (list_x, list_y + len(modes) * 52 + 6))

    # Controls panel (right side)
    panel_w = 220
    panel_h = 200
    panel_x = min(screen_width - panel_w - 36, list_x + list_w + 30)
    panel_y = 240
    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(renderer.screen, C_PANEL, panel, border_radius=12)
    pygame.draw.rect(renderer.screen, C_PANEL_ACC, panel, 2, border_radius=12)
    header = font_small.render("GAME CONTROLS", True, C_HUD_LABEL)
    renderer.screen.blit(header, (panel.x + 12, panel.y + 12))

    y = panel.y + 38
    draw_keycap(panel.x + 12, y, "W")
    draw_keycap(panel.x + 12, y + 22, "S")
    draw_keycap(panel.x + 36, y + 22, "A")
    draw_keycap(panel.x + 60, y + 22, "D")
    move_lbl = font_small.render("MOVE", True, C_LIGHTGRAY)
    renderer.screen.blit(move_lbl, (panel.x + 96, y + 20))

    draw_keycap(panel.x + 12, y + 54, "SPACE", 70)
    fire_lbl = font_small.render("FIRE", True, C_LIGHTGRAY)
    renderer.screen.blit(fire_lbl, (panel.x + 96, y + 56))

    draw_keycap(panel.x + 12, y + 86, "ESC", 40)
    pause_lbl = font_small.render("PAUSE", True, C_LIGHTGRAY)
    renderer.screen.blit(pause_lbl, (panel.x + 60, y + 88))

    note = font_small.render("Modules A-C: CSP  |  Search  |  Adversarial AI", True, C_GRAY)
    renderer.screen.blit(note, note.get_rect(center=(cx, SCREEN_HEIGHT - 30)))


def draw_between_levels(renderer: Renderer, level: int, score: int) -> None:
    renderer.screen.fill(C_BLACK)
    renderer.draw_overlay(
        f"LEVEL {level} CLEAR!",
        f"Score: {score}   Press ENTER for Level {level+1}"
    )


def build_end_stats(loop: GameLoop, player: PlayerTank | None) -> dict:
    time_s = (loop.tick_count / max(1, FPS)) if loop else 0
    score = player.score if player else 0
    kills = loop.kills if loop else 0
    return {
        "Kills": kills,
        "Score": score,
        "Time": f"{time_s:.1f}s",
        "Accuracy": "--%",
    }


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE
    )
    pygame.display.set_caption("Battle City — Tank 1990  |  AL2002 AI Lab")
    clock  = pygame.time.Clock()

    renderer = Renderer(screen)
    if renderer.fx.sfx:
        renderer.fx.sfx.load("shoot", "cannon_fire.wav", 0.6)
        renderer.fx.sfx.load("brick", "canon_hit_wood.wav", 0.6)
        renderer.fx.sfx.load("steel", "cannon_hit_concrete.wav", 0.55)
        renderer.fx.sfx.load("water", "cannon_hit_water.wav", 0.5)
        renderer.fx.sfx.load("tank_destroyed", "tank_destroyed.wav", 0.85)
        renderer.fx.sfx.load("grass", "tank_going_in_grass.wav", 0.35)
        renderer.fx.sfx.load("game_over", "game_over.wav", 0.7)

        renderer.fx.sfx.register_music("menu", "menu.wav")
        renderer.fx.sfx.register_music("game", "background_sound.wav")
    grid     = Grid()

    state       = STATE_MENU
    current_lvl = 1
    loop        = None
    player_ref  = None
    final_stats = None
    menu_index  = 0
    current_mode_label = MENU_MODES[0]["label"]
    transition_timer = 0
    transition_max = 18

    while True:
        if renderer.fx.sfx:
            if state == STATE_MENU:
                renderer.fx.sfx.play_music("menu", volume=0.25, loop=True)
            elif state == STATE_PLAYING:
                renderer.fx.sfx.play_music("game", volume=0.2, loop=True)
            else:
                renderer.fx.sfx.play_music("menu", volume=0.18, loop=True)
        # ── Events ────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_TAB:
                    renderer.ai_debug = not renderer.ai_debug

                if state == STATE_MENU:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_index = (menu_index - 1) % len(MENU_MODES)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_index = (menu_index + 1) % len(MENU_MODES)
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        menu_index = min(len(MENU_MODES) - 1, event.key - pygame.K_1)
                    elif event.key == pygame.K_RETURN:
                        mode = MENU_MODES[menu_index]
                        current_lvl = mode["start_level"]
                        current_mode_label = mode["label"]
                        player, spawner = load_level(current_lvl, grid)
                        player_ref = player
                        loop = GameLoop(grid, player, spawner, renderer)
                        loop.level = current_lvl
                        loop.mode_label = current_mode_label
                        state = STATE_PLAYING
                        transition_timer = transition_max
                        final_stats = None

                elif state == STATE_PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_PAUSED

                elif state == STATE_PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_PLAYING

                elif state == STATE_WIN:
                    if event.key == pygame.K_RETURN:
                        if current_lvl < 3:
                            current_lvl += 1
                            player, spawner = load_level(current_lvl, grid)
                            player_ref = player
                            loop = GameLoop(grid, player, spawner, renderer)
                            loop.level = current_lvl
                            loop.mode_label = current_mode_label
                            state = STATE_PLAYING
                            transition_timer = transition_max
                            final_stats = None
                        else:
                            state = STATE_MENU

                elif state == STATE_LOSE:
                    if event.key == pygame.K_r:
                        current_lvl = 1
                        player, spawner = load_level(current_lvl, grid)
                        player_ref = player
                        loop = GameLoop(grid, player, spawner, renderer)
                        loop.level = current_lvl
                        loop.mode_label = current_mode_label
                        state = STATE_PLAYING
                        transition_timer = transition_max
                        final_stats = None
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MENU

        # ── State rendering / logic ───────────────────────────
        if transition_timer > 0:
            transition_timer -= 1
        renderer.transition_alpha = int(255 * (transition_timer / max(1, transition_max)))

        if state == STATE_MENU:
            draw_menu(renderer, menu_index, MENU_MODES)

        elif state == STATE_PLAYING:
            result = loop.tick()
            if result == 'win':
                state = STATE_WIN
                transition_timer = transition_max
                final_stats = build_end_stats(loop, loop.player if loop else None)
            elif result == 'lose':
                state = STATE_LOSE
                transition_timer = transition_max
                final_stats = build_end_stats(loop, loop.player if loop else None)
                if renderer.fx.sfx:
                    renderer.fx.sfx.play("game_over", volume_scale=0.8)

        elif state == STATE_PAUSED:
            # Render last frame + overlay
            gs = {
                'grid':              grid,
                'player':            loop.player if loop else None,
                'enemies':           loop.enemies if loop else [],
                'bullets':           loop.bullets if loop else [],
                'tick':              loop.tick_count if loop else 0,
                'enemies_remaining': 0,
                'level':             current_lvl,
                'mode_label':        current_mode_label,
                'ai_debug':          renderer.ai_debug,
                'transition_alpha':  renderer.transition_alpha,
            }
            renderer.draw(gs)
            renderer.draw_pause(mode_label=current_mode_label, level=current_lvl)

        elif state == STATE_WIN:
            gs = {
                'grid': grid, 'player': player_ref,
                'enemies': [], 'bullets': [],
                'tick': 0, 'enemies_remaining': 0,
                'level': current_lvl,
                'mode_label':        current_mode_label,
                'ai_debug':          renderer.ai_debug,
                'transition_alpha':  renderer.transition_alpha,
            }
            renderer.draw(gs)
            sub = ("ENTER: Next Level" if current_lvl < 3 else "ESC: Menu")
            renderer.draw_game_over(won=True, stats=final_stats, sub=sub)

        elif state == STATE_LOSE:
            gs = {
                'grid': grid, 'player': player_ref,
                'enemies': [], 'bullets': [],
                'tick': 0, 'enemies_remaining': 0,
                'level': current_lvl,
                'mode_label':        current_mode_label,
                'ai_debug':          renderer.ai_debug,
                'transition_alpha':  renderer.transition_alpha,
            }
            renderer.draw(gs)
            renderer.draw_game_over(won=False, stats=final_stats, sub="R: Restart   |   ESC: Menu")

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()