import pygame
from settings import *


def make_font(size):
    return pygame.font.SysFont("consolas", size, bold=True)


_font_cache = {}


def _font(size):
    if size not in _font_cache:
        _font_cache[size] = make_font(size)
    return _font_cache[size]


def draw_text(screen, text, x, y, color=UI_TEXT_COLOR, size=HUD_FONT_SIZE, center=False):
    surf = _font(size).render(text, True, color)
    if center:
        x -= surf.get_width() // 2
        y -= surf.get_height() // 2
    screen.blit(surf, (x, y))


def draw_bar(screen, x, y, w, h, ratio, fill_color, bg_color=None):
    if bg_color is None:
        bg_color = HP_BAR_BG
    pygame.draw.rect(screen, bg_color, (x, y, w, h))
    if ratio > 0:
        pygame.draw.rect(screen, fill_color, (x, y, int(w * ratio), h))
    # subtle border
    pygame.draw.rect(screen, (80, 80, 85), (x, y, w, h), 1)


def draw_hud(screen, player, game_time):
    # top-left: HP bar
    bx = HUD_MARGIN
    by = HUD_MARGIN
    hp_ratio = player.hp / player.max_hp
    draw_bar(screen, bx, by, HUD_BAR_WIDTH, HUD_BAR_HEIGHT, hp_ratio, HP_BAR_FILL)
    draw_text(screen, f"HP {player.hp}/{player.max_hp}", bx + HUD_BAR_WIDTH + 8, by, UI_TEXT_COLOR, 16)

    # XP bar below HP
    by += HUD_BAR_HEIGHT + 6
    xp_ratio = player.xp / player.xp_to_next
    draw_bar(screen, bx, by, HUD_BAR_WIDTH, HUD_BAR_HEIGHT, xp_ratio, XP_BAR_FILL)
    draw_text(screen, f"XP {player.xp}/{player.xp_to_next}", bx + HUD_BAR_WIDTH + 8, by, UI_TEXT_COLOR, 16)

    # Level
    by += HUD_BAR_HEIGHT + 10
    draw_text(screen, f"Level {player.level}", bx, by, UI_TEXT_COLOR, HUD_FONT_SIZE)

    # top-right: timer and kills
    mins = int(game_time // 60)
    secs = int(game_time % 60)
    timer_text = f"{mins:02d}:{secs:02d}"
    draw_text(screen, timer_text, SCREEN_WIDTH - HUD_MARGIN, HUD_MARGIN, UI_TEXT_COLOR, HUD_FONT_SIZE)
    draw_text(screen, f"Kills: {player.kills}", SCREEN_WIDTH - HUD_MARGIN, HUD_MARGIN + 24, UI_TEXT_COLOR, 16)


def draw_menu(screen, high_score=0.0):
    screen.fill(BG_COLOR)
    draw_text(screen, "SURVIVOR", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3,
              PLAYER_COLOR, HUD_FONT_SIZE_TITLE, center=True)
    draw_text(screen, "Press ENTER to start", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
              UI_TEXT_COLOR, HUD_FONT_SIZE, center=True)
    draw_text(screen, "WASD to move  |  Auto-attack  |  ESC to pause",
              SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, (150, 150, 160), 16, center=True)
    if high_score > 0:
        mins = int(high_score // 60)
        secs = int(high_score % 60)
        draw_text(screen, f"Best: {mins:02d}:{secs:02d}", SCREEN_WIDTH // 2,
                  SCREEN_HEIGHT // 2 + 40, (180, 180, 100), 18, center=True)


def draw_pause_overlay(screen):
    dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    dark.set_alpha(160)
    dark.fill((0, 0, 0))
    screen.blit(dark, (0, 0))
    draw_text(screen, "PAUSED", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20,
              UI_TEXT_COLOR, HUD_FONT_SIZE_LARGE, center=True)
    draw_text(screen, "Press ESC to resume", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
              (150, 150, 160), 18, center=True)


def draw_game_over(screen, player, game_time, new_best=False):
    screen.fill(BG_COLOR)
    draw_text(screen, "GAME OVER", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4,
              HP_BAR_FILL, HUD_FONT_SIZE_TITLE, center=True)

    mins = int(game_time // 60)
    secs = int(game_time % 60)
    lines = [
        f"Survived: {mins:02d}:{secs:02d}",
        f"Level: {player.level}",
        f"Kills: {player.kills}",
    ]
    y = SCREEN_HEIGHT // 2 - 30
    for line in lines:
        draw_text(screen, line, SCREEN_WIDTH // 2, y, UI_TEXT_COLOR, HUD_FONT_SIZE_LARGE, center=True)
        y += 40

    if new_best:
        draw_text(screen, "NEW BEST!", SCREEN_WIDTH // 2, y + 10,
                  (255, 220, 60), HUD_FONT_SIZE_LARGE, center=True)

    draw_text(screen, "Press ENTER to play again", SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4,
              UI_TEXT_COLOR, HUD_FONT_SIZE, center=True)


def show_upgrade_choices(screen, choices):
    """choices is a list of dicts: {name, description}"""
    screen.fill(BG_COLOR)
    dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    dark.set_alpha(100)
    dark.fill((0, 0, 0))
    # we'll draw directly on the screen (already dimmed by the calling code)

    draw_text(screen, "LEVEL UP!", SCREEN_WIDTH // 2, 80,
              PLAYER_COLOR, HUD_FONT_SIZE_LARGE, center=True)
    draw_text(screen, "Choose an upgrade (press 1, 2, or 3):",
              SCREEN_WIDTH // 2, 130, UI_TEXT_COLOR, 18, center=True)

    card_w = 320
    card_h = 180
    spacing = 30
    total_w = len(choices) * card_w + (len(choices) - 1) * spacing
    start_x = (SCREEN_WIDTH - total_w) // 2
    y = 200

    for i, choice in enumerate(choices):
        cx = start_x + i * (card_w + spacing)
        card = pygame.Rect(cx, y, card_w, card_h)
        pygame.draw.rect(screen, (40, 40, 48), card, border_radius=8)
        pygame.draw.rect(screen, (80, 80, 90), card, 2, border_radius=8)

        # number badge
        draw_text(screen, str(i + 1), cx + 16, y + 12, PLAYER_COLOR, HUD_FONT_SIZE_LARGE)

        draw_text(screen, choice["name"], cx + 20, y + 50, UI_TEXT_COLOR, 22)
        draw_text(screen, choice["description"], cx + 20, y + 90, (160, 160, 170), 16)

    return start_x, y, card_w, card_h
