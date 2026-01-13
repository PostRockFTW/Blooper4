"""Master toggle for switching between PIANO ROLL and SAMPLE PADS modes."""

import pygame
from components.base_element import BaseUIElement
from constants import scale, UI_SCALE, COLOR_ACCENT, COLOR_PANEL

class ModeToggleUI(BaseUIElement):
    """Radio button toggle: [PIANO ROLL | SAMPLE PADS]"""

    def __init__(self, x, y):
        super().__init__(x, y, scale(280), scale(40))
        self.font = pygame.font.Font(None, int(24 * UI_SCALE))
        self.piano_rect = None
        self.pads_rect = None

    def move_to(self, x, y):
        """Position the toggle and update anchors for docking system."""
        self.rect.x = x
        self.rect.y = y
        # Update anchors so other elements can dock to this toggle
        self.anchors['TL'] = (self.rect.x, self.rect.y)
        self.anchors['TR'] = (self.rect.right, self.rect.y)
        self.anchors['BL'] = (self.rect.x, self.rect.bottom)
        self.anchors['BR'] = (self.rect.right, self.rect.bottom)

    def draw(self, screen, track_model):
        """Draw toggle with active mode highlighted."""
        # Background frame
        pygame.draw.rect(screen, COLOR_PANEL, self.rect, border_radius=scale(5))

        # Define button areas
        self.piano_rect = pygame.Rect(self.rect.x + scale(5), self.rect.y + scale(5),
                                       scale(135), scale(30))
        self.pads_rect = pygame.Rect(self.rect.x + scale(145), self.rect.y + scale(5),
                                      scale(130), scale(30))

        # Highlight active mode
        if track_model.mode == "SYNTH":
            pygame.draw.rect(screen, COLOR_ACCENT, self.piano_rect, border_radius=scale(3))
            piano_color, pads_color = (0, 0, 0), (200, 200, 200)
        else:  # SAMPLER mode
            pygame.draw.rect(screen, COLOR_ACCENT, self.pads_rect, border_radius=scale(3))
            piano_color, pads_color = (200, 200, 200), (0, 0, 0)

        # Draw text
        piano_surf = self.font.render("PIANO ROLL", True, piano_color)
        pads_surf = self.font.render("SAMPLE PADS", True, pads_color)

        screen.blit(piano_surf, (self.piano_rect.centerx - piano_surf.get_width()//2,
                                  self.piano_rect.centery - piano_surf.get_height()//2))
        screen.blit(pads_surf, (self.pads_rect.centerx - pads_surf.get_width()//2,
                                self.pads_rect.centery - pads_surf.get_height()//2))

    def handle_event(self, event, track_model):
        """Toggle mode on click."""
        if self.piano_rect is None or self.pads_rect is None:
            return None

        if hasattr(event, 'pos'):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.piano_rect.collidepoint(event.pos):
                    if track_model.mode != "SYNTH":
                        # Switch to PIANO ROLL mode
                        # Restore last synth used in SYNTH mode
                        track_model.mode = "SYNTH"
                        track_model.is_drum = False
                        if hasattr(track_model, 'last_synth_source'):
                            track_model.source_type = track_model.last_synth_source
                        # else: keeps current source_type
                        return "MODE_CHANGED"

                elif self.pads_rect.collidepoint(event.pos):
                    if track_model.mode != "SAMPLER":
                        # Switch to SAMPLE PADS mode
                        # Save current synth before switching
                        track_model.last_synth_source = track_model.source_type
                        track_model.mode = "SAMPLER"
                        track_model.is_drum = True
                        return "MODE_CHANGED"
        return None
