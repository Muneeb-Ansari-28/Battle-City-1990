# ============================================================
#  tanks/player.py  —  Player-controlled tank
# ============================================================
import pygame
from constants import *

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tanks.tank import Tank


class PlayerTank(Tank):
    """
    Controlled by WASD or Arrow Keys.
    Player CAN move AND shoot simultaneously (per spec).
    """

    def __init__(self, x: int = None, y: int = None):
        px = PLAYER_SPAWN[0] if x is None else x
        py = PLAYER_SPAWN[1] if y is None else y
        super().__init__(
            x         = px,
            y         = py,
            tank_type = TYPE_PLAYER,
            hp        = PLAYER_HP,
            speed     = SPEED_PLAYER,
            fire_rate = FIRE_PLAYER,
            color     = C_PLAYER,
        )
        self.spawn_pos = (px, py)
        self.direction = UP   # player faces up at spawn
        self.lives     = PLAYER_LIVES
        self.score     = 0

        # Filled by decide() from keyboard state
        self._pending_direction = None
        self._want_shoot        = False

        # Invincibility frames after respawn
        self._invincible_timer  = 0
        self.INVINCIBLE_TICKS   = 120   # 4 seconds

    # ── Read keyboard every tick ──────────────────────────────
    def decide(self, game_state: dict) -> None:
        keys = pygame.key.get_pressed()
        self._pending_direction = None
        self._want_shoot        = False

        if keys[pygame.K_UP]    or keys[pygame.K_w]:
            self._pending_direction = UP
        elif keys[pygame.K_DOWN]  or keys[pygame.K_s]:
            self._pending_direction = DOWN
        elif keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self._pending_direction = LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._pending_direction = RIGHT

        if keys[pygame.K_SPACE] or keys[pygame.K_j]:
            self._want_shoot = True

    # ── Invincibility ─────────────────────────────────────────
    def update_timers(self) -> None:
        super().update_timers()
        if self._invincible_timer > 0:
            self._invincible_timer -= 1

    @property
    def is_invincible(self) -> bool:
        return self._invincible_timer > 0

    # ── Death / respawn ───────────────────────────────────────
    def take_hit(self) -> None:
        if self.is_invincible:
            return
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False
        else:
            self.respawn()

    def respawn(self) -> None:
        self.x, self.y     = self.spawn_pos
        self.direction      = UP
        self.hp             = PLAYER_HP
        self.alive          = True
        self._fire_timer    = 0
        self._move_timer    = 0
        self._invincible_timer = self.INVINCIBLE_TICKS

    # ── Blink effect during invincibility ────────────────────
    @property
    def visible(self) -> bool:
        if not self.is_invincible:
            return True
        # Blink every 6 ticks
        return (self._invincible_timer // 6) % 2 == 0