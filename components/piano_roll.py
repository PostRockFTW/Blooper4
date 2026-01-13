# Blooper4/components/piano_roll.py
import pygame
from constants import *
from components.base_element import BaseUIElement

class PianoRoll(BaseUIElement):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.scroll_x = 0
        self.scroll_y = 60 * scale(GRID_HEIGHT)
        self.zoom_x = 0.5
        self.is_dragging = False
        self.current_note = None

    def get_coords(self, tick, pitch):
        # Math is now relative to self.rect.x/y
        x = (tick - self.scroll_x) * self.zoom_x + self.rect.x
        y = (127 - pitch) * scale(GRID_HEIGHT) - self.scroll_y + self.rect.y
        return x, y

    def get_pitch_at(self, mouse_y):
        relative_y = mouse_y - self.rect.y + self.scroll_y
        return 127 - int(relative_y / scale(GRID_HEIGHT))

    def get_tick_at(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        return int(relative_x / self.zoom_x + self.scroll_x)

    def draw(self, screen, track, current_tick, font):
        self.update_layout(UI_SCALE)
        
        # Clipping: Grid only draws inside its assigned rectangle
        original_clip = screen.get_clip()
        screen.set_clip(self.rect)

        # 1. Background Grid
        row_h = scale(GRID_HEIGHT)
        for p in range(128):
            _, y = self.get_coords(0, p)
            if self.rect.top - row_h <= y <= self.rect.bottom:
                bg = (20, 20, 25)
                if (p % 12) in [1, 3, 6, 8, 10]: bg = (15, 15, 18)
                pygame.draw.rect(screen, bg, (self.rect.x, y, self.rect.width, row_h))
                pygame.draw.line(screen, (30, 30, 35), (self.rect.x, y), (self.rect.right, y))

        # 2. Measure Lines
        for t in range(0, 19200, TPQN):
            x = (t - self.scroll_x) * self.zoom_x + self.rect.x
            if x >= self.rect.x:
                color = (70, 70, 80) if t % (TPQN*4) == 0 else (35, 35, 40)
                pygame.draw.line(screen, color, (x, self.rect.top), (x, self.rect.bottom))

        # 3. Draw Notes
        for n in track.notes:
            nx, ny = self.get_coords(n.tick, n.pitch)
            nw = n.duration * self.zoom_x
            if nx + nw > self.rect.x:
                color = OCTAVE_COLORS[min(n.pitch // 12, len(OCTAVE_COLORS)-1)]
                pygame.draw.rect(screen, color, (max(nx, self.rect.x), ny+1, nw-1, row_h-2))

        # 4. Playhead
        px = (current_tick - self.scroll_x) * self.zoom_x + self.rect.x
        if px > self.rect.x:
            pygame.draw.line(screen, COLOR_ACCENT, (px, self.rect.top), (px, self.rect.bottom), 2)
            
        screen.set_clip(original_clip)

    def global_release(self):
        self.is_dragging = False
        self.current_note = None