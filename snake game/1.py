import pygame
import sys
import random
import time
import json
import os
import psycopg2
from datetime import datetime

# ──────────────────────────────────────────────
#  INIT
# ──────────────────────────────────────────────
pygame.init()
pygame.mixer.init()

CELL = 20
COLS = 30
ROWS = 30
W    = CELL * COLS
H    = CELL * ROWS

# ──────────────────────────────────────────────
#  COLORS
# ──────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = (0,   200, 0)
DARK_GREEN = (0,   150, 0)
RED        = (220, 50,  50)
YELLOW     = (255, 220, 0)
GOLD       = (200, 160, 0)
GRAY       = (40,  40,  40)
LIGHT_GRAY = (120, 120, 120)
DARK_BG    = (18,  18,  18)
SILVER     = (180, 180, 180)
PURPLE     = (180, 0,   220)
DARK_RED   = (139, 0,   0)
CYAN       = (0,   220, 220)
ORANGE     = (255, 140, 0)
BLUE       = (30,  100, 255)
PINK       = (255, 80,  180)

# ──────────────────────────────────────────────
#  SETTINGS (loaded from JSON)
# ──────────────────────────────────────────────
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "snake_color": [0, 200, 0],
    "grid_overlay": True,
    "sound": True,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # merge with defaults for any missing keys
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

# ──────────────────────────────────────────────
#  DATABASE
# ──────────────────────────────────────────────
DB_CONFIG = {
    "dbname":   "snake_game",
    "user":     "postgres",
    "password": "12345678",
    "host":     "localhost",
    "port":     "5432",
}

def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """Create tables if they don't exist."""
    try:
        conn = get_db_conn()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id       SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id            SERIAL PRIMARY KEY,
                player_id     INTEGER REFERENCES players(id),
                score         INTEGER   NOT NULL,
                level_reached INTEGER   NOT NULL,
                played_at     TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] init_db error: {e}")
        return False

def get_or_create_player(username):
    try:
        conn = get_db_conn()
        cur  = conn.cursor()
        cur.execute("INSERT INTO players (username) VALUES (%s) ON CONFLICT (username) DO NOTHING;", (username,))
        conn.commit()
        cur.execute("SELECT id FROM players WHERE username = %s;", (username,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"[DB] get_or_create_player error: {e}")
        return None

def save_game_session(player_id, score, level_reached):
    try:
        conn = get_db_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO game_sessions (player_id, score, level_reached) VALUES (%s, %s, %s);",
            (player_id, score, level_reached)
        )
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception as e:
        print(f"[DB] save_game_session error: {e}")
        return False

def get_personal_best(player_id):
    try:
        conn = get_db_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT COALESCE(MAX(score), 0) FROM game_sessions WHERE player_id = %s;",
            (player_id,)
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0

def get_top10():
    try:
        conn = get_db_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT p.username, gs.score, gs.level_reached, gs.played_at
            FROM game_sessions gs
            JOIN players p ON p.id = gs.player_id
            ORDER BY gs.score DESC
            LIMIT 10;
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Exception as e:
        print(f"[DB] get_top10 error: {e}")
        return []

# ──────────────────────────────────────────────
#  DISPLAY / FONTS
# ──────────────────────────────────────────────
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

font_big   = pygame.font.SysFont("Arial", 48, bold=True)
font_med   = pygame.font.SysFont("Arial", 28)
font_small = pygame.font.SysFont("Arial", 20)
font_tiny  = pygame.font.SysFont("Arial", 13, bold=True)

# ──────────────────────────────────────────────
#  LEVELS
# ──────────────────────────────────────────────
LEVELS = {
    1: (7,  3),
    2: (10, 6),
    3: (13, 10),
    4: (16, 15),
    5: (20, 999),
}

# ──────────────────────────────────────────────
#  FOOD TYPES  (+ poison)
# ──────────────────────────────────────────────
FOOD_TYPES = [
    {"name": "normal",  "color": RED,      "value":  1, "weight": 55, "timer": None, "poison": False},
    {"name": "bonus",   "color": YELLOW,   "value":  3, "weight": 22, "timer": 5,    "poison": False},
    {"name": "rare",    "color": PURPLE,   "value":  5, "weight": 8,  "timer": 3,    "poison": False},
    {"name": "silver",  "color": SILVER,   "value":  2, "weight": 5,  "timer": 7,    "poison": False},
    {"name": "poison",  "color": DARK_RED, "value":  0, "weight": 10, "timer": 6,    "poison": True},
]

