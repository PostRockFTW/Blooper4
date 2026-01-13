# Blooper4/components/base_element.py
import pygame
import constants 

class BaseUIElement:
    """
    The Universal Parent for all 4.0 Widgets (Toolbars) and Plugins (EQ/Synth).
    Handles spatial awareness, Anchor-based docking, and Scaling.
    """
    def __init__(self, x, y, w, h):
        
        # Base dimensions (the 'unscaled' stock size)
        self.base_rect = pygame.Rect(x, y, w, h)
        # Current dimensions (adjusted for UI_SCALE)
        self.rect = pygame.Rect(x, y, w, h)
        
        self.is_visible = True

        self.plugin_id = "BASE" # Overridden by children (e.g., "EQ", "DUAL_OSC")
        self.title = "Base Module"

        self.anchors = {
            'TL': (x, y),
            'TR': (x + w, y),
            'BL': (x, y + h),
            'BR': (x + w, y + h)
        }

        # --- THE FIX: Register for global release ---
        if self not in constants.ACTIVE_COMPONENTS:
            constants.ACTIVE_COMPONENTS.append(self)

    def update_layout(self, scale):
        """Recalculates the screen rect and anchors based on scale."""
        self.rect.width = int(self.base_rect.width * scale)
        self.rect.height = int(self.base_rect.height * scale)
        
        # Anchors are always screen-absolute coordinates
        self.anchors['TL'] = (self.rect.x, self.rect.y)
        self.anchors['TR'] = (self.rect.right, self.rect.y)
        self.anchors['BL'] = (self.rect.x, self.rect.bottom)
        self.anchors['BR'] = (self.rect.right, self.rect.bottom)

    def dock_to(self, other_element, my_corner='TL', target_corner='TR', offset=(0,0)):
        """
        Anchors this widget to another widget.
        Example: Dock my Top-Left (TL) to your Top-Right (TR).
        """
        target_pos = other_element.anchors.get(target_corner)
        if target_pos:
            self.rect.x = target_pos[0] + offset[0]
            self.rect.y = target_pos[1] + offset[1]
            # Immediately update our own anchors so the next widget can dock to us
            self.update_layout(constants.UI_SCALE)

    def draw_modular_frame(self, screen, font, title, active, scale):
        """
        Standardizes the look of all 300px boxes in the Builder.
        Handles the Power Toggle and Delete X automatically.
        """
        # 1. Background Box
        bg_color = (40, 40, 45) if active else (25, 25, 30)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=int(10 * scale))
        pygame.draw.rect(screen, (70, 70, 80), self.rect, 2, border_radius=int(10 * scale))

        # 2. Title
        title_txt = font.render(title, True, constants.COLOR_ACCENT if active else (100, 100, 105))
        screen.blit(title_txt, (self.rect.x + int(10 * scale), self.rect.y + int(10 * scale)))

        # 3. Power Button (Green/Red Circle)
        p_col = (0, 255, 100) if active else (255, 50, 50)
        p_center = (self.rect.right - int(50 * scale), self.rect.y + int(20 * scale))
        pygame.draw.circle(screen, p_col, p_center, int(8 * scale))

        # 4. Delete Button (X)
        x_txt = font.render("X", True, (200, 200, 200))
        screen.blit(x_txt, (self.rect.right - int(25 * scale), self.rect.y + int(10 * scale)))

    def check_standard_interactions(self, pos, scale):
        """
        Generic handler for the Power and Delete buttons found on every module.
        Returns: 'TOGGLE', 'DELETE', or None.
        """
        # Power Button Hitbox
        p_rect = pygame.Rect(0, 0, 30 * scale, 30 * scale)
        p_rect.center = (self.rect.right - int(50 * scale), self.rect.y + int(20 * scale))
        if p_rect.collidepoint(pos):
            return "TOGGLE"
            
        # Delete Button Hitbox
        d_rect = pygame.Rect(self.rect.right - int(30 * scale), self.rect.y, 30 * scale, 30 * scale)
        if d_rect.collidepoint(pos):
            return "DELETE"
            
        return None

    def global_release(self):
        """
        Universal reset for all sub-components (Sliders, etc).
        Ensures nothing stays 'stuck' to the mouse.
        """
        # To be overridden by children who own Sliders/RadioGroups
        pass