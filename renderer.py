# ============================================================
#  renderer.py  —  All Pygame draw calls
# ============================================================
import pygame
from constants import *


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
        self.font_large  = pygame.font.SysFont('Courier New', 28, bold=True)
        self.font_medium = pygame.font.SysFont('Courier New', 18, bold=True)
        self.font_small  = pygame.font.SysFont('Courier New', 13)

    # ── Master draw call ──────────────────────────────────────
    def draw(self, game_state: dict) -> None:
        self.screen.fill(C_BLACK)
        self._draw_grid(game_state['grid'])
        self._draw_eagle(game_state['grid'])
        self._draw_bullets(game_state['bullets'])
        self._draw_tanks(game_state)
        self._draw_sidebar(game_state)

    # ── Grid ──────────────────────────────────────────────────
    def _draw_grid(self, grid) -> None:
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = grid.get(x, y)
                rx   = x * TILE_SIZE
                ry   = y * TILE_SIZE
                rect = pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE)

                if tile == EMPTY:
                    pygame.draw.rect(self.screen, C_EMPTY, rect)

                elif tile == BRICK:
                    pygame.draw.rect(self.screen, C_BRICK, rect)
                    # Mortar lines for texture
                    pygame.draw.line(self.screen, C_BRICK_DARK,
                                     (rx, ry + TILE_SIZE // 2),
                                     (rx + TILE_SIZE, ry + TILE_SIZE // 2), 1)
                    pygame.draw.line(self.screen, C_BRICK_DARK,
                                     (rx + TILE_SIZE // 2, ry),
                                     (rx + TILE_SIZE // 2, ry + TILE_SIZE // 2), 1)
                    pygame.draw.line(self.screen, C_BRICK_DARK,
                                     (rx, ry + TILE_SIZE // 2),
                                     (rx, ry + TILE_SIZE), 1)

                elif tile == STEEL:
                    pygame.draw.rect(self.screen, C_STEEL, rect)
                    pygame.draw.rect(self.screen, C_DARKGRAY, rect, 2)
                    # Cross hatch
                    pygame.draw.line(self.screen, C_DARKGRAY,
                                     (rx + 4, ry + 4),
                                     (rx + TILE_SIZE - 4, ry + TILE_SIZE - 4), 1)
                    pygame.draw.line(self.screen, C_DARKGRAY,
                                     (rx + TILE_SIZE - 4, ry + 4),
                                     (rx + 4, ry + TILE_SIZE - 4), 1)

                elif tile == WATER:
                    pygame.draw.rect(self.screen, C_WATER, rect)
                    # Wave lines
                    for i in range(2):
                        wy = ry + 6 + i * 10
                        pygame.draw.arc(self.screen, C_WATER_DARK,
                                        (rx + 2, wy, 8, 4), 0, 3.14, 2)
                        pygame.draw.arc(self.screen, C_WATER_DARK,
                                        (rx + 12, wy, 8, 4), 0, 3.14, 2)

                elif tile == FOREST:
                    pygame.draw.rect(self.screen, C_EMPTY, rect)   # ground below
                    # Forest drawn LAST (over tanks) — handled in draw_tanks
                    # Here just draw the base
                    pygame.draw.rect(self.screen, C_FOREST, rect, 0)

                elif tile == EAGLE:
                    pass   # drawn separately

    # ── Eagle (base) ──────────────────────────────────────────
    def _draw_eagle(self, grid) -> None:
        ex, ey = EAGLE_POS
        if grid.get(ex, ey) != EAGLE:
            # Eagle destroyed — draw rubble
            rx, ry = ex * TILE_SIZE, ey * TILE_SIZE
            pygame.draw.rect(self.screen, C_DARKGRAY,
                             (rx, ry, TILE_SIZE, TILE_SIZE))
            return
        rx, ry = ex * TILE_SIZE, ey * TILE_SIZE
        # Gold star-like base symbol
        cx, cy = rx + TILE_SIZE // 2, ry + TILE_SIZE // 2
        pygame.draw.polygon(self.screen, C_EAGLE, [
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
                    self.screen.blit(s, (rx, ry))

    def _draw_single_tank(self, tank) -> None:
        rx = tank.x * TILE_SIZE
        ry = tank.y * TILE_SIZE
        cx = rx + TILE_SIZE // 2
        cy = ry + TILE_SIZE // 2
        ts = TILE_SIZE
        color = tank.color

        # Body
        body = pygame.Rect(rx + 3, ry + 3, ts - 6, ts - 6)
        pygame.draw.rect(self.screen, color, body, border_radius=3)

        # Barrel (direction indicator)
        dx, dy = tank.direction
        bx1, by1 = cx, cy
        bx2 = cx + dx * (ts // 2 - 1)
        by2 = cy + dy * (ts // 2 - 1)
        pygame.draw.line(self.screen, C_WHITE, (bx1, by1), (bx2, by2), 3)

        # HP indicator for Armor tanks (colored stages)
        if hasattr(tank, 'hit_count') and tank.hit_count > 0:
            stage_colors = [color, (255, 255, 0), (255, 150, 0), (255, 50, 50)]
            sc = stage_colors[min(tank.hit_count, 3)]
            pygame.draw.rect(self.screen, sc, body, 2)

        # Invincibility ring for player
        if hasattr(tank, 'is_invincible') and tank.is_invincible:
            pygame.draw.circle(self.screen, C_WHITE, (cx, cy), ts // 2, 1)

    # ── Bullets ───────────────────────────────────────────────
    def _draw_bullets(self, bullets: list) -> None:
        for b in bullets:
            if not b.active:
                continue
            bx = b.x * TILE_SIZE + TILE_SIZE // 2
            by = b.y * TILE_SIZE + TILE_SIZE // 2
            col = C_BULLET_PLY if b.is_player_bullet else C_BULLET_ENE
            pygame.draw.circle(self.screen, col, (bx, by), 4)
            # Motion trail
            dx, dy = b.direction
            pygame.draw.line(self.screen, col,
                             (bx, by),
                             (bx - dx * 6, by - dy * 6), 2)

    # ── Sidebar HUD ───────────────────────────────────────────
    def _draw_sidebar(self, game_state: dict) -> None:
        sx = GRID_PIXEL + 4
        w  = SIDEBAR_WIDTH - 8
        pygame.draw.rect(self.screen, C_SIDEBAR,
                         (GRID_PIXEL, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, C_GRAY,
                         (GRID_PIXEL, 0), (GRID_PIXEL, SCREEN_HEIGHT), 2)

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
            label(f" Lives: {player.lives}", C_PLAYER)
            label(f" Score: {player.score}", C_HUD_TEXT)
        else:
            label(" ---", C_GRAY)

        # Controls reminder
        y = SCREEN_HEIGHT - 90
        label("MOVE: WASD", C_GRAY)
        label("FIRE: SPACE", C_GRAY)
        label("PAUSE: ESC", C_GRAY)

    # ── Overlay messages ──────────────────────────────────────
    def draw_overlay(self, message: str, sub: str = '') -> None:
        """Draw a semi-transparent centered message overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
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