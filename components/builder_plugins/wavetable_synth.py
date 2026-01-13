# Blooper4/components/builder_plugins/wavetable_synth.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, Dropdown, Knob

# =============================================================================
# 1. THE AUDIO PROCESSOR
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge

    def generate_modular(self, params, note, bpm):
        # 1. Utility Params
        root = params.get("root_note", 60)
        transpose = params.get("transpose", 0)
        gain = params.get("gain", 1.0)
        decay = params.get("decay", 0.5)

        # 2. Pitch Logic
        pitch_multiplier = 2.0 ** ((note.pitch - root + transpose) / 12.0)
        freq = 261.63 * pitch_multiplier

        # 3. Timing
        num_samples = int(decay * SAMPLE_RATE)
        if num_samples <= 0: return np.zeros(512, dtype=np.float32)
        
        # 4. Wavetable Synthesis
        table = np.array(params.get("table", [np.sin(2 * np.pi * i / 32) for i in range(32)]), dtype=np.float32)
        
        # Read table with linear interpolation
        phase_inc = (freq * 32) / SAMPLE_RATE
        phases = (np.arange(num_samples) * phase_inc) % 32
        indices = phases.astype(int)
        next_indices = (indices + 1) % 32
        frac = phases - indices
        
        buffer = (1.0 - frac) * table[indices] + frac * table[next_indices]
        
        # 5. Envelope (Exponential decay matches Length knob)
        t = np.linspace(0, decay, num_samples, False)
        env = np.exp(-6 * t / decay) # Slightly slower decay than drums for melodic use
            
        return buffer * env * gain * 0.5

# =============================================================================
# 2. THE UI COMPONENT
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400) # Standard Height
        self.font = font
        self.plugin_id = "WAVETABLE_SYNTH"
        self.title = "8-BIT WAVETABLE"
        self.active = True
        
        # 1. Historical Chiptune Presets
        self.presets = {
            "SINE (PURE)":   [float(np.sin(2*np.pi*i/32)) for i in range(32)],
            "PULSE 12.5%":   [1.0 if i < 4 else -1.0 for i in range(32)],
            "SAW (BUZZ)":    [float(1.0 - (i/15.5)) for i in range(32)],
            "TRIANGLE":      [float(i/8 - 1 if i < 16 else 1 - (i-16)/8) for i in range(32)],
            "BELL-SINE":     [float(abs(np.sin(2*np.pi*i/32))) for i in range(32)],
            "RESO-STEP":     [float((i//4)/4 * 2 - 1) for i in range(32)],
            "DIGI-HARP":     [float(np.sin(2*np.pi*i/32) * (1 - i/32)) for i in range(32)]
        }
        self.preset_drop = Dropdown(0, 0, 260, 30, list(self.presets.keys()), "SELECT PRESET")

        # 2. The Grid (H=160 to fit within 400px box)
        self.grid_rect = pygame.Rect(0, 0, 260, 160)

        # 3. Standard Utility Row
        self.knob_trans = Knob(0, 0, 40, -24, 24, 0, "PITCH")
        self.knob_gain = Knob(0, 0, 40, 0, 2.0, 1.0, "GAIN")
        self.knob_len = Knob(0, 0, 40, 0.01, 10.0, 0.5, "LEN", is_log=True)

    def draw(self, screen, track_or_proxy, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        params = track_or_proxy.source_params

        # Initialize table if empty
        if "table" not in params:
            params["table"] = self.presets["SINE (PURE)"]

        cx = self.rect.x + scale(20)
        
        # 1. Preset Dropdown
        self.preset_drop.move_to(cx, self.rect.y + scale(45))
        
        # 2. Wavetable Grid
        self.grid_rect = pygame.Rect(cx, self.rect.y + scale(90), scale(260), scale(160))
        pygame.draw.rect(screen, WHITE, self.grid_rect)
        pygame.draw.rect(screen, GRAY, self.grid_rect, 1)
        
        # Center Line
        pygame.draw.line(screen, (220, 220, 220), 
                         (self.grid_rect.x, self.grid_rect.centery), 
                         (self.grid_rect.right, self.grid_rect.centery), 1)

        # Draw current table values
        table = params["table"]
        step_w = self.grid_rect.width / 32
        for i, val in enumerate(table):
            px = self.grid_rect.x + (i * step_w)
            py = self.grid_rect.centery - (val * (self.grid_rect.height / 2))
            
            # Continuous line drawing
            if i > 0:
                prev_py = self.grid_rect.centery - (table[i-1] * (self.grid_rect.height / 2))
                pygame.draw.line(screen, BLACK, (px - step_w, prev_py), (px, py), 2)
            pygame.draw.rect(screen, BLACK, (px-1, py-1, 3, 3))

        # 3. Utility Row
        util_y = self.rect.y + scale(285)
        self.knob_trans.move_to(self.rect.x + scale(40), util_y)
        self.knob_gain.move_to(self.rect.x + scale(120), util_y)
        self.knob_len.move_to(self.rect.x + scale(200), util_y)

        # Sync values
        self.knob_trans.val = params.get("transpose", 0)
        self.knob_gain.val = params.get("gain", 1.0)
        self.knob_len.val = params.get("decay", 0.5)

        self.knob_trans.draw(screen, self.font, scale_f)
        self.knob_gain.draw(screen, self.font, scale_f)
        self.knob_len.draw(screen, self.font, scale_f)
        
        self.preset_drop.draw(screen, self.font)

    def handle_event(self, event, track_or_proxy):
        params = track_or_proxy.source_params
        
        # 1. Preset Dropdown
        choice = self.preset_drop.handle_event(event)
        if choice and choice in self.presets:
            params["table"] = list(self.presets[choice])
            return
            
        if self.preset_drop.is_open: return

        # 2. Grid Interaction (Click and Drag)
        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if self.grid_rect.collidepoint(m_pos):
                rel_x = m_pos[0] - self.grid_rect.x
                idx = int((rel_x / self.grid_rect.width) * 32)
                idx = max(0, min(31, idx))
                
                rel_y = m_pos[1] - self.grid_rect.centery
                val = -rel_y / (self.grid_rect.height / 2)
                params["table"][idx] = float(max(-1.0, min(1.0, val)))

        # 3. Utility Knobs
        if (t := self.knob_trans.handle_event(event)) is not None: params["transpose"] = int(t)
        if (g := self.knob_gain.handle_event(event)) is not None: params["gain"] = g
        if (l := self.knob_len.handle_event(event)) is not None: params["decay"] = l

    def global_release(self):
        self.knob_trans.grabbed = self.knob_gain.grabbed = self.knob_len.grabbed = False