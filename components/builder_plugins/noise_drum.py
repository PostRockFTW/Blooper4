# Blooper4/components/builder_plugins/noise_drum.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, RadioGroup, Dropdown, Knob

# =============================================================================
# 1. THE AUDIO PROCESSOR (Standardized 4.1 Noise Engine)
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge=None):
        super().__init__()
        self.drum_cache = {}

    def _generate_colored_noise(self, num_samples, noise_color):
        white = np.random.uniform(-1, 1, num_samples).astype(np.float32)
        if noise_color == "PINK":
            # Simple 1-pole lowpass to approximate pink noise
            from scipy.signal import butter, lfilter
            b, a = butter(1, 0.1, btype='low') 
            pink = lfilter(b, a, white)
            return (pink / np.max(np.abs(pink))).astype(np.float32) if np.max(np.abs(pink)) > 0 else pink
        elif noise_color == "BROWN":
            brown = np.cumsum(white).astype(np.float32)
            from scipy.signal import butter, lfilter
            b, a = butter(1, 0.001, btype='high') # DC offset removal
            brown = lfilter(b, a, brown)
            return (brown / np.max(np.abs(brown))).astype(np.float32) if np.max(np.abs(brown)) > 0 else brown
        return white

    def generate_modular(self, params, note, bpm):
        # 1. Standard Utility Extraction
        root = params.get("root_note", 60)
        transpose = params.get("transpose", 0)
        gain = params.get("gain", 1.0)
        dur = params.get("length", 0.3)
        
        # 2. Pitch Calculation
        pitch_multiplier = 2.0 ** ((note.pitch - root + transpose) / 12.0)
        base_pitch = params.get("pitch_hpf", 60) # Renamed slider internal key
        pitch_val = base_pitch * pitch_multiplier

        # 3. Core Engine Params
        n_color = params.get("color", "WHITE")
        p_type = params.get("type", "DRUM")
        
        # Cache key (now rounds less to allow for pitch sliding)
        cache_key = (p_type, round(pitch_val, 0), round(dur, 2), n_color)
        if cache_key in self.drum_cache: return self.drum_cache[cache_key] * gain
        
        num_s = int(dur * SAMPLE_RATE)
        if num_s <= 0: return np.zeros(512, dtype=np.float32)
        t = np.linspace(0, dur, num_s, False)
        noise = self._generate_colored_noise(num_s, n_color)

        if p_type == "DRUM":
            # KICK/TOM: Pitch sweep
            f_start, f_end = pitch_val * 4, max(20, pitch_val)
            freq_env = np.geomspace(f_start, f_end, num_s)
            wave = np.sin(2 * np.pi * freq_env * t)
            click_env = np.exp(-150 * t)
            final_wave = (wave * 0.95) + (noise * 0.2 * click_env)
            final_wave *= np.exp(-12 * t / dur)
        elif p_type == "SNARE":
            # SNARE: Snap + Noise
            tone = np.sin(2 * np.pi * pitch_val * t) * np.exp(-40 * t / dur)
            final_wave = (noise * np.exp(-18 * t / dur)) + (tone * 0.5)
        else: # CYMBAL
            from scipy.signal import butter, lfilter
            nyq = 0.5 * SAMPLE_RATE
            # We map the 20-1000 slider to an audible 1kHz - 15kHz High Pass range
            cutoff_freq = np.clip(1000 + (pitch_val * 14), 1000, nyq * 0.95)
            b, a = butter(2, cutoff_freq / nyq, btype='high')
            filtered_noise = lfilter(b, a, noise)
            
            # Gentle envelope for "Ring" (8 instead of 30)
            final_wave = filtered_noise * np.exp(-8 * t / dur)
        
        if np.max(np.abs(final_wave)) > 0:
            final_wave = final_wave / np.max(np.abs(final_wave))

        res = (final_wave).astype(np.float32)
        self.drum_cache[cache_key] = res
        return res * gain

# =============================================================================
# 2. THE UI COMPONENT (Standardized 400px Layout)
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font = font
        self.plugin_id = "NOISE_DRUM"
        self.title = "NOISE DRUM"
        self.active = True
        
        # 1. Pro Drum Presets
        self.presets = {
            "808 KICK":    {"type": "DRUM",  "color": "BROWN", "pitch_hpf": 45,  "length": 0.45, "gain": 1.5},
            "PUNCHY TOM":  {"type": "DRUM",  "color": "PINK",  "pitch_hpf": 120, "length": 0.35, "gain": 1.2},
            "LIGHT SNARE": {"type": "SNARE", "color": "WHITE", "pitch_hpf": 240, "length": 0.15, "gain": 1.0},
            "HEAVY SNARE": {"type": "SNARE", "color": "PINK",  "pitch_hpf": 180, "length": 0.28, "gain": 1.3},
            "HI-HAT":      {"type": "CYMBAL","color": "WHITE", "pitch_hpf": 800, "length": 0.08, "gain": 0.9},
            "CRASH":       {"type": "CYMBAL","color": "WHITE", "pitch_hpf": 300, "length": 1.80, "gain": 1.0},
            "RIDE":        {"type": "CYMBAL","color": "PINK",  "pitch_hpf": 600, "length": 1.20, "gain": 1.1}
        }
        self.preset_drop = Dropdown(0, 0, 260, 30, list(self.presets.keys()), "SELECT PRESET")

        # 2. Core Control Sliders
        self.pitch_slider = Slider(0, 0, 260, 10, 20, 1000, 60, "FREQ / HPF")
        self.color_sel = RadioGroup(0, 0, ["WHITE", "PINK", "BROWN"], font, cols=3)
        self.type_sel = RadioGroup(0, 0, ["DRUM", "SNARE", "CYMBAL"], font, cols=3)
        
        # 3. Standard Utility Knobs
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
        
        # 2. Type and Color Selectors (Stacked)
        self.type_sel.move_to(self.rect.x + scale(12), self.rect.y + scale(90))
        self.color_sel.move_to(self.rect.x + scale(12), self.rect.y + scale(135))
        
        # 3. Main Slider
        self.pitch_slider.move_to(cx, self.rect.y + scale(200), scale(260), scale(10))
        self.pitch_slider.val = params.get("pitch_hpf", 60)
        
        # 4. Utility Row
        util_y = self.rect.y + scale(285)
        self.knob_trans.move_to(self.rect.x + scale(40), util_y)
        self.knob_gain.move_to(self.rect.x + scale(120), util_y)
        self.knob_len.move_to(self.rect.x + scale(200), util_y)

        # Sync visual state
        self.type_sel.selected = params.get("type", "DRUM")
        self.color_sel.selected = params.get("color", "WHITE")
        self.knob_trans.val = params.get("transpose", 0)
        self.knob_gain.val = params.get("gain", 1.0)
        self.knob_len.val = params.get("length", 0.3)

        # Draw
        self.type_sel.draw(screen, self.font)
        self.color_sel.draw(screen, self.font)
        self.pitch_slider.draw(screen, self.font)
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

        if t := self.type_sel.handle_event(event): params["type"] = t
        if c := self.color_sel.handle_event(event): params["color"] = c
        if p := self.pitch_slider.handle_event(event): params["pitch_hpf"] = p

        if (tr := self.knob_trans.handle_event(event)) is not None: params["transpose"] = int(tr)
        if (g := self.knob_gain.handle_event(event)) is not None: params["gain"] = g
        if (l := self.knob_len.handle_event(event)) is not None: params["length"] = l

    def global_release(self):
        self.pitch_slider.grabbed = False
        self.knob_trans.grabbed = self.knob_gain.grabbed = self.knob_len.grabbed = False