# ============================================================
#  game_loop.py  —  Master game tick (10-step sequence per spec)
# ============================================================
from constants import *
from bullet import Bullet
from level_configs import LEVEL_CONFIGS


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

        # Track boss phases for visuals
        self._boss_phase = {}

        # Register grid change listener for AI path invalidation
        self.grid.add_change_listener(self._on_tile_change)

        # Track total enemies killed this level
        self.kills = 0

        # Grass movement SFX cooldowns
        self._grass_sfx_timers = {}

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
            self.player.update_timers()
            self.player.decide(gs)

        for enemy in self.enemies:
            if enemy.alive and enemy.active:
                enemy.update_timers()
                try:
                    enemy.decide(gs)
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

        # Move player
        if self.player and self.player.alive:
            if self.player._pending_direction:
                if self.player._pending_direction != self.player.direction:
                    # Turn in place first; move on the next tick
                    self.player.direction = self.player._pending_direction
                else:
                    occupied = occupied_positions(exclude=self.player)
                    dx, dy = self.player._pending_direction
                    nx, ny = self.player.x + dx, self.player.y + dy
                    if (nx, ny) not in occupied:
                        moved = self.player.try_move(self.player._pending_direction, self.grid)
                        if moved:
                            self._maybe_play_grass(self.player)
                    else:
                        # Face direction even if blocked by tank
                        self.player.direction = self.player._pending_direction

        for enemy in self.enemies:
            if not (enemy.alive and enemy.active):
                continue
            if enemy._pending_direction:
                if not enemy.can_move():
                    continue
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
                    moved = enemy.try_move(direction, self.grid)
                    if moved:
                        self._maybe_play_grass(enemy)

    # ── Step 4: Shoot ─────────────────────────────────────────
    def _step_shoot(self) -> None:
        if (self.player and self.player.alive
                and self.player._want_shoot):
            b = self.player.shoot()
            if b:
                self._emit_muzzle(self.player)
                self.bullets.append(b)

        for enemy in self.enemies:
            if not (enemy.alive and enemy.active):
                continue
            if enemy._want_shoot:
                b = enemy.shoot()
                if b:
                    self._emit_muzzle(enemy)
                    self.bullets.append(b)

    # ── Step 5: Bullet update ─────────────────────────────────
    def _step_bullets(self) -> None:
        for _ in range(BULLET_SPEED):
            active = [b for b in self.bullets if b.active]
            prev_positions = {b.id: (b.x, b.y) for b in active}

            for b in active:
                if not b.active:
                    continue
                b.step()
                self.renderer.fx.smoke_trail(
                    b.x * TILE_SIZE + TILE_SIZE // 2,
                    b.y * TILE_SIZE + TILE_SIZE // 2,
                )
                # Stop immediately if out of bounds
                if not self.grid.in_bounds(b.x, b.y):
                    b.destroy()
                    continue
                if self._resolve_bullet_hit(b):
                    continue

            # Bullet vs Bullet (same tile)
            active_now = [b for b in self.bullets if b.active]
            pos_map = {}
            for b in active_now:
                pos_map.setdefault((b.x, b.y), []).append(b)
            for bullets in pos_map.values():
                if len(bullets) > 1:
                    for b in bullets:
                        b.destroy()

            # Bullet vs Bullet (crossing swap)
            active_now = [b for b in self.bullets if b.active]
            for i in range(len(active_now)):
                for j in range(i + 1, len(active_now)):
                    bi, bj = active_now[i], active_now[j]
                    pi = prev_positions.get(bi.id)
                    pj = prev_positions.get(bj.id)
                    if not pi or not pj:
                        continue
                    if pi == (bj.x, bj.y) and pj == (bi.x, bi.y):
                        bi.destroy()
                        bj.destroy()

    # ── Step 6: Collision detection ───────────────────────────
    def _step_collisions(self) -> None:
        # Bullet vs Bullet (redundant safety pass)
        active2 = [b for b in self.bullets if b.active]
        for i in range(len(active2)):
            for j in range(i + 1, len(active2)):
                bi, bj = active2[i], active2[j]
                if bi.active and bj.active and bi.x == bj.x and bi.y == bj.y:
                    bi.destroy()
                    bj.destroy()

    def _resolve_bullet_hit(self, b: Bullet) -> bool:
        if not b.active:
            return True

        x, y = b.x, b.y
        tile = self.grid.get(x, y)

        # Bullet vs Eagle
        if tile == EAGLE:
            b.destroy()
            self.eagle_alive = False
            self.grid.set(*EAGLE_POS, EMPTY)
            self.renderer.fx.eagle_destroyed(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
            return True

        # Bullet vs Brick
        if tile == BRICK:
            self.grid.destroy_brick(x, y)
            b.destroy()
            self._add_explosion(x, y, play_sound=False)
            self.renderer.fx.impact_brick(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
            return True

        # Bullet vs Steel
        if tile == STEEL:
            b.destroy()
            self.renderer.fx.impact_steel(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
            return True

        # Bullet vs Water (shouldn't happen — tanks can't be here, but safety)
        if tile == WATER:
            b.destroy()
            self.renderer.fx.impact_water(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
            return True

        # Bullet vs Player
        if (self.player and self.player.alive
                and b.x == self.player.x and b.y == self.player.y
                and not b.is_player_bullet):
            b.destroy()
            self.player.take_hit()
            if self.player.alive:
                self._add_explosion(x, y)
            else:
                self.renderer.fx.explosion_large(
                    x * TILE_SIZE + TILE_SIZE // 2,
                    y * TILE_SIZE + TILE_SIZE // 2,
                )
            return True

        # Bullet vs Enemies
        for enemy in self.enemies:
            if not (enemy.alive and enemy.active):
                continue
            if b.x == enemy.x and b.y == enemy.y and b.is_player_bullet:
                b.destroy()
                enemy.take_hit()
                if not enemy.alive:
                    self._add_explosion(enemy.x, enemy.y)
                    if enemy.tank_type == TYPE_BOSS:
                        self.renderer.fx.explosion_large(
                            enemy.x * TILE_SIZE + TILE_SIZE // 2,
                            enemy.y * TILE_SIZE + TILE_SIZE // 2,
                        )
                    else:
                        self.renderer.fx.explosion_small(
                            enemy.x * TILE_SIZE + TILE_SIZE // 2,
                            enemy.y * TILE_SIZE + TILE_SIZE // 2,
                        )
                    self.kills += 1
                    if self.player:
                        self.player.score += self._score_for(enemy)
                return True

        return False

    # ── Step 7: State update ──────────────────────────────────
    def _step_state(self) -> None:
        self.bullets  = [b for b in self.bullets if b.active]
        self.enemies  = [e for e in self.enemies if e.alive]

        # Boss phase change visuals
        for enemy in self.enemies:
            if enemy.tank_type != TYPE_BOSS:
                continue
            phase = 1
            if enemy.hp <= BOSS_PHASE3_HP:
                phase = 3
            elif enemy.hp <= BOSS_PHASE2_HP:
                phase = 2
            prev = self._boss_phase.get(id(enemy), phase)
            if phase != prev:
                color = (80, 160, 255) if phase == 1 else (255, 150, 60) if phase == 2 else (255, 80, 80)
                self.renderer.fx.boss_phase(
                    enemy.x * TILE_SIZE + TILE_SIZE // 2,
                    enemy.y * TILE_SIZE + TILE_SIZE // 2,
                    color,
                )
            self._boss_phase[id(enemy)] = phase

        # Cool down grass SFX timers
        for key in list(self._grass_sfx_timers.keys()):
            self._grass_sfx_timers[key] = max(0, self._grass_sfx_timers[key] - 1)

    # ── Step 8: Spawn check ───────────────────────────────────
    def _step_spawn(self) -> None:
        new_tank = self.spawner.update(self.enemies, self.player, self.kills)
        if new_tank:
            self.enemies.append(new_tank)
            self.renderer.fx.spawn(
                new_tank.x * TILE_SIZE + TILE_SIZE // 2,
                new_tank.y * TILE_SIZE + TILE_SIZE // 2,
            )

    # ── Step 9: Render ────────────────────────────────────────
    def _step_render(self) -> None:
        gs = self._game_state()
        self.renderer.draw(gs)

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
        level = getattr(self, 'level', 1)
        stage_cfg = LEVEL_CONFIGS.get(level, {})
        stage_name = stage_cfg.get('name', f"Stage {level}")
        if stage_name.startswith("Level "):
            stage_name = f"Stage {stage_name[6:]}"
        return {
            'grid':              self.grid,
            'player':            self.player,
            'enemies':           self.enemies,
            'bullets':           self.bullets,
            'tick':              self.tick_count,
            'kills':             self.kills,
            'enemies_remaining': (len(self.enemies)
                                  + self.spawner.remaining_in_pool),
            'level':             level,
            'stage_name':        stage_name,
            'stage_desc':        stage_cfg.get('description', ''),
            'mode_label':        getattr(self, 'mode_label', 'Adventure (Normal)'),
            'ai_debug':          getattr(self.renderer, 'ai_debug', False),
            'transition_alpha':  getattr(self.renderer, 'transition_alpha', 0),
        }

    def _score_for(self, tank) -> int:
        return {
            TYPE_BASIC: 100,
            TYPE_FAST:  200,
            TYPE_ARMOR: 400,
            TYPE_POWER: 300,
            TYPE_BOSS:  1000,
        }.get(tank.tank_type, 100)

    def _add_explosion(self, x: int, y: int, play_sound: bool = True) -> None:
        self.renderer.fx.explosion_small(
            x * TILE_SIZE + TILE_SIZE // 2,
            y * TILE_SIZE + TILE_SIZE // 2,
            play_sound=play_sound,
        )

    def _emit_muzzle(self, tank) -> None:
        dx, dy = tank.direction
        mx = (tank.x + dx) * TILE_SIZE + TILE_SIZE // 2
        my = (tank.y + dy) * TILE_SIZE + TILE_SIZE // 2
        self.renderer.fx.muzzle(mx, my)
        if tank.tank_type == TYPE_BOSS:
            self.renderer.fx.shake.trigger(intensity=2.0, duration=6)

    def _maybe_play_grass(self, tank) -> None:
        if self.grid.get(tank.x, tank.y) != FOREST:
            return
        key = id(tank)
        if self._grass_sfx_timers.get(key, 0) > 0:
            return
        if self.renderer.fx.sfx:
            self.renderer.fx.sfx.play("grass", volume_scale=0.4)
        self._grass_sfx_timers[key] = 10

    def _on_tile_change(self, x: int, y: int, old: int, new: int) -> None:
        """Notify all AI agents that the map has changed."""
        for enemy in self.enemies:
            if hasattr(enemy, 'on_map_change'):
                enemy.on_map_change(x, y, old, new)