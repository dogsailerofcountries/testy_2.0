import json
import math
import os
import random
import pygame
import sys
from settings import *
from entities import Player, Enemy, Projectile, XPGem
from ui import draw_hud, draw_menu, draw_pause_overlay, draw_game_over, draw_text


# ── Upgrades ──────────────────────────────────────────

def _apply_toughness(p):
    p.max_hp += 20
    p.hp = min(p.hp + 20, p.max_hp)


UPGRADE_POOL = [
    {
        "id": "attack_speed",
        "name": "Attack Speed",
        "description": "Attack 15% faster",
        "apply": lambda p: setattr(p, "attack_cooldown", p.attack_cooldown * 0.85),
    },
    {
        "id": "damage",
        "name": "Damage",
        "description": "+25% projectile damage",
        "apply": lambda p: setattr(p, "damage", int(p.damage * 1.25)),
    },
    {
        "id": "move_speed",
        "name": "Move Speed",
        "description": "+10% movement speed",
        "apply": lambda p: setattr(p, "speed", p.speed * 1.10),
    },
    {
        "id": "max_hp",
        "name": "Toughness",
        "description": "+20 max HP, heal 20",
        "apply": lambda p: _apply_toughness(p),
    },
    {
        "id": "multishot",
        "name": "Multi-Shot",
        "description": "+1 projectile per attack",
        "apply": lambda p: setattr(p, "projectile_count", p.projectile_count + 1),
    },
    {
        "id": "hp_regen",
        "name": "HP Regen",
        "description": "+1 HP every 2 seconds",
        "apply": lambda p: (
            setattr(p, "hp_regen_interval", HP_REGEN_INTERVAL),
            setattr(p, "hp_regen_timer", HP_REGEN_INTERVAL),
        ) if p.hp_regen_interval == 0 else setattr(p, "hp_regen_interval", p.hp_regen_interval * 0.85),
    },
    {
        "id": "pickup_range",
        "name": "Pickup Range",
        "description": "+25% pickup radius",
        "apply": lambda p: setattr(p, "pickup_range_mult", p.pickup_range_mult * 1.25),
    },
    {
        "id": "projectile_size",
        "name": "Projectile Size",
        "description": "+20% bigger projectiles",
        "apply": lambda p: setattr(p, "projectile_radius_mult", p.projectile_radius_mult * 1.20),
    },
    {
        "id": "dash_cooldown",
        "name": "Dash Cooldown",
        "description": "Dash 15% more often",
        "apply": lambda p: setattr(p, "dash_cooldown_base", p.dash_cooldown_base * 0.85),
    },
    {
        "id": "aoe_pulse",
        "name": "AOE Pulse",
        "description": "Every 5s, damage all nearby enemies",
        "apply": lambda p: (
            setattr(p, "pulse_damage", p.pulse_damage + 5) if p.pulse_damage > 0
            else (setattr(p, "pulse_damage", PULSE_DAMAGE), setattr(p, "pulse_timer", 0.5)),
        ),
    },
]


def pick_upgrades(player):
    """Return 3 random upgrade choices."""
    available = [u for u in UPGRADE_POOL]  # infinite scaling, no max levels
    pick_count = min(UPGRADE_CHOICES, len(available))
    return random.sample(available, pick_count)


# ── Helpers ───────────────────────────────────────────

def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def lerp(a, b, t):
    return a + (b - a) * t


def spawn_enemy(game_time):
    """Pick a random screen edge position and enemy type."""
    # pick edge
    edge = random.randint(0, 3)
    if edge == 0:  # top
        x = random.uniform(0, SCREEN_WIDTH)
        y = -SPAWN_MARGIN
    elif edge == 1:  # bottom
        x = random.uniform(0, SCREEN_WIDTH)
        y = SCREEN_HEIGHT + SPAWN_MARGIN
    elif edge == 2:  # left
        x = -SPAWN_MARGIN
        y = random.uniform(0, SCREEN_HEIGHT)
    else:  # right
        x = SCREEN_WIDTH + SPAWN_MARGIN
        y = random.uniform(0, SCREEN_HEIGHT)

    # pick type — bats always, brutes after 30s, sprinters after 60s
    time_mult = min(game_time / DIFFICULTY_RAMP_TIME, 1.0)
    types = ["bat"]
    weights = [1.0]
    if game_time > 30:
        types.append("brute")
        brute_weight = lerp(0.2, 0.6, time_mult)
        weights = [1 - brute_weight, brute_weight]
    if game_time > 60:
        types = ["bat", "brute", "sprinter"]
        sprinter_weight = lerp(0.1, 0.35, time_mult)
        brute_weight = lerp(0.2, 0.4, time_mult)
        weights = [1 - brute_weight - sprinter_weight, brute_weight, sprinter_weight]
    enemy_type = random.choices(types, weights=weights, k=1)[0]

    return Enemy(x, y, enemy_type, time_mult)


