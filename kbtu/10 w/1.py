import pygame, sys
from pygame.locals import *
import random, time

pygame.init()

FPS = 60
FramePerSec = pygame.time.Clock()

BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
SPEED = 5
SCORE = 0
COINS = 0

font       = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
game_over  = font.render("Game Over", True, BLACK)

# Фон — если нет файла, рисуем серую дорогу
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
        # Если нет картинки — рисуем красную машину
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
        # Если нет картинки — рисуем синюю машину
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
    def __init__(self):
        super().__init__()
        # Рисуем жёлтую монету
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (10, 10), 10)
        pygame.draw.circle(self.image, (200, 160, 0), (10, 10), 10, 2)
        font_coin = pygame.font.SysFont("Verdana", 10, bold=True)
        symbol = font_coin.render("$", True, (150, 100, 0))
        self.image.blit(symbol, (5, 3))
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    def move(self):
        self.rect.move_ip(0, SPEED)
        # Если монета уехала за экран — перемещаем наверх
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)


# Создаём объекты
P1 = Player()
E1 = Enemy()
C1 = Coin()

# Группы спрайтов
enemies     = pygame.sprite.Group()
coins       = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

enemies.add(E1)
coins.add(C1)
all_sprites.add(P1)
all_sprites.add(E1)
all_sprites.add(C1)

# Событие увеличения скорости каждую секунду
INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

# Событие появления новой монеты каждые 3 секунды
ADD_COIN = pygame.USEREVENT + 2
pygame.time.set_timer(ADD_COIN, 3000)

# Главный игровой цикл
while True:

    for event in pygame.event.get():

        if event.type == INC_SPEED:
            SPEED += 0.5

        if event.type == ADD_COIN:
            # Добавляем новую монету случайно
            if random.random() > 0.3:
                new_coin = Coin()
                coins.add(new_coin)
                all_sprites.add(new_coin)

        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Рисуем фон
    DISPLAYSURF.blit(background, (0, 0))

    # Счёт слева сверху
    scores = font_small.render(f"Score: {SCORE}", True, BLACK)
    DISPLAYSURF.blit(scores, (10, 10))

    # Монеты справа сверху
    coin_text = font_small.render(f"Coins: {COINS}", True, (180, 130, 0))
    DISPLAYSURF.blit(coin_text, (SCREEN_WIDTH - 110, 10))

    # Двигаем и рисуем все спрайты
    for entity in all_sprites:
        DISPLAYSURF.blit(entity.image, entity.rect)
        entity.move()

    # Проверка: игрок собрал монету
    collected = pygame.sprite.spritecollide(P1, coins, True)
    for coin in collected:
        COINS += 1

    # Проверка: столкновение с врагом
    if pygame.sprite.spritecollideany(P1, enemies):
        try:
            pygame.mixer.Sound('crash.wav').play()
        except:
            pass
        time.sleep(0.5)

        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over, (30, 220))

        final_score = font_small.render(f"Score: {SCORE}", True, BLACK)
        final_coins = font_small.render(f"Coins collected: {COINS}", True, (180, 130, 0))
        DISPLAYSURF.blit(final_score, (150, 320))
        DISPLAYSURF.blit(final_coins, (120, 350))

        pygame.display.update()

        for entity in all_sprites:
            entity.kill()

        time.sleep(2)
        pygame.quit()
        sys.exit()

    pygame.display.update()
    FramePerSec.tick(FPS)