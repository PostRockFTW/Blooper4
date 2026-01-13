# Blooper4/components/builder_plugins/fm_drum.py
import pygame
import numpy as np
from constants import *
# Ensure we import our base and standard UI components
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, Dropdown, Knob

# =============================================================================
# 1. THE AUDIO PROCESSOR (Standard 4.1 FM Engine)
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge

    def generate_modular(self, params, note, bpm):
        # 1. Utility Params (Standardized)
        root = params.get("root_note", 60)
        transpose = params.get("transpose", 0)
        gain = params.get("gain", 1.0)
        decay = params.get("length", 0.3) # Using 'decay' name for clarity in math

        # 2. Pitch Logic (Neutral at 100Hz base for drums)
        pitch_multiplier = 2.0 ** ((note.pitch - root + transpose) / 12.0)
        freq = 100.0 * pitch_multiplier

        # 3. FM Core Params
        fm_ratio = params.get("fm_ratio", 3.5)
        fm_depth = params.get("fm_depth", 5.0)
        
        num_s = int(decay * SAMPLE_RATE)
        if num_s <= 0: return np.zeros(512, dtype=np.float32)
        
        t = np.linspace(0, decay, num_s, False)

        # 4. Envelopes
        # FM Depth decay (how long the 'hit' lasts)
        # Higher index = more 'attack' punch
        fm_env = np.exp(-15 * t / decay) * fm_depth
        # Volume decay
        vol_env = np.exp(-8 * t / decay)

        # 5. FM Math
        mod_freq = freq * fm_ratio
        # Modulator oscillator
        modulator = np.sin(2 * np.pi * mod_freq * t) * fm_env
        # Carrier oscillator (modulated by the signal above)
        buffer = np.sin(2 * np.pi * freq * t + modulator) * vol_env

        return buffer.astype(np.float32) * gain

# =============================================================================
# 2. THE UI COMPONENT (Standardized 400px Layout)
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400) # EXACT Sampler Brain height
        self.font = font
        self.plugin_id = "FM_DRUM"
        self.title = "FM PERCUSSION"
        self.active = True
        
        # 1. Classic FM Presets
        self.presets = {
            "SOLID KICK":   {"fm_ratio": 0.5,   "fm_depth": 10.0, "length": 0.15, "gain": 1.2},
            "METALLIC TOM": {"fm_ratio": 1.0,   "fm_depth": 5.0,  "length": 0.40, "gain": 1.0},
            "SEGA BELL":    {"fm_ratio": 1.414, "fm_depth": 40.0, "length": 0.60, "gain": 0.7},
            "ZAP / LASER":  {"fm_ratio": 15.0,  "fm_depth": 50.0, "length": 0.25, "gain": 0.8},
            "SNAPPY SNARE": {"fm_ratio": 12.0,  "fm_depth": 25.0, "length": 0.12, "gain": 1.1},
            "TINY BLIP":    {"fm_ratio": 2.0,   "fm_depth": 2.0,  "length": 0.05, "gain": 1.0}
        }
        self.preset_drop = Dropdown(0, 0, 260, 30, list(self.presets.keys()), "SELECT PRESET")

        # 2. FM Specific Sliders (Compacted)
        self.ratio_slider = Slider(0, 0, 260, 10, 0.1, 20.0, 3.5, "RATIO (TIMBRE)")
        self.depth_slider = Slider(0, 0, 260, 10, 0.0, 50.0, 5.0, "DEPTH (BITE)")
        
        # 3. Standard Utility Knobs (Bottom Row)
        self.knob_trans = Knob(0, 0, 40, -24, 24, 0, "PITCH")
        self.knob_gain = Knob(0, 0, 40, 0, 2.0, 1.0, "GAIN")
        self.knob_len = Knob(0, 0, 40, 0.01, 10.0, 0.5, "LEN", is_log=True)

    def draw(self, screen, track_or_proxy, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        params = track_or_proxy.source_params

        cx = self.rect.x + scale(20)
        
        # 1. Preset Dropdown (y=45)
        self.preset_drop.move_to(cx, self.rect.y + scale(45))
        
        # 2. FM Sliders (y=100 - 180)
        self.ratio_slider.move_to(cx, self.rect.y + scale(110), scale(260), scale(10))
        self.ratio_slider.val = params.get("fm_ratio", 3.5)
        self.ratio_slider.draw(screen, self.font)
        
        self.depth_slider.move_to(cx, self.rect.y + scale(160), scale(260), scale(10))
        self.depth_slider.val = params.get("fm_depth", 5.0)
        self.depth_slider.draw(screen, self.font)

        # 3. Utility Knobs (Standardized bottom position)
        util_y = self.rect.y + scale(285)
        self.knob_trans.move_to(self.rect.x + scale(40), util_y)
        self.knob_gain.move_to(self.rect.x + scale(120), util_y)
        self.knob_len.move_to(self.rect.x + scale(200), util_y)

        # Sync and render knobs
        self.knob_trans.val = params.get("transpose", 0)
        self.knob_gain.val = params.get("gain", 1.0)
        self.knob_len.val = params.get("length", 0.3)

        self.knob_trans.draw(screen, self.font, scale_f)
        self.knob_gain.draw(screen, self.font, scale_f)
        self.knob_len.draw(screen, self.font, scale_f)
        
        # Dropdown on top
        self.preset_drop.draw(screen, self.font)

    def handle_event(self, event, track_or_proxy):
        params = track_or_proxy.source_params
        
        # 1. Handle Presets
        choice = self.preset_drop.handle_event(event)
        if choice and choice in self.presets:
            for k, v in self.presets[choice].items():
                params[k] = v
            return
            
        if self.preset_drop.is_open: return

        # 2. FM Sliders
        if (r := self.ratio_slider.handle_event(event)) is not None: params["fm_ratio"] = r
        if (d := self.depth_slider.handle_event(event)) is not None: params["fm_depth"] = d

        # 3. Standard Utility Knobs
        if (t := self.knob_trans.handle_event(event)) is not None: params["transpose"] = int(t)
        if (g := self.knob_gain.handle_event(event)) is not None: params["gain"] = g
        if (l := self.knob_len.handle_event(event)) is not None: params["length"] = l

    def global_release(self):
        self.ratio_slider.grabbed = self.depth_slider.grabbed = False
        self.knob_trans.grabbed = self.knob_gain.grabbed = self.knob_len.grabbed = False