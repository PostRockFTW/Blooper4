# Blooper4/ui_components.py
import pygame
import math
from constants import *

class Button:
    """
    A clickable UI box.
    Inputs:
        x, y (int): Top-left corner position.
        w, h (int): Width and Height.
        text (str): String label displayed in center.
        color (tuple): RGB tuple for background.
        border_radius (int): Optional corner rounding.
    """
    def __init__(self, x, y, w, h, text, color, border_radius=5):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.radius = border_radius
        self.enabled = True 

    def draw(self, screen, font):
        draw_color = self.color if self.enabled else (40, 40, 45)
        text_color = WHITE if self.enabled else (80, 80, 85)
        
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=self.radius)
        # Subtle top-lighting highlight
        if self.enabled:
            pygame.draw.line(screen, (255, 255, 255, 30), (self.rect.x, self.rect.y), (self.rect.right, self.rect.y))
        
        # Draw the standardized border
        pygame.draw.rect(screen, (255, 255, 255, 20), self.rect, 1, border_radius=self.radius)
        
        txt = font.render(self.text, True, text_color)
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def is_clicked(self, pos):
        """Returns True only if enabled and position is inside bounds."""
        return self.enabled and self.rect.collidepoint(pos)

    def move_to(self, x, y, w=None, h=None):
        """Updates position and optionally resizes for scaling."""
        self.rect.x = x
        self.rect.y = y
        # FIX: Ensure width and height are updated for collision detection!
        if w is not None: self.rect.width = w
        if h is not None: self.rect.height = h

