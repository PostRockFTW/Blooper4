"""Piano roll scale settings: Chromatic / Modal / Microtonal selector."""

import pygame
from components.base_element import BaseUIElement
from constants import *

class PianoRollSettingsUI(BaseUIElement):
    """Scale mode selector for piano roll. Matches sampler_brain style."""

    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)  # Same size as sampler_brain
        self.font = font
        self.plugin_id = "PIANO_ROLL_SETTINGS"
        self.title = "PIANO ROLL SETTINGS"
        self.chromatic_rect = None
        self.modal_rect = None
        self.microtonal_rect = None

    def draw(self, screen, track, x, y, scale_f):
        """Draw scale mode selector with modular frame."""
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, True, scale_f)

        # Label
        label_txt = "SCALE MODE:"
        screen.blit(self.font.render(label_txt, True, WHITE),
                    (self.rect.x + scale(20), self.rect.y + scale(45)))

        # Define button areas (3 buttons stacked vertically)
        button_width = scale(260)
        button_height = scale(50)
        start_y = self.rect.y + scale(80)

        self.chromatic_rect = pygame.Rect(
            self.rect.x + scale(20), start_y,
            button_width, button_height
        )
        self.modal_rect = pygame.Rect(
            self.rect.x + scale(20), start_y + scale(60),
            button_width, button_height
        )
        self.microtonal_rect = pygame.Rect(
            self.rect.x + scale(20), start_y + scale(120),
            button_width, button_height
        )

        # Get current scale mode (default to CHROMATIC)
        scale_mode = getattr(track, 'piano_roll_scale', 'CHROMATIC')

        # Draw buttons with highlight for active mode
        buttons = [
            (self.chromatic_rect, "CHROMATIC", scale_mode == 'CHROMATIC'),
            (self.modal_rect, "MODAL", scale_mode == 'MODAL'),
            (self.microtonal_rect, "MICROTONAL", scale_mode == 'MICROTONAL')
        ]

        for rect, label, is_active in buttons:
            color = COLOR_ACCENT if is_active else (50, 50, 55)
            pygame.draw.rect(screen, color, rect, border_radius=scale(5))
            text_color = (0, 0, 0) if is_active else WHITE
            txt_surf = self.font.render(label, True, text_color)
            screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2,
                                   rect.centery - txt_surf.get_height()//2))

    def handle_event(self, event, track_model):
        """Handle scale mode selection."""
        if self.chromatic_rect is None:
            return None

        if hasattr(event, 'pos'):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.chromatic_rect.collidepoint(event.pos):
                    track_model.piano_roll_scale = 'CHROMATIC'
                    return "SCALE_CHANGED"
                elif self.modal_rect.collidepoint(event.pos):
                    track_model.piano_roll_scale = 'MODAL'
                    return "SCALE_CHANGED"
                elif self.microtonal_rect.collidepoint(event.pos):
                    track_model.piano_roll_scale = 'MICROTONAL'
                    return "SCALE_CHANGED"
        return None
