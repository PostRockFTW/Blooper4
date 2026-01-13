# Blooper4/components/builder/sampler_brain.py
import pygame
from constants import *
from components.base_element import BaseUIElement
from ui_components import Button

class SamplerBrainUI(BaseUIElement):
    """
    The 'Router' for Sampler Tracks. 
    Displays a 16-pad grid and handles range shifting.
    """
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font = font
        self.plugin_id = "SAMPLER_BRAIN"
        self.title = "SAMPLER BRAIN"
        
        # Navigation Buttons
        self.btn_prev = Button(0, 0, 40, 25, "<", (60, 60, 70))
        self.btn_next = Button(0, 0, 40, 25, ">", (60, 60, 70))

    def _get_pad_rect(self, n, track, scale_f):
        # Calculate grid position (4x4) relative to current base note
        local_idx = n - track.sampler_base_note
        col, row = local_idx % 4, local_idx // 4
        px = self.rect.x + scale(20) + col * scale(65)
        # FIX: Adjust Y offset to match visual rendering (was scale(80), too high by ~80px)
        py = self.rect.y + scale(160) + row * scale(55)
        return pygame.Rect(px, py, scale(60), scale(50))

    def draw(self, screen, track, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, True, scale_f)

        # Draw Range Controls
        range_txt = f"RANGE: {track.sampler_base_note}-{track.sampler_base_note+15}"
        screen.blit(self.font.render(range_txt, True, WHITE), (self.rect.x + scale(20), self.rect.y + scale(45)))
        
        self.btn_prev.move_to(self.rect.right - scale(100), self.rect.y + scale(40), scale(40), scale(25))
        self.btn_next.move_to(self.rect.right - scale(50), self.rect.y + scale(40), scale(40), scale(25))
        self.btn_prev.draw(screen, self.font)
        self.btn_next.draw(screen, self.font)

        # Draw the 16-pad selection grid
        for n in range(track.sampler_base_note, track.sampler_base_note + 16):
            if n > 127: break
            p_rect = self._get_pad_rect(n, track, scale_f)
            
            # Highlight pad currently being edited in the rack
            is_active = (track.active_pad == n)
            color = COLOR_ACCENT if is_active else (50, 50, 55)
            pygame.draw.rect(screen, color, p_rect, border_radius=scale(5))
            
            # Label
            screen.blit(self.font.render(str(n), True, WHITE), (p_rect.x + 5, p_rect.y + 5))
            pad_cfg = track.sampler_map.get(n, {"engine": "NONE"})
            # Display truncated engine name (e.g., 'NOIS')
            eng_name = pad_cfg["engine"][:4]
            screen.blit(self.font.render(eng_name, True, GRAY), (p_rect.x + 5, p_rect.y + 25))

    def handle_event(self, event, track):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Shift 16 notes down/up
            if self.btn_prev.is_clicked(event.pos):
                track.sampler_base_note = max(0, track.sampler_base_note - 16)
                return
            if self.btn_next.is_clicked(event.pos):
                track.sampler_base_note = min(112, track.sampler_base_note + 16)
                return

            # Click a pad to "Focus" the rack on that specific engine
            for n in range(track.sampler_base_note, track.sampler_base_note + 16):
                if n > 127: break
                if self._get_pad_rect(n, track, UI_SCALE).collidepoint(event.pos):
                    track.active_pad = n
                    return