# Blooper 4.0 - Universal Orchestrator
import pygame
import sys
import os

# 1. Environment and Manager Imports
from utils.requirements_check import check_requirements
check_requirements()

from constants import *
from models import Song
from ui_components import MenuButton, Button
from components.mixer_strip import ChannelStrip
from audio_engine.manager import AudioManager
from utils.project_manager import ProjectManager

# 2. View Containers
from containers.editor_view import EditorView
from containers.builder_view import BuilderView
from containers.main_menu import MainMenu

class Blooper4:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption(f"Blooper {VERSION}")
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=BUFFER_SIZE)
        
        self.font = pygame.font.SysFont("Consolas", 12, bold=True)
        self.clock = pygame.time.Clock()

        # Core Engines
        self.song = Song()
        self.audio = AudioManager(self.song)
        
        # State
        self.view_mode = "EDITOR" 
        self.active_track_idx = 0
        self.is_playing = False
        self.current_tick = 0.0
        self.is_fullscreen = False

        # Persistent UI
        self.hamburger_btn = MenuButton(10, 10)
        self.btn_editor_tab = Button(100, 15, 80, 30, "EDITOR", GREEN)
        self.btn_builder_tab = Button(185, 15, 80, 30, "BUILDER", GRAY)

        # Initialize Views
        self.editor_view = EditorView(self.font)
        self.builder_view = BuilderView(self.font, self.audio.factory)
        self.main_menu = MainMenu(self.font)
        self.mixer_strips = []
        self._rebuild_mixer()

    def _rebuild_mixer(self):
        self.mixer_strips = []
        strip_w = scale(WINDOW_W // 16)
        mixer_y = WINDOW_H - scale(MIXER_H)
        for i in range(NUM_TRACKS):
            self.mixer_strips.append(ChannelStrip(i, i * strip_w, mixer_y, strip_w, scale(MIXER_H)))

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.screen.fill(COLOR_BG)

            # --- 1. AUDIO CLOCK ---
            if self.is_playing:
                ticks_per_ms = (self.song.bpm * TPQN) / 60000.0
                prev_tick = self.current_tick
                self.current_tick += (dt * ticks_per_ms)
                
                if self.current_tick >= self.song.length_ticks:
                    self._check_and_trigger(prev_tick, self.song.length_ticks)
                    self.current_tick %= self.song.length_ticks
                    prev_tick = 0.0
                self._check_and_trigger(prev_tick, self.current_tick)

            self.audio.update(self.song)

            # --- 2. UNIVERSAL EVENTS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self._quit_app()
                if event.type == pygame.MOUSEBUTTONUP:
                    for comp in ACTIVE_COMPONENTS: 
                        if hasattr(comp, 'global_release'): comp.global_release()

                # ROUTE: MENU
                if self.view_mode == "MENU":
                    self._handle_menu_events(event)
                    continue

                # ROUTE: HEADER
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.hamburger_btn.is_clicked(event.pos): self.view_mode = "MENU"
                    if self.btn_editor_tab.is_clicked(event.pos): self.view_mode = "EDITOR"
                    if self.btn_builder_tab.is_clicked(event.pos): self.view_mode = "BUILDER"

                # ROUTE: HOTKEYS
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: 
                        self.is_playing = not self.is_playing
                        if not self.is_playing:
                            self.audio.stop_all() # Kills sound on stop
                    if event.key == pygame.K_TAB: self.view_mode = "BUILDER" if self.view_mode == "EDITOR" else "EDITOR"

                # ROUTE: MIXER & CONTENT
                for i, strip in enumerate(self.mixer_strips):
                    if strip.handle_event(event, self.song.tracks[i], UI_SCALE) == "SELECT":
                        self.active_track_idx = i

                if self.view_mode == "EDITOR": self.editor_view.handle_event(event, self.song, self.active_track_idx)
                elif self.view_mode == "BUILDER": self.builder_view.handle_event(event, self.song, self.active_track_idx)

            # --- 3. DRAWING ---
            self._render_ui()
            pygame.display.flip()

    def _handle_menu_events(self, event):
        action = self.main_menu.handle_event(event)
        if not action: return
        
        if action == "RESUME": self.view_mode = "EDITOR"
        elif action == "EXIT": self._quit_app()
        elif action == "NEW": 
            self.song = Song()
            self.audio.current_song_ref = self.song
            self.view_mode = "EDITOR"
        elif action == "SAVE": ProjectManager.save(self.song)
        elif action == "LOAD":
            new_song = ProjectManager.load()
            if new_song:
                self.song = new_song
                self.audio.current_song_ref = self.song
                self.view_mode = "EDITOR"
        elif action == "TOGGLE_FS": self._toggle_fullscreen()
        elif action == "REBUILD_UI": self._refresh_layout()

    def _render_ui(self):
        if self.view_mode == "MENU":
            self.main_menu.draw(self.screen)
        else:
            if self.view_mode == "EDITOR": self.editor_view.draw(self.screen, self.song, self.active_track_idx, self.current_tick, self.font)
            else: self.builder_view.draw(self.screen, self.song, self.active_track_idx)

            for i, strip in enumerate(self.mixer_strips):
                strip.draw(self.screen, self.song.tracks[i], i == self.active_track_idx, self.font, UI_SCALE)

            pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_W, HEADER_H))
            self.hamburger_btn.draw(self.screen)
            self.btn_editor_tab.color = GREEN if self.view_mode == "EDITOR" else GRAY
            self.btn_builder_tab.color = GREEN if self.view_mode == "BUILDER" else GRAY
            self.btn_editor_tab.draw(self.screen, self.font)
            self.btn_builder_tab.draw(self.screen, self.font)
            
            status = f"{'PLAY' if self.is_playing else 'STOP'} | BPM: {self.song.bpm} | TRACK: {self.active_track_idx+1}"
            self.screen.blit(self.font.render(status, True, WHITE), (320, 25))

    def _check_and_trigger(self, start, end):
        for i, track in enumerate(self.song.tracks):
            for note in track.notes:
                if start <= note.tick < end:
                    self.audio.play_note(i, track, note, self.song.bpm)

    def _toggle_fullscreen(self):
        import constants
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            constants.WINDOW_W, constants.WINDOW_H = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((constants.WINDOW_W, constants.WINDOW_H), pygame.FULLSCREEN)
        else:
            constants.WINDOW_W, constants.WINDOW_H = 1280, 800
            self.screen = pygame.display.set_mode((1280, 800))
        self._refresh_layout()

    def _refresh_layout(self):
        self._rebuild_mixer()
        self.editor_view.update_view_rect()
        self.builder_view.update_view_rect()
        self.main_menu.rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)

    def _quit_app(self):
        self.audio.cleanup()
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    Blooper4().run()