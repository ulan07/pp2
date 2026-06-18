import pygame, sys
from pygame.locals import *
import random, time

pygame.init()

FPS = 60
FramePerSec = pygame.time.Clock()

RED    = (255, 0,   0)
BLUE   = (0,   0,   255)
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
YELLOW = (255, 215, 0)
GOLD   = (200, 160, 0)
SILVER = (180, 180, 180)
BRONZE = (180, 100, 30)
GREEN  = (0,   200, 0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
SPEED  = 5
SCORE  = 0
COINS  = 0

COIN_THRESHOLD = 5

font       = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 18)
game_over  = font.render("Game Over", True, BLACK)

try:
    background = pygame.image.load("AnimatedStreet.png")
except:
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((60, 60, 60))
    for i in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.rect(background, WHITE, (195, i, 10, 25))

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Racer")


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.image = pygame.image.load("Enemy.png")
        except:
            self.image = pygame.Surface((40, 60))
            self.image.fill(RED)
            pygame.draw.rect(self.image, BLACK, (5, 10, 30, 40), 2)
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        global SCORE
        self.rect.move_ip(0, SPEED)
        if self.rect.top > SCREEN_HEIGHT:
            SCORE += 1
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.image = pygame.image.load("Player.png")
        except:
            self.image = pygame.Surface((40, 60))
            self.image.fill(BLUE)
            pygame.draw.rect(self.image, BLACK, (5, 10, 30, 40), 2)
        self.rect = self.image.get_rect()
        self.rect.center = (160, 520)

    def move(self):
        pressed_keys = pygame.key.get_pressed()
        if self.rect.left > 0:
            if pressed_keys[K_LEFT]:
                self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH:
            if pressed_keys[K_RIGHT]:
                self.rect.move_ip(5, 0)


class Coin(pygame.sprite.Sprite):
    TYPES = [
        {"name": "bronze", "color": BRONZE, "outline": (120, 60, 10),   "value": 1, "weight": 60, "radius": 10},
        {"name": "silver", "color": SILVER, "outline": (120, 120, 120), "value": 3, "weight": 30, "radius": 13},
        {"name": "gold",   "color": YELLOW, "outline": GOLD,            "value": 5, "weight": 10, "radius": 16},
    ]

    def __init__(self):
        super().__init__()
        chosen = random.choices(
            self.TYPES,
            weights=[t["weight"] for t in self.TYPES],
            k=1
        )[0]

        self.value  = chosen["value"]
        self.radius = chosen["radius"]

        size = self.radius * 2 + 4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)

        pygame.draw.circle(self.image, chosen["color"],  center, self.radius)
        pygame.draw.circle(self.image, chosen["outline"], center, self.radius, 2)

        font_coin = pygame.font.SysFont("Verdana", self.radius - 2, bold=True)
        label = font_coin.render(str(self.value), True, chosen["outline"])
        lrect = label.get_rect(center=center)
        self.image.blit(label, lrect)

        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    def move(self):
        self.rect.move_ip(0, max(SPEED - 1, 3))
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


P1 = Player()
E1 = Enemy()

enemies     = pygame.sprite.Group()
coins       = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

enemies.add(E1)
all_sprites.add(P1)
all_sprites.add(E1)

INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

ADD_COIN = pygame.USEREVENT + 2
pygame.time.set_timer(ADD_COIN, 2500)

next_coin_threshold = COIN_THRESHOLD

while True:

    for event in pygame.event.get():
        if event.type == INC_SPEED:
            SPEED += 0.3
        if event.type == ADD_COIN:
            new_coin = Coin()
            coins.add(new_coin)
            all_sprites.add(new_coin)
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    DISPLAYSURF.blit(background, (0, 0))

    score_txt = font_small.render(f"Score: {SCORE}", True, BLACK)
    DISPLAYSURF.blit(score_txt, (10, 10))

    coin_txt = font_small.render(f"Coins: {COINS}", True, GOLD)
    DISPLAYSURF.blit(coin_txt, (SCREEN_WIDTH - 110, 10))

    threshold_txt = font_small.render(f"Speed up at {next_coin_threshold} coins", True, BLACK)
    DISPLAYSURF.blit(threshold_txt, (SCREEN_WIDTH//2 - 90, 10))

    for entity in all_sprites:
        DISPLAYSURF.blit(entity.image, entity.rect)
        entity.move()

    collected = pygame.sprite.spritecollide(P1, coins, True)
    for coin in collected:
        COINS += coin.value

    if COINS >= next_coin_threshold:
        SPEED += 1.5
        next_coin_threshold += COIN_THRESHOLD

    if pygame.sprite.spritecollideany(P1, enemies):
        try:
            pygame.mixer.Sound('crash.wav').play()
        except:
            pass
        time.sleep(0.5)

        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over, (30, 200))

        final_score = font_small.render(f"Score: {SCORE}", True, BLACK)
        final_coins = font_small.render(f"Coins: {COINS}", True, GOLD)
        final_speed = font_small.render(f"Max speed: {SPEED:.1f}", True, BLACK)

        DISPLAYSURF.blit(final_score, (160, 310))
        DISPLAYSURF.blit(final_coins, (160, 335))
        DISPLAYSURF.blit(final_speed, (160, 360))

        pygame.display.update()

        for entity in all_sprites:
            entity.kill()

        time.sleep(2)
        pygame.quit()
        sys.exit()

    pygame.display.update()
    FramePerSec.tick(FPS)