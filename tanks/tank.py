# ============================================================
#  tanks/tank.py  —  Base Tank class
# ============================================================
from constants import *
from bullet import Bullet


class Tank:
    """
    Abstract base for all tanks (player + all enemy types).
    Subclasses override:
        decide(game_state) → sets self._pending_move / self._want_shoot
    """

    def __init__(self, x: int, y: int, tank_type: str,
                 hp: int, speed: int, fire_rate: int, color: tuple):
        self.x          = x
        self.y          = y
        self.tank_type  = tank_type
        self.hp         = hp
        self.max_hp     = hp
        self.speed      = speed        # ticks between moves
        self.fire_rate  = fire_rate    # ticks between shots
        self.color      = color
        self.direction  = DOWN         # facing direction

        self.alive      = True
        self.active     = True         # False until spawned

        # Internal timers (count down each tick)
        self._move_timer = 0
        self._fire_timer = 0

        # Set by decide() each tick
        self._pending_direction = None  # direction to move this tick
        self._want_shoot        = False

        # Track a single active bullet per tank
        self._active_bullet     = None

    # ── Called every tick by game loop ───────────────────────
    def update_timers(self) -> None:
        if self._move_timer > 0:
            self._move_timer -= 1
        if self._fire_timer > 0:
            self._fire_timer -= 1

    def can_move(self) -> bool:
        return self._move_timer == 0

    def can_shoot(self) -> bool:
        return self._fire_timer == 0

    # ── Movement ─────────────────────────────────────────────
    def try_move(self, direction: tuple, grid) -> bool:
        """
        Attempt to move one tile in `direction`.
        Returns True if move succeeded.
        Updates facing direction regardless of success.
        """
        self.direction = direction
        if not self.can_move():
            return False
        dx, dy = direction
        nx, ny = self.x + dx, self.y + dy
        if grid.is_passable(nx, ny):
            self.x = nx
            self.y = ny
            self._move_timer = self.speed
            return True
        return False

    # ── Shooting ─────────────────────────────────────────────
    def shoot(self) -> 'Bullet | None':
        """
        Fire a bullet from the front of the tank.
        Returns a Bullet object, or None if on cooldown.
        """
        if self._active_bullet is not None and self._active_bullet.active:
            return None
        if self._active_bullet is not None and not self._active_bullet.active:
            self._active_bullet = None
        if not self.can_shoot():
            return None
        dx, dy = self.direction
        bx = self.x + dx
        by = self.y + dy
        self._fire_timer = self.fire_rate
        bullet = Bullet(bx, by, self.direction, self.tank_type, self)
        self._active_bullet = bullet
        return bullet

    # ── Damage ───────────────────────────────────────────────
    def take_hit(self) -> None:
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    # ── AI hook (override in subclasses) ─────────────────────
    def decide(self, game_state: dict) -> None:
        """
        Called once per tick BEFORE movement/shooting.
        Subclasses set self._pending_direction and self._want_shoot.
        game_state keys:
            'grid'        → Grid object
            'player'      → PlayerTank (may be None)
            'enemies'     → list[Tank]
            'bullets'     → list[Bullet]
            'tick'        → int
        """
        raise NotImplementedError

    # ── Utility ──────────────────────────────────────────────
    @property
    def pos(self) -> tuple:
        return (self.x, self.y)

    def manhattan(self, x: int, y: int) -> int:
        return abs(self.x - x) + abs(self.y - y)

    def facing_tile(self) -> tuple:
        dx, dy = self.direction
        return (self.x + dx, self.y + dy)

    def __repr__(self) -> str:
        return (f"{self.tank_type.upper()}Tank("
                f"pos=({self.x},{self.y}), hp={self.hp})")