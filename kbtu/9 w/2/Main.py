import pygame
import sys
from Player import MusicPlayer

SCREEN_W, SCREEN_H = 800, 600

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GRAY       = (50,  50,  50)
LIGHT_GRAY = (100, 100, 100)
GREEN      = (0,   200, 80)
RED        = (200, 50,  50)
BLUE       = (50,  120, 220)
YELLOW     = (255, 220, 0)
DARK_BG    = (18,  18,  18)


def draw_text(screen, text, font, color, x, y, center=False):
    surface = font.render(text, True, color)
    if center:
        rect = surface.get_rect(center=(x, y))
        screen.blit(surface, rect)
    else:
        screen.blit(surface, (x, y))


def draw_progress_bar(screen, progress_sec, bar_x, bar_y, bar_w, bar_h):
    pygame.draw.rect(screen, LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=5)

    max_sec = 300
    fill = min(progress_sec / max_sec, 1.0)
    fill_w = int(bar_w * fill)

    if fill_w > 0:
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_w, bar_h), border_radius=5)

    dot_x = bar_x + fill_w
    pygame.draw.circle(screen, WHITE, (dot_x, bar_y + bar_h // 2), 8)

    minutes = progress_sec // 60
    seconds = progress_sec % 60
    return f"{minutes:02d}:{seconds:02d}"


def draw_playlist(screen, player, font_small, x, y):
    import os
    draw_text(screen, "ПЛЕЙЛИСТ", font_small, LIGHT_GRAY, x, y)
    y += 30

    for i, track_path in enumerate(player.playlist):
        name = os.path.splitext(os.path.basename(track_path))[0]
        if len(name) > 35:
            name = name[:35] + "..."

        if i == player.current_index:
            draw_text(screen, f"▶  {name}", font_small, GREEN, x, y + i * 28)
        else:
            draw_text(screen, f"    {name}", font_small, LIGHT_GRAY, x, y + i * 28)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("🎵 Music Player")
    clock = pygame.time.Clock()

    font_big    = pygame.font.SysFont("Arial", 36, bold=True)
    font_medium = pygame.font.SysFont("Arial", 24)
    font_small  = pygame.font.SysFont("Arial", 18)

    player = MusicPlayer(music_folder="music")

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    player.play()
                elif event.key == pygame.K_s:
                    player.stop()
                elif event.key == pygame.K_n:
                    player.next_track()
                elif event.key == pygame.K_b:
                    player.prev_track()
                elif event.key == pygame.K_q:
                    running = False

        if player.is_track_finished():
            player.next_track()

        screen.fill(DARK_BG)

        pygame.draw.rect(screen, GRAY, (0, 0, SCREEN_W, 70))
        draw_text(screen, "🎵 MUSIC PLAYER", font_big, WHITE, SCREEN_W // 2, 35, center=True)

        track_name = player.get_track_name()
        if len(track_name) > 40:
            track_name = track_name[:40] + "..."
        draw_text(screen, track_name, font_big, WHITE, SCREEN_W // 2, 160, center=True)

        if player.is_playing:
            status = "▶  ИГРАЕТ"
            status_color = GREEN
        elif player.is_paused:
            status = "⏸  ПАУЗА"
            status_color = YELLOW
        else:
            status = "⏹  СТОП"
            status_color = RED

        draw_text(screen, status, font_medium, status_color, SCREEN_W // 2, 210, center=True)

        progress = player.get_progress()
        bar_x, bar_y = 100, 260
        bar_w, bar_h  = 600, 8
        time_str = draw_progress_bar(screen, progress, bar_x, bar_y, bar_w, bar_h)
        draw_text(screen, time_str, font_small, WHITE, bar_x, bar_y + 20)

        pygame.draw.rect(screen, GRAY, (50, 310, SCREEN_W - 100, 200), border_radius=10)
        if player.playlist:
            draw_playlist(screen, player, font_small, 80, 325)
        else:
            draw_text(screen, "Положи MP3/WAV файлы в папку music/", font_medium, LIGHT_GRAY, SCREEN_W // 2, 400, center=True)

        controls = "[P] Play/Pause    [S] Stop    [N] Next    [B] Back    [Q] Quit"
        draw_text(screen, controls, font_small, LIGHT_GRAY, SCREEN_W // 2, 540, center=True)

        if player.playlist:
            track_num = f"Трек {player.current_index + 1} из {len(player.playlist)}"
            draw_text(screen, track_num, font_small, LIGHT_GRAY, SCREEN_W // 2, 570, center=True)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()