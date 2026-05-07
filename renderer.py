# ============================================================
#  renderer.py  —  All Pygame draw calls
# ============================================================
import math
import os
import pygame
from constants import *
from effects import FXManager
from ai.bfs import bfs_full_path
from ai.astar import astar_full_path
from ai.greedy_bfs import greedy_next_step


class Renderer:
    """
    Draws the complete frame:
      1. Grid tiles (terrain)
      2. Eagles (base)
      3. Tanks
      4. Bullets
      5. Sidebar HUD (lives, score, enemy count, level)
      6. Overlay messages (pause, win, lose)
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame.font.init()
        self.font_large  = pygame.font.SysFont('Bahnschrift', 28, bold=True)
        self.font_medium = pygame.font.SysFont('Bahnschrift', 18, bold=True)
        self.font_small  = pygame.font.SysFont('Bahnschrift', 13)
        self.font_tiny   = pygame.font.SysFont('Bahnschrift', 11)

        self.fx = FXManager(assets_dir="assets/sounds")
        self.ai_debug = False
        self.transition_alpha = 0
        self._score_display = 0
        self._world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._target = self._world_surface
        self._menu_bg = None
        self._menu_bg_scaled = None
        self._menu_bg_size = None
        self._load_menu_bg()

    def _load_menu_bg(self) -> None:
        path = os.path.join("assets", "Menu-Background-Image", "Background.jpg")
        if os.path.exists(path):
            try:
                self._menu_bg = pygame.image.load(path).convert()
            except Exception:
                self._menu_bg = None

    def get_menu_bg(self, size: tuple[int, int]):
        if not self._menu_bg:
            return None
        if self._menu_bg_scaled is None or self._menu_bg_size != size:
            self._menu_bg_scaled = pygame.transform.smoothscale(self._menu_bg, size)
            self._menu_bg_size = size
        return self._menu_bg_scaled

    # ── Master draw call ──────────────────────────────────────
    def draw(self, game_state: dict) -> None:
        self._ensure_surfaces()
        self._target = self._world_surface
        self._target.fill((0, 0, 0, 0))

        self._draw_background()
        self._draw_grid(game_state['grid'])
        self._draw_eagle(game_state['grid'])
        self._draw_bullets(game_state['bullets'])
        self._draw_tanks(game_state)

        if game_state.get('ai_debug'):
            self._draw_ai_debug(game_state)

        self.fx.update()
        self.fx.draw(self._target)

        offset = self.fx.shake.offset()
        self.screen.fill(C_BLACK)
        self.screen.blit(self._world_surface, (int(offset[0]), int(offset[1])))

        self._draw_sidebar(game_state)
        self._draw_crt(self.screen)

        transition_alpha = game_state.get('transition_alpha', 0)
        if transition_alpha > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, transition_alpha))
            self.screen.blit(overlay, (0, 0))

        self.fx.draw_flash(self.screen)

    def _ensure_surfaces(self) -> None:
        if (self._world_surface.get_width() != SCREEN_WIDTH
                or self._world_surface.get_height() != SCREEN_HEIGHT):
            self._world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # ── Grid ──────────────────────────────────────────────────
    def _draw_grid(self, grid) -> None:
        surface = self._target
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = grid.get(x, y)
                rx   = x * TILE_SIZE
                ry   = y * TILE_SIZE
                rect = pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE)
                v = self._tile_variation(x, y)

                if tile == EMPTY:
                    pygame.draw.rect(surface, self._shade(C_EMPTY, v), rect)
                    pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

                elif tile == BRICK:
                    shadow = pygame.Rect(rx + 2, ry + 2, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(surface, (0, 0, 0, 80), shadow)
                    pygame.draw.rect(surface, self._shade(C_BRICK, v), rect)
                    # Mortar lines for texture
                    pygame.draw.line(surface, C_BRICK_DARK,
                                     (rx, ry + TILE_SIZE // 2),
                                     (rx + TILE_SIZE, ry + TILE_SIZE // 2), 1)
                    pygame.draw.line(surface, C_BRICK_DARK,
                                     (rx + TILE_SIZE // 2, ry),
                                     (rx + TILE_SIZE // 2, ry + TILE_SIZE // 2), 1)
                    pygame.draw.line(surface, C_BRICK_DARK,
                                     (rx, ry + TILE_SIZE // 2),
                                     (rx, ry + TILE_SIZE), 1)

                elif tile == STEEL:
                    shadow = pygame.Rect(rx + 2, ry + 2, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(surface, (0, 0, 0, 80), shadow)
                    pygame.draw.rect(surface, self._shade(C_STEEL, v), rect)
                    pygame.draw.rect(surface, C_DARKGRAY, rect, 2)
                    # Cross hatch
                    pygame.draw.line(surface, C_DARKGRAY,
                                     (rx + 4, ry + 4),
                                     (rx + TILE_SIZE - 4, ry + TILE_SIZE - 4), 1)
                    pygame.draw.line(surface, C_DARKGRAY,
                                     (rx + TILE_SIZE - 4, ry + 4),
                                     (rx + 4, ry + TILE_SIZE - 4), 1)

                elif tile == WATER:
                    pygame.draw.rect(surface, self._shade(C_WATER, v), rect)
                    # Wave lines (animated using a time offset)
                    for i in range(2):
                        wy = ry + 5 + i * 10 + (self._time_offset % 4)
                        pygame.draw.arc(surface, C_WATER_DARK,
                                        (rx + 2, wy, 8, 4), 0, 3.14, 2)
                        pygame.draw.arc(surface, C_WATER_DARK,
                                        (rx + 12, wy, 8, 4), 0, 3.14, 2)

                elif tile == FOREST:
                    pygame.draw.rect(surface, self._shade(C_EMPTY, v), rect)   # ground below
                    # Forest drawn LAST (over tanks) — handled in draw_tanks
                    # Here just draw the base
                    pygame.draw.rect(surface, self._shade(C_FOREST, v - 4), rect, 0)
                    pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

                elif tile == EAGLE:
                    pass   # drawn separately

    # ── Eagle (base) ──────────────────────────────────────────
    def _draw_eagle(self, grid) -> None:
        surface = self._target
        ex, ey = EAGLE_POS
        if grid.get(ex, ey) != EAGLE:
            # Eagle destroyed — draw rubble
            rx, ry = ex * TILE_SIZE, ey * TILE_SIZE
            pygame.draw.rect(surface, C_DARKGRAY,
                             (rx, ry, TILE_SIZE, TILE_SIZE))
            return
        rx, ry = ex * TILE_SIZE, ey * TILE_SIZE
        # Gold star-like base symbol
        cx, cy = rx + TILE_SIZE // 2, ry + TILE_SIZE // 2
        self._glow_circle(surface, (cx, cy), 12, (255, 210, 120), 60)
        pygame.draw.polygon(surface, C_EAGLE, [
            (cx,      cy - 10),
            (cx + 4,  cy - 4),
            (cx + 11, cy - 3),
            (cx + 6,  cy + 2),
            (cx + 7,  cy + 9),
            (cx,      cy + 5),
            (cx - 7,  cy + 9),
            (cx - 6,  cy + 2),
            (cx - 11, cy - 3),
            (cx - 4,  cy - 4),
        ])

    # ── Tanks ─────────────────────────────────────────────────
    def _draw_tanks(self, game_state: dict) -> None:
        surface = self._target
        player   = game_state.get('player')
        enemies  = game_state.get('enemies', [])
        grid     = game_state['grid']

        all_tanks = []
        if player and player.alive:
            all_tanks.append(player)
        all_tanks.extend([e for e in enemies if e.active])

        for tank in all_tanks:
            if hasattr(tank, 'visible') and not tank.visible:
                continue
            self._draw_single_tank(tank)

        # Draw forest tiles OVER everything (partial observability)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid.get(x, y) == FOREST:
                    rx, ry = x * TILE_SIZE, y * TILE_SIZE
                    s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    s.fill((30, 100, 30, 200))
                    surface.blit(s, (rx, ry))

    def _draw_single_tank(self, tank) -> None:
        surface = self._target
        rx = tank.x * TILE_SIZE
        ry = tank.y * TILE_SIZE
        cx = rx + TILE_SIZE // 2
        cy = ry + TILE_SIZE // 2
        ts = TILE_SIZE
        color = tank.color

        if tank.tank_type == TYPE_BASIC:
            base_col = (90, 170, 90)
        elif tank.tank_type == TYPE_FAST:
            base_col = (220, 90, 50)
        elif tank.tank_type == TYPE_ARMOR:
            base_col = (120, 150, 190)
        elif tank.tank_type == TYPE_BOSS:
            base_col = (200, 60, 60)
        else:
            base_col = color

        # Shadow
        shadow = pygame.Rect(rx + 4, ry + 4, ts - 6, ts - 6)
        pygame.draw.rect(surface, (0, 0, 0, 120), shadow, border_radius=4)

        # Body
        body = pygame.Rect(rx + 3, ry + 3, ts - 6, ts - 6)
        pygame.draw.rect(surface, base_col, body, border_radius=3)

        # Highlight edge
        pygame.draw.rect(surface, C_WHITE, body, 1, border_radius=3)

        # Barrel (direction indicator)
        dx, dy = tank.direction
        bx1, by1 = cx, cy
        bx2 = cx + dx * (ts // 2 - 1)
        by2 = cy + dy * (ts // 2 - 1)
        pygame.draw.line(surface, C_WHITE, (bx1, by1), (bx2, by2), 3)

        if tank.tank_type == TYPE_FAST:
            trail = pygame.Surface((ts, ts), pygame.SRCALPHA)
            pygame.draw.polygon(trail, (255, 120, 80, 90), [
                (2, ts - 4), (ts // 2, 2), (ts - 2, ts - 4)
            ])
            surface.blit(trail, (rx, ry))

        if tank.tank_type == TYPE_ARMOR and hasattr(tank, 'hit_count'):
            if tank.hit_count > 0:
                pygame.draw.line(surface, (60, 70, 90), (rx + 5, ry + 7), (rx + 16, ry + 5), 2)
                pygame.draw.line(surface, (60, 70, 90), (rx + 8, ry + 16), (rx + 18, ry + 14), 2)

        # HP indicator for Armor tanks (colored stages)
        if hasattr(tank, 'hit_count') and tank.hit_count > 0:
            stage_colors = [color, (255, 255, 0), (255, 150, 0), (255, 50, 50)]
            sc = stage_colors[min(tank.hit_count, 3)]
            pygame.draw.rect(surface, sc, body, 2)

        # Invincibility ring for player
        if hasattr(tank, 'is_invincible') and tank.is_invincible:
            pygame.draw.circle(surface, C_WHITE, (cx, cy), ts // 2, 1)

        if tank.tank_type == TYPE_BOSS:
            glow = self._boss_phase_color(tank)
            self._glow_circle(surface, (cx, cy), 14, glow, 90)
            pygame.draw.rect(surface, glow, body, 2)

    # ── Bullets ───────────────────────────────────────────────
    def _draw_bullets(self, bullets: list) -> None:
        surface = self._target
        for b in bullets:
            if not b.active:
                continue
            bx = b.x * TILE_SIZE + TILE_SIZE // 2
            by = b.y * TILE_SIZE + TILE_SIZE // 2
            col = C_BULLET_PLY if b.is_player_bullet else C_BULLET_ENE
            # Shadow
            pygame.draw.circle(surface, (0, 0, 0, 120), (bx + 2, by + 2), 4)
            # Glow
            glow = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*col, 80), (8, 8), 7)
            surface.blit(glow, (bx - 8, by - 8))
            pygame.draw.circle(surface, col, (bx, by), 4)
            # Motion trail
            dx, dy = b.direction
            pygame.draw.line(surface, col,
                             (bx, by),
                             (bx - dx * 6, by - dy * 6), 2)

    # ── Sidebar HUD ───────────────────────────────────────────
    def _draw_sidebar(self, game_state: dict) -> None:
        sx = GRID_PIXEL + 4
        w  = SIDEBAR_WIDTH - 8
        pygame.draw.rect(self.screen, C_PANEL,
                         (GRID_PIXEL, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, C_GRID_LINE,
                         (GRID_PIXEL, 0), (GRID_PIXEL, SCREEN_HEIGHT), 2)

        # Accent strip
        pygame.draw.rect(self.screen, C_PANEL_ACC,
                         (GRID_PIXEL, 0, 3, SCREEN_HEIGHT))

        player  = game_state.get('player')
        level   = game_state.get('level', 1)
        enemies_left = game_state.get('enemies_remaining', 0)

        y = 16
        def label(text, color=C_HUD_TEXT, font=None):
            nonlocal y
            f = font or self.font_small
            surf = f.render(text, True, color)
            self.screen.blit(surf, (sx, y))
            y += surf.get_height() + 4

        label(f" LVL {level}", C_EAGLE, self.font_medium)
        y += 8

        # Enemy remaining icons
        label("ENEMIES", C_LIGHTGRAY)
        cols = 2
        per_row = cols
        ix = sx + 4
        iy = y
        for i in range(min(enemies_left, 20)):
            ex = ix + (i % per_row) * 14
            ey = iy + (i // per_row) * 14
            pygame.draw.rect(self.screen, C_FAST,
                             (ex, ey, 10, 10), border_radius=2)
        y = iy + ((min(enemies_left, 20) - 1) // per_row + 1) * 14 + 8

        y += 8
        label("PLAYER", C_LIGHTGRAY)
        if player:
            lives = player.lives
            label("LIVES", C_PLAYER)
            lx = sx + 2
            for i in range(min(lives, 10)):
                rx = lx + (i % 2) * 16
                ry = y + (i // 2) * 14
                pygame.draw.rect(self.screen, C_PLAYER, (rx, ry, 12, 8), border_radius=2)
            y += ((min(lives, 10) - 1) // 2 + 1) * 14 + 6

            self._score_display += (player.score - self._score_display) * 0.1
            label(f" SCORE", C_HUD_TEXT)
            label(f" {int(self._score_display)}", C_HUD_TEXT, self.font_medium)
        else:
            label(" ---", C_GRAY)

        # Controls reminder
        y = SCREEN_HEIGHT - 90
        label("MOVE: WASD", C_GRAY)
        label("FIRE: SPACE", C_GRAY)
        label("PAUSE: ESC", C_GRAY)
        label(f"AI VIS: {'ON' if self.ai_debug else 'OFF'}", C_PANEL_ACC)

    # ── Overlay messages ──────────────────────────────────────
    def draw_overlay(self, message: str, sub: str = '') -> None:
        """Draw a semi-transparent centered message overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        cx = GRID_PIXEL // 2
        cy = SCREEN_HEIGHT // 2

        surf = self.font_large.render(message, True, C_EAGLE)
        self.screen.blit(surf, surf.get_rect(center=(cx, cy - 20)))

        if sub:
            surf2 = self.font_medium.render(sub, True, C_HUD_TEXT)
            self.screen.blit(surf2, surf2.get_rect(center=(cx, cy + 20)))

    def draw_pause(self) -> None:
        self.draw_overlay("PAUSED", "ESC to resume")

    def draw_game_over(self, won: bool) -> None:
        msg = "YOU WIN!" if won else "GAME OVER"
        sub = "Press R to restart" if not won else "Press ENTER for next level"
        col = C_PLAYER if won else (220, 50, 50)
        self.draw_overlay(msg, sub)

    # ── Background ─────────────────────────────────────────
    def _draw_background(self) -> None:
        surface = self._target
        # Vertical gradient
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(C_BG_TOP[0] * (1 - t) + C_BG_BOTTOM[0] * t)
            g = int(C_BG_TOP[1] * (1 - t) + C_BG_BOTTOM[1] * t)
            b = int(C_BG_TOP[2] * (1 - t) + C_BG_BOTTOM[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Subtle scanlines
        for y in range(0, SCREEN_HEIGHT, 6):
            pygame.draw.line(surface, (0, 0, 0), (0, y), (SCREEN_WIDTH, y), 1)

        # Time offset used for water waves
        self._time_offset = (getattr(self, "_time_offset", 0) + 1) % 60

    # ── Helpers ─────────────────────────────────────────────
    def _shade(self, color, delta):
        r, g, b = color
        return (max(0, min(255, r + delta)),
                max(0, min(255, g + delta)),
                max(0, min(255, b + delta)))

    def _tile_variation(self, x, y):
        seed = (x * 73856093) ^ (y * 19349663)
        return (seed % 7) - 3

    def _glow_circle(self, surface, pos, radius, color, alpha):
        glow = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (radius + 1, radius + 1), radius)
        surface.blit(glow, (pos[0] - radius - 1, pos[1] - radius - 1))

    def _boss_phase_color(self, tank):
        if tank.hp <= BOSS_PHASE3_HP:
            return (255, 80, 80)
        if tank.hp <= BOSS_PHASE2_HP:
            return (255, 150, 60)
        return (80, 160, 255)

    def _draw_crt(self, surface):
        # Vignette
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 60), vignette.get_rect(), border_radius=0)
        surface.blit(vignette, (0, 0))

    def _draw_ai_debug(self, game_state: dict) -> None:
        surface = self._target
        grid = game_state['grid']
        enemies = game_state.get('enemies', [])
        for e in enemies:
            if not (e.alive and e.active):
                continue
            if e.tank_type == TYPE_BASIC:
                path = bfs_full_path(grid, (e.x, e.y), EAGLE_POS)
                self._draw_path(surface, path, (60, 220, 255, 120))
            elif e.tank_type == TYPE_FAST:
                nxt = greedy_next_step(grid, (e.x, e.y), EAGLE_POS)
                if nxt:
                    self._draw_arrow(surface, (e.x, e.y), nxt, (255, 120, 80))
            elif e.tank_type == TYPE_ARMOR:
                path = astar_full_path(grid, (e.x, e.y), EAGLE_POS)
                self._draw_path(surface, path, (120, 180, 255, 120))
            elif e.tank_type == TYPE_BOSS:
                self._draw_boss_zones(surface, e)

    def _draw_path(self, surface, path, color):
        if not path or len(path) < 2:
            return
        pts = []
        for x, y in path[:16]:
            pts.append((x * TILE_SIZE + TILE_SIZE // 2,
                        y * TILE_SIZE + TILE_SIZE // 2))
        if len(pts) >= 2:
            pygame.draw.lines(surface, color, False, pts, 2)

    def _draw_arrow(self, surface, start, end, color):
        sx, sy = start
        ex, ey = end
        x1 = sx * TILE_SIZE + TILE_SIZE // 2
        y1 = sy * TILE_SIZE + TILE_SIZE // 2
        x2 = ex * TILE_SIZE + TILE_SIZE // 2
        y2 = ey * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)
        pygame.draw.circle(surface, color, (x2, y2), 3)

    def _draw_boss_zones(self, surface, boss):
        bx = boss.x * TILE_SIZE
        by = boss.y * TILE_SIZE
        zone = pygame.Surface((TILE_SIZE * 3, TILE_SIZE * 3), pygame.SRCALPHA)
        zone.fill((255, 60, 60, 40))
        surface.blit(zone, (bx - TILE_SIZE, by - TILE_SIZE))