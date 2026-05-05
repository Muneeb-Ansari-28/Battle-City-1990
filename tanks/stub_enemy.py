
#  tanks/stub_enemy.py  —  Temporary stub enemy for Module 0 testing
#  This will be REPLACED by proper AI tanks in Module 2.
#  It gives the spawner something to spawn so the engine can be tested.

import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tanks.tank import Tank
from constants import *


class StubEnemyTank(Tank):
    """
    Dumb enemy: moves randomly, shoots randomly.
    No AI — just proves the engine works.
    Replace with BasicTank / FastTank / ArmorTank in Module 2.
    """

    def __init__(self, x: int = 0, y: int = 0,
                 tank_type: str = TYPE_BASIC):
        color_map = {
            TYPE_BASIC: C_BASIC,
            TYPE_FAST:  C_FAST,
            TYPE_ARMOR: C_ARMOR,
            TYPE_POWER: C_POWER,
        }
        hp_map = {
            TYPE_BASIC: 1,
            TYPE_FAST:  1,
            TYPE_ARMOR: 4,
            TYPE_POWER: 2,
        }
        speed_map = {
            TYPE_BASIC: SPEED_SLOW,
            TYPE_FAST:  SPEED_FAST,
            TYPE_ARMOR: SPEED_MEDIUM,
            TYPE_POWER: SPEED_MEDIUM,
        }
        super().__init__(
            x         = x,
            y         = y,
            tank_type = tank_type,
            hp        = hp_map.get(tank_type, 1),
            speed     = speed_map.get(tank_type, SPEED_SLOW),
            fire_rate = FIRE_BASIC,
            color     = color_map.get(tank_type, C_BASIC),
        )
        self._dir_timer = 0

    def decide(self, game_state: dict) -> None:
        # Change direction every ~30 ticks
        self._dir_timer -= 1
        if self._dir_timer <= 0:
            self._pending_direction = random.choice(DIRECTIONS)
            self._dir_timer = random.randint(15, 45)
        else:
            self._pending_direction = self.direction

        # Shoot randomly ~5% of ticks
        self._want_shoot = random.random() < 0.05

    def on_map_change(self, x, y, old, new):
        pass   # stub ignores map changes