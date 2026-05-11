# ============================================================
#  effects.py  —  Particles, screen shake, and lightweight SFX
# ============================================================
import math
import os
import random
import pygame


class Particle:
    __slots__ = (
        "x", "y", "vx", "vy", "life", "max_life",
        "size", "color", "fade", "gravity",
    )

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0
        self.max_life = 0
        self.size = 1.0
        self.color = (255, 255, 255)
        self.fade = True
        self.gravity = 0.0

    def reset(self, x, y, vx, vy, life, size, color, fade=True, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.fade = fade
        self.gravity = gravity


class ParticleSystem:
    def __init__(self, max_particles=900):
        self._active = []
        self._pool = [Particle() for _ in range(max_particles)]

    def emit(self, x, y, count=6, speed=1.0, spread=math.tau,
             life=(10, 20), size=(1.0, 2.5), colors=None,
             fade=True, gravity=0.0):
        if colors is None:
            colors = [(255, 255, 255)]
        for _ in range(count):
            if not self._pool:
                return
            p = self._pool.pop()
            ang = random.random() * spread
            spd = speed * (0.4 + random.random() * 0.8)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            life_i = random.randint(life[0], life[1])
            size_i = random.uniform(size[0], size[1])
            color = random.choice(colors)
            p.reset(x, y, vx, vy, life_i, size_i, color, fade, gravity)
            self._active.append(p)

    def update(self):
        alive = []
        for p in self._active:
            p.life -= 1
            if p.life <= 0:
                self._pool.append(p)
                continue
            p.vy += p.gravity
            p.x += p.vx
            p.y += p.vy
            alive.append(p)
        self._active = alive

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        for p in self._active:
            if p.fade:
                alpha = int(255 * (p.life / max(1, p.max_life)))
            else:
                alpha = 200
            r, g, b = p.color
            size = max(1, int(p.size))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (size, size), size)
            surface.blit(s, (int(p.x + ox - size), int(p.y + oy - size)))


