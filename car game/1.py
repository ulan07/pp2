import pygame, sys, random, time, json, os, math
from pygame.locals import *

pygame.init()

SW, SH = 480, 700
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Racer")
clock = pygame.time.Clock()
FPS = 60

# ── Colours ──────────────────────────────────────────────
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
GRAY   = (80,  80,  80)
LGRAY  = (160, 160, 160)
DGRAY  = (30,  30,  30)
RED    = (220, 50,  50)
GREEN  = (0,   200, 80)
BLUE   = (50,  120, 220)
YELLOW = (255, 220, 0)
GOLD   = (200, 160, 0)
ORANGE = (255, 140, 0)
CYAN   = (0,   220, 220)
PURPLE = (180, 0,   220)
ROAD   = (50,  50,  50)
LANE_C = (200, 200, 200)

# ── Fonts ────────────────────────────────────────────────
F64 = pygame.font.SysFont("Arial", 64, bold=True)
F36 = pygame.font.SysFont("Arial", 36, bold=True)
F28 = pygame.font.SysFont("Arial", 28, bold=True)
F20 = pygame.font.SysFont("Arial", 20)
F16 = pygame.font.SysFont("Arial", 16)

# ── Files ────────────────────────────────────────────────
LB_FILE  = "leaderboard.json"
SET_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "blue",
    "difficulty": "normal",
}

CAR_COLORS = {
    "blue":   BLUE,
    "red":    RED,
    "green":  GREEN,
    "yellow": YELLOW,
}

DIFF = {
    "easy":   {"enemy_start": 3, "inc": 0.2, "coin_thresh": 8},
    "normal": {"enemy_start": 5, "inc": 0.3, "coin_thresh": 5},
    "hard":   {"enemy_start": 7, "inc": 0.5, "coin_thresh": 3},
}

# ── Road layout ──────────────────────────────────────────
ROAD_X = 60
ROAD_W = SW - 120
LANES  = 4
LANE_W = ROAD_W // LANES


def lane_cx(lane):
    return ROAD_X + lane * LANE_W + LANE_W // 2


# ═════════════════════════════════════════════════════════
#  Persistence helpers
# ═════════════════════════════════════════════════════════
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return default.copy() if isinstance(default, dict) else list(default)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def save_score(name, score, distance):
    lb = load_json(LB_FILE, [])
    lb.append({"name": name, "score": score, "distance": int(distance)})
    lb.sort(key=lambda x: x["score"], reverse=True)
    lb = lb[:10]
    save_json(LB_FILE, lb)


# ═════════════════════════════════════════════════════════
#  Drawing helpers
# ═════════════════════════════════════════════════════════
def txt(surface, text, font, color, cx, cy):
    s = font.render(str(text), True, color)
    r = s.get_rect(center=(cx, cy))
    surface.blit(s, r)
    return r


def button(surface, text, font, rect, col_bg, col_txt, col_border=None):
    pygame.draw.rect(surface, col_bg, rect, border_radius=10)
    if col_border:
        pygame.draw.rect(surface, col_border, rect, 2, border_radius=10)
    txt(surface, text, font, col_txt, rect.centerx, rect.centery)


def is_clicked(rect, events):
    for e in events:
        if e.type == MOUSEBUTTONDOWN and e.button == 1:
            if rect.collidepoint(e.pos):
                return True
    return False


