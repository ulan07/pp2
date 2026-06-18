import pygame
import os

class MusicPlayer:
    def __init__(self, music_folder="music"):
        pygame.mixer.init()

        self.music_folder = music_folder
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0

        self.load_playlist()

    def load_playlist(self):
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            return

        for file in sorted(os.listdir(self.music_folder)):
            if file.endswith((".mp3", ".wav")):
                full_path = os.path.join(self.music_folder, file)
                self.playlist.append(full_path)

    def get_track_name(self):
        if not self.playlist:
            return "Нет треков"
        path = self.playlist[self.current_index]
        name = os.path.basename(path)
        name = os.path.splitext(name)[0]
        return name

    def play(self):
        if not self.playlist:
            return

        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True

        elif not self.is_playing:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            self.start_time = pygame.time.get_ticks()

        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0

    def next_track(self):
        if not self.playlist:
            return
        self.stop()
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def prev_track(self):
        if not self.playlist:
            return
        self.stop()
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play()

    def get_progress(self):
        if self.is_playing:
            ms = pygame.mixer.music.get_pos()
            return ms // 1000
        return 0

    def is_track_finished(self):
        if self.is_playing and not pygame.mixer.music.get_busy():
            return True
        return False