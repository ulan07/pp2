import pygame
import sys
from ball import Ball

SCREEN_W, SCREEN_H = 800, 600
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Moving Ball")
clock = pygame.time.Clock()

ball = Ball(SCREEN_W, SCREEN_H)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                ball.move("up")
            elif event.key == pygame.K_DOWN:
                ball.move("down")
            elif event.key == pygame.K_LEFT:
                ball.move("left")
            elif event.key == pygame.K_RIGHT:
                ball.move("right")

    screen.fill(WHITE)
    ball.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
