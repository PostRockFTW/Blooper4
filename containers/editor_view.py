# Blooper4/containers/editor_view.py
import pygame
from constants import *
from containers.base_view import BaseView
from components.note_type_toolbar import NoteTypeToolbar
from components.piano_roll import PianoRoll
from components.drum_roll import DrumRoll

class EditorView(BaseView):
    def __init__(self, font):
        super().__init__(font, has_header=True, has_mixer=True)
        
        # 1. Toolbar
        self.toolbar = NoteTypeToolbar(self.rect.x, self.rect.y, self.rect.width, scale(60), font)
        
        # 2. Grids
        grid_w = self.rect.width - scale(EDITOR_SIDEBAR_W)
        grid_h = self.rect.height - scale(60)
        self.piano_roll = PianoRoll(0, 0, grid_w, grid_h)
        self.drum_roll = DrumRoll(0, 0, grid_w, grid_h)
        
        # 3. Register for events and global releases
        self.widgets = [self.toolbar, self.piano_roll, self.drum_roll]
        self.quantize = "1/16"
        self.input_velocity = 100

    def draw(self, screen, song, active_idx, current_tick, font):
        track = song.tracks[active_idx]
        grid = self.drum_roll if track.is_drum else self.piano_roll
        
        # Maintenance
        self.update_view_rect()
        self.toolbar.draw(screen, song)
        
        # Dynamic Docking
        grid.dock_to(self.toolbar, my_corner='TL', target_corner='BL', offset=(scale(EDITOR_SIDEBAR_W), 0))
        grid.draw(screen, track, current_tick, font)

        # Sidebar
        sidebar_rect = pygame.Rect(0, grid.rect.y, scale(EDITOR_SIDEBAR_W), grid.rect.height)
        pygame.draw.rect(screen, COLOR_PANEL, sidebar_rect)
        pygame.draw.line(screen, (60, 60, 70), (sidebar_rect.right, sidebar_rect.top), (sidebar_rect.right, sidebar_rect.bottom), 2)
        
        self._draw_labels(screen, track, grid, sidebar_rect, font)

    def _draw_labels(self, screen, track, grid, sidebar_rect, font):
        # 4.1 Logic: If track is a Sampler, show Pad Labels
        if track.mode == "SAMPLER":
            for p in range(128):
                _, y = grid.get_coords(0, p)
                if sidebar_rect.top <= y <= sidebar_rect.bottom:
                    pad_cfg = track.sampler_map.get(p, {})
                    # Show User Label or default to Pad number
                    label = pad_cfg.get("label") or f"Pad {p}"
                    # Add a tiny indicator of what engine is on that pad
                    eng = pad_cfg.get("engine", "NONE")[:3]
                    lbl = font.render(f"{label} [{eng}]", True, WHITE)
                    screen.blit(lbl, (5, y + (grid.row_h // 2 - 6)))
        else:
            # Standard Piano Roll Labels
            for p in range(128):
                _, y = grid.get_coords(0, p)
                if sidebar_rect.top <= y <= sidebar_rect.bottom:
                    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                    lbl = font.render(f"{notes[p%12]}{p//12}", True, WHITE)
                    screen.blit(lbl, (5, y + 2))

    def handle_event(self, event, song, active_idx):
        mx, my = pygame.mouse.get_pos()
        track = song.tracks[active_idx]
        grid = self.drum_roll if track.is_drum else self.piano_roll

        # --- THE FIX: Local Mouse Release ---
        if event.type == pygame.MOUSEBUTTONUP:
            self.piano_roll.is_dragging = False
            self.drum_roll.is_dragging = False
            self.piano_roll.current_note = None
            self.drum_roll.current_note = None
            self.toolbar.vel_slider.grabbed = False
            return
        
        # Route to Toolbar
        if self.toolbar.rect.collidepoint((mx, my)):
            t_data = self.toolbar.handle_event(event, song)
            self.quantize = t_data.get("quantize", "1/16")
            self.input_velocity = t_data.get("velocity", 100)
            return


        if grid.rect.collidepoint((mx, my)):
            if event.type == pygame.MOUSEWHEEL:
                # Horizontal Scroll (CTRL + Wheel)
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    grid.scroll_x = max(0, grid.scroll_x - event.y * 120)
                else:
                    # Vertical Scroll (Standard Wheel)
                    # We removed 'if not track.is_drum' so it works for both!
                    scroll_speed = scale(GRID_HEIGHT) * 2
                    grid.scroll_y = max(0, min(127 * scale(GRID_HEIGHT), grid.scroll_y - event.y * scroll_speed))
                    
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                tick, pitch = grid.get_tick_at(mx), grid.get_pitch_at(my)
                q = QUANT_MAP[self.quantize]
                quant_tick = (tick // q) * q
                existing = next((n for n in track.notes if n.pitch == pitch and n.tick <= tick < n.tick + n.duration), None)
                if existing:
                    track.notes.remove(existing)
                    self.toolbar.log(f"Del: {pitch}")
                else:
                    grid.is_dragging = True
                    grid.current_note = track.add_note(quant_tick, pitch, q, velocity=int(self.input_velocity))
                    self.toolbar.log(f"Add: {pitch}")
                song.is_dirty = True

            # --- THE FIX: Only update duration if left button is actually held ---
            if event.type == pygame.MOUSEMOTION and grid.is_dragging:
                if pygame.mouse.get_pressed()[0]: # Verified hold
                    q = QUANT_MAP[self.quantize]
                    mouse_tick = grid.get_tick_at(mx)
                    grid.current_note.duration = max(q, ((mouse_tick // q) + 1) * q - grid.current_note.tick)
                else:
                    # Safety reset if we somehow missed the MOUSEBUTTONUP
                    grid.is_dragging = False