# ═════════════════════════════════════════════════════════
#  Sprites
# ═════════════════════════════════════════════════════════
class Car(pygame.sprite.Sprite):
    W, H = 36, 60

    def __init__(self, lane, y, color, is_player=False):
        super().__init__()
        self.image = pygame.Surface((self.W, self.H), SRCALPHA)
        self._color = color
        self._draw(color)
        self.rect  = self.image.get_rect()
        self.lane  = lane
        self.rect.centerx = lane_cx(lane)
        self.rect.centery  = y
        self.is_player = is_player
        self.speed = 0

    def _draw(self, color):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, color,
                         (4, 8, self.W-8, self.H-16), border_radius=6)
        pygame.draw.rect(self.image, (30, 30, 30),
                         (4, 8, self.W-8, self.H-16), 2, border_radius=6)
        pygame.draw.rect(self.image, CYAN,   (7,  12, 22, 12), border_radius=3)
        pygame.draw.rect(self.image, YELLOW, (4,  self.H-50, 10, 8), border_radius=2)
        pygame.draw.rect(self.image, YELLOW, (self.W-14, self.H-50, 10, 8), border_radius=2)

    def set_color(self, color):
        self._color = color
        self._draw(color)

    def move_lane(self, delta):
        new = self.lane + delta
        if 0 <= new < LANES:
            self.lane = new
            self.rect.centerx = lane_cx(self.lane)

    def update(self):
        if not self.is_player:
            self.rect.y += int(self.speed)
        self.rect.centerx = lane_cx(self.lane)


