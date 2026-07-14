# ── Window ──────────────────────────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Survivor"

# ── Colors ──────────────────────────────────────────
BG_COLOR = (28, 28, 32)
PLAYER_COLOR = (60, 140, 240)
PROJECTILE_COLOR = (255, 220, 60)
XP_GEM_COLOR = (100, 240, 100)
HP_BAR_BG = (50, 50, 55)
HP_BAR_FILL = (220, 60, 60)
XP_BAR_BG = (50, 50, 55)
XP_BAR_FILL = (60, 140, 240)
UI_TEXT_COLOR = (220, 220, 230)
OVERLAY_COLOR = (0, 0, 0, 140)

# ── Player ──────────────────────────────────────────
PLAYER_RADIUS = 14
PLAYER_SPEED = 280
PLAYER_MAX_HP = 100
PLAYER_INVINCIBILITY_TIME = 0.5  # seconds after being hit
DASH_COOLDOWN = 3.0
DASH_DURATION = 0.15
DASH_SPEED_MULT = 2.5

# ── Combat ──────────────────────────────────────────
ATTACK_RANGE = 350
ATTACK_COOLDOWN = 0.8  # seconds between attacks
PROJECTILE_SPEED = 500
PROJECTILE_RADIUS = 4
PROJECTILE_DAMAGE = 10
PROJECTILE_COUNT = 1  # base projectiles per attack

# ── Enemies ─────────────────────────────────────────
ENEMY_TYPES = {
    "bat": {
        "hp": 2,
        "speed_min": 140,
        "speed_max": 200,
        "damage": 5,
        "xp": 1,
        "radius": 8,
        "color": (180, 60, 200),
    },
    "brute": {
        "hp": 8,
        "speed_min": 60,
        "speed_max": 100,
        "damage": 15,
        "xp": 3,
        "radius": 16,
        "color": (50, 160, 50),
    },
    "sprinter": {
        "hp": 1,
        "speed_min": 220,
        "speed_max": 280,
        "damage": 3,
        "xp": 1,
        "radius": 5,
        "color": (240, 210, 40),
    },
}

# ── Elites ──────────────────────────────────────────
ELITE_HP_MULT = 3
ELITE_RADIUS_MULT = 1.5
ELITE_XP_MULT = 5
ELITE_COLOR = (255, 80, 40)

# ── Spawning ────────────────────────────────────────
SPAWN_INTERVAL_INITIAL = 1.8  # seconds between spawns at start
SPAWN_INTERVAL_MIN = 0.25  # fastest spawn interval
SPAWN_COUNT_INITIAL = 2  # enemies per spawn at start
SPAWN_COUNT_MAX = 10  # enemies per spawn at peak
DIFFICULTY_RAMP_TIME = 300  # seconds to reach max difficulty (5 min)
SPAWN_MARGIN = 40  # pixels outside screen edge to spawn
DESPAWN_MARGIN = 300  # pixels off-screen before cleanup

# ── XP & Leveling ──────────────────────────────────
XP_BASE = 10  # xp needed for level 1
XP_PER_LEVEL = 5  # additional xp per level (linear)
XP_GEM_RADIUS = 5
XP_PICKUP_RANGE = 65

# ── Upgrades ────────────────────────────────────────
UPGRADE_CHOICES = 3  # how many upgrades to pick from on level-up

# ── New upgrade constants ───────────────────────────
HP_REGEN_INTERVAL = 2.0
PULSE_COOLDOWN = 5.0
PULSE_DAMAGE = 15
PULSE_RANGE = 120

# ── Juice ───────────────────────────────────────────
SHAKE_DURATION = 0.15
SHAKE_INTENSITY = 5
PARTICLE_COUNT = 5
PARTICLE_SPEED = 150
PARTICLE_LIFETIME = 0.4

# ── HUD ─────────────────────────────────────────────
HUD_MARGIN = 16
HUD_BAR_WIDTH = 200
HUD_BAR_HEIGHT = 18
HUD_FONT_SIZE = 20
HUD_FONT_SIZE_LARGE = 36
HUD_FONT_SIZE_TITLE = 56
HIGH_SCORE_FILE = "highscore.json"
