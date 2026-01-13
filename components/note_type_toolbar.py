# Blooper4/components/note_type_toolbar.py
import pygame
from constants import *
from components.base_element import BaseUIElement
from ui_components import RadioGroup, Slider, Button

class NoteTypeToolbar(BaseUIElement):
    def __init__(self, x, y, w, h, font):
        super().__init__(x, y, w, h)
        self.font = font
        
        # We initialize sub-components with 0,0; they will be moved during draw()
        self.quant_menu = RadioGroup(0, 0, QUANT_LABELS, font, cols=4)
        self.btn_add_bar = Button(0, 0, 60, 22, "+ BAR", (60, 60, 70))
        self.btn_rem_bar = Button(0, 0, 60, 22, "- BAR", (60, 60, 70))
        self.vel_slider = Slider(0, 0, 150, 10, 1, 127, 100, "VELOCITY")
        
        self.debug_log = ["4.0 Editor Ready"]

    def log(self, message):
        self.debug_log.append(message)
        if len(self.debug_log) > 4: self.debug_log.pop(0)

    def draw(self, screen, song):
        # 1. Update layout based on current UI_SCALE
        self.update_layout(UI_SCALE)
        
        # 2. Draw Background
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.rect(screen, (60, 60, 70), self.rect, 1)

        # 3. Position and Draw Sub-components (Relative to self.rect)
        self.quant_menu.move_to(self.rect.x + scale(10), self.rect.y + scale(10))
        self.quant_menu.draw(screen, self.font)

        self.btn_add_bar.move_to(self.rect.x + scale(300), self.rect.y + scale(10))
        self.btn_rem_bar.move_to(self.rect.x + scale(365), self.rect.y + scale(10))
        self.btn_rem_bar.enabled = (song.length_ticks > TPQN * 4)
        self.btn_add_bar.draw(screen, self.font)
        self.btn_rem_bar.draw(screen, self.font)

        self.vel_slider.move_to(self.rect.x + scale(450), self.rect.y + scale(25))
        self.vel_slider.draw(screen, self.font)

        # 4. Draw Debug Window
        debug_rect = pygame.Rect(self.rect.right - scale(260), self.rect.y + scale(5), scale(250), scale(50))
        pygame.draw.rect(screen, (5, 5, 10), debug_rect, border_radius=scale(3))
        for i, msg in enumerate(self.debug_log):
            txt = self.font.render(f"> {msg}", True, (0, 255, 100))
            screen.blit(txt, (debug_rect.x + scale(5), debug_rect.y + scale(5) + (i * scale(11))))

    def handle_event(self, event, song):
        q_sel = self.quant_menu.handle_event(event)
        v_val = self.vel_slider.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_add_bar.is_clicked(event.pos):
                song.length_ticks += TPQN * 4
                self.log("Added Bar")
            if self.btn_rem_bar.is_clicked(event.pos):
                if song.length_ticks > TPQN * 4:
                    song.length_ticks -= TPQN * 4
                    self.log("Removed Bar")

        return {"quantize": self.quant_menu.selected, "velocity": self.vel_slider.val}

    def global_release(self):
        """Universal fix for sticky sliders in this component."""
        self.vel_slider.grabbed = False