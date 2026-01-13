# Blooper4/components/mixer_panel.py
import pygame
from constants import *
from components.mixer_strip import ChannelStrip
from components.base_element import BaseUIElement

class MixerPanel(BaseUIElement):
    """
    The Horizontal Mixer Widget.
    Contains 16 ChannelStrips and anchors to the bottom of the screen.
    """
    def __init__(self, font):
        # Initial Stock Size: Full width, MIXER_H high, at the bottom
        super().__init__(0, WINDOW_H - MIXER_H, WINDOW_W, MIXER_H)
        self.font = font
        self.strips = [
            ChannelStrip(i, 0, 0, WINDOW_W // 16, MIXER_H) for i in range(16)
        ]

    def draw(self, screen, song, active_idx):
        # Draw the main panel background
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.line(screen, (50, 50, 60), self.rect.topleft, self.rect.topright, 2)

        # Draw each channel strip
        strip_w = self.rect.width // 16
        for i, strip in enumerate(self.strips):
            # Tell the strip to draw at its calculated horizontal position
            strip.draw(screen, i * strip_w, self.rect.y, song.tracks[i], i == active_idx, self.font, UI_SCALE)

    def handle_event(self, event, song):
        active_track_change = None
        for i, strip in enumerate(self.strips):
            res = strip.handle_event(event, song.tracks[i], UI_SCALE)
            if res == "SELECT":
                active_track_change = i
        return active_track_change