class RadioGroup:
    """
    A set of mutually exclusive toggle buttons.
    Inputs:
        x, y (int): Top-left corner of the button group area.
        options (list): List of strings for labels.
        font (pygame.font): Font object for labels.
        cols (int): Buttons per row before wrapping.
        default_idx (int): Which index starts selected.
    """
    def __init__(self, x, y, options, font, cols=5, default_idx=0):
        self.options = options
        self.selected = options[default_idx] if default_idx < len(options) else (options[0] if options else "")
        self.buttons = []
        self.cols = cols
        
        # Initial construction (default sizes)
        #self.move_to(x, y, 55, 22)
        self.move_to(x, y)

    def draw(self, screen, font):
        for btn in self.buttons:
            is_sel = btn['text'] == self.selected
            color = COLOR_ACCENT if is_sel else (60, 60, 65)
            pygame.draw.rect(screen, color, btn['rect'], border_radius=3)
            
            txt_color = BLACK if is_sel else WHITE
            txt = font.render(btn['text'], True, txt_color)
            screen.blit(txt, (btn['rect'].centerx - txt.get_width()//2, btn['rect'].centery - txt.get_height()//2))

    def handle_event(self, event):
        """Checks for clicks and updates the internal selection state."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn['rect'].collidepoint(event.pos):
                    self.selected = btn['text']
                    return self.selected
        return None
    
    def move_to(self, x, y, btn_w=55, btn_h=22):
        """Re-calculates button grid layout."""
        self.buttons = []
        # Use scale() from constants to ensure button size matches theme
        from constants import scale
        sw, sh = scale(btn_w), scale(btn_h)
        gap = scale(5)
        for i, opt in enumerate(self.options):
            bx = x + (i % self.cols) * (sw + gap)
            by = y + (i // self.cols) * (sh + gap)
            self.buttons.append({'rect': pygame.Rect(bx, by, sw, sh), 'text': opt})

class MenuButton:
    """
    A square 'Hamburger' icon button used for global navigation.
    Inputs:
        x, y (int): Screen coordinates.
        size (int): Width and height of the button.
    """
    def __init__(self, x, y, size=40):
        self.rect = pygame.Rect(x, y, size, size)

    def draw(self, screen):
        # Draw background container
        pygame.draw.rect(screen, (45, 45, 50), self.rect, border_radius=3)
        pygame.draw.rect(screen, (70, 70, 75), self.rect, 1, border_radius=3)
        
        # Draw 3 horizontal lines (proportionally)
        line_w = self.rect.width * 0.6
        start_x = self.rect.x + (self.rect.width - line_w) // 2
        for i in range(3):
            ly = self.rect.y + (self.rect.height * 0.3) + (i * (self.rect.height * 0.2))
            pygame.draw.line(screen, WHITE, (start_x, ly), (start_x + line_w, ly), 2)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Slider:
    """
    A generic value controller.
    Inputs:
        x, y, w, h: Rect bounds.
        min_val, max_val: Floating point range.
        start_val: Initial position.
        label: Text displayed above or near slider.
        vertical: Boolean orientation.
    """
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label, vertical=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.vertical = vertical
        self.grabbed = False

    def draw(self, screen, font):
        # Track Background
        pygame.draw.rect(screen, (20, 20, 25), self.rect, border_radius=3)
        
        # Handle position calculation
        range_val = self.max_val - self.min_val
        ratio = (self.val - self.min_val) / range_val if range_val != 0 else 0
        
        if self.vertical:
            handle_y = self.rect.bottom - (ratio * self.rect.height) - 5
            handle_rect = pygame.Rect(self.rect.x - 5, handle_y, self.rect.width + 10, 10)
        else:
            handle_x = self.rect.x + (ratio * self.rect.width) - 5
            handle_rect = pygame.Rect(handle_x, self.rect.y - 5, 10, self.rect.height + 10)
            
        pygame.draw.rect(screen, COLOR_ACCENT, handle_rect, border_radius=2)
        
        if self.label:
            # High precision for small ranges (mix/gain), integers for MIDI ranges
            display_val = f"{self.val:.2f}" if range_val <= 2 else f"{int(self.val)}"
            txt = font.render(f"{self.label}: {display_val}", True, WHITE)
            screen.blit(txt, (self.rect.x, self.rect.y - 20))

    def handle_event(self, event):
        # Increased hitbox for easier grabbing
        hitbox = self.rect.inflate(20, 20)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hitbox.collidepoint(event.pos):
                self.grabbed = True
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False

        if self.grabbed:
            m_pos = pygame.mouse.get_pos()
            # SAFETY: Clamp mouse coordinates to window bounds to prevent offscreen crashes
            from constants import WINDOW_W, WINDOW_H
            clamped_x = max(0, min(m_pos[0], WINDOW_W - 1))
            clamped_y = max(0, min(m_pos[1], WINDOW_H - 1))

            if self.vertical:
                rel = 1.0 - (max(0, min(clamped_y - self.rect.y, self.rect.height)) / self.rect.height)
            else:
                rel = (max(0, min(clamped_x - self.rect.x, self.rect.width)) / self.rect.width)
            self.val = self.min_val + rel * (self.max_val - self.min_val)
            return self.val
        return None
    
    def move_to(self, x, y, w=None, h=None):
        """Adjusts placement and size dynamically."""
        self.rect.x = x
        self.rect.y = y
        if w: self.rect.width = w
        if h: self.rect.height = h

class Dropdown:
    """
    A dropdown menu that displays a list of options when opened.
    Inputs:
        x, y (int): Position of the dropdown trigger button
        w, h (int): Size of the trigger button
        options (list): List of string options to display
        label (str): Text to show on the trigger button
    """
    def __init__(self, x, y, w, h, options, label="SELECT"):
        self.rect = pygame.Rect(x, y, w, h)  # Trigger button area
        self.options = options
        self.label = label
        self.is_open = False
        self.selected_option = None
        self.dropdown_rect = None  # Calculated in draw()

    def draw(self, screen, font):
        """Draw the trigger button and dropdown menu if open."""
        # Draw trigger button
        pygame.draw.rect(screen, COLOR_PANEL, self.rect, border_radius=scale(5))

        # Display label
        txt_surf = font.render(self.label, True, WHITE)
        screen.blit(txt_surf, (self.rect.x + scale(10),
                              self.rect.centery - txt_surf.get_height()//2))

        # Dropdown arrow
        arrow = font.render("▼", True, WHITE)
        screen.blit(arrow, (self.rect.right - scale(30),
                           self.rect.centery - arrow.get_height()//2))

        # Draw dropdown menu if open
        if self.is_open:
            # Position dropdown below trigger
            self.dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom + scale(5),
                self.rect.width,
                scale(30 * len(self.options))
            )

            # Draw background
            pygame.draw.rect(screen, COLOR_PANEL, self.dropdown_rect, border_radius=scale(5))
            pygame.draw.rect(screen, COLOR_ACCENT, self.dropdown_rect, width=2, border_radius=scale(5))

            # Draw options
            mouse_pos = pygame.mouse.get_pos()
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.dropdown_rect.x + scale(5),
                    self.dropdown_rect.y + scale(5) + i * scale(30),
                    self.dropdown_rect.width - scale(10),
                    scale(25)
                )

                # Highlight on hover
                if option_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, (60, 60, 70), option_rect, border_radius=scale(3))

                txt_surf = font.render(option, True, WHITE)
                screen.blit(txt_surf, (option_rect.x + scale(5), option_rect.y + scale(5)))

    def handle_event(self, event):
        """
        Handle click events.
        Returns:
            - Selected option string if user clicked an option
            - "TOGGLE" if user clicked the trigger button
            - None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicked on trigger button
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return "TOGGLE"

            # Check if clicked on dropdown option (when open)
            if self.is_open and self.dropdown_rect and self.dropdown_rect.collidepoint(event.pos):
                idx = (event.pos[1] - self.dropdown_rect.y - scale(5)) // scale(30)
                if 0 <= idx < len(self.options):
                    self.selected_option = self.options[idx]
                    self.is_open = False
                    return self.selected_option

            # Click outside dropdown - close it
            if self.is_open:
                self.is_open = False

        return None

    def move_to(self, x, y, w=None, h=None):
        """Updates position and optionally resizes."""
        self.rect.x = x
        self.rect.y = y
        if w is not None: self.rect.width = w
        if h is not None: self.rect.height = h

    def set_label(self, label):
        """Update the trigger button label."""
        self.label = label

class Knob:
    def __init__(self, x, y, size, min_val, max_val, start_val, label, is_log=False):
        self.rect = pygame.Rect(x, y, size, size)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.is_log = is_log
        self.grabbed = False
        self.sensivity = 0.005 # How fast it turns

    def draw(self, screen, font, scale_f):
        # Draw background circle
        cx, cy = self.rect.center
        r = self.rect.width // 2
        pygame.draw.circle(screen, (35, 35, 40), (cx, cy), r)
        pygame.draw.circle(screen, (60, 60, 65), (cx, cy), r, 2)

        # Calculate angle based on value
        # Logarithmic vs Linear conversion
        if self.is_log:
            # Avoid log(0)
            v_min = math.log(max(0.001, self.min_val))
            v_max = math.log(self.max_val)
            v_cur = math.log(max(0.001, self.val))
            ratio = (v_cur - v_min) / (v_max - v_min) if v_max != v_min else 0
        else:
            ratio = (self.val - self.min_val) / (self.max_val - self.min_val)

        # Map ratio to 270 degrees of rotation (start at 135 deg)
        angle = math.radians(135 + ratio * 270)
        line_len = r * 0.8
        end_x = cx + math.cos(angle) * line_len
        end_y = cy + math.sin(angle) * line_len
        
        from constants import COLOR_ACCENT
        pygame.draw.line(screen, COLOR_ACCENT, (cx, cy), (end_x, end_y), 3)
        
        # Label
        lbl = font.render(self.label, True, (180, 180, 180))
        screen.blit(lbl, (cx - lbl.get_width()//2, self.rect.bottom + 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.grabbed = True
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False

        if self.grabbed and event.type == pygame.MOUSEMOTION:
            # Industry standard: Vertical drag moves the knob
            dy = -event.rel[1] 
            
            if self.is_log:
                # Logarithmic movement is tricky, let's work in 'ratio' space
                v_min, v_max = math.log(max(0.001, self.min_val)), math.log(self.max_val)
                curr_log = math.log(max(0.001, self.val))
                ratio = (curr_log - v_min) / (v_max - v_min)
                ratio = max(0, min(1, ratio + dy * self.sensivity))
                self.val = math.exp(v_min + ratio * (v_max - v_min))
            else:
                diff = self.max_val - self.min_val
                self.val = max(self.min_val, min(self.max_val, self.val + dy * self.sensivity * diff))
            
            return self.val
        return None

    def move_to(self, x, y, size=None):
        self.rect.x, self.rect.y = x, y
        if size: self.rect.width = self.rect.height = size