# ──────────────────────────────────────────────
#  POWER-UP TYPES
# ──────────────────────────────────────────────
POWERUP_TYPES = [
    {"name": "speed_boost", "color": ORANGE, "label": "⚡ SPEED",  "duration": 5000},
    {"name": "slow_motion", "color": CYAN,   "label": "🐢 SLOW",   "duration": 5000},
    {"name": "shield",      "color": BLUE,   "label": "🛡 SHIELD",  "duration": None},  # until triggered
]
POWERUP_FIELD_DURATION = 8000  # ms on field before disappearing

# ──────────────────────────────────────────────
#  SOUND HELPERS (simple beeps with pygame.sndarray)
# ──────────────────────────────────────────────
import numpy as np

def make_beep(freq=440, duration=0.05, volume=0.3, sample_rate=44100):
    t     = np.linspace(0, duration, int(sample_rate * duration), False)
    wave  = (np.sin(2 * np.pi * freq * t) * volume * 32767).astype(np.int16)
    stereo = np.column_stack([wave, wave])
    sound = pygame.sndarray.make_sound(stereo)
    return sound

try:
    SND_EAT     = make_beep(660,  0.07, 0.3)
    SND_POISON  = make_beep(220,  0.15, 0.4)
    SND_POWERUP = make_beep(880,  0.10, 0.3)
    SND_DIE     = make_beep(110,  0.30, 0.5)
    SND_LEVELUP = make_beep(1047, 0.20, 0.4)
    SOUND_OK    = True
except Exception:
    SOUND_OK = False

def play_sound(snd):
    if settings.get("sound", True) and SOUND_OK:
        snd.play()

# ──────────────────────────────────────────────
#  OBSTACLE GENERATION (Level 3+)
# ──────────────────────────────────────────────
def generate_obstacles(level, snake, existing_foods):
    if level < 3:
        return []
    count    = (level - 2) * 4
    occupied = set(snake) | {f["pos"] for f in existing_foods}
    # border cells
    border = set()
    for x in range(COLS):
        border.add((x, 0)); border.add((x, ROWS-1))
    for y in range(ROWS):
        border.add((0, y)); border.add((COLS-1, y))
    occupied |= border

    blocks = []
    attempts = 0
    while len(blocks) < count and attempts < 2000:
        attempts += 1
        x = random.randint(1, COLS-2)
        y = random.randint(1, ROWS-2)
        if (x, y) in occupied:
            continue
        # don't block snake head vicinity (2 cells)
        sx, sy = snake[0]
        if abs(x - sx) <= 2 and abs(y - sy) <= 2:
            continue
        blocks.append((x, y))
        occupied.add((x, y))
    return blocks

# ──────────────────────────────────────────────
#  FOOD / POWERUP HELPERS
# ──────────────────────────────────────────────
def random_pos(snake, existing_foods, obstacles, powerup=None):
    occupied = (set(snake)
                | {f["pos"] for f in existing_foods}
                | set(obstacles))
    if powerup and powerup.get("pos"):
        occupied.add(powerup["pos"])
    attempts = 0
    while attempts < 10000:
        attempts += 1
        x = random.randint(1, COLS-2)
        y = random.randint(1, ROWS-2)
        if (x, y) not in occupied:
            return (x, y)
    return None

def spawn_food(snake, existing_foods, obstacles, powerup=None):
    chosen = random.choices(FOOD_TYPES,
                            weights=[f["weight"] for f in FOOD_TYPES], k=1)[0]
    pos = random_pos(snake, existing_foods, obstacles, powerup)
    if pos is None:
        return None
    return {
        "pos":        pos,
        "color":      chosen["color"],
        "value":      chosen["value"],
        "timer":      chosen["timer"],
        "name":       chosen["name"],
        "poison":     chosen["poison"],
        "spawned_at": pygame.time.get_ticks(),
    }

def spawn_powerup(snake, foods, obstacles):
    pt  = random.choice(POWERUP_TYPES)
    pos = random_pos(snake, foods, obstacles)
    if pos is None:
        return None
    return {
        "pos":        pos,
        "color":      pt["color"],
        "label":      pt["label"],
        "name":       pt["name"],
        "duration":   pt["duration"],
        "spawned_at": pygame.time.get_ticks(),
    }

