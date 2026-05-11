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
    TURN_HOLD_TICKS = 6

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
        # Turn on first press, move on second press.
        # Once moving, keep moving while the key is held.
        self._turn_only_dir     = None
        self._turn_hold_ticks   = 0
        self._move_hold_dir     = None
        self._prev_dir_pressed  = {
            UP: False,
            DOWN: False,
            LEFT: False,
            RIGHT: False,
        }

        # Invincibility frames after respawn
        self._invincible_timer  = 0
        self.INVINCIBLE_TICKS   = 120   # 4 seconds

    # ── Read keyboard every tick ──────────────────────────────
    def decide(self, game_state: dict) -> None:
        keys = pygame.key.get_pressed()
        self._pending_direction = None
        self._want_shoot        = False

        dir_pressed = {
            UP: keys[pygame.K_UP] or keys[pygame.K_w],
            DOWN: keys[pygame.K_DOWN] or keys[pygame.K_s],
            LEFT: keys[pygame.K_LEFT] or keys[pygame.K_a],
            RIGHT: keys[pygame.K_RIGHT] or keys[pygame.K_d],
        }
        just_pressed = {
            direction: (pressed and not self._prev_dir_pressed.get(direction, False))
            for direction, pressed in dir_pressed.items()
        }
        self._prev_dir_pressed = dir_pressed

        just_dir = None
        if just_pressed[UP]:
            just_dir = UP
        elif just_pressed[DOWN]:
            just_dir = DOWN
        elif just_pressed[LEFT]:
            just_dir = LEFT
        elif just_pressed[RIGHT]:
            just_dir = RIGHT

        if just_dir:
            if just_dir != self.direction:
                self._turn_only_dir = just_dir
                self._turn_hold_ticks = 0
                self._move_hold_dir = None
                self._pending_direction = just_dir
            else:
                if self._turn_only_dir == just_dir:
                    self._turn_only_dir = None
                    self._turn_hold_ticks = 0
                self._move_hold_dir = just_dir
                self._pending_direction = just_dir
        else:
            if self._turn_only_dir:
                if dir_pressed.get(self._turn_only_dir, False):
                    self._turn_hold_ticks += 1
                    if self._turn_hold_ticks >= self.TURN_HOLD_TICKS:
                        self._move_hold_dir = self._turn_only_dir
                        self._turn_only_dir = None
                        self._turn_hold_ticks = 0
                        self._pending_direction = self._move_hold_dir
                else:
                    self._turn_hold_ticks = 0
            elif (self._move_hold_dir
                    and dir_pressed.get(self._move_hold_dir, False)):
                self._pending_direction = self._move_hold_dir
            else:
                self._move_hold_dir = None

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
        self._pending_direction = None
        self._turn_only_dir = None
        self._turn_hold_ticks = 0
        self._move_hold_dir = None
        self._prev_dir_pressed = {
            UP: False,
            DOWN: False,
            LEFT: False,
            RIGHT: False,
        }

    # ── Blink effect during invincibility ────────────────────
    @property
    def visible(self) -> bool:
        if not self.is_invincible:
            return True
        # Blink every 6 ticks
        return (self._invincible_timer // 6) % 2 == 0