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


def draw_menu(renderer: Renderer) -> None:
    import pygame
    time_s = pygame.time.get_ticks() / 1000.0
    bg = renderer.get_menu_bg((SCREEN_WIDTH, SCREEN_HEIGHT))
    if bg:
        renderer.screen.blit(bg, (0, 0))
        dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark.fill((10, 12, 18, 190))
        renderer.screen.blit(dark, (0, 0))
    else:
        # Gradient background fallback
        for y in range(SCREEN_HEIGHT):
            tv = y / SCREEN_HEIGHT
            r = int(C_BG_TOP[0] * (1 - tv) + C_BG_BOTTOM[0] * tv)
            g = int(C_BG_TOP[1] * (1 - tv) + C_BG_BOTTOM[1] * tv)
            b = int(C_BG_TOP[2] * (1 - tv) + C_BG_BOTTOM[2] * tv)
            pygame.draw.line(renderer.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Subtle scanlines
    for y in range(0, SCREEN_HEIGHT, 6):
        pygame.draw.line(renderer.screen, (0, 0, 0), (0, y), (SCREEN_WIDTH, y), 1)
    cx = GRID_PIXEL // 2

    font_title = pygame.font.SysFont('Bahnschrift', 48, bold=True)
    font_sub   = pygame.font.SysFont('Bahnschrift', 18)
    font_small = pygame.font.SysFont('Bahnschrift', 14)

    # Title panel
    panel = pygame.Rect(cx - 210, 110, 420, 140)
    pygame.draw.rect(renderer.screen, C_PANEL, panel, border_radius=12)
    pygame.draw.rect(renderer.screen, C_GRID_LINE, panel, 2, border_radius=12)
    pygame.draw.rect(renderer.screen, C_PANEL_ACC,
                     (panel.left, panel.top, 6, panel.height), border_radius=8)

    glow = int(80 + (math.sin(time_s * 3.0) + 1) * 40)
    title = font_title.render("BATTLE CITY", True, C_EAGLE)
    renderer.screen.blit(title, title.get_rect(center=(cx, 160)))
    halo = pygame.Surface((title.get_width() + 40, title.get_height() + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(halo, (255, 200, 80, glow), halo.get_rect())
    renderer.screen.blit(halo, (cx - halo.get_width() // 2, 140))

    sub = font_sub.render("TANK 1990 — AI LAB EDITION", True, C_HUD_TEXT)
    renderer.screen.blit(sub, sub.get_rect(center=(cx, 205)))

    # Start button
    btn = pygame.Rect(cx - 160, 280, 320, 44)
    pygame.draw.rect(renderer.screen, C_PANEL, btn, border_radius=10)
    pygame.draw.rect(renderer.screen, C_PANEL_ACC, btn, 2, border_radius=10)
    pulse = 140 + int(60 * (math.sin(time_s * 4.0) * 0.5 + 0.5))
    start = font_sub.render("PRESS ENTER TO START", True, (60, pulse, 120))
    renderer.screen.blit(start, start.get_rect(center=btn.center))

    controls = [
        "WASD / Arrow Keys  —  Move",
        "SPACE or J         —  Shoot",
        "ESC                —  Pause",
        "R                  —  Restart (on Game Over)",
    ]
    y = 360
    for line in controls:
        s = font_small.render(line, True, C_LIGHTGRAY)
        renderer.screen.blit(s, s.get_rect(center=(cx, y)))
        y += 22

    # Module progress indicator
    note = font_small.render(
        "Modules A–C: CSP • Search • Adversarial AI", True, C_GRAY)
    renderer.screen.blit(note, note.get_rect(center=(cx, SCREEN_HEIGHT - 30)))


def draw_between_levels(renderer: Renderer, level: int, score: int) -> None:
    renderer.screen.fill(C_BLACK)
    renderer.draw_overlay(
        f"LEVEL {level} CLEAR!",
        f"Score: {score}   Press ENTER for Level {level+1}"
    )


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
                    if event.key == pygame.K_RETURN:
                        current_lvl = 1
                        player, spawner = load_level(current_lvl, grid)
                        player_ref = player
                        loop = GameLoop(grid, player, spawner, renderer)
                        loop.level = current_lvl
                        state = STATE_PLAYING
                        transition_timer = transition_max

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
                            state = STATE_PLAYING
                            transition_timer = transition_max
                        else:
                            state = STATE_MENU

                elif state == STATE_LOSE:
                    if event.key == pygame.K_r:
                        current_lvl = 1
                        player, spawner = load_level(current_lvl, grid)
                        player_ref = player
                        loop = GameLoop(grid, player, spawner, renderer)
                        loop.level = current_lvl
                        state = STATE_PLAYING
                        transition_timer = transition_max
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_MENU

        # ── State rendering / logic ───────────────────────────
        if transition_timer > 0:
            transition_timer -= 1
        renderer.transition_alpha = int(255 * (transition_timer / max(1, transition_max)))

        if state == STATE_MENU:
            draw_menu(renderer)

        elif state == STATE_PLAYING:
            result = loop.tick()
            if result == 'win':
                state = STATE_WIN
                transition_timer = transition_max
            elif result == 'lose':
                state = STATE_LOSE
                transition_timer = transition_max
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
                'ai_debug':          renderer.ai_debug,
                'transition_alpha':  renderer.transition_alpha,
            }
            renderer.draw(gs)
            renderer.draw_pause()

        elif state == STATE_WIN:
            gs = {
                'grid': grid, 'player': player_ref,
                'enemies': [], 'bullets': [],
                'tick': 0, 'enemies_remaining': 0,
                'level': current_lvl,
                'ai_debug':          renderer.ai_debug,
                'transition_alpha':  renderer.transition_alpha,
            }
            renderer.draw(gs)
            score = player_ref.score if player_ref else 0
            renderer.draw_overlay(
                "LEVEL CLEAR!",
                f"Score: {score}  — ENTER: Next Level  |  ESC: Menu"
            )

        elif state == STATE_LOSE:
            gs = {
                'grid': grid, 'player': player_ref,
                'enemies': [], 'bullets': [],
                'tick': 0, 'enemies_remaining': 0,
                'level': current_lvl,
                'ai_debug':          renderer.ai_debug,
                'transition_alpha':  renderer.transition_alpha,
            }
            renderer.draw(gs)
            renderer.draw_game_over(won=False)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()