def update_foods(foods):
    now   = pygame.time.get_ticks()
    alive = []
    for food in foods:
        if food["timer"] is not None:
            if now - food["spawned_at"] >= food["timer"] * 1000:
                continue
        alive.append(food)
    return alive

# ──────────────────────────────────────────────
#  DRAWING
# ──────────────────────────────────────────────
def draw_grid():
    if not settings.get("grid_overlay", True):
        return
    for x in range(0, W, CELL):
        pygame.draw.line(screen, (30, 30, 30), (x, 0), (x, H))
    for y in range(0, H, CELL):
        pygame.draw.line(screen, (30, 30, 30), (0, y), (W, y))

def draw_walls():
    for x in range(COLS):
        pygame.draw.rect(screen, GRAY, (x*CELL, 0, CELL, CELL))
        pygame.draw.rect(screen, GRAY, (x*CELL, (ROWS-1)*CELL, CELL, CELL))
    for y in range(ROWS):
        pygame.draw.rect(screen, GRAY, (0, y*CELL, CELL, CELL))
        pygame.draw.rect(screen, GRAY, ((COLS-1)*CELL, y*CELL, CELL, CELL))

def draw_obstacles(obstacles):
    for (x, y) in obstacles:
        pygame.draw.rect(screen, (80, 80, 80), (x*CELL, y*CELL, CELL, CELL))
        pygame.draw.rect(screen, (120, 120, 120), (x*CELL+1, y*CELL+1, CELL-2, CELL-2), 1)

def draw_snake(snake, shield_active):
    head_color   = tuple(settings["snake_color"])
    # darken for body
    body_color   = tuple(max(0, c - 60) for c in head_color)
    for i, (x, y) in enumerate(snake):
        color = head_color if i == 0 else body_color
        pygame.draw.rect(screen, color,
                         (x*CELL+1, y*CELL+1, CELL-2, CELL-2),
                         border_radius=4)
        if i == 0 and shield_active:
            pygame.draw.rect(screen, BLUE,
                             (x*CELL, y*CELL, CELL, CELL),
                             2, border_radius=4)

