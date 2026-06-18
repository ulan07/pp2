import pygame

class Ball:
    def __init__(self, screen_w, screen_h):
        self.radius = 25
        self.x = screen_w // 2
        self.y = screen_h // 2
        self.speed = 20
        self.color = (255, 0, 0)
        self.screen_w = screen_w
        self.screen_h = screen_h

    def move(self, direction):
        new_x = self.x
        new_y = self.y

        if direction == "up":
            new_y -= self.speed
        elif direction == "down":
            new_y += self.speed
        elif direction == "left":
            new_x -= self.speed
        elif direction == "right":
            new_x += self.speed

        if new_x - self.radius >= 0 and new_x + self.radius <= self.screen_w:
            self.x = new_x
        if new_y - self.radius >= 0 and new_y + self.radius <= self.screen_h:
            self.y = new_y

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
