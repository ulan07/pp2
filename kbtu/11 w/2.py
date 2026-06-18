import pygame
import sys
import random
import time

pygame.init()

CELL = 20
COLS = 30
ROWS = 30
W    = CELL * COLS
H    = CELL * ROWS

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = (0,   200, 0)
DARK_GREEN = (0,   150, 0)
RED        = (220, 50,  50)
YELLOW     = (255, 220, 0)
GOLD       = (200, 160, 0)
GRAY       = (40,  40,  40)
DARK_BG    = (18,  18,  18)
SILVER     = (180, 180, 180)
PURPLE     = (180, 0,   220)

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

font_big   = pygame.font.SysFont("Arial", 48, bold=True)
font_med   = pygame.font.SysFont("Arial", 28)
font_small = pygame.font.SysFont("Arial", 20)
font_tiny  = pygame.font.SysFont("Arial", 13, bold=True)

LEVELS = {
    1: (7,  3),
    2: (10, 6),
    3: (13, 10),
    4: (16, 15),
    5: (20, 999),
}

FOOD_TYPES = [
    {"name": "normal", "color": RED,    "value": 1, "weight": 60, "timer": None},
    {"name": "bonus",  "color": YELLOW, "value": 3, "weight": 25, "timer": 5},
    {"name": "rare",   "color": PURPLE, "value": 5, "weight": 10, "timer": 3},
    {"name": "silver", "color": SILVER, "value": 2, "weight": 5,  "timer": 7},
]


def random_food_pos(snake, existing_foods):
    occupied = set(snake) | {f["pos"] for f in existing_foods}
    while True:
        x = random.randint(1, COLS - 2)
        y = random.randint(1, ROWS - 2)
        if (x, y) not in occupied:
            return (x, y)


def spawn_food(snake, existing_foods):
    chosen = random.choices(
        FOOD_TYPES,
        weights=[f["weight"] for f in FOOD_TYPES],
        k=1
    )[0]
    pos = random_food_pos(snake, existing_foods)
    return {
        "pos":        pos,
        "color":      chosen["color"],
        "value":      chosen["value"],
        "timer":      chosen["timer"],
        "name":       chosen["name"],
        "spawned_at": time.time(),
    }


def draw_grid():
    for x in range(0, W, CELL):
        pygame.draw.line(screen, (30, 30, 30), (x, 0), (x, H))
    for y in range(0, H, CELL):
        pygame.draw.line(screen, (30, 30, 30), (0, y), (W, y))


def draw_walls():
    for x in range(COLS):
        pygame.draw.rect(screen, GRAY, (x * CELL, 0, CELL, CELL))
        pygame.draw.rect(screen, GRAY, (x * CELL, (ROWS-1) * CELL, CELL, CELL))
    for y in range(ROWS):
        pygame.draw.rect(screen, GRAY, (0, y * CELL, CELL, CELL))
        pygame.draw.rect(screen, GRAY, ((COLS-1) * CELL, y * CELL, CELL, CELL))


def draw_snake(snake):
    for i, (x, y) in enumerate(snake):
        color = GREEN if i > 0 else DARK_GREEN
        pygame.draw.rect(screen, color,
                         (x*CELL+1, y*CELL+1, CELL-2, CELL-2),
                         border_radius=4)