def spawn_elite(game_time):
    """Spawn an elite enemy at a random edge — bigger, tougher, more XP."""
    edge = random.randint(0, 3)
    if edge == 0:
        x, y = random.uniform(0, SCREEN_WIDTH), -SPAWN_MARGIN
    elif edge == 1:
        x, y = random.uniform(0, SCREEN_WIDTH), SCREEN_HEIGHT + SPAWN_MARGIN
    elif edge == 2:
        x, y = -SPAWN_MARGIN, random.uniform(0, SCREEN_HEIGHT)
    else:
        x, y = SCREEN_WIDTH + SPAWN_MARGIN, random.uniform(0, SCREEN_HEIGHT)

    etype = random.choice(["bat", "brute", "sprinter"])
    e = Enemy(x, y, etype, min(game_time / DIFFICULTY_RAMP_TIME, 1.0))
    e.hp = int(e.hp * ELITE_HP_MULT)
    e.max_hp = e.hp
    e.radius = int(e.radius * ELITE_RADIUS_MULT)
    e.xp_value = int(e.xp_value * ELITE_XP_MULT)
    e.color = ELITE_COLOR
    return e


def is_offscreen(entity):
    return (entity.x < -DESPAWN_MARGIN or
            entity.x > SCREEN_WIDTH + DESPAWN_MARGIN or
            entity.y < -DESPAWN_MARGIN or
            entity.y > SCREEN_HEIGHT + DESPAWN_MARGIN)


# ── High Score ────────────────────────────────────────

def _high_score_path():
    return os.path.join(os.path.dirname(__file__), HIGH_SCORE_FILE)


def load_high_score():
    try:
        with open(_high_score_path()) as f:
            return json.load(f).get("best_time", 0.0)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return 0.0


def save_high_score(game_time):
    with open(_high_score_path(), "w") as f:
        json.dump({"best_time": game_time}, f)


# ── Main Game ─────────────────────────────────────────

