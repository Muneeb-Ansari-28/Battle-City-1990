# ============================================================
#  tanks/boss_tank.py  —  Boss Tank | Adversarial Agent
#  Minimax + Alpha-Beta Pruning with phase-based depth
# ============================================================

from constants import *
from tanks.tank import Tank


class BossTank(Tank):
    def __init__(self, x: int = 0, y: int = 0, grid=None):
        super().__init__(
            x=x,
            y=y,
            tank_type=TYPE_BOSS,
            hp=BOSS_HP,
            speed=BOSS_SPEED_P1,
            fire_rate=FIRE_BOSS_P1,
            color=C_BOSS,
        )
        self.grid = grid
        self.direction = DOWN
        self.active = False
        self.last_search_stats = None

    def decide(self, game_state: dict) -> None:
        self._pending_direction = None
        self._want_shoot = False

        if not (self.alive and self.active):
            return

        grid = game_state['grid']
        player = game_state.get('player')
        if not player or not player.alive:
            return

        self._sync_phase_stats()

        depth = self._phase_depth()
        state = {
            'boss_pos': (self.x, self.y),
            'player_pos': (player.x, player.y),
            'boss_hp': self.hp,
            'player_hp': player.lives,
        }

        self._nodes_ab = 0
        action = self._minimax_root(grid, state, depth, self.can_shoot())

        self._nodes_plain = 0
        self._minimax_plain(grid, state, depth, True)

        nodes_ab = max(1, self._nodes_ab)
        self.last_search_stats = {
            'nodes_ab': self._nodes_ab,
            'nodes_plain': self._nodes_plain,
            'speedup': round(self._nodes_plain / nodes_ab, 2),
        }

        if action is None:
            return

        if action[0] == 'shoot':
            self._want_shoot = True
            return

        if action[0] == 'move':
            self._pending_direction = action[1]

    def _sync_phase_stats(self) -> None:
        if self.hp <= BOSS_PHASE3_HP:
            self.speed = BOSS_SPEED_P3
            self.fire_rate = FIRE_BOSS_P3
        elif self.hp <= BOSS_PHASE2_HP:
            self.speed = BOSS_SPEED_P2
            self.fire_rate = FIRE_BOSS_P2
        else:
            self.speed = BOSS_SPEED_P1
            self.fire_rate = FIRE_BOSS_P1

    def _phase_depth(self) -> int:
        if self.hp <= BOSS_PHASE3_HP:
            return 4
        if self.hp <= BOSS_PHASE2_HP:
            return 3
        return 2

    def _minimax_root(self, grid, state, depth: int, allow_shoot: bool):
        alpha = float('-inf')
        beta = float('inf')
        best_action = None
        best_score = float('-inf')

        for action in self._legal_actions(
            grid, state['boss_pos'], state['player_pos'], allow_shoot
        ):
            next_state = self._apply_action(grid, state, action, is_boss=True)
            score = self._min_value(grid, next_state, depth - 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_action = action
            alpha = max(alpha, best_score)
        return best_action

    def _max_value(self, grid, state, depth: int, alpha: float, beta: float) -> float:
        self._nodes_ab += 1
        if depth <= 0 or self._is_terminal(state):
            return self._evaluate(grid, state)

        value = float('-inf')
        for action in self._legal_actions(grid, state['boss_pos'], state['player_pos']):
            next_state = self._apply_action(grid, state, action, is_boss=True)
            value = max(value, self._min_value(grid, next_state, depth - 1, alpha, beta))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    def _min_value(self, grid, state, depth: int, alpha: float, beta: float) -> float:
        self._nodes_ab += 1
        if depth <= 0 or self._is_terminal(state):
            return self._evaluate(grid, state)

        value = float('inf')
        for action in self._legal_actions(grid, state['player_pos'], state['boss_pos']):
            next_state = self._apply_action(grid, state, action, is_boss=False)
            value = min(value, self._max_value(grid, next_state, depth - 1, alpha, beta))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    def _minimax_plain(self, grid, state, depth: int, is_max: bool) -> float:
        self._nodes_plain += 1
        if depth <= 0 or self._is_terminal(state):
            return self._evaluate(grid, state)

        if is_max:
            value = float('-inf')
            for action in self._legal_actions(grid, state['boss_pos'], state['player_pos']):
                next_state = self._apply_action(grid, state, action, is_boss=True)
                value = max(value, self._minimax_plain(grid, next_state, depth - 1, False))
            return value

        value = float('inf')
        for action in self._legal_actions(grid, state['player_pos'], state['boss_pos']):
            next_state = self._apply_action(grid, state, action, is_boss=False)
            value = min(value, self._minimax_plain(grid, next_state, depth - 1, True))
        return value

    def _legal_actions(self, grid, actor_pos, other_pos, allow_shoot: bool = True):
        actions = []
        ax, ay = actor_pos

        for direction in DIRECTIONS:
            nx, ny = ax + direction[0], ay + direction[1]
            if (nx, ny) == other_pos:
                continue
            if grid.is_passable(nx, ny) or grid.is_eagle(nx, ny):
                actions.append(('move', direction))

        if allow_shoot:
            actions.append(('shoot', None))
        return actions

    def _apply_action(self, grid, state, action, is_boss: bool):
        boss_pos = state['boss_pos']
        player_pos = state['player_pos']
        boss_hp = state['boss_hp']
        player_hp = state['player_hp']

        actor_pos = boss_pos if is_boss else player_pos
        target_pos = player_pos if is_boss else boss_pos

        if action[0] == 'move':
            dx, dy = action[1]
            actor_pos = (actor_pos[0] + dx, actor_pos[1] + dy)

        if action[0] == 'shoot':
            if grid.line_of_sight(actor_pos[0], actor_pos[1], target_pos[0], target_pos[1]):
                if is_boss:
                    player_hp = max(0, player_hp - 1)
                else:
                    boss_hp = max(0, boss_hp - 1)

        if is_boss:
            boss_pos = actor_pos
        else:
            player_pos = actor_pos

        return {
            'boss_pos': boss_pos,
            'player_pos': player_pos,
            'boss_hp': boss_hp,
            'player_hp': player_hp,
        }

    def _evaluate(self, grid, state) -> float:
        boss_x, boss_y = state['boss_pos']
        player_x, player_y = state['player_pos']
        boss_hp = state['boss_hp']
        player_hp = state['player_hp']

        if boss_hp <= 0:
            return float('-inf')
        if player_hp <= 0:
            return float('inf')

        score = 0.0
        dist = abs(boss_x - player_x) + abs(boss_y - player_y)
        score += max(0, 12 - dist) * 4

        if dist <= 3:
            score += 60

        if grid.line_of_sight(boss_x, boss_y, player_x, player_y):
            score += 50

        if self._adjacent_to_steel(grid, boss_x, boss_y):
            score += 30

        player_max = PLAYER_LIVES
        score += (player_max - player_hp) * 20
        score -= (BOSS_HP - boss_hp) * 40

        if grid.get(player_x, player_y) == FOREST:
            score -= 20

        return score

    def _adjacent_to_steel(self, grid, x: int, y: int) -> bool:
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if grid.in_bounds(nx, ny) and grid.get(nx, ny) == STEEL:
                return True
        return False

    def _is_terminal(self, state) -> bool:
        return state['boss_hp'] <= 0 or state['player_hp'] <= 0