def draw_foods(foods):
    now = time.time()
    for food in foods:
        x, y = food["pos"]
        cx   = x * CELL + CELL // 2
        cy   = y * CELL + CELL // 2
        color = food["color"]

        if food["timer"] is not None:
            elapsed   = now - food["spawned_at"]
            remaining = food["timer"] - elapsed
            if remaining < 2:
                if int(remaining / 0.3) % 2 == 0:
                    color = DARK_BG
            timer_txt = font_tiny.render(f"{remaining:.1f}", True, WHITE)
            screen.blit(timer_txt, (x * CELL, y * CELL - 14))

        pygame.draw.circle(screen, color, (cx, cy), CELL // 2 - 2)
        val_txt  = font_tiny.render(str(food["value"]), True, BLACK)
        val_rect = val_txt.get_rect(center=(cx, cy))
        screen.blit(val_txt, val_rect)


def update_foods(foods, snake):
    now   = time.time()
    alive = []
    for food in foods:
        if food["timer"] is not None:
            if now - food["spawned_at"] >= food["timer"]:
                continue
        alive.append(food)
    return alive


def draw_hud(score, level, food_count, foods_needed):
    score_txt = font_small.render(f"Score: {score}",                True, WHITE)
    level_txt = font_small.render(f"Level: {level}",                True, YELLOW)
    food_txt  = font_small.render(f"Food: {food_count}/{foods_needed}", True, GREEN)
    screen.blit(score_txt, (10,        8))
    screen.blit(level_txt, (W//2 - 40, 8))
    screen.blit(food_txt,  (W - 130,   8))


def draw_legend():
    x, y = 5, H - 80
    legend_title = font_tiny.render("FOOD TYPES:", True, GRAY)
    screen.blit(legend_title, (x, y))
    for i, ft in enumerate(FOOD_TYPES):
        timer_str = f"{ft['timer']}s" if ft["timer"] else "∞"
        txt = font_tiny.render(
            f"{ft['name']}  +{ft['value']}  [{timer_str}]", True, ft["color"])
        screen.blit(txt, (x, y + 14 + i * 14))


def show_screen(title, subtitle, color):
    screen.fill(DARK_BG)
    t1 = font_big.render(title,    True, color)
    t2 = font_med.render(subtitle, True, WHITE)
    t3 = font_small.render("SPACE — play again  |  Q — quit", True, GRAY)
    screen.blit(t1, t1.get_rect(center=(W//2, H//2 - 60)))
    screen.blit(t2, t2.get_rect(center=(W//2, H//2)))
    screen.blit(t3, t3.get_rect(center=(W//2, H//2 + 60)))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()


def show_level_up(level):
    screen.fill(DARK_BG)
    t1 = font_big.render(f"Level {level}!", True, YELLOW)
    t2 = font_med.render("Speed increased!", True, WHITE)
    screen.blit(t1, t1.get_rect(center=(W//2, H//2 - 30)))
    screen.blit(t2, t2.get_rect(center=(W//2, H//2 + 30)))
    pygame.display.flip()
    pygame.time.wait(1500)


def game_loop():
    snake     = [(COLS//2, ROWS//2),
                 (COLS//2 - 1, ROWS//2),
                 (COLS//2 - 2, ROWS//2)]
    direction = (1, 0)
    next_dir  = (1, 0)

    foods      = [spawn_food(snake, [])]
    score      = 0
    level      = 1
    food_count = 0
    fps        = LEVELS[level][0]

    last_spawn     = time.time()
    SPAWN_INTERVAL = 8
    MAX_FOODS      = 4

    while True:

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

        direction = next_dir
        head      = snake[0]
        new_head  = (head[0] + direction[0], head[1] + direction[1])

        if new_head[0] <= 0 or new_head[0] >= COLS - 1 or \
           new_head[1] <= 0 or new_head[1] >= ROWS - 1:
            return score, level, "wall"

        if new_head in snake:
            return score, level, "self"

        snake.insert(0, new_head)

        ate = False
        for food in foods[:]:
            if new_head == food["pos"]:
                score      += food["value"]
                food_count += 1
                foods.remove(food)
                ate = True

                if len(foods) < 1:
                    foods.append(spawn_food(snake, foods))

                foods_needed = LEVELS[level][1]
                if food_count >= foods_needed and level < len(LEVELS):
                    level      += 1
                    food_count  = 0
                    fps         = LEVELS[level][0]
                    show_level_up(level)
                break

        if not ate:
            snake.pop()

        foods = update_foods(foods, snake)

        if len(foods) == 0:
            foods.append(spawn_food(snake, foods))

        now = time.time()
        if now - last_spawn > SPAWN_INTERVAL and len(foods) < MAX_FOODS:
            foods.append(spawn_food(snake, foods))
            last_spawn = now

        screen.fill(DARK_BG)
        draw_grid()
        draw_walls()
        draw_snake(snake)
        draw_foods(foods)
        draw_hud(score, level, food_count, LEVELS[level][1])
        draw_legend()

        pygame.display.flip()
        clock.tick(fps)


while True:
    show_screen("SNAKE", "Press SPACE to start", GREEN)
    score, level, reason = game_loop()

    if reason == "wall":
        msg = f"Hit the wall!   Score: {score}   Level: {level}"
    else:
        msg = f"Hit yourself!   Score: {score}   Level: {level}"

    show_screen("Game Over", msg, RED)