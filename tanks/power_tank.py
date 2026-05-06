# ============================================================
#  tanks/power_tank.py  —  Power Tank | Utility-Based Agent
# ============================================================

from constants import *
from tanks.tank import Tank


class PowerTank(Tank):
    def __init__(self, x: int = 0, y: int = 0, grid=None):
        super().__init__(
            x=x,
            y=y,
            tank_type=TYPE_POWER,
            hp=2,
            speed=SPEED_MEDIUM,
            fire_rate=FIRE_FAST,
            color=C_POWER,
        )
        self.grid = grid
        self.direction = DOWN
        self.active = False

    def decide(self, game_state: dict) -> None:
        self._pending_direction = None
        self._want_shoot = False

        if not (self.alive and self.active):
            return

        grid = game_state['grid']
        player = game_state.get('player')
        bullets = game_state.get('bullets', [])

        actions = []
        if self.can_shoot():
            actions.append(('shoot', None))

        for direction in DIRECTIONS:
            nx, ny = self.x + direction[0], self.y + direction[1]
            if grid.is_passable(nx, ny) or grid.is_eagle(nx, ny):
                actions.append(('move', direction))

        best_action = None
        best_score = float('-inf')
        for action, direction in actions:
            score = self._utility_for_action(grid, player, bullets, action, direction)
            if score > best_score:
                best_score = score
                best_action = (action, direction)

        if not best_action:
            return

        action, direction = best_action
        if action == 'shoot':
            self._want_shoot = True
        elif action == 'move' and direction is not None:
            self._pending_direction = direction

    def _utility_for_action(self, grid, player, bullets, action, direction) -> float:
        x, y = self.x, self.y
        if action == 'move' and direction is not None:
            x, y = x + direction[0], y + direction[1]

        score = 0.0

        if player and player.alive:
            dist = abs(x - player.x) + abs(y - player.y)
            score += max(0, 10 - dist) * 3
            if grid.line_of_sight(x, y, player.x, player.y):
                score += 50
                if action == 'shoot':
                    score += 60

        if self._adjacent_to_steel(grid, x, y):
            score += 20

        if self._bullet_threat(grid, bullets, x, y):
            score -= 60

        if grid.is_eagle(x, y):
            score += 10

        return score

    def _adjacent_to_steel(self, grid, x: int, y: int) -> bool:
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if grid.in_bounds(nx, ny) and grid.get(nx, ny) == STEEL:
                return True
        return False

    def _bullet_threat(self, grid, bullets, x: int, y: int) -> bool:
        for b in bullets:
            if not b.active:
                continue
            if b.direction == UP and b.x == x and b.y > y:
                if grid.line_of_sight(b.x, b.y, x, y):
                    return True
            if b.direction == DOWN and b.x == x and b.y < y:
                if grid.line_of_sight(b.x, b.y, x, y):
                    return True
            if b.direction == LEFT and b.y == y and b.x > x:
                if grid.line_of_sight(b.x, b.y, x, y):
                    return True
            if b.direction == RIGHT and b.y == y and b.x < x:
                if grid.line_of_sight(b.x, b.y, x, y):
                    return True
        return False