class Obstacle(pygame.sprite.Sprite):
    KINDS = {
        "oil":    (PURPLE, "OIL",   30, 16, False),
        "bump":   (LGRAY,  "BUMP",  40, 12, False),
        "pothole":(DGRAY,  "HOLE",  28, 28, False),
        "barrier":(ORANGE, "|||",   50, 20, True),
    }

    def __init__(self, lane, speed, kind=None):
        super().__init__()
        self.kind = kind or random.choice(list(self.KINDS))
        col, label, w, h, self.moving = self.KINDS[self.kind]
        self.image = pygame.Surface((w, h), SRCALPHA)
        pygame.draw.rect(self.image, col, (0, 0, w, h), border_radius=4)
        lbl = F16.render(label, True, WHITE)
        self.image.blit(lbl, lbl.get_rect(center=(w//2, h//2)))
        self.rect  = self.image.get_rect()
        self.lane  = lane
        self.rect.centerx = lane_cx(lane)
        self.rect.top = -h
        self.speed = speed
        self.dir   = 1

    def update(self):
        self.rect.y += int(self.speed)
        if self.moving:
            self.lane += self.dir * 0.02
            if self.lane >= LANES - 0.5 or self.lane <= 0.5:
                self.dir *= -1
            self.rect.centerx = int(lane_cx(int(self.lane)))


class HazardZone(pygame.sprite.Sprite):
    def __init__(self, lane, speed, kind="oil"):
        super().__init__()
        colors = {"oil": (100, 0, 180, 120), "slow": (0, 120, 200, 100)}
        col = colors.get(kind, (100, 0, 180, 120))
        self.image = pygame.Surface((LANE_W - 4, 40), SRCALPHA)
        self.image.fill(col)
        label = F16.render("SLOW" if kind == "slow" else "OIL", True, WHITE)
        self.image.blit(label, label.get_rect(center=(self.image.get_width()//2, 20)))
        self.rect  = self.image.get_rect()
        self.rect.centerx = lane_cx(lane)
        self.rect.top = -40
        self.speed = speed
        self.kind  = kind

    def update(self):
        self.rect.y += int(self.speed)


class Coin(pygame.sprite.Sprite):
    TYPES = [
        {"value": 1, "weight": 60, "color": (180, 100, 30), "r": 10},
        {"value": 3, "weight": 30, "color": LGRAY,           "r": 12},
        {"value": 5, "weight": 10, "color": YELLOW,          "r": 14},
    ]

    def __init__(self, lane, speed):
        super().__init__()
        ct = random.choices(self.TYPES,
                            weights=[t["weight"] for t in self.TYPES])[0]
        self.value = ct["value"]
        r = ct["r"]
        self.image = pygame.Surface((r*2, r*2), SRCALPHA)
        pygame.draw.circle(self.image, ct["color"], (r, r), r)
        pygame.draw.circle(self.image, BLACK, (r, r), r, 1)
        lbl = F16.render(str(ct["value"]), True, BLACK)
        self.image.blit(lbl, lbl.get_rect(center=(r, r)))
        self.rect  = self.image.get_rect()
        self.rect.centerx = lane_cx(lane)
        self.rect.top = -r*2
        self.speed = speed

    def update(self):
        self.rect.y += int(self.speed)


class PowerUp(pygame.sprite.Sprite):
    KINDS = {
        "nitro":  (ORANGE, "N", 5),
        "shield": (CYAN,   "S", 0),
        "repair": (GREEN,  "R", 0),
    }

    def __init__(self, lane, speed):
        super().__init__()
        self.kind = random.choice(list(self.KINDS))
        col, label, self.duration = self.KINDS[self.kind]
        self.image = pygame.Surface((32, 32), SRCALPHA)
        pygame.draw.polygon(self.image, col,
                            [(16, 0), (32, 12), (26, 32), (6, 32), (0, 12)])
        lbl = F20.render(label, True, WHITE)
        self.image.blit(lbl, lbl.get_rect(center=(16, 16)))
        self.rect = self.image.get_rect()
        self.rect.centerx = lane_cx(lane)
        self.rect.top = -32
        self.speed = speed
        self.spawned = time.time()

    def update(self):
        self.rect.y += int(self.speed)


class RoadEvent(pygame.sprite.Sprite):
    def __init__(self, speed, kind="nitro_strip"):
        super().__init__()
        self.kind = kind
        if kind == "nitro_strip":
            self.image = pygame.Surface((ROAD_W, 16), SRCALPHA)
            self.image.fill((255, 140, 0, 160))
            lbl = F16.render("NITRO BOOST!", True, WHITE)
            self.image.blit(lbl, lbl.get_rect(center=(ROAD_W//2, 8)))
        else:
            self.image = pygame.Surface((ROAD_W, 12), SRCALPHA)
            self.image.fill((140, 140, 140, 200))
            lbl = F16.render("SPEED BUMP", True, BLACK)
            self.image.blit(lbl, lbl.get_rect(center=(ROAD_W//2, 6)))
        self.rect = self.image.get_rect()
        self.rect.x   = ROAD_X
        self.rect.top = -20
        self.speed = speed

    def update(self):
        self.rect.y += int(self.speed)


# ═════════════════════════════════════════════════════════
#  Road scroll
# ═════════════════════════════════════════════════════════
class Road:
    def __init__(self):
        self.offset = 0
        self.stripe_h = 60

    def update(self, speed):
        self.offset = (self.offset + speed) % self.stripe_h

    def draw(self, surface):
        pygame.draw.rect(surface, ROAD, (ROAD_X, 0, ROAD_W, SH))
        for lane in range(1, LANES):
            x = ROAD_X + lane * LANE_W
            y = -self.stripe_h + self.offset
            while y < SH:
                pygame.draw.rect(surface, LANE_C, (x - 1, y, 3, 30))
                y += self.stripe_h
        pygame.draw.rect(surface, WHITE, (ROAD_X - 3, 0, 3, SH))
        pygame.draw.rect(surface, WHITE, (ROAD_X + ROAD_W, 0, 3, SH))


# ═════════════════════════════════════════════════════════
#  HUD
# ═════════════════════════════════════════════════════════
def draw_hud(surface, score, coins, distance, finish,
             active_pu, pu_end, shield, speed):
    pygame.draw.rect(surface, DGRAY, (0, 0, ROAD_X, SH))
    pygame.draw.rect(surface, DGRAY, (ROAD_X + ROAD_W + 3, 0, SW, SH))

    left_x = ROAD_X // 2
    txt(surface, "SCR",   F16, LGRAY,  left_x, 30)
    txt(surface, score,   F20, WHITE,  left_x, 50)
    txt(surface, "COIN",  F16, GOLD,   left_x, 80)
    txt(surface, coins,   F20, YELLOW, left_x, 100)
    txt(surface, "DIST",  F16, LGRAY,  left_x, 130)
    txt(surface, f"{int(distance)}m", F16, WHITE, left_x, 150)
    txt(surface, "LEFT",  F16, LGRAY,  left_x, 180)
    remaining = max(0, finish - distance)
    txt(surface, f"{int(remaining)}m", F16, GREEN if remaining > 0 else YELLOW, left_x, 200)

    right_x = ROAD_X + ROAD_W + (SW - ROAD_X - ROAD_W) // 2
    txt(surface, "SPD",   F16, LGRAY,  right_x, 30)
    txt(surface, f"{speed:.0f}", F20, ORANGE, right_x, 50)

    if shield:
        txt(surface, "🛡", F20, CYAN, right_x, 90)

    if active_pu:
        col = {"nitro": ORANGE, "shield": CYAN, "repair": GREEN}.get(active_pu, WHITE)
        txt(surface, active_pu[:3].upper(), F16, col,   right_x, 130)
        remaining_t = max(0, pu_end - time.time())
        txt(surface, f"{remaining_t:.1f}s", F16, WHITE, right_x, 150)


# ═════════════════════════════════════════════════════════
#  Username entry screen
# ═════════════════════════════════════════════════════════
def screen_username():
    name = ""
    cursor_vis = True
    cursor_timer = 0

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_RETURN and name.strip():
                    return name.strip()
                elif e.key == K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 16 and e.unicode.isprintable():
                    name += e.unicode

        cursor_timer += clock.get_time()
        if cursor_timer > 500:
            cursor_vis = not cursor_vis
            cursor_timer = 0

        screen.fill(DGRAY)
        txt(screen, "ENTER YOUR NAME", F36, WHITE, SW//2, SH//2 - 80)
        box = pygame.Rect(SW//2 - 150, SH//2 - 30, 300, 50)
        pygame.draw.rect(screen, GRAY, box, border_radius=8)
        pygame.draw.rect(screen, WHITE, box, 2, border_radius=8)
        display = name + ("|" if cursor_vis else "")
        txt(screen, display, F28, WHITE, SW//2, SH//2 - 5)
        txt(screen, "Press ENTER to continue", F16, LGRAY, SW//2, SH//2 + 50)
        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════
#  Settings screen
# ═════════════════════════════════════════════════════════
def screen_settings(settings):
    colors_list = list(CAR_COLORS.keys())
    diffs_list  = ["easy", "normal", "hard"]

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                save_json(SET_FILE, settings)
                return settings

        screen.fill(DGRAY)
        txt(screen, "SETTINGS", F36, WHITE, SW//2, 60)

        # Sound toggle
        r_snd = pygame.Rect(SW//2 - 100, 130, 200, 44)
        snd_lbl = "Sound: ON" if settings["sound"] else "Sound: OFF"
        snd_col = GREEN if settings["sound"] else RED
        button(screen, snd_lbl, F20, r_snd, GRAY, snd_col, WHITE)
        if is_clicked(r_snd, events):
            settings["sound"] = not settings["sound"]

        # Car color
        txt(screen, "Car Color:", F20, LGRAY, SW//2, 220)
        for i, c in enumerate(colors_list):
            rx = SW//2 - 180 + i * 90
            r_col = pygame.Rect(rx, 240, 80, 36)
            border = WHITE if settings["car_color"] == c else None
            button(screen, c.capitalize(), F16, r_col, CAR_COLORS[c], BLACK, border)
            if is_clicked(r_col, events):
                settings["car_color"] = c

        # Difficulty
        txt(screen, "Difficulty:", F20, LGRAY, SW//2, 320)
        for i, d in enumerate(diffs_list):
            rx = SW//2 - 165 + i * 110
            r_dif = pygame.Rect(rx, 340, 100, 36)
            border = WHITE if settings["difficulty"] == d else None
            button(screen, d.capitalize(), F16, r_dif, GRAY, WHITE, border)
            if is_clicked(r_dif, events):
                settings["difficulty"] = d

        r_back = pygame.Rect(SW//2 - 80, SH - 100, 160, 44)
        button(screen, "Back", F28, r_back, GRAY, WHITE, WHITE)
        if is_clicked(r_back, events):
            save_json(SET_FILE, settings)
            return settings

        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════
#  Leaderboard screen
# ═════════════════════════════════════════════════════════
def screen_leaderboard():
    lb = load_json(LB_FILE, [])
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                return

        screen.fill(DGRAY)
        txt(screen, "LEADERBOARD", F36, YELLOW, SW//2, 50)

        headers = ["#", "Name", "Score", "Dist"]
        xs = [40, 110, 310, 410]
        for hx, h in zip(xs, headers):
            txt(screen, h, F16, LGRAY, hx, 95)

        pygame.draw.line(screen, LGRAY, (20, 108), (SW - 20, 108), 1)

        for i, entry in enumerate(lb):
            y = 125 + i * 48
            col = YELLOW if i == 0 else (LGRAY if i >= 3 else WHITE)
            txt(screen, f"{i+1}", F20, col, xs[0], y)
            txt(screen, entry["name"][:10], F20, col, xs[1]+30, y)
            txt(screen, entry["score"],     F20, col, xs[2], y)
            txt(screen, f'{entry["distance"]}m', F20, col, xs[3], y)

        r_back = pygame.Rect(SW//2 - 80, SH - 80, 160, 44)
        button(screen, "Back", F28, r_back, GRAY, WHITE, WHITE)
        if is_clicked(r_back, events):
            return

        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════
#  Main menu
# ═════════════════════════════════════════════════════════
def screen_menu():
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == QUIT:
                pygame.quit(); sys.exit()

        screen.fill(DGRAY)
        txt(screen, "RACER", F64, YELLOW, SW//2, 110)
        txt(screen, "Arcade Edition", F20, LGRAY, SW//2, 165)

        btns = [
            ("Play",        GREEN,  280),
            ("Leaderboard", BLUE,   350),
            ("Settings",    GRAY,   420),
            ("Quit",        RED,    490),
        ]
        rects = {}
        for label, col, y in btns:
            r = pygame.Rect(SW//2 - 110, y, 220, 50)
            button(screen, label, F28, r, col, WHITE)
            rects[label] = r

        for label, r in rects.items():
            if is_clicked(r, events):
                return label

        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════
#  Game Over screen
# ═════════════════════════════════════════════════════════
def screen_game_over(score, distance, coins):
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == QUIT:
                pygame.quit(); sys.exit()

        screen.fill(DGRAY)
        txt(screen, "GAME OVER", F64, RED, SW//2, 120)
        txt(screen, f"Score:    {score}",       F28, WHITE,  SW//2, 220)
        txt(screen, f"Distance: {int(distance)}m", F28, WHITE,  SW//2, 265)
        txt(screen, f"Coins:    {coins}",       F28, YELLOW, SW//2, 310)

        r_retry = pygame.Rect(SW//2 - 130, 400, 120, 50)
        r_menu  = pygame.Rect(SW//2 + 10,  400, 120, 50)
        button(screen, "Retry",     F28, r_retry, GREEN, WHITE)
        button(screen, "Main Menu", F20, r_menu,  GRAY,  WHITE)

        if is_clicked(r_retry, events):
            return "retry"
        if is_clicked(r_menu, events):
            return "menu"

        pygame.display.flip()
        clock.tick(60)


# ═════════════════════════════════════════════════════════
#  GAME LOOP
# ═════════════════════════════════════════════════════════
def run_game(username, settings):
    diff   = DIFF[settings["difficulty"]]
    p_col  = CAR_COLORS[settings["car_color"]]

    road   = Road()
    player = Car(lane=1, y=SH - 100, color=p_col, is_player=True)

    all_sprites = pygame.sprite.Group()
    enemies     = pygame.sprite.Group()
    obstacles   = pygame.sprite.Group()
    hazards     = pygame.sprite.Group()
    coins_grp   = pygame.sprite.Group()
    powerups    = pygame.sprite.Group()
    events_grp  = pygame.sprite.Group()

    all_sprites.add(player)

    speed       = float(diff["enemy_start"])
    scroll_spd  = speed * 1.5
    score       = 0
    coins_total = 0
    distance    = 0.0
    FINISH      = 2000.0

    shield_active = False
    active_pu     = None
    pu_end        = 0.0

    next_coin_thresh = diff["coin_thresh"]

    timers = {
        "enemy":   time.time(),
        "obs":     time.time(),
        "hazard":  time.time(),
        "coin":    time.time(),
        "powerup": time.time(),
        "event":   time.time(),
        "score":   time.time(),
        "inc":     time.time(),
    }

    def safe_lane(exclude_lane):
        choices = [l for l in range(LANES) if l != player.lane]
        return random.choice(choices) if choices else random.randint(0, LANES-1)

    running = True
    while running:
        dt     = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for e in events:
            if e.type == QUIT:
                pygame.quit(); sys.exit()
            if e.type == KEYDOWN:
                if e.key in (K_LEFT, K_a):
                    player.move_lane(-1)
                if e.key in (K_RIGHT, K_d):
                    player.move_lane(1)
                if e.key == K_ESCAPE:
                    running = False

        now = time.time()

        # ── Speed increase every second ─────────────────
        if now - timers["inc"] > 1.0:
            speed      = min(speed + diff["inc"], 25)
            scroll_spd = speed * 1.5
            timers["inc"] = now

        # ── Score tick ──────────────────────────────────
        if now - timers["score"] > 0.5:
            score += 1
            timers["score"] = now

        # ── Distance ────────────────────────────────────
        distance += scroll_spd * dt

        # ── Spawn enemy ─────────────────────────────────
        enemy_interval = max(0.6, 2.5 - distance / 600)
        if now - timers["enemy"] > enemy_interval:
            lane = safe_lane(player.lane)
            e_car = Car(lane=lane, y=-70,
                        color=random.choice([RED, ORANGE, PURPLE]), is_player=False)
            e_car.speed = speed
            enemies.add(e_car)
            all_sprites.add(e_car)
            timers["enemy"] = now

        # ── Spawn obstacle ──────────────────────────────
        obs_interval = max(1.0, 4.0 - distance / 500)
        if now - timers["obs"] > obs_interval:
            lane = safe_lane(player.lane)
            ob = Obstacle(lane, speed)
            obstacles.add(ob)
            all_sprites.add(ob)
            timers["obs"] = now

        # ── Spawn lane hazard ───────────────────────────
        if now - timers["hazard"] > 5.0:
            lane = safe_lane(player.lane)
            kind = random.choice(["oil", "slow"])
            hz = HazardZone(lane, speed, kind)
            hazards.add(hz)
            all_sprites.add(hz)
            timers["hazard"] = now

        # ── Spawn coin ──────────────────────────────────
        if now - timers["coin"] > 2.0:
            lane = random.randint(0, LANES - 1)
            c = Coin(lane, speed)
            coins_grp.add(c)
            all_sprites.add(c)
            timers["coin"] = now

        # ── Spawn power-up ──────────────────────────────
        if now - timers["powerup"] > 8.0:
            lane = random.randint(0, LANES - 1)
            pu = PowerUp(lane, speed)
            powerups.add(pu)
            all_sprites.add(pu)
            timers["powerup"] = now

        # ── Spawn road event ────────────────────────────
        if now - timers["event"] > 10.0:
            kind = random.choice(["nitro_strip", "speed_bump"])
            ev = RoadEvent(speed, kind)
            events_grp.add(ev)
            all_sprites.add(ev)
            timers["event"] = now

        # ── Remove off-screen sprites ───────────────────
        for grp in (enemies, obstacles, hazards, coins_grp, powerups, events_grp):
            for sp in list(grp):
                if sp.rect.top > SH + 60:
                    sp.kill()

        # ── Power-up timeout (10 s uncollected) ─────────
        for pu in list(powerups):
            if now - pu.spawned > 10:
                pu.kill()

        # ── Active power-up expiry ───────────────────────
        if active_pu and now > pu_end:
            if active_pu == "nitro":
                speed = max(speed - 4, diff["enemy_start"])
            active_pu = None

        # ── Update ──────────────────────────────────────
        road.update(scroll_spd)
        enemies.update()
        obstacles.update()
        hazards.update()
        coins_grp.update()
        powerups.update()
        events_grp.update()

        # ── Collect coins ────────────────────────────────
        hit_coins = pygame.sprite.spritecollide(player, coins_grp, True)
        for c in hit_coins:
            coins_total += c.value
            score       += c.value * 5

        # ── Coin threshold speed boost ───────────────────
        if coins_total >= next_coin_thresh:
            speed += 1.5
            next_coin_thresh += diff["coin_thresh"]

        # ── Collect power-ups ────────────────────────────
        hit_pu = pygame.sprite.spritecollide(player, powerups, True)
        for pu in hit_pu:
            if active_pu is None:
                active_pu = pu.kind
                if pu.kind == "nitro":
                    speed  += 4
                    pu_end  = now + pu.duration
                elif pu.kind == "shield":
                    shield_active = True
                    pu_end        = now + 999
                elif pu.kind == "repair":
                    pass

        # ── Road events effect ───────────────────────────
        hit_ev = pygame.sprite.spritecollide(player, events_grp, False)
        for ev in hit_ev:
            if ev.kind == "nitro_strip" and active_pu != "nitro":
                speed = min(speed + 2, 28)
            elif ev.kind == "speed_bump":
                speed = max(speed - 1, 2)

        # ── Hazard effect ────────────────────────────────
        hit_hz = pygame.sprite.spritecollide(player, hazards, True)
        for hz in hit_hz:
            if hz.kind == "slow":
                speed = max(speed - 1.5, 2)

        # ── Collision with enemy ─────────────────────────
        hit_enemy = pygame.sprite.spritecollide(player, enemies, True)
        if hit_enemy:
            if shield_active:
                shield_active = False
                active_pu     = None
            else:
                return score, distance, coins_total

        # ── Collision with obstacle ──────────────────────
        hit_obs = pygame.sprite.spritecollide(player, obstacles, True)
        if hit_obs:
            if active_pu == "repair":
                active_pu = None
            elif shield_active:
                shield_active = False
                active_pu     = None
            else:
                return score, distance, coins_total

        # ── Finish ──────────────────────────────────────
        if distance >= FINISH:
            score += 500
            return score, distance, coins_total

        # ── Draw ────────────────────────────────────────
        screen.fill(BLACK)
        road.draw(screen)
        events_grp.draw(screen)
        hazards.draw(screen)
        coins_grp.draw(screen)
        powerups.draw(screen)
        obstacles.draw(screen)
        enemies.draw(screen)
        screen.blit(player.image, player.rect)
        draw_hud(screen, score, coins_total, distance, FINISH,
                 active_pu, pu_end, shield_active, scroll_spd)

        pygame.display.flip()

    return score, distance, coins_total


# ═════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════
def main():
    settings = load_json(SET_FILE, DEFAULT_SETTINGS)
    username = None

    while True:
        choice = screen_menu()

        if choice == "Quit":
            pygame.quit(); sys.exit()

        elif choice == "Leaderboard":
            screen_leaderboard()

        elif choice == "Settings":
            settings = screen_settings(settings)

        elif choice == "Play":
            if username is None:
                username = screen_username()

            while True:
                score, distance, coins = run_game(username, settings)
                save_score(username, score, distance)
                result = screen_game_over(score, distance, coins)
                if result == "retry":
                    continue
                else:
                    break


main()