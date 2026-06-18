import pygame
import math
import sys
from datetime import datetime
from collections import deque

# ── константы ──────────────────────────────────────────────────────────────
W, H        = 900, 620
TOOLBAR_H   = 56
CANVAS_TOP  = TOOLBAR_H
CANVAS_H    = H - TOOLBAR_H
BG          = (18, 18, 24)
TB_BG       = (28, 28, 36)
TB_BORDER   = (55, 55, 70)
ACCENT      = (99, 179, 237)
TEXT_DIM    = (140, 140, 160)
TEXT_BRIGHT = (230, 230, 240)
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)

TOOLS = ['pencil','line','rectangle','circle',
         'square','right_triangle','eq_triangle','rhombus',
         'eraser','fill','text']

TOOL_ICONS = {
    'pencil':         '✏',
    'line':           '╱',
    'rectangle':      '▭',
    'circle':         '◯',
    'square':         '■',
    'right_triangle': '◺',
    'eq_triangle':    '△',
    'rhombus':        '◇',
    'eraser':         '⌫',
    'fill':           '▓',
    'text':           'T',
}

SIZES       = [2, 5, 10]
SIZE_LABELS = ['S', 'M', 'L']

PALETTE = [
    (0,   0,   0),   (255,255,255), (192, 57, 43), (231,  76,  60),
    (230,126, 34),   (241,196,  15),(39, 174,  96),(26, 188, 156),
    (41, 128,185),   (52, 152,219), (155, 89,182),(52,  73,  94),
]

# ── вспомогательные функции ────────────────────────────────────────────────