def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    state = "menu"
    running = True
    shake_timer = 0.0
    particles = []  # list of dicts: {x, y, vx, vy, life, color}

    # game objects — created fresh per run
    player = None
    enemies = []
    projectiles = []
    xp_gems = []
    game_time = 0.0
    spawn_timer = 0.0
    upgrading = False
    upgrade_choices = []
    elite_120_spawned = False
    elite_240_spawned = False
    high_score = load_high_score()
    new_best = False

    def start_game():
        nonlocal player, enemies, projectiles, xp_gems, game_time, spawn_timer, upgrading, upgrade_choices, shake_timer, particles, elite_120_spawned, elite_240_spawned, new_best
        player = Player()
        enemies.clear()
        projectiles.clear()
        xp_gems.clear()
        particles.clear()
        game_time = 0.0
        spawn_timer = 0.0
        shake_timer = 0.0
        upgrading = False
        upgrade_choices.clear()
        elite_120_spawned = False
        elite_240_spawned = False
        new_best = False

    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.05:
            dt = 0.05

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    start_game()
                    state = "playing"

            elif state == "playing":
                if not upgrading:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            state = "paused"
                        elif event.key == pygame.K_SPACE:
                            player.start_dash()
                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                            idx = event.key - pygame.K_1
                            if idx < len(upgrade_choices):
                                upgrade_choices[idx]["apply"](player)
                                upgrading = False
                                upgrade_choices.clear()

            elif state == "paused":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "playing"

            elif state == "game_over":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    start_game()
                    state = "playing"

        # ── Update ────────────────────────────────────

        if state == "playing" and not upgrading:
            keys = pygame.key.get_pressed()
            player.update(dt, keys)

            # spawn enemies
            spawn_interval = lerp(SPAWN_INTERVAL_INITIAL, SPAWN_INTERVAL_MIN,
                                  min(game_time / DIFFICULTY_RAMP_TIME, 1.0))
            spawn_count = int(lerp(SPAWN_COUNT_INITIAL, SPAWN_COUNT_MAX,
                                   min(game_time / DIFFICULTY_RAMP_TIME, 1.0)))

            spawn_timer -= dt
            if spawn_timer <= 0:
                spawn_timer = spawn_interval
                for _ in range(spawn_count):
                    enemies.append(spawn_enemy(game_time))

            # auto-attack: find nearest enemy
            if player.attack_timer <= 0:
                nearest = None
                nearest_dist = ATTACK_RANGE
                for enemy in enemies:
                    if not enemy.alive:
                        continue
                    d = math.hypot(enemy.x - player.x, enemy.y - player.y)
                    if d < nearest_dist:
                        nearest = enemy
                        nearest_dist = d
                if nearest is not None:
                    dx = nearest.x - player.x
                    dy = nearest.y - player.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        base_angle = math.atan2(dy, dx)
                        spread = 0.12  # radians between projectiles
                        count = player.projectile_count
                        for i in range(count):
                            if count == 1:
                                angle = base_angle
                            else:
                                angle = base_angle + spread * (i - (count - 1) / 2)
                            vx = math.cos(angle) * player.projectile_speed
                            vy = math.sin(angle) * player.projectile_speed
                            proj = Projectile(player.x, player.y, vx, vy, player.damage)
                            proj.radius = int(PROJECTILE_RADIUS * player.projectile_radius_mult)
                            projectiles.append(proj)
                    player.attack_timer = player.attack_cooldown

            # update enemies
            for enemy in enemies:
                enemy.update(dt, player.x, player.y)

            # update projectiles
            for proj in projectiles:
                proj.update(dt)

            # update xp gems
            pickup_range = XP_PICKUP_RANGE * player.pickup_range_mult
            for gem in xp_gems:
                gem.update(dt, player.x, player.y, pickup_range)

            # AOE pulse
            if player.pulse_damage > 0 and player.pulse_timer <= 0:
                player.pulse_timer = player.pulse_cooldown
                player.pulse_anim = 0.2
                for enemy in enemies:
                    if not enemy.alive:
                        continue
                    if math.hypot(enemy.x - player.x, enemy.y - player.y) < player.pulse_range:
                        enemy.take_damage(player.pulse_damage)
                        if not enemy.alive:
                            player.kills += 1
                            xp_gems.append(XPGem(enemy.x, enemy.y, enemy.xp_value))
                            for _ in range(PARTICLE_COUNT):
                                angle = random.uniform(0, math.pi * 2)
                                speed = random.uniform(50, PARTICLE_SPEED)
                                particles.append({
                                    "x": enemy.x, "y": enemy.y,
                                    "vx": math.cos(angle) * speed,
                                    "vy": math.sin(angle) * speed,
                                    "life": PARTICLE_LIFETIME,
                                    "color": enemy.color,
                                })

            # ── Collisions ────────────────────────────

            # projectile vs enemy
            for proj in projectiles:
                if not proj.alive:
                    continue
                for enemy in enemies:
                    if not enemy.alive:
                        continue
                    if math.hypot(proj.x - enemy.x, proj.y - enemy.y) < proj.radius + enemy.radius:
                        enemy.take_damage(proj.damage)
                        proj.alive = False
                        if not enemy.alive:
                            player.kills += 1
                            xp_gems.append(XPGem(enemy.x, enemy.y, enemy.xp_value))
                            # death particles
                            for _ in range(PARTICLE_COUNT):
                                angle = random.uniform(0, math.pi * 2)
                                speed = random.uniform(50, PARTICLE_SPEED)
                                particles.append({
                                    "x": enemy.x, "y": enemy.y,
                                    "vx": math.cos(angle) * speed,
                                    "vy": math.sin(angle) * speed,
                                    "life": PARTICLE_LIFETIME,
                                    "color": enemy.color,
                                })
                        break  # projectile dies after one hit

            # enemy vs player (contact damage)
            for enemy in enemies:
                if not enemy.alive:
                    continue
                if math.hypot(enemy.x - player.x, enemy.y - player.y) < enemy.radius + player.radius:
                    player.take_damage(enemy.damage)
                    shake_timer = SHAKE_DURATION

            # player vs xp gems (pickup)
            for gem in xp_gems:
                if not gem.alive:
                    continue
                if math.hypot(gem.x - player.x, gem.y - player.y) < player.radius + gem.radius:
                    gem.alive = False
                    player.xp += gem.xp_value
                    # check level up (only if player still alive)
                    while player.alive and player.xp >= player.xp_to_next:
                        player.xp -= player.xp_to_next
                        player.level += 1
                        player.xp_to_next = XP_BASE + player.level * XP_PER_LEVEL
                        # trigger upgrade
                        upgrade_choices = pick_upgrades(player)
                        upgrading = True

            # update particles
            for p in particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["life"] -= dt

            # decay shake
            if shake_timer > 0:
                shake_timer -= dt

            # ── Cleanup ────────────────────────────────

            enemies = [e for e in enemies if e.alive and not is_offscreen(e)]
            projectiles = [p for p in projectiles if p.alive]
            xp_gems = [g for g in xp_gems if g.alive]
            particles = [p for p in particles if p["life"] > 0]

            game_time += dt

            # elite spawns at time milestones
            if game_time >= 120 and not elite_120_spawned:
                enemies.append(spawn_elite(game_time))
                elite_120_spawned = True
            if game_time >= 240 and not elite_240_spawned:
                enemies.append(spawn_elite(game_time))
                elite_240_spawned = True

            # check player death (allow final enemy cleanup first)
            if not player.alive and not upgrading:
                if game_time > high_score:
                    high_score = game_time
                    save_high_score(high_score)
                    new_best = True
                state = "game_over"

        # ── Draw ──────────────────────────────────────

        screen.fill(BG_COLOR)

        if state == "menu":
            draw_menu(screen, high_score)

        elif state in ("playing", "paused"):
            # screen shake offset
            sx = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if shake_timer > 0 else 0
            sy = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if shake_timer > 0 else 0

            game_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            game_surf.fill(BG_COLOR)

            # draw particles
            for p in particles:
                alpha = p["life"] / PARTICLE_LIFETIME
                r, g, b = p["color"]
                c = (int(r * alpha), int(g * alpha), int(b * alpha))
                pygame.draw.circle(game_surf, c, (int(p["x"]), int(p["y"])), 2)

            # draw entities
            for gem in xp_gems:
                gem.draw(game_surf)
            for enemy in enemies:
                enemy.draw(game_surf)
            for proj in projectiles:
                proj.draw(game_surf)
            player.draw(game_surf)

            # pulse visual
            if player.pulse_anim > 0:
                anim_ratio = 1 - (player.pulse_anim / 0.2)
                ring_r = int(player.pulse_range * anim_ratio)
                alpha = int(200 * (1 - anim_ratio))
                ring_color = (alpha, alpha, 255)
                pygame.draw.circle(game_surf, ring_color,
                                   (int(player.x), int(player.y)), ring_r, 2)

            # draw hud
            draw_hud(game_surf, player, game_time)

            # upgrade overlay
            if upgrading and upgrade_choices:
                dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                dark.set_alpha(140)
                dark.fill((0, 0, 0))
                game_surf.blit(dark, (0, 0))
                draw_text(game_surf, "LEVEL UP!", SCREEN_WIDTH // 2, 80,
                          PLAYER_COLOR, HUD_FONT_SIZE_LARGE, center=True)
                draw_text(game_surf, "Choose (1 / 2 / 3):",
                          SCREEN_WIDTH // 2, 130, UI_TEXT_COLOR, 18, center=True)

                card_w = 320
                card_h = 160
                spacing = 30
                total_w = len(upgrade_choices) * card_w + (len(upgrade_choices) - 1) * spacing
                start_x = (SCREEN_WIDTH - total_w) // 2
                y = 200
                for i, choice in enumerate(upgrade_choices):
                    cx = start_x + i * (card_w + spacing)
                    card = pygame.Rect(cx, y, card_w, card_h)
                    pygame.draw.rect(game_surf, (40, 40, 48), card, border_radius=8)
                    pygame.draw.rect(game_surf, (80, 80, 90), card, 2, border_radius=8)
                    draw_text(game_surf, str(i + 1), cx + 16, y + 12, PLAYER_COLOR, HUD_FONT_SIZE_LARGE)
                    draw_text(game_surf, choice["name"], cx + 20, y + 55, UI_TEXT_COLOR, 22)
                    draw_text(game_surf, choice["description"], cx + 20, y + 95, (160, 160, 170), 16)

            screen.blit(game_surf, (sx, sy))

            # pause overlay (drawn on top of the shaken surface)
            if state == "paused":
                draw_pause_overlay(screen)

        elif state == "game_over":
            draw_game_over(screen, player, game_time, new_best)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
