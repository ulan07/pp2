import pygame
import math

def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()

    canvas = pygame.Surface(screen.get_size())
    canvas.fill((0, 0, 0))

    radius = 15
    points = []

    # Инструменты: line, rectangle, circle, eraser, square,
    #              right_triangle, eq_triangle, rhombus
    tool = 'line'
    color = (0, 0, 255)
    start_pos = None
    drawing = False

    while True:
        pressed = pygame.key.get_pressed()
        alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.KEYDOWN:
                # Выход
                if event.key == pygame.K_w and ctrl_held:
                    return
                if event.key == pygame.K_F4 and alt_held:
                    return
                if event.key == pygame.K_ESCAPE:
                    return

                # Выбор инструмента цифрами
                if event.key == pygame.K_1:
                    tool = 'line'
                elif event.key == pygame.K_2:
                    tool = 'rectangle'
                elif event.key == pygame.K_3:
                    tool = 'circle'
                elif event.key == pygame.K_4:
                    tool = 'eraser'
                elif event.key == pygame.K_5:
                    tool = 'square'
                elif event.key == pygame.K_6:
                    tool = 'right_triangle'
                elif event.key == pygame.K_7:
                    tool = 'eq_triangle'
                elif event.key == pygame.K_8:
                    tool = 'rhombus'

                # Выбор цвета буквами
                if event.key == pygame.K_r:
                    color = (255, 0, 0)
                elif event.key == pygame.K_g:
                    color = (0, 255, 0)
                elif event.key == pygame.K_b:
                    color = (0, 0, 255)
                elif event.key == pygame.K_w:
                    color = (255, 255, 255)

            if event.type == pygame.MOUSEBUTTONDOWN:
                start_pos = event.pos
                drawing = True
                if event.button == 1:
                    radius = min(200, radius + 1)
                elif event.button == 3:
                    radius = max(1, radius - 1)

            if event.type == pygame.MOUSEBUTTONUP:
                end_pos = event.pos
                drawing = False

                if tool == 'rectangle':
                    # Прямоугольник от start до end
                    rect = pygame.Rect(
                        start_pos,
                        (end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
                    )
                    pygame.draw.rect(canvas, color, rect, 2)

                elif tool == 'circle':
                    # Круг — радиус = расстояние от start до end
                    r = int(math.hypot(
                        end_pos[0] - start_pos[0],
                        end_pos[1] - start_pos[1]
                    ))
                    pygame.draw.circle(canvas, color, start_pos, r, 2)

                elif tool == 'square':
                    # Квадрат — сторона = расстояние от start до end по X
                    side = end_pos[0] - start_pos[0]
                    rect = pygame.Rect(start_pos, (side, side))
                    pygame.draw.rect(canvas, color, rect, 2)

                elif tool == 'right_triangle':
                    # Прямоугольный треугольник
                    # Вершины: start, (start_x, end_y), end
                    x0, y0 = start_pos
                    x1, y1 = end_pos
                    pts = [
                        (x0, y0),   # верхний левый угол
                        (x0, y1),   # нижний левый угол (прямой угол)
                        (x1, y1),   # нижний правый угол
                    ]
                    pygame.draw.polygon(canvas, color, pts, 2)

                elif tool == 'eq_triangle':
                    # Равносторонний треугольник
                    # Основание горизонтальное от start до end
                    x0, y0 = start_pos
                    x1, y1 = end_pos
                    base   = x1 - x0
                    # Высота равностороннего треугольника = side * sqrt(3)/2
                    height = int(abs(base) * math.sqrt(3) / 2)
                    pts = [
                        (x0, y0),               # левый нижний
                        (x1, y0),               # правый нижний
                        (x0 + base // 2, y0 - height),  # верхний центр
                    ]
                    pygame.draw.polygon(canvas, color, pts, 2)

                elif tool == 'rhombus':
                    # Ромб — центр в start, полуоси до end по x и y
                    cx, cy = start_pos
                    dx = abs(end_pos[0] - cx)   # горизонтальная полуось
                    dy = abs(end_pos[1] - cy)   # вертикальная полуось
                    pts = [
                        (cx,      cy - dy),     # верхний
                        (cx + dx, cy),          # правый
                        (cx,      cy + dy),     # нижний
                        (cx - dx, cy),          # левый
                    ]
                    pygame.draw.polygon(canvas, color, pts, 2)

            if event.type == pygame.MOUSEMOTION and drawing:
                if tool == 'line':
                    # Запоминаем последние 256 точек для рисования линии
                    points.append(event.pos)
                    points = points[-256:]
                elif tool == 'eraser':
                    # Стираем чёрным кругом
                    pygame.draw.circle(canvas, (0, 0, 0), event.pos, 20)

        # Рисуем линию через все запомненные точки
        if tool == 'line':
            i = 0
            while i < len(points) - 1:
                drawLineBetween(canvas, i, points[i], points[i + 1], radius, color)
                i += 1

        # Показываем подсказку по инструментам внизу экрана
        hint_font = pygame.font.SysFont("Arial", 13)
        hint = hint_font.render(
            "1:Line 2:Rect 3:Circle 4:Eraser 5:Square 6:RightTri 7:EqTri 8:Rhombus | R G B W",
            True, (180, 180, 180)
        )
        screen.blit(canvas, (0, 0))
        screen.blit(hint, (5, 462))
        pygame.display.flip()
        clock.tick(60)


def drawLineBetween(screen, index, start, end, width, color):
    dx = start[0] - end[0]
    dy = start[1] - end[1]
    iterations = max(abs(dx), abs(dy))

    for i in range(iterations):
        progress  = i / iterations if iterations != 0 else 0
        aprogress = 1 - progress
        x = int(aprogress * start[0] + progress * end[0])
        y = int(aprogress * start[1] + progress * end[1])
        pygame.draw.circle(screen, color, (x, y), width)


main()
