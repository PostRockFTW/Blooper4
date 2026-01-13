# Blooper4/containers/main_menu.py
import pygame
from constants import *
from containers.base_view import BaseView
from ui_components import Button

class MainMenu(BaseView):
    """
    4.0 Splash Screen & Settings Hub.
    Handles Fullscreen toggles and dynamic UI Scaling.
    """
    def __init__(self, font):
        # Menu takes the full screen (No header or mixer reserved)
        super().__init__(font, has_header=False, has_mixer=False)
        
        self.state = "MAIN" # "MAIN" or "VIDEO"
        
        # --- MAIN MENU BUTTONS ---
        # Positioned logically (unscaled); layout() handles scaling/centering
        self.main_buttons = {
            "RESUME":     Button(0, 0, 250, 45, "RESUME", (60, 60, 70)),
            "NEW":        Button(0, 0, 250, 45, "NEW PROJECT", BLUE),
            "LOAD":       Button(0, 0, 250, 45, "LOAD PROJECT", GRAY),
            "SAVE":       Button(0, 0, 250, 45, "SAVE PROJECT", GRAY),
            "VIDEO":      Button(0, 0, 250, 45, "VIDEO SETTINGS", GRAY),
            "EXIT":       Button(0, 0, 250, 45, "EXIT DAW", (150, 50, 50))
        }

        # --- VIDEO SETTINGS BUTTONS ---
        self.video_buttons = {
            "SCALE_UP":   Button(0, 0, 60, 50, "+", GREEN),
            "SCALE_DOWN": Button(0, 0, 60, 50, "-", RED),
            "FULLSCREEN": Button(0, 0, 250, 50, "TOGGLE FULLSCREEN", (100, 100, 110)),
            "BACK":       Button(0, 0, 250, 50, "BACK", GRAY)
        }

    def _layout_buttons(self):
        """Centers buttons based on current UI_SCALE."""
        cx = WINDOW_W // 2
        cy = WINDOW_H // 2
        
        # Scale button dimensions
        bw, bh = scale(250), scale(50)
        gap = scale(15)

        if self.state == "MAIN":
            y_start = cy - (len(self.main_buttons) * (bh + gap)) // 2
            for i, btn in enumerate(self.main_buttons.values()):
                btn.move_to(cx - bw // 2, y_start + i * (bh + gap), bw, bh)
        
        elif self.state == "VIDEO":
            y_start = cy - scale(100)
            # Scale control row
            sw, sh = scale(60), scale(50)
            self.video_buttons["SCALE_DOWN"].move_to(cx - sw - scale(10), y_start, sw, sh)
            self.video_buttons["SCALE_UP"].move_to(cx + scale(10), y_start, sw, sh)
            
            # Other video buttons
            self.video_buttons["FULLSCREEN"].move_to(cx - bw // 2, y_start + scale(70), bw, bh)
            self.video_buttons["BACK"].move_to(cx - bw // 2, y_start + scale(140), bw, bh)

    def draw(self, screen):
        # 1. Maintenance
        self.update_view_rect()
        self._layout_buttons()
        
        # 2. Draw Background
        pygame.draw.rect(screen, (15, 15, 20), self.rect)
        
        # 3. Draw Title
        title_size = scale(72)
        title_font = pygame.font.SysFont("Consolas", title_size, bold=True)
        title_txt = title_font.render("BLOOPER 4.0", True, COLOR_ACCENT)
        screen.blit(title_txt, (WINDOW_W//2 - title_txt.get_width()//2, scale(100)))

        # 4. Draw Current Sub-Menu
        buttons = self.main_buttons if self.state == "MAIN" else self.video_buttons
        for btn in buttons.values():
            btn.draw(screen, self.font)
            
        # Draw current scale info if in video menu
        if self.state == "VIDEO":
            scale_info = self.font.render(f"CURRENT SCALE: {int(UI_SCALE * 100)}%", True, WHITE)
            screen.blit(scale_info, (WINDOW_W//2 - scale_info.get_width()//2, WINDOW_H//2 - scale(140)))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "MAIN":
                if self.main_buttons["RESUME"].is_clicked(event.pos): return "RESUME"
                if self.main_buttons["EXIT"].is_clicked(event.pos): return "EXIT"
                if self.main_buttons["NEW"].is_clicked(event.pos): return "NEW"
                if self.main_buttons["LOAD"].is_clicked(event.pos): return "LOAD"
                if self.main_buttons["SAVE"].is_clicked(event.pos): return "SAVE"
                
                if self.main_buttons["VIDEO"].is_clicked(event.pos): 
                    self.state = "VIDEO"
                    return "MENU_NAVIGATE" # Tell main.py we handled the click
            
            elif self.state == "VIDEO":
                if self.video_buttons["BACK"].is_clicked(event.pos): 
                    self.state = "MAIN"
                    return "MENU_NAVIGATE"
                
                if self.video_buttons["FULLSCREEN"].is_clicked(event.pos): return "TOGGLE_FS"
                
                import constants
                if self.video_buttons["SCALE_UP"].is_clicked(event.pos):
                    constants.UI_SCALE = min(2.0, constants.UI_SCALE + 0.1)
                    return "REBUILD_UI"
                if self.video_buttons["SCALE_DOWN"].is_clicked(event.pos):
                    constants.UI_SCALE = max(0.5, constants.UI_SCALE - 0.1)
                    return "REBUILD_UI"
        
        return None