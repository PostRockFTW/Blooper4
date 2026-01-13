# Blooper4/components/builder_plugins/dual_osc.py
import pygame
import numpy as np
from scipy.signal import butter, lfilter
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, RadioGroup, Dropdown, Knob

# =============================================================================
# 1. THE AUDIO PROCESSOR (Standard 4.1 Dual-Osc)
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        # Map symbols to engine integers
        # Sine:~, Square:|_|, Saw:|/, Triangle:/\, None:X
        self.wave_map = {"~": 0, "|_|": 1, "|/": 2, "/\\": 3, "X": 4}

    def generate_modular(self, params, note, bpm):
        root = params.get("root_note", 60)
        transpose = params.get("transpose", 0)
        gain = params.get("gain", 1.0)
        attack = params.get("attack", 0.01)
        decay = params.get("length", 0.5)
        
        total_dur = attack + decay
        num_samples = int(total_dur * SAMPLE_RATE)
        if num_samples <= 0: return np.zeros(512, dtype=np.float32)
        t = np.linspace(0, total_dur, num_samples, False)

        pitch_multiplier = 2.0 ** ((note.pitch - root + transpose) / 12.0)
        freq1 = 261.63 * pitch_multiplier
        
        interval = params.get("osc2_interval", 0)
        detune_cents = params.get("osc2_detune", 10)
        freq2 = freq1 * (2.0 ** ((interval + (detune_cents/100.0)) / 12.0))

        # Wave Selection
        o1_type = self.wave_map.get(params.get("osc1_type", "|/"), 2)
        o2_type = self.wave_map.get(params.get("osc2_type", "~"), 0)
        mix = params.get("osc_mix", 0.5)

        buf1 = self.bridge.get_buffer(freq1, 1.0 - mix, o1_type, num_samples) if o1_type != 4 else np.zeros(num_samples)
        buf2 = self.bridge.get_buffer(freq2, mix, o2_type, num_samples) if o2_type != 4 else np.zeros(num_samples)
        combined = buf1 + buf2

        # Simple Filter
        cutoff = params.get("filter_cutoff", 5000)
        try:
            nyq = 0.5 * SAMPLE_RATE
            b, a = butter(1, np.clip(cutoff / nyq, 0.01, 0.99), btype='low')
            filtered = lfilter(b, a, combined)
        except: filtered = combined

        # AR Envelope
        env = np.ones(num_samples, dtype=np.float32)
        att_samples = int(attack * SAMPLE_RATE)
        if att_samples > 0:
            env[:att_samples] = np.linspace(0, 1, att_samples)
        decay_t = t[att_samples:] - t[att_samples]
        env[att_samples:] = np.exp(-6 * decay_t / decay)

        return (filtered * env * gain).astype(np.float32)

