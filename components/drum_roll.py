# Blooper4/components/drum_roll.py
import pygame
from constants import *
from components.base_element import BaseUIElement

class DrumRoll(BaseUIElement):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.scroll_x = 0
        self.zoom_x = 0.5
        # FIX: Start scrolled to note 33
        self.scroll_y = (127 - (SAMPLER_DEFAULT_START + 15)) * GRID_HEIGHT
        self.row_h = scale(GRID_HEIGHT * 1.5) # Slightly taller than synth rows 
        self.is_dragging = False
        self.current_note = None

    def update_layout(self, scale_f):
        """Override to update row height when UI_SCALE changes."""
        super().update_layout(scale_f)
        self.row_h = self.rect.height // 19

    def get_coords(self, tick, pitch):
        # Align this math with PianoRoll's logic
        x = (tick - self.scroll_x) * self.zoom_x + self.rect.x
        y = (127 - pitch) * scale(GRID_HEIGHT) - self.scroll_y + self.rect.y
        return x, y

    def get_pitch_at(self, mouse_y):
        # Align this math with PianoRoll's logic
        relative_y = mouse_y - self.rect.y + self.scroll_y
        return 127 - int(relative_y / scale(GRID_HEIGHT))


    def get_tick_at(self, mouse_x):
        return int((mouse_x - self.rect.x) / self.zoom_x + self.scroll_x)

    def draw(self, screen, track, current_tick, font):
        self.update_layout(UI_SCALE)
        
        original_clip = screen.get_clip()
        screen.set_clip(self.rect)

        # 1. Draw Pad Rows
        row_h = scale(GRID_HEIGHT)
        for p in range(0, 128):
            _, y = self.get_coords(0, p)
            # Only draw if the row is actually visible on screen
            if self.rect.top - row_h <= y <= self.rect.bottom:
                # Alternating row colors for better visibility
                bg = (20, 20, 25) if (p % 2 == 0) else (15, 15, 18)
                pygame.draw.rect(screen, bg, (self.rect.x, y, self.rect.width, row_h))
                pygame.draw.line(screen, (30, 30, 35), (self.rect.x, y), (self.rect.right, y))

        # 2. Draw Measure Lines
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
                pygame.draw.rect(screen, COLOR_ACCENT, (max(nx, self.rect.x), ny + 2, nw - 1, self.row_h - 4))

        # 4. Playhead
        px = (current_tick - self.scroll_x) * self.zoom_x + self.rect.x
        if px > self.rect.x:
            pygame.draw.line(screen, WHITE, (px, self.rect.top), (px, self.rect.bottom), 1)
            
        screen.set_clip(original_clip)

    def global_release(self):
        self.is_dragging = False
        self.current_note = None