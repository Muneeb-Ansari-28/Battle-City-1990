# Battle City 1990

Battle City 1990 is a Python + Pygame reimplementation of the classic top-down tank game. The project runs on a 26x26 tile grid and uses AI concepts as the core gameplay system rather than as a side feature.

## Overview

The codebase is organized around three AI modules from the project guide:

- CSP-based procedural map generation with validation constraints
- Search-based enemy movement using BFS, Greedy Best-First Search, and A*
- Adversarial boss behavior using Minimax with Alpha-Beta pruning

The game also includes a full loop with menu, play, pause, win/lose states, tank spawning, bullet collisions, destructible terrain, score tracking, lives, sound effects, and a polished HUD.

## Game ScreenShots
 # Menu
<img width="1393" height="1111" alt="Image" src="https://github.com/user-attachments/assets/9cb05d27-b671-49b2-8252-cac931fb8ae6" />
 
 # Stage 1 (OutPost)
<img width="1512" height="1198" alt="Image" src="https://github.com/user-attachments/assets/9c127b36-f4e9-48a5-839b-d4c485c51b85" />

 # Stage 2 (Steel Factory)
 <img width="1501" height="1198" alt="Image" src="https://github.com/user-attachments/assets/a25c8209-0208-4894-9657-2c08191a75d7" />

# Stage 3 (Boss Level)
<img width="1500" height="1198" alt="Image" src="https://github.com/user-attachments/assets/db672fca-95fa-4e72-addf-2bc1e3b7fcf1" />

## Implemented Features

- Grid-based gameplay on a 26x26 tile map
- Destructible brick walls and permanent terrain changes during play
- CSP map generation with reachability, fairness, density, and base-protection constraints
- Dynamic enemy AI behaviors:
  - Basic Tank: Simple Reflex Agent with BFS pathfinding
  - Fast Tank: Goal-Based Agent with Greedy Best-First Search
  - Armor Tank: Model-Based Reflex Agent with A* and retreat logic
  - Power Tank: Utility-Based decision making
  - Boss Tank: Adversarial Agent with Minimax + Alpha-Beta pruning
- Boss phase behavior with different speed, fire rate, and search depth by HP stage
- Enemy spawning with active-enemy limits, spawn delay, and fairness checks
- Player respawn with invincibility frames
- Particle effects, screen shake, and impact feedback
- Optional menu background image and sound effects/music hooks
- AI debug toggle for visual inspection during gameplay

## Levels

- Level 1: Brick Maze
  - Dense brick-heavy map
  - Basic Tanks dominate early, Fast Tanks appear later
  - Highlights BFS pathfinding and wall destruction
- Level 2: Steel Fortress
  - Mixed brick, steel, water, and forest terrain
  - Fast, Armor, and Power tanks appear together
  - Highlights cost-aware movement and retreat behavior
- Level 3: Boss Arena
  - Fixed arena centered on a one-on-one boss fight
  - Boss uses phase-based Minimax with Alpha-Beta pruning

## Project Structure

```
Battle-City-1990/
├─ main.py
├─ game_loop.py
├─ grid.py
├─ renderer.py
├─ spawner.py
├─ constants.py
├─ csp_generator.py
├─ level_configs.py
├─ bullet.py
├─ effects.py
├─ assets/
│  ├─ Menu-Background-Image/
│  │  └─ Background.jpg
│  └─ sounds/
│     ├─ background_sound.wav
│     ├─ cannon_fire.wav
│     ├─ cannon_hit_concrete.wav
│     ├─ cannon_hit_water.wav
│     ├─ canon_hit_wood.wav
│     ├─ game_over.wav
│     ├─ menu.wav
│     ├─ tank_destroyed.wav
│     └─ tank_going_in_grass.wav
├─ ai/
│  ├─ bfs.py
│  ├─ greedy_bfs.py
│  └─ astar.py
└─ tanks/
   ├─ tank.py
   ├─ player.py
   ├─ basic_tank.py
   ├─ fast_tank.py
   ├─ armor_tank.py
   ├─ power_tank.py
   ├─ boss_tank.py
   └─ stub_enemy.py
```

## Requirements

- Python 3.10+ (tested on Python 3.12)
- Pygame

## Setup

```bash
pip install pygame
```

If you want the optional report-generation dependency used in the workspace, install:

```bash
pip install python-docx
```

## Run

```bash
python main.py
```

## Controls

- Move: WASD or Arrow Keys
- Shoot: Space or J
- Pause: ESC
- Restart after Game Over: R
- Toggle AI debug overlay: TAB

## Assets

Optional assets already wired into the project:

- Menu background image: assets/Menu-Background-Image/Background.jpg
- Sounds:
  - assets/sounds/cannon_fire.wav
  - assets/sounds/canon_hit_wood.wav
  - assets/sounds/cannon_hit_concrete.wav
  - assets/sounds/cannon_hit_water.wav
  - assets/sounds/tank_destroyed.wav
  - assets/sounds/tank_going_in_grass.wav
  - assets/sounds/game_over.wav
  - assets/sounds/menu.wav
  - assets/sounds/background_sound.wav

## Notes

- The project guide describes a 20-enemy pool per level, but the current implementation uses the level-specific enemy pools defined in level_configs.py.
- The codebase includes a Power Tank implementation in addition to the manual's core search agents.
- Terrain changes during play affect pathfinding, so AI routes may be recomputed after brick destruction.

## Credits

- Project guide: AL2002 Artificial Intelligence Lab, Spring 2026
- Built with Pygame
