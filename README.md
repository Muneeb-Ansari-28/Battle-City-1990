# Battle City — Tank 1990 (AL2002 AI Lab)

A Python + Pygame reimagining of the classic **Battle City / Tank 1990**, built for the AL2002 AI Lab project. The game runs on a 26×26 grid and demonstrates AI concepts through multiple enemy tank behaviors (BFS, Greedy Best-First, A*, Utility-Based agents, and a Minimax + Alpha-Beta boss).

## Features

- **Grid-based gameplay** with destructible terrain and dynamic map changes
- **CSP map generation** with constraints for fairness, reachability, and density
- **Enemy AI suite**:
  - Basic Tank (Simple Reflex, BFS)
  - Fast Tank (Goal-Based, Greedy Best-First)
  - Armor Tank (Model-Based Reflex, A*)
  - Power Tank (Utility-Based)
  - Boss Tank (Minimax + Alpha-Beta)
- **Boss Arena** with phase-based behavior and adversarial planning
- Modernized **UI/HUD** styling and effects

## Requirements

- Python 3.10+ (tested on 3.12)
- Pygame

## Setup

```bash
pip install pygame
```

## Run

```bash
python main.py
```

## Controls

- **Move:** WASD or Arrow Keys
- **Shoot:** Space or J
- **Pause:** ESC
- **Restart (Game Over):** R

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
   └─ boss_tank.py
```

## Notes

- **Level 1** spawns 7 Basic + 5 Fast tanks, with Fast tanks gated after 7 kills.
- **Level 2** mixes Fast, Armor, and Power tanks for higher difficulty.
- **Level 3** is a **Boss Arena** with Minimax + Alpha-Beta pruning.

## Credits

- Project Guide: AL2002 Artificial Intelligence Lab (Spring 2026)
- Built with **Pygame**
