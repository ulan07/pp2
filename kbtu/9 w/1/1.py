import pygame
import datetime

pygame.init()
screen = pygame.display.set_mode((800, 600))

bg = pygame.image.load("clock_face.png")
bg = pygame.transform.scale(bg, (800, 600))

minute_hand = pygame.image.load("hand_minute.png")
minute_hand = pygame.transform.scale(minute_hand, (50, 220))

second_hand = pygame.image.load("hand_second.png")
second_hand = pygame.transform.scale(second_hand, (40, 250))

clock = pygame.time.Clock()
running = True

CENTER = (400, 300)

# смещение до "основания" стрелки
pivot_min = pygame.math.Vector2(0, 100)
pivot_sec = pygame.math.Vector2(0, 110)

def draw_hand(image, angle, pivot):
    rotated_offset = pivot.rotate(-angle)
    pos = (CENTER[0] - rotated_offset.x, CENTER[1] - rotated_offset.y)

    rotated_image = pygame.transform.rotate(image, angle)
    rect = rotated_image.get_rect(center=pos)

    screen.blit(rotated_image, rect)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # текущее время
    screen.fill((255,255,255))
    now = datetime.datetime.now()
    minutes = now.minute
    seconds = now.second

    # углы
    angle_sec = -seconds * 6
    angle_min = -(minutes * 6 + seconds * 0.1)

    screen.blit(bg, (0, 0))

    # рисуем стрелки
    draw_hand(minute_hand, angle_min, pivot_min)
    draw_hand(second_hand, angle_sec, pivot_sec)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()