# ============================================================
#  game_loop.py  —  Master game tick (10-step sequence per spec)
# ============================================================
from constants import *
from bullet import Bullet


class GameLoop:
    """
    Executes the 10-step tick sequence defined in spec §1.4:
      1  INPUT
      2  AGENT DECISIONS
      3  MOVE
      4  SHOOT
      5  BULLET UPDATE
      6  COLLISION DETECTION
      7  STATE UPDATE
      8  SPAWN CHECK
      9  RENDER
      10 WIN/LOSE CHECK

    Returns a game-status string each tick:
      'running' | 'win' | 'lose' | 'boss_win'
    """

    def __init__(self, grid, player, spawner, renderer):
        self.grid      = grid
        self.player    = player
        self.spawner   = spawner
        self.renderer  = renderer

        self.enemies:  list = []   # active enemy tank instances
        self.bullets:  list = []   # all active bullets

        self.tick_count   = 0
        self.eagle_alive  = True
        self.paused       = False
        self.status       = 'running'

        # Explosion flash effects [(x, y, ttl)]
        self._explosions: list = []

        # Register grid change listener for AI path invalidation
        self.grid.add_change_listener(self._on_tile_change)

        # Track total enemies killed this level
        self.kills = 0

    # ── Main tick ─────────────────────────────────────────────
    def tick(self) -> str:
        if self.status != 'running':
            return self.status

        self.tick_count += 1

        # 1. INPUT — handled by PlayerTank.decide()
        # 2. AGENT DECISIONS
        self._step_decisions()

        # 3. MOVE
        self._step_move()

        # 4. SHOOT
        self._step_shoot()

        # 5. BULLET UPDATE
        self._step_bullets()

        # 6. COLLISION DETECTION
        self._step_collisions()

        # 7. STATE UPDATE
        self._step_state()

        # 8. SPAWN CHECK
        self._step_spawn()

        # 9. RENDER
        self._step_render()

        # 10. WIN/LOSE CHECK
        self.status = self._check_win_lose()
        return self.status

    # ── Step 1+2: Decisions ───────────────────────────────────
    def _step_decisions(self) -> None:
        gs = self._game_state()

        if self.player and self.player.alive:
            self.player.decide(gs)

        for enemy in self.enemies:
            if enemy.alive and enemy.active:
                try:
                    player_pos = (self.player.x, self.player.y) if self.player and self.player.alive else None
                    enemy.decide(player_pos)
                except Exception:
                    pass   # never crash game on AI error

    # ── Step 3: Move ──────────────────────────────────────────
    def _step_move(self) -> None:
        # Build set of all occupied positions for tank-tank blocking
        def occupied_positions(exclude=None):
            pos = set()
            if self.player and self.player.alive and self.player != exclude:
                pos.add((self.player.x, self.player.y))
            for e in self.enemies:
                if e.alive and e.active and e != exclude:
                    pos.add((e.x, e.y))
            return pos

        # Update timers + move player
        if self.player and self.player.alive:
            self.player.update_timers()
            if self.player._pending_direction:
                occupied = occupied_positions(exclude=self.player)
                dx, dy = self.player._pending_direction
                nx, ny = self.player.x + dx, self.player.y + dy
                if (nx, ny) not in occupied:
                    self.player.try_move(self.player._pending_direction, self.grid)
                else:
                    # Face direction even if blocked by tank
                    self.player.direction = self.player._pending_direction

        for enemy in self.enemies:
            if not (enemy.alive and enemy.active):
                continue
            enemy.update_timers()
            if enemy._pending_direction:
                direction = enemy._pending_direction
                dx, dy = direction
                nx, ny = enemy.x + dx, enemy.y + dy
                occupied = occupied_positions(exclude=enemy)
                # If blocked by another tank
                if (nx, ny) in occupied:
                    enemy.direction = direction   # face direction, don't move
                    continue
                # If direction is blocked by brick and tank wants to shoot it
                if self.grid.get(nx, ny) == BRICK and enemy._want_shoot:
                    enemy.direction = direction
                else:
                    enemy.try_move(direction, self.grid)

    # ── Step 4: Shoot ─────────────────────────────────────────
    def _step_shoot(self) -> None:
        if (self.player and self.player.alive
                and self.player._want_shoot):
            b = self.player.shoot()
            if b:
                self.bullets.append(b)

        for enemy in self.enemies:
            if not (enemy.alive and enemy.active):
                continue
            if enemy._want_shoot:
                b = enemy.shoot()
                if b:
                    self.bullets.append(b)

    # ── Step 5: Bullet update ─────────────────────────────────
    def _step_bullets(self) -> None:
        for b in self.bullets:
            if not b.active:
                continue
            for _ in range(BULLET_SPEED):
                b.step()
                # Stop immediately if out of bounds
                if not self.grid.in_bounds(b.x, b.y):
                    b.destroy()
                    break

    # ── Step 6: Collision detection ───────────────────────────
    def _step_collisions(self) -> None:
        active = [b for b in self.bullets if b.active]

        for b in active:
            if not b.active:
                continue
            x, y = b.x, b.y

            if not self.grid.in_bounds(x, y):
                b.destroy()
                continue

            tile = self.grid.get(x, y)

            # Bullet vs Eagle
            if tile == EAGLE:
                b.destroy()
                self.eagle_alive = False
                self.grid.set(*EAGLE_POS, EMPTY)
                continue

            # Bullet vs Brick
            if tile == BRICK:
                self.grid.destroy_brick(x, y)
                b.destroy()
                self._add_explosion(x, y)
                continue

            # Bullet vs Steel
            if tile == STEEL:
                b.destroy()
                continue

            # Bullet vs Water (shouldn't happen — tanks can't be here, but safety)
            if tile == WATER:
                b.destroy()
                continue

            # Bullet vs Player
            if (self.player and self.player.alive
                    and b.x == self.player.x and b.y == self.player.y
                    and not b.is_player_bullet):
                b.destroy()
                self.player.take_hit()
                if self.player.alive:
                    self._add_explosion(x, y)
                continue

            # Bullet vs Enemies
            for enemy in self.enemies:
                if not (enemy.alive and enemy.active):
                    continue
                if b.x == enemy.x and b.y == enemy.y and b.is_player_bullet:
                    b.destroy()
                    enemy.take_hit()
                    if not enemy.alive:
                        self._add_explosion(enemy.x, enemy.y)
                        self.kills += 1
                        if self.player:
                            self.player.score += self._score_for(enemy)
                    break

        # Bullet vs Bullet (mutual destruction)
        active2 = [b for b in self.bullets if b.active]
        for i in range(len(active2)):
            for j in range(i + 1, len(active2)):
                bi, bj = active2[i], active2[j]
                if bi.active and bj.active and bi.x == bj.x and bi.y == bj.y:
                    bi.destroy()
                    bj.destroy()

    # ── Step 7: State update ──────────────────────────────────
    def _step_state(self) -> None:
        self.bullets  = [b for b in self.bullets if b.active]
        self.enemies  = [e for e in self.enemies if e.alive]

        # Tick down explosions
        self._explosions = [(x, y, t - 1)
                            for x, y, t in self._explosions if t > 1]

    # ── Step 8: Spawn check ───────────────────────────────────
    def _step_spawn(self) -> None:
        new_tank = self.spawner.update(self.enemies, self.player)
        if new_tank:
            self.enemies.append(new_tank)

    # ── Step 9: Render ────────────────────────────────────────
    def _step_render(self) -> None:
        gs = self._game_state()
        self.renderer.draw(gs)
        self._draw_explosions()

    # ── Step 10: Win / Lose ───────────────────────────────────
    def _check_win_lose(self) -> str:
        # Lose B: Eagle destroyed
        if not self.eagle_alive:
            return 'lose'

        # Lose A: Player out of lives
        if self.player and not self.player.alive and self.player.lives <= 0:
            return 'lose'

        # Win: all 20 enemies destroyed AND none active
        if (self.spawner.pool_exhausted
                and len(self.enemies) == 0):
            return 'win'

        return 'running'

    # ── Helpers ───────────────────────────────────────────────
    def _game_state(self) -> dict:
        return {
            'grid':              self.grid,
            'player':            self.player,
            'enemies':           self.enemies,
            'bullets':           self.bullets,
            'tick':              self.tick_count,
            'kills':             self.kills,
            'enemies_remaining': (len(self.enemies)
                                  + self.spawner.remaining_in_pool),
            'level':             getattr(self, 'level', 1),
        }

    def _score_for(self, tank) -> int:
        return {
            TYPE_BASIC: 100,
            TYPE_FAST:  200,
            TYPE_ARMOR: 400,
            TYPE_POWER: 300,
            TYPE_BOSS:  1000,
        }.get(tank.tank_type, 100)

    def _add_explosion(self, x: int, y: int) -> None:
        self._explosions.append((x, y, 12))   # 12-tick flash

    def _draw_explosions(self) -> None:
        import pygame
        for ex, ey, ttl in self._explosions:
            alpha = int(255 * ttl / 12)
            radius = int((12 - ttl + 4))
            rx = ex * TILE_SIZE + TILE_SIZE // 2
            ry = ey * TILE_SIZE + TILE_SIZE // 2
            color = (255, 200 - (12 - ttl) * 10, 0)
            pygame.draw.circle(self.renderer.screen, color, (rx, ry), radius)

    def _on_tile_change(self, x: int, y: int, old: int, new: int) -> None:
        """Notify all AI agents that the map has changed."""
        for enemy in self.enemies:
            if hasattr(enemy, 'on_map_change'):
                enemy.on_map_change(x, y, old, new)