class DebrisPiece:
    __slots__ = (
        "x", "y", "vx", "vy", "life", "max_life",
        "w", "h", "color", "angle", "ang_vel", "gravity",
    )

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0
        self.max_life = 0
        self.w = 2
        self.h = 2
        self.color = (200, 200, 200)
        self.angle = 0.0
        self.ang_vel = 0.0
        self.gravity = 0.0

    def reset(self, x, y, vx, vy, life, w, h, color, angle, ang_vel, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.w = w
        self.h = h
        self.color = color
        self.angle = angle
        self.ang_vel = ang_vel
        self.gravity = gravity


class Shockwave:
    __slots__ = ("x", "y", "radius", "speed", "life", "max_life", "color")

    def __init__(self, x, y, radius, speed, life, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.life = life
        self.max_life = life
        self.color = color


class ScreenShake:
    def __init__(self):
        self._time = 0
        self._duration = 0
        self._intensity = 0.0

    def trigger(self, intensity=2.0, duration=10):
        self._intensity = max(self._intensity, intensity)
        self._duration = max(self._duration, duration)
        self._time = self._duration

    def update(self):
        if self._time > 0:
            self._time -= 1
        if self._time <= 0:
            self._intensity = 0.0

    def offset(self):
        if self._time <= 0:
            return (0, 0)
        jitter = self._intensity * (self._time / max(1, self._duration))
        return (random.uniform(-jitter, jitter), random.uniform(-jitter, jitter))


class SFX:
    def __init__(self, base_dir):
        self._sounds = {}
        self._sound_base = {}
        self._music = {}
        self._current_music = None
        self._active_channels = []
        self._enabled = False
        self._base_dir = base_dir
        try:
            pygame.mixer.init()
            self._enabled = True
        except Exception:
            self._enabled = False

    def load(self, name, filename, volume=0.5):
        if not self._enabled:
            return
        path = os.path.join(self._base_dir, filename)
        if not os.path.exists(path):
            return
        try:
            snd = pygame.mixer.Sound(path)
            self._sounds[name] = snd
            self._sound_base[name] = volume
        except Exception:
            return

    def register_music(self, name, filename):
        if not self._enabled:
            return
        path = os.path.join(self._base_dir, filename)
        if not os.path.exists(path):
            return
        self._music[name] = path

    def play_music(self, name, volume=0.2, loop=True):
        if not self._enabled:
            return
        if name == self._current_music:
            return
        path = self._music.get(name)
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self._current_music = name
        except Exception:
            return

    def stop_music(self):
        if not self._enabled:
            return
        pygame.mixer.music.stop()
        self._current_music = None

    def play(self, name, volume_scale=1.0, max_duration_ms=None):
        if not self._enabled:
            return
        snd = self._sounds.get(name)
        if not snd:
            return
        ch = snd.play()
        if ch:
            base = self._sound_base.get(name, 0.5)
            ch.set_volume(min(1.0, base * volume_scale))
            if max_duration_ms is not None:
                end_time = pygame.time.get_ticks() + max_duration_ms
                self._active_channels.append((ch, end_time))

    def update(self):
        if not self._enabled:
            return
        now = pygame.time.get_ticks()
        alive = []
        for ch, end_time in self._active_channels:
            if not ch.get_busy():
                continue
            if now >= end_time:
                ch.stop()
                continue
            alive.append((ch, end_time))
        self._active_channels = alive


class FXManager:
    def __init__(self, assets_dir=None):
        self.particles = ParticleSystem()
        self._debris_pool = [DebrisPiece() for _ in range(120)]
        self._debris_active = []
        self._shockwaves = []
        self.shake = ScreenShake()
        self.flash_color = None
        self.flash_timer = 0
        self.sfx = None

        if assets_dir:
            self.sfx = SFX(assets_dir)

    # ── Effects emitters ──────────────────────────────────
    def impact_brick(self, x, y):
        self.particles.emit(x, y, count=10, speed=1.8, life=(10, 18),
                            size=(1.0, 2.5), colors=[(200, 80, 40), (160, 60, 30)],
                            gravity=0.05)
        self.debris(x, y, count=8, colors=[(170, 70, 40), (120, 50, 30)])
        self._flash((255, 140, 90), 3)
        self.shake.trigger(intensity=1.4, duration=8)
        if self.sfx:
            self.sfx.play("brick")

    def impact_steel(self, x, y):
        self.particles.emit(x, y, count=8, speed=2.4, life=(8, 14),
                            size=(1.0, 2.0), colors=[(160, 170, 200), (90, 100, 130)],
                            gravity=0.02)
        self.sparks(x, y, count=8, colors=[(210, 230, 255), (120, 160, 220)])
        self._flash((140, 200, 255), 2)
        if self.sfx:
            self.sfx.play("steel")

    def impact_water(self, x, y):
        self.particles.emit(x, y, count=6, speed=1.6, life=(10, 16),
                            size=(1.0, 2.0), colors=[(60, 120, 200), (40, 80, 160)],
                            gravity=0.03)
        self._flash((90, 150, 255), 2)
        if self.sfx:
            self.sfx.play("water")

    def muzzle(self, x, y, color=(255, 210, 120)):
        self.particles.emit(x, y, count=6, speed=1.2, life=(6, 10),
                            size=(1.0, 2.0), colors=[color, (255, 120, 80)],
                            fade=True)
        self._flash((255, 200, 120), 2)
        if self.sfx:
            self.sfx.play("shoot", max_duration_ms=400)

    def smoke_trail(self, x, y):
        self.particles.emit(x, y, count=2, speed=0.4, life=(14, 22),
                            size=(1.5, 3.0), colors=[(80, 80, 90)],
                            gravity=-0.01)

    def exhaust(self, x, y, direction, color=(110, 110, 120)):
        dx, dy = direction
        ox = -dx * 2
        oy = -dy * 2
        self.particles.emit(x + ox, y + oy, count=3, speed=0.6, spread=1.2,
                            life=(8, 14), size=(1.0, 2.0), colors=[color, (60, 60, 70)],
                            gravity=-0.01)

    def explosion_small(self, x, y, play_sound=True):
        self.particles.emit(x, y, count=18, speed=2.2, life=(12, 20),
                            size=(1.0, 2.8), colors=[(255, 180, 80), (255, 90, 40)],
                            gravity=0.04)
        self.particles.emit(x, y, count=10, speed=1.0, life=(20, 30),
                            size=(2.0, 3.5), colors=[(60, 60, 70)],
                            gravity=-0.01)
        self._add_shockwave(x, y, color=(255, 180, 120), radius=4, speed=2.0, life=10)
        self._flash((255, 160, 80), 4)
        self.shake.trigger(intensity=2.4, duration=12)
        if self.sfx and play_sound:
            self.sfx.play("tank_destroyed", max_duration_ms=500)

    def explosion_large(self, x, y, play_sound=True):
        self.particles.emit(x, y, count=30, speed=2.6, life=(14, 24),
                            size=(1.5, 3.4), colors=[(255, 200, 90), (255, 80, 40)],
                            gravity=0.05)
        self.particles.emit(x, y, count=18, speed=1.2, life=(24, 36),
                            size=(2.5, 4.5), colors=[(70, 70, 80)],
                            gravity=-0.01)
        self._add_shockwave(x, y, color=(255, 160, 110), radius=6, speed=2.4, life=14)
        self._flash((255, 120, 60), 6)
        self.shake.trigger(intensity=3.2, duration=18)
        if self.sfx and play_sound:
            self.sfx.play("tank_destroyed", volume_scale=1.2, max_duration_ms=500)

    def boss_phase(self, x, y, phase_color):
        self.particles.emit(x, y, count=26, speed=2.0, life=(14, 24),
                            size=(1.5, 3.0), colors=[phase_color],
                            gravity=0.02)
        self._add_shockwave(x, y, color=phase_color, radius=6, speed=2.0, life=12)
        self._flash(phase_color, 8)
        self.shake.trigger(intensity=3.8, duration=20)
        if self.sfx:
            self.sfx.play("boss")

    def spawn(self, x, y):
        self.particles.emit(x, y, count=18, speed=1.6, life=(12, 20),
                            size=(1.0, 2.4), colors=[(60, 220, 255), (140, 240, 255)],
                            gravity=-0.02)
        self._flash((120, 220, 255), 3)
        if self.sfx:
            self.sfx.play("spawn")

    def eagle_destroyed(self, x, y):
        self.explosion_large(x, y)
        self._flash((255, 60, 60), 12)

    def sparks(self, x, y, count=6, colors=None):
        if colors is None:
            colors = [(255, 240, 200), (200, 220, 255)]
        self.particles.emit(x, y, count=count, speed=2.8, life=(4, 8),
                            size=(0.8, 1.6), colors=colors, fade=True, gravity=0.05)

    def debris(self, x, y, count=6, colors=None):
        if colors is None:
            colors = [(190, 90, 50), (150, 60, 40)]
        for _ in range(count):
            if not self._debris_pool:
                return
            p = self._debris_pool.pop()
            ang = random.random() * math.tau
            spd = 1.4 + random.random() * 1.2
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 0.6
            life = random.randint(16, 28)
            w = random.randint(2, 4)
            h = random.randint(2, 5)
            color = random.choice(colors)
            p.reset(x, y, vx, vy, life, w, h, color,
                    angle=random.random() * 360.0,
                    ang_vel=random.uniform(-8, 8),
                    gravity=0.08)
            self._debris_active.append(p)

    def _add_shockwave(self, x, y, color=(255, 180, 120), radius=4, speed=2.0, life=12):
        self._shockwaves.append(Shockwave(x, y, radius, speed, life, color))

    def _flash(self, color, timer):
        self.flash_color = color
        self.flash_timer = max(self.flash_timer, timer)

    # ── Update/Draw ───────────────────────────────────────
    def update(self):
        self.particles.update()
        self.shake.update()
        if self.sfx:
            self.sfx.update()
        # Debris
        alive = []
        for p in self._debris_active:
            p.life -= 1
            if p.life <= 0:
                self._debris_pool.append(p)
                continue
            p.vy += p.gravity
            p.x += p.vx
            p.y += p.vy
            p.angle += p.ang_vel
            alive.append(p)
        self._debris_active = alive

        # Shockwaves
        alive_waves = []
        for w in self._shockwaves:
            w.life -= 1
            if w.life <= 0:
                continue
            w.radius += w.speed
            alive_waves.append(w)
        self._shockwaves = alive_waves

        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface, offset=(0, 0)):
        self._draw_shockwaves(surface, offset)
        self._draw_debris(surface, offset)
        self.particles.draw(surface, offset)

    def draw_flash(self, surface):
        if self.flash_timer <= 0 or not self.flash_color:
            return
        alpha = min(255, int(160 * (self.flash_timer / 8)))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self.flash_color, alpha))
        surface.blit(overlay, (0, 0))

    def _draw_debris(self, surface, offset=(0, 0)):
        ox, oy = offset
        for p in self._debris_active:
            alpha = int(220 * (p.life / max(1, p.max_life)))
            s = pygame.Surface((p.w, p.h), pygame.SRCALPHA)
            s.fill((*p.color, alpha))
            rot = pygame.transform.rotate(s, p.angle)
            surface.blit(rot, (int(p.x + ox - rot.get_width() / 2),
                               int(p.y + oy - rot.get_height() / 2)))

    def _draw_shockwaves(self, surface, offset=(0, 0)):
        ox, oy = offset
        for w in self._shockwaves:
            alpha = int(180 * (w.life / max(1, w.max_life)))
            s = pygame.Surface((w.radius * 2 + 4, w.radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*w.color, alpha),
                               (w.radius + 2, w.radius + 2), w.radius, 2)
            surface.blit(s, (int(w.x + ox - w.radius - 2), int(w.y + oy - w.radius - 2)))
