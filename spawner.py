# ============================================================
#  spawner.py  —  Enemy pool & spawn controller
# ============================================================
import random
from constants import *


class Spawner:
    """
    Manages the 20-enemy pool for a level.
    Spawns enemies through 3 fixed top spawn points,
    chosen randomly (per spec).
    Enforces:
      - max MAX_ACTIVE_ENEMIES on field at once
      - fairness: no spawn within SPAWN_FAIRNESS_DIST of player
      - delay of SPAWN_DELAY_TICKS between each spawn
    """

    SPAWN_POINTS = ENEMY_SPAWNS   # [(0,0),(12,0),(24,0)]

    def __init__(self, tank_queue: list):
        """
        tank_queue: ordered list of Tank instances representing
                    the 20-enemy pool for this level (not yet active).
        """
        self._queue:  list = list(tank_queue)   # remaining to spawn
        self._timer:  int  = 0                  # ticks until next spawn
        self._pending_spawn = None              # next tank waiting for safe spawn

    # ── Called every tick from game loop ─────────────────────
    def update(self, active_enemies: list, player) -> 'Tank | None':
        """
        Returns a Tank to activate this tick, or None.
        active_enemies: list of currently alive enemy tanks
        player: PlayerTank (may be None if dead)
        """
        if self._timer > 0:
            self._timer -= 1
            return None

        if len(active_enemies) >= MAX_ACTIVE_ENEMIES:
            return None

        if not self._queue and self._pending_spawn is None:
            return None   # pool exhausted

        # Pick next tank from queue if nothing pending
        if self._pending_spawn is None:
            self._pending_spawn = self._queue.pop(0)

        # Try to find a safe spawn point
        spawn_pos = self._pick_spawn_point(player, active_enemies)
        if spawn_pos is None:
            return None   # all spawn points blocked — try next tick

        tank = self._pending_spawn
        self._pending_spawn = None
        tank.x, tank.y = spawn_pos
        tank.active = True
        self._timer = SPAWN_DELAY_TICKS
        return tank

    # ── Spawn point selection ─────────────────────────────────
    def _pick_spawn_point(self, player, active_enemies: list):
        """
        Choose a random spawn point that:
          1. Is >= SPAWN_FAIRNESS_DIST from player (Manhattan)
          2. Is not occupied by an active enemy
        Returns (x, y) or None if all blocked.
        """
        occupied = {(e.x, e.y) for e in active_enemies}
        candidates = list(self.SPAWN_POINTS)
        random.shuffle(candidates)

        for sx, sy in candidates:
            # Fairness check
            if player and player.alive:
                dist = abs(sx - player.x) + abs(sy - player.y)
                if dist < SPAWN_FAIRNESS_DIST:
                    continue
            # Occupancy check
            if (sx, sy) in occupied:
                continue
            return (sx, sy)
        return None

    # ── Queries ───────────────────────────────────────────────
    @property
    def remaining_in_pool(self) -> int:
        return len(self._queue) + (1 if self._pending_spawn else 0)

    @property
    def pool_exhausted(self) -> bool:
        return len(self._queue) == 0 and self._pending_spawn is None

    def __repr__(self) -> str:
        return (f"Spawner(queue={len(self._queue)}, "
                f"timer={self._timer})")