def draw_foods(foods):
    now = pygame.time.get_ticks()
    for food in foods:
        x, y  = food["pos"]
        cx    = x*CELL + CELL//2
        cy    = y*CELL + CELL//2
        color = food["color"]

        if food["timer"] is not None:
            elapsed   = (now - food["spawned_at"]) / 1000.0
            remaining = food["timer"] - elapsed
            if remaining < 2:
                if int(remaining / 0.3) % 2 == 0:
                    color = DARK_BG
            timer_txt = font_tiny.render(f"{remaining:.1f}", True, WHITE)
            screen.blit(timer_txt, (x*CELL, y*CELL - 14))

        pygame.draw.circle(screen, color, (cx, cy), CELL//2 - 2)

        if food["poison"]:
            # draw an X on poison
            pygame.draw.line(screen, WHITE,
                             (cx-4, cy-4), (cx+4, cy+4), 2)
            pygame.draw.line(screen, WHITE,
                             (cx+4, cy-4), (cx-4, cy+4), 2)
        else:
            val_txt  = font_tiny.render(str(food["value"]), True, BLACK)
            val_rect = val_txt.get_rect(center=(cx, cy))
            screen.blit(val_txt, val_rect)

def draw_powerup(powerup):
    if powerup is None:
        return
    now  = pygame.time.get_ticks()
    age  = now - powerup["spawned_at"]
    frac = age / POWERUP_FIELD_DURATION
    x, y = powerup["pos"]
    cx   = x*CELL + CELL//2
    cy   = y*CELL + CELL//2

    color = powerup["color"]
    if frac > 0.75:
        # flash
        if int((POWERUP_FIELD_DURATION - age) / 200) % 2 == 0:
            color = DARK_BG

    pygame.draw.rect(screen, color,
                     (x*CELL+1, y*CELL+1, CELL-2, CELL-2),
                     border_radius=5)
    lbl = font_tiny.render(powerup["label"][0], True, BLACK)
    lbl_rect = lbl.get_rect(center=(cx, cy))
    screen.blit(lbl, lbl_rect)

def draw_hud(score, level, food_count, foods_needed, personal_best,
             active_powerup_name, active_powerup_end):
    now = pygame.time.get_ticks()

    score_txt = font_small.render(f"Score: {score}", True, WHITE)
    level_txt = font_small.render(f"Level: {level}", True, YELLOW)
    food_txt  = font_small.render(f"Food: {food_count}/{foods_needed}", True, GREEN)
    pb_txt    = font_small.render(f"Best: {personal_best}", True, GOLD)

    screen.blit(score_txt, (10,        8))
    screen.blit(level_txt, (W//2-40,   8))
    screen.blit(food_txt,  (W-160,     8))
    screen.blit(pb_txt,    (10,        30))

    if active_powerup_name and active_powerup_end:
        remaining_ms = active_powerup_end - now
        if remaining_ms > 0:
            secs = remaining_ms / 1000.0
            color_map = {
                "speed_boost": ORANGE,
                "slow_motion": CYAN,
                "shield":      BLUE,
            }
            col = color_map.get(active_powerup_name, WHITE)
            pu_txt = font_small.render(
                f"{active_powerup_name.replace('_',' ').upper()} {secs:.1f}s", True, col)
            screen.blit(pu_txt, (W//2 - pu_txt.get_width()//2, 30))
    elif active_powerup_name == "shield":
        sh_txt = font_small.render("SHIELD ACTIVE", True, BLUE)
        screen.blit(sh_txt, (W//2 - sh_txt.get_width()//2, 30))

def draw_legend():
    x, y = 5, H - 90
    legend_title = font_tiny.render("FOOD TYPES:", True, GRAY)
    screen.blit(legend_title, (x, y))
    for i, ft in enumerate(FOOD_TYPES):
        timer_str = f"{ft['timer']}s" if ft["timer"] else "∞"
        suffix    = "  [POISON -2]" if ft["poison"] else f"  +{ft['value']}  [{timer_str}]"
        txt = font_tiny.render(f"{ft['name']}{suffix}", True, ft["color"])
        screen.blit(txt, (x, y + 14 + i*13))

# ──────────────────────────────────────────────
#  SCREENS
# ──────────────────────────────────────────────
def draw_button(rect, text, hover=False,
                base=(50, 50, 50), hover_color=(80, 80, 80)):
    color = hover_color if hover else base
    pygame.draw.rect(screen, color, rect, border_radius=8)
    pygame.draw.rect(screen, LIGHT_GRAY, rect, 2, border_radius=8)
    txt   = font_med.render(text, True, WHITE)
    trect = txt.get_rect(center=rect.center)
    screen.blit(txt, trect)

def get_hover(rects):
    mx, my = pygame.mouse.get_pos()
    return [r.collidepoint(mx, my) for r in rects]

# ── Main Menu ──────────────────────────────────
def screen_main_menu():
    """Returns action string: 'play', 'leaderboard', 'settings', 'quit'"""
    btn_w, btn_h = 220, 52
    cx = W//2 - btn_w//2
    btn_play   = pygame.Rect(cx, H//2 - 20,  btn_w, btn_h)
    btn_lb     = pygame.Rect(cx, H//2 + 46,  btn_w, btn_h)
    btn_set    = pygame.Rect(cx, H//2 + 112, btn_w, btn_h)
    btn_quit   = pygame.Rect(cx, H//2 + 178, btn_w, btn_h)
    buttons    = [btn_play, btn_lb, btn_set, btn_quit]
    labels     = ["▶  Play", "🏆  Leaderboard", "⚙  Settings", "✕  Quit"]
    actions    = ["play", "leaderboard", "settings", "quit"]

    while True:
        screen.fill(DARK_BG)
        title = font_big.render("SNAKE", True, GREEN)
        screen.blit(title, title.get_rect(center=(W//2, H//2 - 110)))
        sub = font_small.render("Classic arcade — enhanced edition", True, GRAY)
        screen.blit(sub, sub.get_rect(center=(W//2, H//2 - 60)))

        hovers = get_hover(buttons)
        for i, (r, lbl) in enumerate(zip(buttons, labels)):
            draw_button(r, lbl, hovers[i])

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, r in enumerate(buttons):
                    if r.collidepoint(event.pos):
                        return actions[i]
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()

# ── Username Entry ─────────────────────────────
def screen_enter_username():
    """Returns (username_str, player_id) or (None, None) if quit."""
    username   = ""
    cursor_vis = True
    cursor_t   = pygame.time.get_ticks()

    while True:
        now = pygame.time.get_ticks()
        if now - cursor_t > 500:
            cursor_vis = not cursor_vis
            cursor_t   = now

        screen.fill(DARK_BG)
        t1 = font_big.render("Enter Username", True, GREEN)
        screen.blit(t1, t1.get_rect(center=(W//2, H//2 - 80)))

        hint = font_small.render("Type your name, then press ENTER", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(W//2, H//2 - 30)))

        box = pygame.Rect(W//2 - 150, H//2 + 10, 300, 50)
        pygame.draw.rect(screen, (50, 50, 50), box, border_radius=8)
        pygame.draw.rect(screen, LIGHT_GRAY, box, 2, border_radius=8)

        display_text = username + ("|" if cursor_vis else " ")
        name_surf    = font_med.render(display_text, True, WHITE)
        screen.blit(name_surf, name_surf.get_rect(center=box.center))

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username.strip():
                    uname     = username.strip()[:20]
                    player_id = get_or_create_player(uname)
                    return uname, player_id
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif event.key == pygame.K_ESCAPE:
                    return None, None
                elif len(username) < 20:
                    ch = event.unicode
                    if ch.isprintable() and ch != " " or (ch == " " and username):
                        username += ch

# ── Leaderboard ────────────────────────────────
def screen_leaderboard():
    rows   = get_top10()
    btn    = pygame.Rect(W//2 - 80, H - 70, 160, 48)

    while True:
        screen.fill(DARK_BG)
        t1 = font_big.render("LEADERBOARD", True, GOLD)
        screen.blit(t1, t1.get_rect(center=(W//2, 50)))

        headers = ["#", "Player", "Score", "Level", "Date"]
        col_x   = [40, 100, 290, 390, 460]
        for hx, h in zip(col_x, headers):
            ht = font_small.render(h, True, YELLOW)
            screen.blit(ht, (hx, 100))
        pygame.draw.line(screen, GRAY, (30, 125), (W-30, 125), 1)

        if not rows:
            no_data = font_med.render("No records yet!", True, GRAY)
            screen.blit(no_data, no_data.get_rect(center=(W//2, H//2)))
        else:
            for i, (uname, score, level, played_at) in enumerate(rows):
                y   = 135 + i*38
                rank_color = [GOLD, SILVER, (205, 127, 50)] if i < 3 else [WHITE]*10
                rc   = rank_color[min(i, len(rank_color)-1)]
                rank_txt  = font_small.render(f"{i+1}", True, rc)
                name_txt  = font_small.render(str(uname)[:14], True, WHITE)
                score_txt = font_small.render(str(score), True, GREEN)
                level_txt = font_small.render(str(level), True, CYAN)
                date_str  = played_at.strftime("%m/%d %H:%M") if played_at else "—"
                date_txt  = font_small.render(date_str, True, LIGHT_GRAY)

                screen.blit(rank_txt,  (col_x[0], y))
                screen.blit(name_txt,  (col_x[1], y))
                screen.blit(score_txt, (col_x[2], y))
                screen.blit(level_txt, (col_x[3], y))
                screen.blit(date_txt,  (col_x[4], y))

        hovers = get_hover([btn])
        draw_button(btn, "← Back", hovers[0])
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn.collidepoint(event.pos):
                    return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return

# ── Settings ───────────────────────────────────
SNAKE_COLOR_OPTIONS = [
    ("Green",  [0,   200, 0]),
    ("Red",    [220, 50,  50]),
    ("Cyan",   [0,   220, 220]),
    ("Yellow", [255, 220, 0]),
    ("Pink",   [255, 80,  180]),
    ("White",  [220, 220, 220]),
]

def screen_settings():
    local = dict(settings)  # work on a copy

    btn_save = pygame.Rect(W//2 - 100, H - 70, 200, 48)

    def find_color_idx(color):
        for i, (_, c) in enumerate(SNAKE_COLOR_OPTIONS):
            if c == color:
                return i
        return 0

    color_idx = find_color_idx(local["snake_color"])

    while True:
        screen.fill(DARK_BG)
        t1 = font_big.render("SETTINGS", True, WHITE)
        screen.blit(t1, t1.get_rect(center=(W//2, 50)))

        # Grid overlay toggle
        grid_lbl  = font_med.render("Grid Overlay:", True, WHITE)
        grid_val  = font_med.render("ON" if local["grid_overlay"] else "OFF",
                                    True, GREEN if local["grid_overlay"] else RED)
        grid_btn  = pygame.Rect(W//2+80, 130, 80, 38)
        screen.blit(grid_lbl, (80, 138))
        screen.blit(grid_val, grid_val.get_rect(center=grid_btn.center))
        pygame.draw.rect(screen, LIGHT_GRAY, grid_btn, 2, border_radius=6)

        # Sound toggle
        snd_lbl  = font_med.render("Sound:", True, WHITE)
        snd_val  = font_med.render("ON" if local["sound"] else "OFF",
                                   True, GREEN if local["sound"] else RED)
        snd_btn  = pygame.Rect(W//2+80, 190, 80, 38)
        screen.blit(snd_lbl, (80, 198))
        screen.blit(snd_val, snd_val.get_rect(center=snd_btn.center))
        pygame.draw.rect(screen, LIGHT_GRAY, snd_btn, 2, border_radius=6)

        # Snake color picker
        sc_lbl = font_med.render("Snake Color:", True, WHITE)
        screen.blit(sc_lbl, (80, 258))
        for i, (name, col) in enumerate(SNAKE_COLOR_OPTIONS):
            bx = 80 + i*68
            cr = pygame.Rect(bx, 295, 58, 30)
            pygame.draw.rect(screen, tuple(col), cr, border_radius=5)
            if i == color_idx:
                pygame.draw.rect(screen, WHITE, cr, 3, border_radius=5)
            ct = font_tiny.render(name, True, BLACK)
            screen.blit(ct, ct.get_rect(center=cr.center))

        # Preview snake
        px, py = W//2, 380
        preview_color = tuple(local["snake_color"])
        body_color    = tuple(max(0, c-60) for c in preview_color)
        for seg in range(5):
            c = preview_color if seg == 0 else body_color
            pygame.draw.rect(screen, c,
                             (px - seg*CELL + seg, py, CELL-2, CELL-2),
                             border_radius=4)

        hovers = get_hover([btn_save])
        draw_button(btn_save, "💾 Save & Back", hovers[0])
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if grid_btn.collidepoint(event.pos):
                    local["grid_overlay"] = not local["grid_overlay"]
                elif snd_btn.collidepoint(event.pos):
                    local["sound"] = not local["sound"]
                elif btn_save.collidepoint(event.pos):
                    settings.update(local)
                    save_settings(settings)
                    return
                else:
                    for i, (_, col) in enumerate(SNAKE_COLOR_OPTIONS):
                        bx = 80 + i*68
                        cr = pygame.Rect(bx, 295, 58, 30)
                        if cr.collidepoint(event.pos):
                            color_idx = i
                            local["snake_color"] = col
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

# ── Game Over Screen ────────────────────────────
def screen_game_over(score, level, reason, personal_best):
    btn_retry = pygame.Rect(W//2 - 210, H//2 + 70, 180, 48)
    btn_menu  = pygame.Rect(W//2 + 30,  H//2 + 70, 180, 48)

    while True:
        screen.fill(DARK_BG)

        t1 = font_big.render("GAME OVER", True, RED)
        screen.blit(t1, t1.get_rect(center=(W//2, H//2 - 100)))

        reason_map = {
            "wall":     "You hit the wall!",
            "self":     "You bit yourself!",
            "obstacle": "You hit an obstacle!",
            "poison":   "Eaten too much poison!",
        }
        r_txt = font_med.render(reason_map.get(reason, ""), True, WHITE)
        screen.blit(r_txt, r_txt.get_rect(center=(W//2, H//2 - 40)))

        score_txt = font_med.render(f"Score:  {score}", True, GREEN)
        level_txt = font_med.render(f"Level:  {level}", True, YELLOW)
        pb_txt    = font_med.render(f"Personal Best:  {personal_best}", True, GOLD)
        screen.blit(score_txt, score_txt.get_rect(center=(W//2, H//2)))
        screen.blit(level_txt, level_txt.get_rect(center=(W//2, H//2 + 32)))
        screen.blit(pb_txt,    pb_txt.get_rect(center=(W//2, H//2 + 62)))   # Adjusted

        hovers = get_hover([btn_retry, btn_menu])
        draw_button(btn_retry, "▶  Retry",     hovers[0])
        draw_button(btn_menu,  "⌂  Main Menu", hovers[1])
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_retry.collidepoint(event.pos):
                    return "retry"
                if btn_menu.collidepoint(event.pos):
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key == pygame.K_ESCAPE:
                    return "menu"

# ── Level Up Splash ─────────────────────────────
def show_level_up(level):
    screen.fill(DARK_BG)
    t1 = font_big.render(f"LEVEL {level}!", True, YELLOW)
    t2 = font_med.render("Speed increased!" if level < 5 else "MAX SPEED!", True, WHITE)
    screen.blit(t1, t1.get_rect(center=(W//2, H//2 - 30)))
    screen.blit(t2, t2.get_rect(center=(W//2, H//2 + 30)))
    if level >= 3:
        t3 = font_small.render("New obstacles placed!", True, GRAY)
        screen.blit(t3, t3.get_rect(center=(W//2, H//2 + 70)))
    pygame.display.flip()
    pygame.time.wait(1500)

# ──────────────────────────────────────────────
#  MAIN GAME LOOP
# ──────────────────────────────────────────────
def game_loop(player_id, personal_best_ref):
    snake     = [(COLS//2,   ROWS//2),
                 (COLS//2-1, ROWS//2),
                 (COLS//2-2, ROWS//2)]
    direction = (1, 0)
    next_dir  = (1, 0)

    level      = 1
    score      = 0
    food_count = 0
    fps        = LEVELS[level][0]

    obstacles  = []
    foods      = [spawn_food(snake, [], obstacles)]
    foods      = [f for f in foods if f]  # filter None

    last_food_spawn = pygame.time.get_ticks()
    SPAWN_INTERVAL  = 8000   # ms
    MAX_FOODS       = 4

    # Power-up state
    powerup_on_field   = None
    last_powerup_spawn = pygame.time.get_ticks()
    POWERUP_SPAWN_INT  = 15000

    active_powerup     = None   # name of active effect
    active_powerup_end = None   # ticks when effect ends (None for shield)

    shield_active      = False

    personal_best = personal_best_ref[0]

    while True:
        now = pygame.time.get_ticks()

        # ── Events ─────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP    and direction != (0,  1):
                    next_dir = (0, -1)
                if event.key == pygame.K_DOWN  and direction != (0, -1):
                    next_dir = (0,  1)
                if event.key == pygame.K_LEFT  and direction != (1,  0):
                    next_dir = (-1, 0)
                if event.key == pygame.K_RIGHT and direction != (-1, 0):
                    next_dir = (1,  0)
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_ESCAPE:
                    return score, level, "quit"

        direction = next_dir
        head      = snake[0]
        new_head  = (head[0]+direction[0], head[1]+direction[1])

        # ── Wall collision ──────────────────────
        wall_hit = (new_head[0] <= 0 or new_head[0] >= COLS-1 or
                    new_head[1] <= 0 or new_head[1] >= ROWS-1)
        if wall_hit:
            if shield_active:
                shield_active      = False
                active_powerup     = None
                active_powerup_end = None
                # teleport to opposite side (clamped)
                nx = max(1, min(COLS-2, new_head[0]))
                ny = max(1, min(ROWS-2, new_head[1]))
                new_head = (nx, ny)
                play_sound(SND_POWERUP)
            else:
                play_sound(SND_DIE)
                return score, level, "wall"

        # ── Self collision ──────────────────────
        if new_head in snake:
            if shield_active:
                shield_active      = False
                active_powerup     = None
                active_powerup_end = None
                play_sound(SND_POWERUP)
                # just don't move forward — skip this tick
                new_head = head
            else:
                play_sound(SND_DIE)
                return score, level, "self"

        # ── Obstacle collision ──────────────────
        if new_head in obstacles:
            if shield_active:
                shield_active      = False
                active_powerup     = None
                active_powerup_end = None
                play_sound(SND_POWERUP)
                new_head = head
            else:
                play_sound(SND_DIE)
                return score, level, "obstacle"

        snake.insert(0, new_head)

        # ── Food collision ──────────────────────
        ate = False
        for food in foods[:]:
            if new_head == food["pos"]:
                if food["poison"]:
                    # Shorten by 2
                    play_sound(SND_POISON)
                    for _ in range(2):
                        if len(snake) > 1:
                            snake.pop()
                    if len(snake) <= 1:
                        return score, level, "poison"
                else:
                    score      += food["value"]
                    food_count += 1
                    play_sound(SND_EAT)

                foods.remove(food)
                ate = True

                if len(foods) < 1:
                    nf = spawn_food(snake, foods, obstacles, powerup_on_field)
                    if nf:
                        foods.append(nf)

                if not food["poison"]:
                    foods_needed = LEVELS[level][1]
                    if food_count >= foods_needed and level < len(LEVELS):
                        level      += 1
                        food_count  = 0
                        fps         = LEVELS[level][0]
                        play_sound(SND_LEVELUP)
                        obstacles = generate_obstacles(level, snake, foods)
                        show_level_up(level)
                break

        if not ate:
            snake.pop()

        # ── Power-up collision ──────────────────
        if powerup_on_field and new_head == powerup_on_field["pos"]:
            play_sound(SND_POWERUP)
            pname = powerup_on_field["name"]
            if pname == "speed_boost":
                active_powerup     = pname
                active_powerup_end = now + powerup_on_field["duration"]
                fps = LEVELS[level][0] + 6
            elif pname == "slow_motion":
                active_powerup     = pname
                active_powerup_end = now + powerup_on_field["duration"]
                fps = max(3, LEVELS[level][0] - 4)
            elif pname == "shield":
                shield_active      = True
                active_powerup     = "shield"
                active_powerup_end = None
            powerup_on_field = None
            last_powerup_spawn = now

        # ── Expire active power-up ──────────────
        if active_powerup and active_powerup != "shield":
            if active_powerup_end and now >= active_powerup_end:
                fps            = LEVELS[level][0]
                active_powerup = None
                active_powerup_end = None

        # ── Expire power-up on field ────────────
        if powerup_on_field:
            if now - powerup_on_field["spawned_at"] >= POWERUP_FIELD_DURATION:
                powerup_on_field   = None
                last_powerup_spawn = now

        # ── Spawn new power-up ──────────────────
        if (powerup_on_field is None and
                now - last_powerup_spawn > POWERUP_SPAWN_INT):
            powerup_on_field   = spawn_powerup(snake, foods, obstacles)
            last_powerup_spawn = now

        # ── Update expiring foods ───────────────
        foods = update_foods(foods)
        if len(foods) == 0:
            nf = spawn_food(snake, foods, obstacles, powerup_on_field)
            if nf:
                foods.append(nf)

        # ── Periodic extra food spawn ───────────
        if (now - last_food_spawn > SPAWN_INTERVAL and
                len(foods) < MAX_FOODS):
            nf = spawn_food(snake, foods, obstacles, powerup_on_field)
            if nf:
                foods.append(nf)
            last_food_spawn = now

        # ── Update personal best live ───────────
        if score > personal_best:
            personal_best = score
            personal_best_ref[0] = score

        # ── Draw ────────────────────────────────
        screen.fill(DARK_BG)
        draw_grid()
        draw_walls()
        draw_obstacles(obstacles)
        draw_snake(snake, shield_active)
        draw_foods(foods)
        draw_powerup(powerup_on_field)
        draw_hud(score, level, food_count, LEVELS[level][1],
                 personal_best, active_powerup, active_powerup_end)
        draw_legend()
        pygame.display.flip()
        clock.tick(fps)

# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────
def main():
    db_ok = init_db()
    if not db_ok:
        print("[WARN] Database not available — leaderboard disabled.")

    username  = None
    player_id = None
    personal_best_ref = [0]

    while True:
        action = screen_main_menu()

        if action == "quit":
            pygame.quit(); sys.exit()

        elif action == "leaderboard":
            screen_leaderboard()

        elif action == "settings":
            screen_settings()

        elif action == "play":
            # Ask for username if not set
            if username is None:
                username, player_id = screen_enter_username()
                if username is None:
                    continue  # user pressed ESC
                if player_id and db_ok:
                    personal_best_ref[0] = get_personal_best(player_id)

            # Game loop (retry support)
            while True:
                score, level, reason = game_loop(player_id, personal_best_ref)

                # Save to DB
                if player_id and db_ok and reason != "quit":
                    save_game_session(player_id, score, level)
                    new_pb = get_personal_best(player_id)
                    personal_best_ref[0] = max(personal_best_ref[0], new_pb)

                if reason == "quit":
                    break

                outcome = screen_game_over(score, level, reason,
                                           personal_best_ref[0])
                if outcome == "retry":
                    continue
                else:  # "menu"
                    break


if __name__ == "__main__":
    main()