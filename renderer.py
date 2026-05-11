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
        self.font_huge   = pygame.font.SysFont('Bahnschrift', 40, bold=True)
        self.font_title  = pygame.font.SysFont('Bahnschrift', 32, bold=True)

        self.fx = FXManager(assets_dir="assets/sounds")
        self.ai_debug = False
        self.transition_alpha = 0
        self._score_display = 0
        self._world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._target = self._world_surface
        self._time_offset = 0
        self._tank_prev_pos = {}
        self._kill_feed = []
        self._last_kills = 0
        self._vignette = None
        self._vignette_size = None
        self._scanlines = None
        self._scanlines_size = None
        self._overlay_key = None
        self._overlay_start = 0
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
        self._update_kill_feed(game_state)
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
                    base = self._shade(C_EMPTY, v)
                    alt = self._shade(C_EMPTY_ALT, v)
                    pygame.draw.rect(surface, alt if (x + y) % 2 == 0 else base, rect)
                    # subtle floor dots
                    if (x * 3 + y * 5) % 7 == 0:
                        pygame.draw.circle(surface, self._shade(C_GRID_LINE, -6),
                                           (rx + TILE_SIZE - 6, ry + 6), 1)
                    pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

                elif tile == BRICK:
                    pygame.draw.rect(surface, self._shade(C_BRICK, v), rect)
                    bw = TILE_SIZE // 2
                    bh = TILE_SIZE // 2
                    for by in range(2):
                        for bx in range(2):
                            brect = pygame.Rect(rx + bx * bw, ry + by * bh, bw, bh)
                            main = self._shade(C_BRICK, v + (bx - by) * 2)
                            pygame.draw.rect(surface, main, brect)
                            # highlight and shadow
                            pygame.draw.line(surface, C_BRICK_HI,
                                             (brect.left + 1, brect.top + 1),
                                             (brect.right - 2, brect.top + 1), 1)
                            pygame.draw.line(surface, C_BRICK_DARK,
                                             (brect.left + 1, brect.bottom - 2),
                                             (brect.right - 2, brect.bottom - 2), 1)
                            pygame.draw.line(surface, C_BRICK_DARK,
                                             (brect.right - 2, brect.top + 1),
                                             (brect.right - 2, brect.bottom - 2), 1)
                    # mortar grooves
                    pygame.draw.line(surface, C_BRICK_MORTAR,
                                     (rx, ry + bh), (rx + TILE_SIZE, ry + bh), 1)
                    pygame.draw.line(surface, C_BRICK_MORTAR,
                                     (rx + bw, ry), (rx + bw, ry + TILE_SIZE), 1)

                elif tile == STEEL:
                    pygame.draw.rect(surface, self._shade(C_STEEL, v), rect)
                    pygame.draw.line(surface, C_STEEL_HI,
                                     (rx + 2, ry + 4),
                                     (rx + TILE_SIZE - 4, ry + TILE_SIZE - 6), 2)
                    pygame.draw.line(surface, C_STEEL_DARK,
                                     (rx + 4, ry + TILE_SIZE - 4),
                                     (rx + TILE_SIZE - 4, ry + 4), 1)
                    for px, py in [(3, 3), (TILE_SIZE - 5, 3), (3, TILE_SIZE - 5), (TILE_SIZE - 5, TILE_SIZE - 5)]:
                        pygame.draw.circle(surface, C_STEEL_RIVET, (rx + px, ry + py), 2)
                        pygame.draw.circle(surface, C_STEEL_HI, (rx + px - 1, ry + py - 1), 1)
                    pygame.draw.rect(surface, C_STEEL_DARK, rect, 1)

                elif tile == WATER:
                    pygame.draw.rect(surface, self._shade(C_WATER, v), rect)
                    t = self._time_offset / 10.0
                    for i in range(3):
                        wy = ry + 4 + i * 7 + int(math.sin(t + (x + i) * 0.6) * 2)
                        pygame.draw.arc(surface, C_WATER_DARK,
                                        (rx + 2, wy, 10, 5), 0, math.pi, 1)
                        pygame.draw.arc(surface, C_WATER_HI,
                                        (rx + 10, wy, 10, 5), 0, math.pi, 1)
                    pygame.draw.circle(surface, C_WATER_HI, (rx + 4, ry + 4), 1)
                    pygame.draw.circle(surface, C_WATER_HI, (rx + TILE_SIZE - 5, ry + TILE_SIZE - 5), 1)

                elif tile == FOREST:
                    pygame.draw.rect(surface, self._shade(C_EMPTY, v), rect)
                    pygame.draw.rect(surface, self._shade(C_FOREST, v - 2), rect)
                    for i in range(3):
                        dx = (x * 7 + y * 11 + i * 5) % (TILE_SIZE - 4) + 2
                        dy = (x * 5 + y * 9 + i * 7) % (TILE_SIZE - 4) + 2
                        col = C_FOREST_HI if i % 2 == 0 else C_FOREST_DARK
                        pygame.draw.circle(surface, col, (rx + dx, ry + dy), 2)
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
            pygame.draw.rect(surface, C_DARKGRAY, (rx, ry, TILE_SIZE, TILE_SIZE))
            t = pygame.time.get_ticks() / 1000.0
            for i in range(6):
                dx = int((math.sin(t * 2.4 + i) + 1) * 4) + (i % 3) * 6
                dy = int((math.cos(t * 2.0 + i) + 1) * 3) + (i // 3) * 6
                w = 3 if i % 2 == 0 else 2
                h = 2 if i % 3 == 0 else 3
                col = C_BRICK_DARK if i % 2 == 0 else C_GRAY
                pygame.draw.rect(surface, col, (rx + dx, ry + dy, w, h))
            return
        rx, ry = ex * TILE_SIZE, ey * TILE_SIZE
        # Gold star-like base symbol
        cx, cy = rx + TILE_SIZE // 2, ry + TILE_SIZE // 2
        t = pygame.time.get_ticks() / 1000.0
        pulse = 1.0 + 0.08 * math.sin(t * 4.0)
        glow_alpha = 70 + int((math.sin(t * 3.0) + 1) * 30)
        self._glow_circle(surface, (cx, cy), int(14 * pulse), C_EAGLE_GLOW, glow_alpha)
        self._glow_circle(surface, (cx, cy), int(9 * pulse), C_EAGLE, 60)
        pygame.draw.circle(surface, C_EAGLE_GLOW, (cx, cy), int(12 * pulse), 1)
        pygame.draw.polygon(surface, C_EAGLE, [
            (cx,      cy - int(11 * pulse)),
            (cx + 4,  cy - 4),
            (cx + int(12 * pulse), cy - 3),
            (cx + 6,  cy + 2),
            (cx + 7,  cy + int(9 * pulse)),
            (cx,      cy + 5),
            (cx - 7,  cy + int(9 * pulse)),
            (cx - 6,  cy + 2),
            (cx - int(12 * pulse), cy - 3),
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

        next_prev = {}
        for tank in all_tanks:
            if hasattr(tank, 'visible') and not tank.visible:
                continue
            prev = self._tank_prev_pos.get(id(tank))
            moved = prev is not None and prev != (tank.x, tank.y)
            self._draw_single_tank(tank, moved=moved)
            next_prev[id(tank)] = (tank.x, tank.y)
        self._tank_prev_pos = next_prev

        # Draw forest tiles OVER everything (partial observability)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid.get(x, y) == FOREST:
                    rx, ry = x * TILE_SIZE, y * TILE_SIZE
                    s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    s.fill((20, 90, 30, 170))
                    for i in range(3):
                        dx = (x * 9 + y * 7 + i * 4) % (TILE_SIZE - 4) + 2
                        dy = (x * 5 + y * 11 + i * 6) % (TILE_SIZE - 4) + 2
                        col = (50, 140, 70, 180) if i % 2 == 0 else (10, 60, 20, 180)
                        pygame.draw.circle(s, col, (dx, dy), 2)
                    surface.blit(s, (rx, ry))

    def _draw_single_tank(self, tank, moved: bool = False) -> None:
        surface = self._target
        rx = tank.x * TILE_SIZE
        ry = tank.y * TILE_SIZE
        cx = rx + TILE_SIZE // 2
        cy = ry + TILE_SIZE // 2
        ts = TILE_SIZE
        if tank.tank_type == TYPE_PLAYER:
            base_col, dark_col, glow_col = C_PLAYER, C_PLAYER_DARK, C_PLAYER_GLOW
        elif tank.tank_type == TYPE_BASIC:
            base_col, dark_col, glow_col = C_BASIC, C_BASIC_DARK, C_BASIC_GLOW
        elif tank.tank_type == TYPE_FAST:
            base_col, dark_col, glow_col = C_FAST, C_FAST_DARK, C_FAST_GLOW
        elif tank.tank_type == TYPE_ARMOR:
            base_col, dark_col, glow_col = C_ARMOR, C_ARMOR_DARK, C_ARMOR_GLOW
        elif tank.tank_type == TYPE_POWER:
            base_col, dark_col, glow_col = C_POWER, C_POWER_DARK, C_POWER_GLOW
        elif tank.tank_type == TYPE_BOSS:
            base_col, dark_col, glow_col = C_BOSS, C_BOSS_DARK, C_BOSS_GLOW
        else:
            base_col, dark_col, glow_col = tank.color, C_DARKGRAY, tank.color

        dx, dy = tank.direction
        # Glow halo underneath
        glow_rect = pygame.Rect(rx + 2, ry + 6, ts - 4, ts - 8)
        self._glow_ellipse(surface, glow_rect, glow_col, 70)

        # Exhaust particles for moving tanks
        if moved:
            ex = cx - dx * (ts // 2 - 2)
            ey = cy - dy * (ts // 2 - 2)
            self.fx.exhaust(ex, ey, tank.direction, color=self._shade(dark_col, -10))

        # Shadow
        shadow = pygame.Rect(rx + 4, ry + 5, ts - 6, ts - 6)
        pygame.draw.rect(surface, (0, 0, 0, 120), shadow, border_radius=4)

        # Treads (direction-aware)
        tread_col = self._shade(dark_col, -12)
        if dx != 0:
            pygame.draw.rect(surface, tread_col, (rx + 2, ry + 2, ts - 4, 3), border_radius=2)
            pygame.draw.rect(surface, tread_col, (rx + 2, ry + ts - 5, ts - 4, 3), border_radius=2)
        else:
            pygame.draw.rect(surface, tread_col, (rx + 2, ry + 2, 3, ts - 4), border_radius=2)
            pygame.draw.rect(surface, tread_col, (rx + ts - 5, ry + 2, 3, ts - 4), border_radius=2)

        # Body
        body = pygame.Rect(rx + 4, ry + 4, ts - 8, ts - 8)
        pygame.draw.rect(surface, base_col, body, border_radius=4)
        pygame.draw.rect(surface, self._shade(base_col, 28), body, 1, border_radius=4)
        pygame.draw.rect(surface, self._shade(dark_col, -6), body, 1, border_radius=4)

        # Turret
        if dx != 0:
            turret = pygame.Rect(cx - 6, cy - 4, 12, 8)
        else:
            turret = pygame.Rect(cx - 4, cy - 6, 8, 12)
        pygame.draw.rect(surface, self._shade(base_col, 18), turret, border_radius=3)
        pygame.draw.rect(surface, self._shade(dark_col, -8), turret, 1, border_radius=3)

        # Barrel
        bx1, by1 = cx, cy
        bx2 = cx + dx * (ts // 2 - 1)
        by2 = cy + dy * (ts // 2 - 1)
        pygame.draw.line(surface, C_WHITE, (bx1, by1), (bx2, by2), 3)

        # Speed lines for fast tanks
        if tank.tank_type == TYPE_FAST and moved:
            for i in range(3):
                offset = (i - 1) * 3
                sx = cx - dx * 10 + dy * offset
                sy = cy - dy * 10 + dx * offset
                exl = sx - dx * 6
                eyl = sy - dy * 6
                pygame.draw.line(surface, (*glow_col, 140), (sx, sy), (exl, eyl), 2)

        # Armor shield overlay and cracks
        if tank.tank_type == TYPE_ARMOR and hasattr(tank, 'hit_count'):
            if tank.hit_count > 0:
                overlay = pygame.Surface((body.width, body.height), pygame.SRCALPHA)
                overlay.fill((80, 120, 160, 70))
                surface.blit(overlay, (body.x, body.y))
                cracks = [
                    ((body.x + 3, body.y + 5), (body.x + body.width - 4, body.y + 3)),
                    ((body.x + 4, body.y + body.height - 4), (body.x + body.width - 6, body.y + 7)),
                    ((body.x + 6, body.y + 8), (body.x + body.width - 8, body.y + body.height - 6)),
                ]
                for i in range(min(tank.hit_count, len(cracks))):
                    pygame.draw.line(surface, (200, 220, 240), cracks[i][0], cracks[i][1], 1)

        # Boss aura + HP bar above head
        if tank.tank_type == TYPE_BOSS:
            t = pygame.time.get_ticks() / 1000.0
            phase_col = self._boss_phase_color(tank)
            for ring in range(2):
                radius = 12 + ring * 4 + int((math.sin(t * 3.0 + ring) + 1) * 2)
                self._glow_circle(surface, (cx, cy), radius, phase_col, 70 - ring * 10)
            hp_pct = max(0.0, min(1.0, tank.hp / max(1, tank.max_hp)))
            bar_w = ts - 4
            bar_x = rx + 2
            bar_y = ry - 6
            pygame.draw.rect(surface, C_HP_BG, (bar_x, bar_y, bar_w, 4))
            pygame.draw.rect(surface, phase_col, (bar_x, bar_y, int(bar_w * hp_pct), 4))

        # Invincibility ring for player
        if hasattr(tank, 'is_invincible') and tank.is_invincible:
            t = pygame.time.get_ticks() / 1000.0
            pulse = 1.0 + 0.1 * math.sin(t * 6.0)
            pygame.draw.circle(surface, C_PLAYER_GLOW, (cx, cy), int((ts // 2) * pulse), 2)

    # ── Bullets ───────────────────────────────────────────────
    def _draw_bullets(self, bullets: list) -> None:
        surface = self._target
        for b in bullets:
            if not b.active:
                continue
            bx = b.x * TILE_SIZE + TILE_SIZE // 2
            by = b.y * TILE_SIZE + TILE_SIZE // 2
            col = C_BULLET_PLY if b.is_player_bullet else C_BULLET_ENE
            glow_col = C_BULLET_GLOW_PLY if b.is_player_bullet else C_BULLET_GLOW_ENE
            # Shadow
            pygame.draw.circle(surface, (0, 0, 0, 120), (bx + 2, by + 2), 4)
            # Radial glow
            glow = pygame.Surface((20, 20), pygame.SRCALPHA)
            for r, a in [(8, 50), (6, 90), (4, 140)]:
                pygame.draw.circle(glow, (*glow_col, a), (10, 10), r)
            surface.blit(glow, (bx - 10, by - 10))
            pygame.draw.circle(surface, col, (bx, by), 3)

            # Motion trail with fade
            dx, dy = b.direction
            trail = pygame.Surface((24, 24), pygame.SRCALPHA)
            for i in range(3):
                alpha = 140 - i * 40
                sx = 12 - dx * (i * 4)
                sy = 12 - dy * (i * 4)
                ex = sx - dx * 5
                ey = sy - dy * 5
                pygame.draw.line(trail, (*col, alpha), (sx, sy), (ex, ey), 2)
            surface.blit(trail, (bx - 12, by - 12))

    # ── Sidebar HUD ───────────────────────────────────────────
    def _draw_sidebar(self, game_state: dict) -> None:
        sidebar = pygame.Surface((SIDEBAR_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            t = y / max(1, SCREEN_HEIGHT)
            col = self._lerp_color(C_SIDEBAR_TOP, C_SIDEBAR_BOTTOM, t)
            pygame.draw.line(sidebar, col, (0, y), (SIDEBAR_WIDTH, y))

        # Border and accent
        pygame.draw.rect(sidebar, C_PANEL_BORDER, sidebar.get_rect(), 1)
        pygame.draw.rect(sidebar, C_PANEL_ACC, (0, 0, 4, SCREEN_HEIGHT))

        player  = game_state.get('player')
        level   = game_state.get('level', 1)
        enemies_left = game_state.get('enemies_remaining', 0)
        enemies = game_state.get('enemies', [])
        boss = next((e for e in enemies if e.tank_type == TYPE_BOSS and e.active), None)

        def draw_label(text, x, y, color=C_HUD_TEXT, font=None):
            f = font or self.font_small
            surf = f.render(text, True, color)
            sidebar.blit(surf, (x, y))
            return y + surf.get_height() + 4

        # Level banner
        banner = pygame.Rect(10, 10, SIDEBAR_WIDTH - 20, 32)
        pygame.draw.rect(sidebar, C_PANEL_TOP, banner, border_radius=8)
        pygame.draw.rect(sidebar, C_PANEL_ACC, banner, 2, border_radius=8)
        label = self.font_medium.render(f"LEVEL {level}", True, C_EAGLE)
        sidebar.blit(label, label.get_rect(center=banner.center))

        y = 54
        if boss:
            y = draw_label("BOSS", 12, y, C_FEED_WARN, self.font_small)
            hp_pct = max(0.0, min(1.0, boss.hp / max(1, boss.max_hp)))
            bar = pygame.Rect(12, y, SIDEBAR_WIDTH - 24, 8)
            pygame.draw.rect(sidebar, C_HP_BG, bar, border_radius=4)
            pygame.draw.rect(sidebar, C_BOSS_GLOW, (bar.x, bar.y, int(bar.w * hp_pct), bar.h), border_radius=4)
            y += 14

        # Enemy count
        y = draw_label("ENEMIES", 12, y, C_HUD_LABEL, self.font_small)
        cols = 4
        ix = 12
        iy = y
        for i in range(min(enemies_left, 20)):
            ex = ix + (i % cols) * 16
            ey = iy + (i // cols) * 16
            self._draw_mini_tank(sidebar, ex, ey, C_FAST)
        if enemies_left > 0:
            y = iy + ((min(enemies_left, 20) - 1) // cols + 1) * 16 + 8
        else:
            y = iy + 12

        # Player lives
        y = draw_label("PLAYER", 12, y, C_HUD_LABEL, self.font_small)
        if player:
            y = draw_label("LIVES", 12, y, C_PLAYER, self.font_small)
            lives = player.lives
            cols = 3
            lx = 12
            ly = y
            for i in range(min(lives, 12)):
                ex = lx + (i % cols) * 18
                ey = ly + (i // cols) * 16
                self._draw_mini_tank(sidebar, ex, ey, C_PLAYER)
            y = ly + ((min(lives, 12) - 1) // cols + 1) * 16 + 6

            # Score roll-up
            self._score_display += (player.score - self._score_display) * 0.12
            y = draw_label("SCORE", 12, y, C_HUD_LABEL, self.font_small)
            score_text = self.font_medium.render(f"{int(self._score_display)}", True, C_HUD_TEXT)
            sidebar.blit(score_text, (12, y - 2))
            y += score_text.get_height() + 6
        else:
            y = draw_label("--", 12, y, C_GRAY, self.font_small)

        # Kill feed
        y = max(y + 4, SCREEN_HEIGHT - 180)
        y = draw_label("FEED", 12, y, C_HUD_LABEL, self.font_small)
        for entry in self._kill_feed[:3]:
            age = entry["age"]
            alpha = max(0, 255 - age * 8)
            col = entry["color"]
            txt = self.font_tiny.render(entry["text"], True, col)
            txt.set_alpha(alpha)
            sidebar.blit(txt, (12, y))
            y += txt.get_height() + 2

        # Status bar
        stage_name = game_state.get('stage_name', '')
        stage_desc = game_state.get('stage_desc', '')
        tick = game_state.get('tick', 0)
        time_s = tick / max(1, FPS)
        mins = int(time_s // 60)
        secs = int(time_s % 60)
        status = pygame.Rect(10, SCREEN_HEIGHT - 122, SIDEBAR_WIDTH - 20, 22)
        pygame.draw.rect(sidebar, C_PANEL_TOP, status, border_radius=8)
        pygame.draw.rect(sidebar, C_PANEL_BORDER, status, 1, border_radius=8)
        glow = pygame.Surface((status.width, status.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*C_PANEL_ACC, 24), glow.get_rect(), border_radius=8)
        sidebar.blit(glow, status.topleft)

        if stage_desc:
            stage_desc = stage_desc.split('.')[0]
        if not stage_name:
            stage_name = f"Stage {level}"
        stage_label = stage_name if not stage_desc else f"{stage_name} - {stage_desc}"

        time_txt = self.font_tiny.render(f"{mins:02d}:{secs:02d}", True, C_HUD_TEXT)
        time_pad = 6
        time_rect = pygame.Rect(
            status.right - time_txt.get_width() - time_pad * 2,
            status.y + 3,
            time_txt.get_width() + time_pad * 2,
            status.height - 6,
        )
        pygame.draw.rect(sidebar, C_KEY_BG, time_rect, border_radius=6)
        pygame.draw.rect(sidebar, C_KEY_EDGE, time_rect, 1, border_radius=6)
        sidebar.blit(
            time_txt,
            (time_rect.centerx - time_txt.get_width() // 2,
             time_rect.centery - time_txt.get_height() // 2),
        )

        def fit_text(text: str, font, max_width: int) -> str:
            if font.size(text)[0] <= max_width:
                return text
            ell = "..."
            max_len = max(0, len(text))
            for i in range(max_len, 0, -1):
                candidate = text[:i].rstrip() + ell
                if font.size(candidate)[0] <= max_width:
                    return candidate
            return ell

        label_max = time_rect.x - status.x - 10
        label_txt = fit_text(stage_label, self.font_tiny, label_max)
        label_surf = self.font_tiny.render(label_txt, True, C_HUD_TEXT)
        sidebar.blit(label_surf, (status.x + 6, status.y + 4))

        # Controls (keycaps)
        y = SCREEN_HEIGHT - 88
        draw_label("CONTROLS", 12, y, C_HUD_LABEL, self.font_small)
        y += 16
        self._draw_keycap(sidebar, pygame.Rect(12, y, 20, 18), "W")
        self._draw_keycap(sidebar, pygame.Rect(12, y + 20, 20, 18), "S")
        self._draw_keycap(sidebar, pygame.Rect(34, y + 20, 20, 18), "A")
        self._draw_keycap(sidebar, pygame.Rect(56, y + 20, 20, 18), "D")
        self._draw_keycap(sidebar, pygame.Rect(84, y, 60, 18), "SPACE")
        self._draw_keycap(sidebar, pygame.Rect(84, y + 20, 40, 18), "ESC")

        # AI debug toggle
        txt = self.font_tiny.render(f"AI VIS: {'ON' if self.ai_debug else 'OFF'}", True, C_PANEL_ACC)
        sidebar.blit(txt, (12, SCREEN_HEIGHT - 20))

        self.screen.blit(sidebar, (GRID_PIXEL, 0))

    # ── Overlay messages ──────────────────────────────────────
    def draw_overlay(self, message: str, sub: str = '', stats: dict | None = None,
                     accent: tuple = C_PANEL_ACC) -> None:
        """Draw a styled centered message overlay with optional stats."""
        key = f"{message}|{sub}"
        now = pygame.time.get_ticks()
        if key != self._overlay_key:
            self._overlay_key = key
            self._overlay_start = now

        elapsed = (now - self._overlay_start) / 1000.0
        ease = min(1.0, elapsed / 0.35)
        offset = int((1.0 - ease) * 24)
        fade = int(220 * ease)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 180))
        self.screen.blit(overlay, (0, 0))

        cx = GRID_PIXEL // 2
        cy = SCREEN_HEIGHT // 2
        panel = pygame.Rect(cx - 220, cy - 120, 440, 220)
        pygame.draw.rect(self.screen, C_PANEL, panel, border_radius=14)
        pygame.draw.rect(self.screen, accent, panel, 2, border_radius=14)
        self._glow_rect(self.screen, panel.inflate(6, 6), accent, 60)

        title = self.font_huge.render(message, True, accent)
        title.set_alpha(fade)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 60 + offset)))

        if sub:
            surf2 = self.font_medium.render(sub, True, C_HUD_TEXT)
            surf2.set_alpha(fade)
            self.screen.blit(surf2, surf2.get_rect(center=(cx, cy - 20 + offset)))

        if stats:
            sx = cx - 180
            sy = cy + 10 + offset
            for label, value in stats.items():
                lbl = self.font_small.render(label, True, C_HUD_LABEL)
                val = self.font_small.render(str(value), True, C_HUD_TEXT)
                self.screen.blit(lbl, (sx, sy))
                self.screen.blit(val, (sx + 180, sy))
                sy += 20

    def draw_pause(self, mode_label: str | None = None, level: int | None = None) -> None:
        self._draw_frosted_glass()
        self.draw_overlay("PAUSED", "ESC to resume", accent=C_PANEL_ACC)
        if mode_label or level is not None:
            label = f"MODE: {mode_label}" if mode_label else "MODE: --"
            if level is not None:
                label += f"  |  LEVEL {level}"
            tag = self.font_small.render(label, True, C_HUD_TEXT)
            pad_x = 12
            pad_y = 6
            rect = tag.get_rect()
            rect = pygame.Rect(0, 0, rect.width + pad_x * 2, rect.height + pad_y * 2)
            rect.centerx = GRID_PIXEL // 2
            rect.top = 24
            pygame.draw.rect(self.screen, C_PANEL, rect, border_radius=8)
            pygame.draw.rect(self.screen, C_PANEL_ACC, rect, 1, border_radius=8)
            self.screen.blit(tag, tag.get_rect(center=rect.center))

    def draw_game_over(self, won: bool, stats: dict | None = None, sub: str | None = None) -> None:
        msg = "YOU WIN!" if won else "GAME OVER"
        sub_text = sub or ("Press R to restart" if not won else "Press ENTER for next level")
        accent = C_PLAYER_GLOW if won else C_FEED_BAD
        self.draw_overlay(msg, sub_text, stats=stats, accent=accent)

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

        # Time offset used for water waves
        self._time_offset = (self._time_offset + 1) % 120

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

    def _glow_ellipse(self, surface, rect, color, alpha):
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*color, alpha), glow.get_rect())
        surface.blit(glow, rect.topleft)

    def _glow_rect(self, surface, rect, color, alpha):
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=12)
        surface.blit(glow, rect.topleft)

    def _lerp_color(self, a, b, t: float):
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )

    def _draw_keycap(self, surface, rect, label: str) -> None:
        pygame.draw.rect(surface, C_KEY_BG, rect, border_radius=4)
        pygame.draw.rect(surface, C_KEY_EDGE, rect, 1, border_radius=4)
        highlight = pygame.Surface((rect.width, max(1, rect.height // 2)), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 30))
        surface.blit(highlight, rect.topleft)
        text = self.font_tiny.render(label, True, C_KEY_TEXT)
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_mini_tank(self, surface, x: int, y: int, color: tuple) -> None:
        body = pygame.Rect(x, y + 3, 10, 6)
        turret = pygame.Rect(x + 3, y + 1, 4, 4)
        pygame.draw.rect(surface, color, body, border_radius=2)
        pygame.draw.rect(surface, self._shade(color, 24), turret, border_radius=1)
        pygame.draw.line(surface, C_WHITE, (x + 5, y + 3), (x + 5, y - 1), 1)

    def _draw_frosted_glass(self) -> None:
        w, h = self.screen.get_size()
        snapshot = self.screen.copy()
        small = pygame.transform.smoothscale(snapshot, (max(1, w // 8), max(1, h // 8)))
        blur = pygame.transform.smoothscale(small, (w, h))
        self.screen.blit(blur, (0, 0))
        tint = pygame.Surface((w, h), pygame.SRCALPHA)
        tint.fill((8, 12, 18, 140))
        self.screen.blit(tint, (0, 0))

    def _ensure_post_fx(self) -> None:
        size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        if self._vignette is None or self._vignette_size != size:
            self._vignette = self._build_vignette(*size)
            self._vignette_size = size
        if self._scanlines is None or self._scanlines_size != size:
            self._scanlines = self._build_scanlines(*size)
            self._scanlines_size = size

    def _build_vignette(self, w: int, h: int) -> pygame.Surface:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        cx = w / 2
        cy = h / 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        for y in range(h):
            for x in range(w):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                t = min(1.0, dist / max_dist)
                alpha = int(140 * (t ** 1.8))
                surface.set_at((x, y), (0, 0, 0, alpha))
        return surface

    def _build_scanlines(self, w: int, h: int) -> pygame.Surface:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 4):
            pygame.draw.line(surface, (*C_SCANLINE, 22), (0, y), (w, y), 1)
        return surface

    def _update_kill_feed(self, game_state: dict) -> None:
        kills = game_state.get('kills', 0)
        if kills > self._last_kills:
            for _ in range(kills - self._last_kills):
                self._kill_feed.insert(0, {
                    "text": "ENEMY DOWN",
                    "age": 0,
                    "color": C_FEED_GOOD,
                })
        self._last_kills = kills
        for entry in self._kill_feed:
            entry["age"] += 1
        self._kill_feed = [e for e in self._kill_feed if e["age"] < 60]

    def _boss_phase_color(self, tank):
        if tank.hp <= BOSS_PHASE3_HP:
            return (255, 80, 80)
        if tank.hp <= BOSS_PHASE2_HP:
            return (255, 150, 60)
        return (80, 160, 255)

    def _draw_crt(self, surface):
        self._ensure_post_fx()
        if self._vignette:
            surface.blit(self._vignette, (0, 0))
        if self._scanlines:
            surface.blit(self._scanlines, (0, 0))

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