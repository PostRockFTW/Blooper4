# Blooper4/containers/base_view.py
import pygame
from constants import *

class BaseView:
    """
    The Layout Manager for Blooper 4.0 screens.
    Calculates the 'Main Working Area' based on scaling and layout requirements.
    """
    def __init__(self, font, has_header=True, has_mixer=True):
        self.font = font
        self.has_header = has_header
        self.has_mixer = has_mixer
        
        # This list will hold the Widgets (Components) assigned to this view
        self.widgets = []
        
        # Calculate the 'Safe Zone' for content
        self.update_view_rect()

    def update_view_rect(self):
        """Recalculates the screen area available between the header and mixer."""
        top_offset = scale(HEADER_H) if self.has_header else 0
        bottom_offset = scale(MIXER_H) if self.has_mixer else 0
        
        # The main 'stage' rect
        self.rect = pygame.Rect(
            0, 
            top_offset, 
            WINDOW_W, 
            WINDOW_H - top_offset - bottom_offset
        )

    def draw_widgets(self, screen):
        """Standard loop to draw all widgets attached to this view."""
        for widget in self.widgets:
            if hasattr(widget, 'draw') and widget.is_visible:
                # Most 4.0 widgets now expect scale in their draw call
                widget.draw(screen)

    def handle_widget_events(self, event):
        """Standard loop to route events to widgets."""
        for widget in self.widgets:
            if hasattr(widget, 'handle_event') and widget.is_visible:
                widget.handle_event(event)