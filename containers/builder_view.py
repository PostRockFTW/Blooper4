# Blooper4/containers/builder_view.py
import pygame
from constants import *
from containers.base_view import BaseView
from components.builder.sampler_brain import SamplerBrainUI
from components.builder.mode_toggle import ModeToggleUI
from components.builder.piano_roll_settings import PianoRollSettingsUI
from ui_components import Dropdown

class BuilderView(BaseView):
    def __init__(self, font, factory):
        super().__init__(font, has_header=True, has_mixer=True)
        self.factory = factory
        self.scroll_x = 0

        # UI Instance Cache
        self.ui_instances = {i: {"SOURCE": None, "SAMPLER_BRAIN": None, "FX": []} for i in range(NUM_TRACKS)}

         # FIX: Explicitly create the Sampler Brain UI once
        from components.builder.sampler_brain import SamplerBrainUI
        self.sampler_brain_ui = SamplerBrainUI(0, 0, self.font)

        # Master mode toggle (PIANO ROLL | SAMPLE PADS)
        self.mode_toggle_ui = ModeToggleUI(0, 0)

        # Piano roll settings (CHROMATIC | MODAL | MICROTONAL)
        self.piano_roll_settings_ui = PianoRollSettingsUI(0, 0, self.font)

        # Dropdown components
        self.source_dropdown = Dropdown(0, 0, scale(280), scale(40),
                                        list(factory.source_registry.keys()),
                                        "SOURCE: DUAL_OSC")

        self.fx_dropdown = Dropdown(0, 0, scale(180), scale(30),
                                   list(factory.effect_registry.keys()),
                                   "+ FX")

    def _sync_ui_instances(self, track, idx):
        data = self.ui_instances[idx]
        
        # 1. Sync Sampler Brain (Only if in Sampler Mode)
        if track.mode == "SAMPLER" and not data["SAMPLER_BRAIN"]:
            data["SAMPLER_BRAIN"] = SamplerBrainUI(0, 0, self.font)

        # 2. Sync Source UI
        target_source = track.source_type if track.mode == "SYNTH" else track.sampler_map[track.active_pad]["engine"]
        if not data["SOURCE"] or data["SOURCE"].plugin_id != target_source:
            ui_class = self.factory.get_ui_class(target_source)
            if ui_class:
                data["SOURCE"] = ui_class(0, 0, self.font)
                data["SOURCE"].plugin_id = target_source

        # 3. Sync FX Chain
        if len(data["FX"]) != len(track.effects):
            data["FX"] = []
            for fx in track.effects:
                ui_class = self.factory.get_ui_class(fx["type"])
                if ui_class:
                    instance = ui_class(0, 0, self.font)
                    instance.plugin_id = fx["type"]
                    data["FX"].append(instance)

    def draw(self, screen, song, active_idx):
        track = song.tracks[active_idx]
        self.update_view_rect()
        self._sync_ui_instances(track, active_idx)

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        pygame.draw.rect(screen, COLOR_BG, self.rect)

        ui_data = self.ui_instances[active_idx]

        # === TWO-COLUMN LAYOUT WITH HORIZONTAL SCROLL ===
        # Apply scroll_x to both columns so everything scrolls together
        left_x = self.rect.x + scale(20) - self.scroll_x
        right_x = left_x + scale(320)  # 300 (panel width) + 20 (gap)
        curr_y = self.rect.y + scale(10)

        # --- ROW 1: TOP BAR ---
        # Left: MODE TOGGLE
        self.mode_toggle_ui.move_to(left_x, curr_y)
        self.mode_toggle_ui.draw(screen, track)

        # Right: SOURCE SELECTOR DROPDOWN (position it, but draw it LAST for z-order)
        if track.mode == "SYNTH":
            self.source_dropdown.move_to(right_x, curr_y, scale(280), scale(40))
            self.source_dropdown.set_label(f"SOURCE: {track.source_type}")
        else:  # SAMPLER mode - show active pad's engine
            active_engine = track.sampler_map[track.active_pad]["engine"]
            self.source_dropdown.move_to(right_x, curr_y, scale(280), scale(40))
            self.source_dropdown.set_label(f"ENGINE: {active_engine}")

        curr_y = self.mode_toggle_ui.rect.bottom + scale(10)

        # --- ROW 2: MAIN CONTENT (TWO COLUMNS) ---
        # LEFT COLUMN: MODE-SPECIFIC PANEL (now scrolls with everything)
        if track.mode == "SAMPLER":
            self.sampler_brain_ui.draw(screen, track, left_x, curr_y, UI_SCALE)
        else:  # SYNTH mode
            self.piano_roll_settings_ui.draw(screen, track, left_x, curr_y, UI_SCALE)

        # RIGHT COLUMN: SOURCE RACK (Horizontal chain)
        curr_x = right_x
        prev_module = None

        # A. DRAW ACTIVE SOURCE
        if ui_data["SOURCE"]:
            ui_data["SOURCE"].rect.topleft = (curr_x, curr_y)

            if track.mode == "SYNTH":
                ui_data["SOURCE"].draw(screen, track, curr_x, curr_y, UI_SCALE)
            else:
                # Sampler mode: Pass proxy for active pad
                class PadProxy: pass
                proxy = PadProxy()
                proxy.source_params = track.sampler_map[track.active_pad]["params"]
                proxy.drum_pads = track.drum_pads
                ui_data["SOURCE"].draw(screen, proxy, curr_x, curr_y, UI_SCALE)

            prev_module = ui_data["SOURCE"]
            curr_x = prev_module.rect.right + scale(20)

        # B. DRAW FX CHAIN
        for i, fx_ui in enumerate(ui_data["FX"]):
            fx_ui.dock_to(prev_module, 'TL', 'TR', offset=(scale(20), 0))
            fx_ui.draw(screen, track.effects[i], fx_ui.rect.x, fx_ui.rect.y, UI_SCALE)
            prev_module = fx_ui
            curr_x = prev_module.rect.right + scale(20)

        # C. DRAW ADD FX BUTTON (position it for fx_dropdown)
        self.add_btn_rect = pygame.Rect(curr_x, curr_y, scale(80), scale(60))
        pygame.draw.rect(screen, (30, 30, 35), self.add_btn_rect, border_radius=scale(10))
        txt = self.font.render("+ FX", True, GRAY)
        screen.blit(txt, (self.add_btn_rect.centerx - txt.get_width()//2,
                          self.add_btn_rect.centery - 5))

        # Position the fx_dropdown at the button location
        self.fx_dropdown.move_to(curr_x, curr_y, scale(80), scale(60))

        # D. DRAW DROPDOWNS LAST (so they appear on top of everything)
        self.source_dropdown.draw(screen, self.font)
        self.fx_dropdown.draw(screen, self.font)

        screen.set_clip(old_clip)

    def handle_event(self, event, song, active_idx):
        track = song.tracks[active_idx]
        ui_data = self.ui_instances[active_idx]

        # Handle horizontal scrolling for entire builder view
        if event.type == pygame.MOUSEWHEEL:
            # Check if mouse is over the builder view area
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                # Horizontal scroll with mouse wheel
                scroll_speed = scale(100)
                self.scroll_x = max(0, self.scroll_x - event.y * scroll_speed)
                return

        # Guard: Only route if event has position
        if not hasattr(event, 'pos'):
            return

        # 0. ROUTE TO MODE TOGGLE (highest priority, always visible)
        result = self.mode_toggle_ui.handle_event(event, track)
        if result == "MODE_CHANGED":
            self._sync_ui_instances(track, active_idx)
            return

        # 1. HANDLE SOURCE SELECTOR DROPDOWN (both modes)
        result = self.source_dropdown.handle_event(event)
        if result and result != "TOGGLE":
            # User selected a new source plugin/engine
            if track.mode == "SYNTH":
                if result != track.source_type:
                    track.source_type = result
                    self._sync_ui_instances(track, active_idx)
            else:  # SAMPLER mode
                # Update the active pad's engine
                if result != track.sampler_map[track.active_pad]["engine"]:
                    track.sampler_map[track.active_pad]["engine"] = result
                    self._sync_ui_instances(track, active_idx)
            return

        # 2. ROUTE TO MODE-SPECIFIC PANEL (with collision check)
        if track.mode == "SAMPLER":
            # Check if click is within sampler brain bounds
            if self.sampler_brain_ui.rect.collidepoint(event.pos):
                self.sampler_brain_ui.handle_event(event, track)
                return  # Don't cascade to source if sampler handled it
        else:  # SYNTH mode
            # Check if click is within piano roll settings bounds
            if self.piano_roll_settings_ui.rect.collidepoint(event.pos):
                result = self.piano_roll_settings_ui.handle_event(event, track)
                if result == "SCALE_CHANGED":
                    return

        # 3. ROUTE TO SOURCE (with collision check)
        if ui_data["SOURCE"] and ui_data["SOURCE"].rect.collidepoint(event.pos):
            if track.mode == "SAMPLER":
                class PadProxy: pass
                proxy = PadProxy()
                proxy.source_params = track.sampler_map[track.active_pad]["params"]
                proxy.drum_pads = track.drum_pads
                proxy.source_type = track.sampler_map[track.active_pad]["engine"]
                ui_data["SOURCE"].handle_event(event, proxy)
                track.sampler_map[track.active_pad]["engine"] = proxy.source_type
            else:
                ui_data["SOURCE"].handle_event(event, track)
            return

        # 4. ROUTE TO FX CHAIN (with collision check and DELETE handling)
        for i, fx_ui in enumerate(ui_data["FX"]):
            if fx_ui.rect.collidepoint(event.pos):
                result = fx_ui.handle_event(event, track.effects[i])
                if result == "DELETE":
                    # Remove the effect from the track
                    track.effects.pop(i)
                    # Resync UI to rebuild FX chain
                    self._sync_ui_instances(track, active_idx)
                return

        # 5. HANDLE FX DROPDOWN (Add new effects)
        result = self.fx_dropdown.handle_event(event)
        if result and result != "TOGGLE":
            # User selected an effect type to add
            track.add_effect(result)
            # Resync UI to show the new FX module
            self._sync_ui_instances(track, active_idx)
            return