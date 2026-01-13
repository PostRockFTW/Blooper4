# Blooper4/components/mixer_strip.py
import pygame
from constants import *
from components.base_element import BaseUIElement

class ChannelStrip(BaseUIElement):
    """
    4.0 Channel Strip: A scalable vertical slice of the mixer.
    Inherits from BaseUIElement to support Anchors and Scaling.
    """
    def __init__(self, index, x, y, w, h):
        super().__init__(x, y, w, h)
        self.idx = index
        # We define logical offsets (unscaled) for internal UI
        # These will be multiplied by the scale factor during draw()
        self.logical_pan_y = 35
        self.logical_fader_y = 60
        self.logical_btns_y = h - 40

    def draw(self, screen, track, is_active, font, scale_f):
        # 1. Update the main container rect based on global scale
        self.update_layout(scale_f)
        
        # 2. Draw Background
        bg_color = (40, 40, 45) if is_active else (25, 25, 30)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=int(3 * scale_f))
        pygame.draw.rect(screen, (60, 60, 65), self.rect, 1, border_radius=int(3 * scale_f))

        # 3. Track Label
        color = COLOR_ACCENT if is_active else WHITE
        txt_num = font.render(str(track.channel), True, color)
        screen.blit(txt_num, (self.rect.x + int(5 * scale_f), self.rect.y + int(5 * scale_f)))
        
        # 4. Pan Slider (Scalable)
        pan_rect = pygame.Rect(self.rect.x + int(10 * scale_f), 
                               self.rect.y + int(self.logical_pan_y * scale_f), 
                               self.rect.width - int(20 * scale_f), int(8 * scale_f))
        pygame.draw.rect(screen, (10, 10, 10), pan_rect, border_radius=int(4 * scale_f))
        
        pan_val = track.params.get("pan", 0.5)
        handle_x = pan_rect.x + (pan_val * pan_rect.width)
        pygame.draw.rect(screen, WHITE, (handle_x - 2, pan_rect.y - 2, 4, int(12 * scale_f)))

        # 5. Volume Fader (Scalable)
        fader_area = pygame.Rect(self.rect.x + int(self.rect.width // 2 - 5), 
                                 self.rect.y + int(self.logical_fader_y * scale_f), 
                                 int(10 * scale_f), self.rect.height - int(130 * scale_f))
        pygame.draw.rect(screen, (10, 10, 10), fader_area)
        
        vol = track.params.get("volume", 0.8)
        handle_y = fader_area.bottom - (vol * fader_area.height)
        pygame.draw.rect(screen, COLOR_ACCENT, (fader_area.x - int(10 * scale_f), handle_y - 5, int(30 * scale_f), 10), border_radius=2)

        # 6. Mute / Solo Buttons
        btn_w = (self.rect.width // 2) - int(5 * scale_f)
        mute_rect = pygame.Rect(self.rect.x + int(5 * scale_f), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        solo_rect = pygame.Rect(self.rect.x + (self.rect.width // 2), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        
        m_col = RED if track.params.get("mute", False) else (60, 60, 65)
        s_col = (255, 200, 0) if track.params.get("solo", False) else (60, 60, 65)
        
        pygame.draw.rect(screen, m_col, mute_rect, border_radius=3)
        pygame.draw.rect(screen, s_col, solo_rect, border_radius=3)
        
        screen.blit(font.render("M", True, WHITE), (mute_rect.x + int(8 * scale_f), mute_rect.y + 5))
        screen.blit(font.render("S", True, BLACK if track.params.get("solo", False) else WHITE), (solo_rect.x + int(8 * scale_f), solo_rect.y + 5))

    def handle_event(self, event, track, scale_f):
        # We re-calculate hitboxes during event handling to match current scale
        btn_w = (self.rect.width // 2) - int(5 * scale_f)
        mute_rect = pygame.Rect(self.rect.x + int(5 * scale_f), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        solo_rect = pygame.Rect(self.rect.x + (self.rect.width // 2), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        pan_rect = pygame.Rect(self.rect.x + int(10 * scale_f), self.rect.y + int(self.logical_pan_y * scale_f), self.rect.width - int(20 * scale_f), int(15 * scale_f))
        fader_area = pygame.Rect(self.rect.x + int(self.rect.width // 2 - 15), self.rect.y + int(self.logical_fader_y * scale_f), int(30 * scale_f), self.rect.height - int(130 * scale_f))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if mute_rect.collidepoint(event.pos):
                track.params["mute"] = not track.params.get("mute", False)
                return "UPDATE"
            if solo_rect.collidepoint(event.pos):
                track.params["solo"] = not track.params.get("solo", False)
                return "UPDATE"
            if self.rect.collidepoint(event.pos) and not fader_area.collidepoint(event.pos) and not pan_rect.collidepoint(event.pos):
                return "SELECT"

        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if fader_area.collidepoint(m_pos):
                rel_y = fader_area.bottom - m_pos[1]
                track.params["volume"] = max(0.0, min(1.0, rel_y / fader_area.height))
                return "UPDATE"
            if pan_rect.collidepoint(m_pos):
                rel_x = m_pos[0] - pan_rect.x
                track.params["pan"] = max(0.0, min(1.0, rel_x / pan_rect.width))
                return "UPDATE"
        return None