# =============================================================================
# 2. THE UI COMPONENT (Wide 450px Box)
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 450, 400) 
        self.font = font
        self.plugin_id = "DUAL_OSC"
        self.title = "DUAL OSCILLATOR"
        self.active = True
        
        # Wave Symbols: Sine, Square, Saw, Triangle, None
        self.symbols = ["~", "|_|", "|/", "/\\", "X"]
        
        # 1. Presets
        self.presets = {
            "UNISON LEAD": {"osc1_type":"|/", "osc2_type":"|/", "osc2_interval":0,  "osc2_detune":15, "osc_mix":0.5, "filter_cutoff":8000, "attack":0.01},
            "8-BIT BASS":  {"osc1_type":"/\\", "osc2_type":"|_|", "osc2_interval":-12,"osc2_detune":0,  "osc_mix":0.3, "filter_cutoff":1500, "attack":0.01},
            "POWER LEAD":  {"osc1_type":"|/", "osc2_type":"|/", "osc2_interval":7,  "osc2_detune":5,  "osc_mix":0.4, "filter_cutoff":6000, "attack":0.02},
            "WARM PAD":    {"osc1_type":"~",  "osc2_type":"/\\", "osc2_interval":0,  "osc2_detune":20, "osc_mix":0.6, "filter_cutoff":1200, "attack":0.40},
            "CHURCH ORGAN":{"osc1_type":"|_|", "osc2_type":"|_|", "osc2_interval":12, "osc2_detune":8,  "osc_mix":0.5, "filter_cutoff":3000, "attack":0.08}
        }
        self.preset_drop = Dropdown(0, 0, 410, 30, list(self.presets.keys()), "SELECT PRESET")

        # 2. Controls - Clear column Separation
        # Column 1 (OSC 1)
        self.osc1_sel = RadioGroup(0, 0, self.symbols, font, cols=5)
        # Column 2 (OSC 2)
        self.osc2_sel = RadioGroup(0, 0, self.symbols, font, cols=5)
        
        # Center Sliders
        self.mix_slider = Slider(0, 0, 180, 10, 0, 1.0, 0.5, "OSC MIX")
        self.filter_slider = Slider(0, 0, 180, 10, 50, 12000, 5000, "FILTER")
        
        # Right Side Sliders
        self.interval_slider = Slider(0, 0, 180, 10, -12, 12, 0, "OSC 2 SEMI")
        self.detune_slider = Slider(0, 0, 180, 10, 0, 100, 15, "OSC 2 DETUNE")
        
        # Utility Row
        self.knob_trans = Knob(0, 0, 40, -24, 24, 0, "PITCH")
        self.knob_att =   Knob(0, 0, 40, 0.001, 2.0, 0.01, "ATTACK", is_log=True)
        self.knob_gain =  Knob(0, 0, 40, 0, 2.0, 1.0, "GAIN")
        self.knob_len =   Knob(0, 0, 40, 0.01, 10.0, 0.5, "DECAY", is_log=True)

    def draw(self, screen, track_or_proxy, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        params = track_or_proxy.source_params

        lx, rx = self.rect.x + scale(20), self.rect.x + scale(245)
        
        # 1. Preset Dropdown
        self.preset_drop.move_to(lx, self.rect.y + scale(45), scale(410), scale(30))
        
        # 2. OSC Labels and Symbols
        small_f = pygame.font.SysFont("Consolas", int(10 * UI_SCALE), bold=True)
        screen.blit(small_f.render("OSC 1 TYPE", True, (150,150,150)), (lx, self.rect.y + scale(90)))
        screen.blit(small_f.render("OSC 2 TYPE", True, (150,150,150)), (rx, self.rect.y + scale(90)))
        
        # Wider buttons (42px) to fit symbols cleanly
        self.osc1_sel.move_to(lx, self.rect.y + scale(105), 35, 20)
        self.osc2_sel.move_to(rx, self.rect.y + scale(105), 35, 20)

        # 3. Mixing & Tone (Left Column)
        self.mix_slider.move_to(lx, self.rect.y + scale(165), scale(180), scale(10))
        self.filter_slider.move_to(lx, self.rect.y + scale(215), scale(180), scale(10))

        # 4. Osc 2 Customization (Right Column)
        self.interval_slider.move_to(rx, self.rect.y + scale(165), scale(180), scale(10))
        self.detune_slider.move_to(rx, self.rect.y + scale(215), scale(180), scale(10))

        # 5. Utility Row (Always visible at bottom)
        util_y = self.rect.y + scale(285)
        for i, knob in enumerate([self.knob_trans, self.knob_att, self.knob_gain, self.knob_len]):
            knob.move_to(self.rect.x + scale(45 + i*105), util_y)
            knob.draw(screen, self.font, scale_f)

        # Sync visual state
        self.osc1_sel.selected = params.get("osc1_type", "|/")
        self.osc2_sel.selected = params.get("osc2_type", "~")
        self.mix_slider.val = params.get("osc_mix", 0.5)
        self.filter_slider.val = params.get("filter_cutoff", 5000)
        self.interval_slider.val = params.get("osc2_interval", 0)
        self.detune_slider.val = params.get("osc2_detune", 15)
        
        self.knob_trans.val = params.get("transpose", 0)
        self.knob_att.val = params.get("attack", 0.01)
        self.knob_gain.val = params.get("gain", 1.0)
        self.knob_len.val = params.get("length", 0.5)

        # Final Draw
        self.osc1_sel.draw(screen, self.font)
        self.osc2_sel.draw(screen, self.font)
        self.mix_slider.draw(screen, self.font)
        self.filter_slider.draw(screen, self.font)
        self.interval_slider.draw(screen, self.font)
        self.detune_slider.draw(screen, self.font)
        self.preset_drop.draw(screen, self.font)

    def handle_event(self, event, track_or_proxy):
        params = track_or_proxy.source_params
        
        # 1. Preset Dropdown (With guard fix)
        choice = self.preset_drop.handle_event(event)
        if choice and choice != "TOGGLE":
            if choice in self.presets:
                for k, v in self.presets[choice].items(): params[k] = v
            return
            
        if self.preset_drop.is_open: return

        # 2. Component Event Routing
        if o1 := self.osc1_sel.handle_event(event): params["osc1_type"] = o1
        if o2 := self.osc2_sel.handle_event(event): params["osc2_type"] = o2
        if v := self.mix_slider.handle_event(event): params["osc_mix"] = v
        if v := self.filter_slider.handle_event(event): params["filter_cutoff"] = v
        if v := self.interval_slider.handle_event(event): params["osc2_interval"] = int(v)
        if v := self.detune_slider.handle_event(event): params["osc2_detune"] = v

        if (v := self.knob_trans.handle_event(event)) is not None: params["transpose"] = int(v)
        if (v := self.knob_att.handle_event(event)) is not None: params["attack"] = v
        if (v := self.knob_gain.handle_event(event)) is not None: params["gain"] = v
        if (v := self.knob_len.handle_event(event)) is not None: params["length"] = v

    def global_release(self):
        for s in [self.mix_slider, self.filter_slider, self.interval_slider, self.detune_slider]: s.grabbed = False
        for k in [self.knob_trans, self.knob_att, self.knob_gain, self.knob_len]: k.grabbed = False