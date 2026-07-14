import math
import pygame
from settings import *


class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.radius = PLAYER_RADIUS
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.speed = PLAYER_SPEED
        self.level = 1
        self.xp = 0
        self.xp_to_next = XP_BASE
        self.kills = 0
        self.attack_cooldown = ATTACK_COOLDOWN
        self.attack_timer = 0.0
        self.damage = PROJECTILE_DAMAGE
        self.projectile_speed = PROJECTILE_SPEED
        self.projectile_count = PROJECTILE_COUNT
        self.invincibility_timer = 0.0
        self.alive = True
        # dash
        self.dash_cooldown_base = DASH_COOLDOWN
        self.dash_cooldown = 0.0  # current timer (ready at 0)
        self.dash_timer = 0.0
        self.dashing = False
        # expandable stats
        self.hp_regen_timer = 0.0
        self.hp_regen_interval = 0.0  # 0 = disabled
        self.pickup_range_mult = 1.0
        self.projectile_radius_mult = 1.0
        self.pulse_timer = 0.0
        self.pulse_cooldown = PULSE_COOLDOWN
        self.pulse_damage = 0  # 0 = disabled
        self.pulse_range = PULSE_RANGE
        self.pulse_anim = 0.0  # animation timer for expanding ring
        # upgrade tracking — ponytail: not read back, just for upgrade count
        self.attack_speed_level = 0
        self.damage_level = 0
        self.move_speed_level = 0
        self.max_hp_level = 0
        self.multishot_level = 0

    def update(self, dt, keys):
        if not self.alive:
            return
        # movement
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        # normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        speed_mult = DASH_SPEED_MULT if self.dashing else 1.0
        self.x += dx * self.speed * speed_mult * dt
        self.y += dy * self.speed * speed_mult * dt

        # clamp to screen
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        # cooldowns
        if self.attack_timer > 0:
            self.attack_timer -= dt
        if self.invincibility_timer > 0:
            self.invincibility_timer -= dt

        # dash
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dashing = False

        # hp regen
        if self.hp_regen_interval > 0 and self.hp < self.max_hp:
            self.hp_regen_timer -= dt
            if self.hp_regen_timer <= 0:
                self.hp = min(self.hp + 1, self.max_hp)
                self.hp_regen_timer = self.hp_regen_interval

        # pulse weapon timer
        if self.pulse_damage > 0:
            self.pulse_timer -= dt
        if self.pulse_anim > 0:
            self.pulse_anim -= dt

    def start_dash(self):
        if self.dash_cooldown <= 0 and self.alive:
            self.dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown = self.dash_cooldown_base
            self.invincibility_timer = DASH_DURATION

    def take_damage(self, amount):
        if self.invincibility_timer > 0 or not self.alive:
            return
        self.hp -= amount
        self.invincibility_timer = PLAYER_INVINCIBILITY_TIME
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        # flash during invincibility
        if self.invincibility_timer > 0 and int(self.invincibility_timer * 20) % 2 == 0:
            return
        pygame.draw.circle(screen, PLAYER_COLOR, (int(self.x), int(self.y)), self.radius)
        # small white highlight
        pygame.draw.circle(
            screen, (180, 210, 255),
            (int(self.x - self.radius * 0.3), int(self.y - self.radius * 0.3)),
            max(2, self.radius // 3)
        )


class Enemy:
    def __init__(self, x, y, enemy_type, time_mult=1.0):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.alive = True

        tdef = ENEMY_TYPES[enemy_type]
        hp_base = tdef["hp"]
        self.hp = int(hp_base + hp_base * time_mult * 0.5)
        self.max_hp = self.hp
        self.speed = tdef["speed_min"] + (tdef["speed_max"] - tdef["speed_min"]) * time_mult * 0.5
        self.damage = tdef["damage"]
        self.xp_value = tdef["xp"]
        self.radius = tdef["radius"]
        self.color = tdef["color"]
        self.type = enemy_type

    def update(self, dt, player_x, player_y):
        if not self.alive:
            return
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # simple hp bar if damaged
        if self.hp < self.max_hp:
            bar_w = self.radius * 2
            bar_h = 3
            bar_x = int(self.x - bar_w / 2)
            bar_y = int(self.y - self.radius - 6)
            ratio = self.hp / self.max_hp
            pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, (200, 50, 50), (bar_x, bar_y, int(bar_w * ratio), bar_h))


class Projectile:
    def __init__(self, x, y, vx, vy, damage):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = PROJECTILE_RADIUS
        self.damage = damage
        self.lifetime = ATTACK_RANGE / PROJECTILE_SPEED
        self.alive = True

    def update(self, dt):
        if not self.alive:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        pygame.draw.circle(screen, PROJECTILE_COLOR, (int(self.x), int(self.y)), self.radius)


class XPGem:
    def __init__(self, x, y, xp_value):
        self.x = x
        self.y = y
        self.radius = XP_GEM_RADIUS
        self.xp_value = xp_value
        self.alive = True
        self.attracted = False

    def update(self, dt, player_x, player_y, pickup_range=XP_PICKUP_RANGE):
        if not self.alive:
            return
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist < pickup_range:
            self.attracted = True
        if self.attracted:
            speed = 350
            if dist > 0:
                self.x += (dx / dist) * speed * dt
                self.y += (dy / dist) * speed * dt

    def draw(self, screen):
        if not self.alive:
            return
        pygame.draw.circle(screen, XP_GEM_COLOR, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (160, 255, 160), (int(self.x), int(self.y)), max(2, self.radius // 2))