def draw_aa_line(surf, color, p1, p2, width):
    """Рисует линию кружками — работает для всех инструментов."""
    x0, y0 = p1; x1, y1 = p2
    dx, dy = abs(x1-x0), abs(y1-y0)
    steps  = max(dx, dy, 1)
    for i in range(steps + 1):
        t = i / steps
        x = int(x0 + t*(x1-x0))
        y = int(y0 + t*(y1-y0))
        pygame.draw.circle(surf, color, (x, y), width // 2)


def flood_fill(surf, start, fill_color):
    """BFS flood-fill прямо по пикселям поверхности."""
    sx, sy = start
    sw, sh = surf.get_size()
    if not (0 <= sx < sw and 0 <= sy < sh):
        return
    target = surf.get_at((sx, sy))[:3]
    if target == fill_color[:3]:
        return

    visited = set()
    q = deque()
    q.append((sx, sy))
    visited.add((sx, sy))

    while q:
        x, y = q.popleft()
        surf.set_at((x, y), fill_color)
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if (nx, ny) not in visited and 0 <= nx < sw and 0 <= ny < sh:
                if surf.get_at((nx, ny))[:3] == target:
                    visited.add((nx, ny))
                    q.append((nx, ny))


def save_canvas(canvas):
    name = datetime.now().strftime("canvas_%Y%m%d_%H%M%S.png")
    pygame.image.save(canvas, name)
    return name

# ── рисование фигур на поверхности ────────────────────────────────────────

def draw_shape(surf, tool, p1, p2, color, width):
    x0, y0 = p1; x1, y1 = p2
    w2 = max(1, width)

    if tool == 'rectangle':
        rect = pygame.Rect(min(x0,x1), min(y0,y1), abs(x1-x0), abs(y1-y0))
        pygame.draw.rect(surf, color, rect, w2)

    elif tool == 'circle':
        r = int(math.hypot(x1-x0, y1-y0))
        if r > 0:
            pygame.draw.circle(surf, color, p1, r, w2)

    elif tool == 'square':
        side = max(abs(x1-x0), abs(y1-y0))
        sx   = x0 + (side if x1 >= x0 else -side)
        sy   = y0 + (side if y1 >= y0 else -side)
        rect = pygame.Rect(min(x0,sx), min(y0,sy), side, side)
        pygame.draw.rect(surf, color, rect, w2)

    elif tool == 'right_triangle':
        pts = [(x0,y0),(x0,y1),(x1,y1)]
        pygame.draw.polygon(surf, color, pts, w2)

    elif tool == 'eq_triangle':
        base   = x1 - x0
        height = int(abs(base) * math.sqrt(3) / 2)
        sign   = -1 if y1 <= y0 else 1
        pts = [(x0,y0),(x1,y0),(x0 + base//2, y0 + sign*height)]
        pygame.draw.polygon(surf, color, pts, w2)

    elif tool == 'rhombus':
        cx, cy = x0, y0
        dx, dy = abs(x1-cx), abs(y1-cy)
        pts = [(cx, cy-dy),(cx+dx, cy),(cx, cy+dy),(cx-dx, cy)]
        pygame.draw.polygon(surf, color, pts, w2)

    elif tool == 'line':
        draw_aa_line(surf, color, p1, p2, w2)

# ── тулбар ─────────────────────────────────────────────────────────────────

class Toolbar:
    def __init__(self, font_icon, font_small):
        self.font_icon  = font_icon
        self.font_small = font_small
        self.rects      = {}   # key → pygame.Rect

    def _btn(self, surf, key, x, y, w, h, label, active=False, color=None):
        r = pygame.Rect(x, y, w, h)
        self.rects[key] = r
        bg = ACCENT if active else (42, 42, 56)
        pygame.draw.rect(surf, bg, r, border_radius=6)
        pygame.draw.rect(surf, TB_BORDER, r, 1, border_radius=6)
        if color:
            inner = r.inflate(-6, -6)
            pygame.draw.rect(surf, color, inner, border_radius=4)
            pygame.draw.rect(surf, WHITE, inner, 1, border_radius=4)
        else:
            txt   = self.font_icon.render(label, True, WHITE if active else TEXT_BRIGHT)
            tr    = txt.get_rect(center=r.center)
            surf.blit(txt, tr)
        return r

    def draw(self, surf, tool, size_idx, color):
        surf.fill(TB_BG, (0, 0, W, TOOLBAR_H))
        pygame.draw.line(surf, TB_BORDER, (0, TOOLBAR_H-1), (W, TOOLBAR_H-1))

        x = 8
        # ── инструменты
        for t in TOOLS:
            self._btn(surf, f'tool_{t}', x, 8, 36, 40,
                      TOOL_ICONS[t], active=(tool == t))
            x += 40

        x += 6
        # ── размеры кисти
        for i, lbl in enumerate(SIZE_LABELS):
            self._btn(surf, f'size_{i}', x, 8, 30, 40,
                      lbl, active=(size_idx == i))
            x += 34

        x += 6
        # ── палитра
        for i, c in enumerate(PALETTE):
            self._btn(surf, f'color_{i}', x, 10, 28, 36,
                      '', active=(color == c), color=c)
            x += 32

        # ── подсказка справа
        hint = self.font_small.render(
            "Ctrl+S: save   Esc/Enter: text", True, TEXT_DIM)
        surf.blit(hint, (W - hint.get_width() - 10, 20))

    def hit(self, pos):
        for key, r in self.rects.items():
            if r.collidepoint(pos):
                return key
        return None

# ── главная функция ────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Paint v3")
    clock  = pygame.time.Clock()

    font_icon  = pygame.font.SysFont("Segoe UI Symbol", 20)
    font_small = pygame.font.SysFont("Arial", 12)
    font_text  = pygame.font.SysFont("Arial", 20)

    toolbar = Toolbar(font_icon, font_small)

    canvas = pygame.Surface((W, CANVAS_H))
    canvas.fill(WHITE)

    # состояние
    tool       = 'pencil'
    color      = BLACK
    size_idx   = 0          # 0=small 1=medium 2=large
    drawing    = False
    start_pos  = None
    prev_pos   = None
    preview    = None       # Surface для предпросмотра линии/фигур

    # text tool
    text_mode   = False
    text_pos    = None
    text_buf    = ''

    # сообщение о сохранении
    save_msg    = ''
    save_timer  = 0

    def canvas_pos(screen_pos):
        return (screen_pos[0], screen_pos[1] - CANVAS_TOP)

    def in_canvas(screen_pos):
        return screen_pos[1] >= CANVAS_TOP

    running = True
    while running:
        pressed   = pygame.key.get_pressed()
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
        alt_held  = pressed[pygame.K_LALT]  or pressed[pygame.K_RALT]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ── клавиатура ────────────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                # выход
                if event.key == pygame.K_F4 and alt_held:
                    running = False

                # сохранение
                if event.key == pygame.K_s and ctrl_held:
                    name = save_canvas(canvas)
                    save_msg   = f"Saved: {name}"
                    save_timer = 180

                # инструменты цифрами (кроме text mode)
                if not text_mode:
                    key_map = {
                        pygame.K_q: 'pencil',  pygame.K_w: 'line',
                        pygame.K_e: 'rectangle', pygame.K_r: 'circle',
                        pygame.K_t: 'square',   pygame.K_y: 'right_triangle',
                        pygame.K_u: 'eq_triangle', pygame.K_i: 'rhombus',
                        pygame.K_o: 'eraser',   pygame.K_p: 'fill',
                        pygame.K_MINUS: 'text',
                    }
                    if event.key in key_map:
                        tool = key_map[event.key]

                    # размер кисти []
                    if event.key == pygame.K_LEFTBRACKET:
                        size_idx = max(0, size_idx - 1)
                    if event.key == pygame.K_RIGHTBRACKET:
                        size_idx = min(2, size_idx + 1)

                # ── текстовый режим ───────────────────────────────────────
                if text_mode:
                    if event.key == pygame.K_RETURN:
                        # зафиксировать
                        if text_buf:
                            txt_surf = font_text.render(text_buf, True, color)
                            canvas.blit(txt_surf, text_pos)
                        text_mode = False
                        text_buf  = ''
                        text_pos  = None
                    elif event.key == pygame.K_ESCAPE:
                        text_mode = False
                        text_buf  = ''
                        text_pos  = None
                    elif event.key == pygame.K_BACKSPACE:
                        text_buf = text_buf[:-1]
                    else:
                        if event.unicode and event.unicode.isprintable():
                            text_buf += event.unicode

            # ── мышь ──────────────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hit = toolbar.hit(event.pos)
                if hit:
                    if hit.startswith('tool_'):
                        tool      = hit[5:]
                        text_mode = False
                        text_buf  = ''
                    elif hit.startswith('size_'):
                        size_idx = int(hit[5:])
                    elif hit.startswith('color_'):
                        color = PALETTE[int(hit[6:])]
                else:
                    if in_canvas(event.pos):
                        cp = canvas_pos(event.pos)
                        if tool == 'fill':
                            flood_fill(canvas, cp, color)
                        elif tool == 'text':
                            text_mode = True
                            text_pos  = cp
                            text_buf  = ''
                        else:
                            drawing   = True
                            start_pos = cp
                            prev_pos  = cp
                            preview   = canvas.copy()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing and in_canvas(event.pos):
                    cp = canvas_pos(event.pos)
                    w  = SIZES[size_idx]
                    if tool in ('rectangle','circle','square',
                                'right_triangle','eq_triangle','rhombus','line'):
                        draw_shape(canvas, tool, start_pos, cp, color, w)
                    # pencil/eraser уже нарисованы в MOUSEMOTION
                drawing   = False
                start_pos = None
                prev_pos  = None
                preview   = None

            elif event.type == pygame.MOUSEMOTION:
                if drawing and in_canvas(event.pos):
                    cp = canvas_pos(event.pos)
                    w  = SIZES[size_idx]
                    if tool == 'pencil':
                        if prev_pos:
                            draw_aa_line(canvas, color, prev_pos, cp, w)
                        prev_pos = cp
                    elif tool == 'eraser':
                        pygame.draw.circle(canvas, WHITE, cp, max(8, w*3))
                        prev_pos = cp
                    else:
                        # предпросмотр для фигур/линий
                        preview = canvas.copy()
                        draw_shape(preview, tool, start_pos, cp, color, w)

        # ── отрисовка ─────────────────────────────────────────────────────
        screen.fill(BG)

        # холст (или превью)
        disp = preview if (preview and drawing) else canvas
        screen.blit(disp, (0, CANVAS_TOP))

        # текстовый курсор
        if text_mode and text_pos:
            rendered = font_text.render(text_buf + '|', True, color)
            screen.blit(rendered, (text_pos[0], text_pos[1] + CANVAS_TOP))

        # тулбар поверх
        toolbar.draw(screen, tool, size_idx, color)

        # сообщение о сохранении
        if save_timer > 0:
            alpha = min(255, save_timer * 4)
            msg   = font_small.render(save_msg, True, (120, 220, 120))
            screen.blit(msg, (W // 2 - msg.get_width() // 2, CANVAS_TOP + 10))
            save_timer -= 1

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
