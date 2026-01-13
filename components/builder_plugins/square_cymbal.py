# Blooper4/components/builder_plugins/square_cymbal.py
import pygame
import numpy as np
from scipy.signal import butter, lfilter
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, Dropdown, Knob 

class Processor(BaseProcessor):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.cache = {}

    def generate_modular(self, params, note, bpm):
        root = params.get("root_note", 60)
        transpose = params.get("transpose", 0)
        gain = params.get("gain", 1.0)
        decay = params.get("decay", 0.5) 
        
        pitch_multiplier = 2.0 ** ((note.pitch - root + transpose) / 12.0)
        base_freq = params.get("base_freq", 200.0) * pitch_multiplier
        cutoff = params.get("bp_cutoff", 5000.0)

        ratios = [params.get(f"r{i+1}", 1.0 + (i*0.6)) for i in range(6)]

        key = (tuple(ratios), round(base_freq, 1), round(decay, 2), round(cutoff, 0))
        if key in self.cache: return self.cache[key] * gain

        num_s = int(decay * SAMPLE_RATE)
        if num_s <= 0: return np.zeros(512, dtype=np.float32)

        combined_buffer = np.zeros(num_s, dtype=np.float32)
        for r in ratios:
            combined_buffer += self.bridge.get_buffer(base_freq * r, 0.15, 1, num_s)

        try:
            nyq = 0.5 * SAMPLE_RATE
            low, high = max(20, cutoff * 0.8) / nyq, min(nyq * 0.95, cutoff * 1.2) / nyq
            b, a = butter(1, [low, high], btype='band')
            filtered = lfilter(b, a, combined_buffer)
        except:
            filtered = combined_buffer

        t = np.linspace(0, decay, num_s, False)
        env = np.exp(-8 * t / decay)
        final_wave = (filtered * env).astype(np.float32)
        self.cache[key] = final_wave
        return final_wave * gain

class UI(BaseUIElement):
    def __init__(self, x, y, font):
        # EXACT Match to Sampler Brain height (400px)
        super().__init__(x, y, 300, 400) 
        self.font = font
        self.plugin_id = "SQUARE_CYMBAL"
        self.title = "SQUARE CYMBAL"
        self.active = True

        self.presets = {
            "808 COWBELL": {"base_freq": 165, "decay": 0.4, "bp_cutoff": 800,  "r1":1.0, "r2":1.5, "r3":2.1, "r4":2.6, "r5":3.1, "r6":4.3},
            "CLOSED HAT":  {"base_freq": 400, "decay": 0.05,"bp_cutoff": 8000, "r1":1.2, "r2":2.8, "r3":4.1, "r4":5.5, "r5":6.2, "r6":8.0},
            "GONG":        {"base_freq": 60,  "decay": 2.5, "bp_cutoff": 1200, "r1":1.0, "r2":1.1, "r3":1.4, "r4":1.9, "r5":2.4, "r6":3.1},
            "ANVIL":       {"base_freq": 300, "decay": 0.1, "bp_cutoff": 4000, "r1":1.0, "r2":3.0, "r3":3.1, "r4":3.2, "r5":5.0, "r6":5.1}
        }
        self.preset_drop = Dropdown(0, 0, 260, 30, list(self.presets.keys()), "SELECT PRESET")

        # Compact Sliders
        self.freq_slider = Slider(0, 0, 260, 10, 40, 800, 200, "FREQ")
        self.cutoff_slider = Slider(0, 0, 260, 10, 500, 12000, 5000, "BANDPASS")
        
        # Mini Vertical Sliders
        self.ratio_sliders = [Slider(0, 0, 12, 60, 0.5, 8.0, 1.0, "", vertical=True) for _ in range(6)]

        # Utility Knobs
        self.knob_trans = Knob(0, 0, 40, -24, 24, 0, "PITCH")
        self.knob_gain = Knob(0, 0, 40, 0, 2.0, 1.0, "GAIN")
        self.knob_len = Knob(0, 0, 40, 0.01, 10.0, 0.5, "LEN", is_log=True)

    def draw(self, screen, track_or_proxy, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        params = track_or_proxy.source_params

        # --- COMPACT STACK ---
        cx = self.rect.x + scale(20)
        
        # 1. Preset (y=50)
        self.preset_drop.move_to(cx, self.rect.y + scale(45))
        
        # 2. Main Sliders (y=90)
        self.freq_slider.move_to(cx, self.rect.y + scale(100), scale(260), scale(10))
        self.freq_slider.val = params.get("base_freq", 200)
        self.freq_slider.draw(screen, self.font)
        
        self.cutoff_slider.move_to(cx, self.rect.y + scale(140), scale(260), scale(10))
        self.cutoff_slider.val = params.get("bp_cutoff", 5000)
        self.cutoff_slider.draw(screen, self.font)

        # 3. Cluster (y=170-240)
        lbl = self.font.render("RATIOS", True, (150, 150, 150))
        screen.blit(lbl, (cx, self.rect.y + scale(165)))
        for i, s in enumerate(self.ratio_sliders):
            s.move_to(self.rect.x + scale(30 + i*43), self.rect.y + scale(185), scale(12), scale(60))
            s.val = params.get(f"r{i+1}", 1.0 + (i*0.6))
            s.draw(screen, self.font)

        # 4. Utility Row (Always visible at the bottom)
        util_y = self.rect.y + scale(285)
        self.knob_trans.move_to(self.rect.x + scale(40), util_y)
        self.knob_gain.move_to(self.rect.x + scale(120), util_y)
        self.knob_len.move_to(self.rect.x + scale(200), util_y)

        self.knob_trans.val = params.get("transpose", 0)
        self.knob_gain.val = params.get("gain", 1.0)
        self.knob_len.val = params.get("decay", 0.5)

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

        if f := self.freq_slider.handle_event(event): params["base_freq"] = f
        if c := self.cutoff_slider.handle_event(event): params["bp_cutoff"] = c
        for i, s in enumerate(self.ratio_sliders):
            if rv := s.handle_event(event): params[f"r{i+1}"] = rv

        if t := self.knob_trans.handle_event(event): params["transpose"] = int(t)
        if g := self.knob_gain.handle_event(event): params["gain"] = g
        if l := self.knob_len.handle_event(event): params["decay"] = l

    def global_release(self):
        self.freq_slider.grabbed = self.cutoff_slider.grabbed = False
        for s in self.ratio_sliders: s.grabbed = False
        self.knob_trans.grabbed = self.knob_gain.grabbed = self.knob_len.grabbed = False