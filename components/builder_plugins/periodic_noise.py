# Blooper4/components/builder_plugins/periodic_noise.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, RadioGroup, Dropdown, Knob

# =============================================================================
# 1. THE AUDIO PROCESSOR (Standardized 4.1 Periodic Noise)
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge

    def generate_modular(self, params, note, bpm):
        # 1. Standard Utility Extraction
        root = params.get("root_note", 60)
        transpose = params.get("transpose", 0)
        gain = params.get("gain", 1.0)
        dur = params.get("length", 0.3)
        
        # 2. NES Pitch Logic (Divisor-based)
        # Shift rate scales inversely with pitch (Higher pitch = faster shifts)
        pitch_multiplier = 2.0 ** ((note.pitch - root + transpose) / 12.0)
        base_rate = params.get("sample_rate_div", 4)
        effective_rate = max(1, int(base_rate / pitch_multiplier))

        num_samples = int(dur * SAMPLE_RATE)
        if num_samples <= 0: return np.zeros(512, dtype=np.float32)
        
        # 3. LFSR Emulation
        mode = params.get("noise_mode", "STATIC")
        period = 93 if mode == "METALLIC" else 32767
        
        # Create the 'locked' random sequence for this trigger
        seed_sequence = np.random.uniform(-1, 1, period).astype(np.float32)
        buffer = np.zeros(num_samples, dtype=np.float32)
        
        # Step through bits at the effective hardware rate
        for i in range(num_samples):
            seq_idx = (i // effective_rate) % period
            buffer[i] = seed_sequence[seq_idx]

        # 4. Decay Envelope
        t = np.linspace(0, dur, num_samples, False)
        env = np.exp(-10 * t / dur)
        
        return (buffer * env * gain).astype(np.float32)

# =============================================================================
# 2. THE UI COMPONENT (Standardized 400px Layout)
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400) # EXACT Sampler Brain height
        self.font = font
        self.plugin_id = "PERIODIC_NOISE"
        self.title = "PERIODIC NOISE"
        self.active = True
        
        # 1. Authentic NES Presets
        self.presets = {
            "8-BIT HI-HAT": {"noise_mode": "STATIC",   "sample_rate_div": 2,  "length": 0.06, "gain": 0.8},
            "NES EXPLOSION": {"noise_mode": "STATIC",   "sample_rate_div": 16, "length": 1.20, "gain": 1.4},
            "ROBO-SNARE":   {"noise_mode": "METALLIC", "sample_rate_div": 8,  "length": 0.15, "gain": 1.0},
            "PITCHED ZAP":  {"noise_mode": "METALLIC", "sample_rate_div": 4,  "length": 0.40, "gain": 0.9}
        }
        self.preset_drop = Dropdown(0, 0, 260, 30, list(self.presets.keys()), "SELECT PRESET")

        # 2. Core Controls
        self.mode_sel = RadioGroup(0, 0, ["STATIC", "METALLIC"], font, cols=2)
        self.rate_slider = Slider(0, 0, 260, 10, 1, 32, 4, "DIVISOR (TIMBRE)")
        
        # 3. Standard Utility Row
        self.knob_trans = Knob(0, 0, 40, -24, 24, 0, "PITCH")
        self.knob_gain = Knob(0, 0, 40, 0, 2.0, 1.0, "GAIN")
        self.knob_len = Knob(0, 0, 40, 0.01, 10.0, 0.3, "LEN", is_log=True)

    def draw(self, screen, track_or_proxy, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        params = track_or_proxy.source_params
        
        cx = self.rect.x + scale(20)
        
        # 1. Preset Dropdown
        self.preset_drop.move_to(cx, self.rect.y + scale(45))
        
        # 2. Mode Selector
        self.mode_sel.move_to(self.rect.x + scale(15), self.rect.y + scale(90))
        
        # 3. Rate Slider
        self.rate_slider.move_to(cx, self.rect.y + scale(180), scale(260), scale(10))
        self.rate_slider.val = params.get("sample_rate_div", 4)
        
        # 4. Utility Row (Standard position)
        util_y = self.rect.y + scale(285)
        self.knob_trans.move_to(self.rect.x + scale(40), util_y)
        self.knob_gain.move_to(self.rect.x + scale(120), util_y)
        self.knob_len.move_to(self.rect.x + scale(200), util_y)

        # Sync
        self.mode_sel.selected = params.get("noise_mode", "STATIC")
        self.knob_trans.val = params.get("transpose", 0)
        self.knob_gain.val = params.get("gain", 1.0)
        self.knob_len.val = params.get("length", 0.3)

        # Render
        self.mode_sel.draw(screen, self.font)
        self.rate_slider.draw(screen, self.font)
        self.knob_trans.draw(screen, self.font, scale_f)
        self.knob_gain.draw(screen, self.font, scale_f)
        self.knob_len.draw(screen, self.font, scale_f)
        
        self.preset_drop.draw(screen, self.font)

    def handle_event(self, event, track_or_proxy):
        params = track_or_proxy.source_params
        
        choice = self.preset_drop.handle_event(event)
        if choice and choice in self.presets:
            for k, v in self.presets[choice].items(): params[k] = v
            return
            
        if self.preset_drop.is_open: return

        if m := self.mode_sel.handle_event(event): params["noise_mode"] = m
        if r := self.rate_slider.handle_event(event): params["sample_rate_div"] = r

        if (tr := self.knob_trans.handle_event(event)) is not None: params["transpose"] = int(tr)
        if (g := self.knob_gain.handle_event(event)) is not None: params["gain"] = g
        if (l := self.knob_len.handle_event(event)) is not None: params["length"] = l

    def global_release(self):
        self.rate_slider.grabbed = False
        self.knob_trans.grabbed = self.knob_gain.grabbed = self.knob_len.grabbed = False